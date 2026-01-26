"""
Utility functions for EmbedGuard.

This module provides shared utilities including:
- Embedding generation
- Hashing functions
- Timing utilities
- Data validation
"""

import hashlib
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar, Union

import numpy as np
from loguru import logger

T = TypeVar("T")


# =============================================================================
# Timing Utilities
# =============================================================================


@contextmanager
def timer(name: str = "Operation") -> Generator[Dict[str, float], None, None]:
    """Context manager for timing operations.

    Example:
        >>> with timer("Embedding generation") as t:
        ...     embeddings = model.encode(texts)
        >>> print(f"Took {t['elapsed_ms']:.2f}ms")
    """
    result = {"elapsed_ms": 0.0, "elapsed_s": 0.0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        elapsed = time.perf_counter() - start
        result["elapsed_s"] = elapsed
        result["elapsed_ms"] = elapsed * 1000


def timed(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for timing function execution.

    Example:
        >>> @timed
        ... def slow_function():
        ...     time.sleep(0.1)
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"{func.__name__} took {elapsed:.2f}ms")
        return result
    return wrapper


# =============================================================================
# Hashing Utilities
# =============================================================================


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content.

    Args:
        content: String content to hash

    Returns:
        Hex-encoded SHA-256 hash
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_embedding_hash(embedding: Union[List[float], np.ndarray]) -> str:
    """Compute hash of embedding vector.

    Args:
        embedding: Embedding vector

    Returns:
        Hex-encoded hash
    """
    arr = np.array(embedding, dtype=np.float32)
    return hashlib.sha256(arr.tobytes()).hexdigest()


def compute_batch_hash(items: List[str]) -> str:
    """Compute hash of multiple items.

    Args:
        items: List of strings to hash

    Returns:
        Combined hash
    """
    combined = "|".join(sorted(items))
    return compute_content_hash(combined)


# =============================================================================
# Embedding Utilities
# =============================================================================


class EmbeddingCache:
    """Simple LRU cache for embeddings.

    Avoids recomputing embeddings for frequently seen documents.
    """

    def __init__(self, max_size: int = 1000):
        """Initialize cache.

        Args:
            max_size: Maximum number of embeddings to cache
        """
        self.max_size = max_size
        self._cache: Dict[str, np.ndarray] = {}
        self._access_order: List[str] = []

    def get(self, key: str) -> Optional[np.ndarray]:
        """Get embedding from cache.

        Args:
            key: Cache key (typically content hash)

        Returns:
            Cached embedding or None
        """
        if key in self._cache:
            # Update access order
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None

    def put(self, key: str, embedding: np.ndarray) -> None:
        """Add embedding to cache.

        Args:
            key: Cache key
            embedding: Embedding vector
        """
        if key in self._cache:
            self._access_order.remove(key)
        elif len(self._cache) >= self.max_size:
            # Evict least recently used
            lru_key = self._access_order.pop(0)
            del self._cache[lru_key]

        self._cache[key] = embedding
        self._access_order.append(key)

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._access_order.clear()

    @property
    def size(self) -> int:
        """Current cache size."""
        return len(self._cache)


class EmbeddingGenerator:
    """Utility for generating embeddings with caching.

    Example:
        >>> generator = EmbeddingGenerator()
        >>> embedding = generator.encode("Hello world")
        >>> embeddings = generator.encode_batch(["Hello", "World"])
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        device: str = "cpu",
        cache_size: int = 1000,
        use_cache: bool = True,
    ):
        """Initialize generator.

        Args:
            model_name: Sentence transformer model name
            device: Device for inference
            cache_size: Maximum cache size
            use_cache: Whether to use caching
        """
        self.model_name = model_name
        self.device = device
        self.use_cache = use_cache
        self._model = None
        self._cache = EmbeddingCache(max_size=cache_size) if use_cache else None

    def _get_model(self):
        """Lazily load embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(
                    self.model_name, device=self.device
                )
                logger.debug(f"Loaded embedding model: {self.model_name}")
            except ImportError:
                logger.warning("sentence-transformers not available")
        return self._model

    def encode(self, text: str) -> Optional[np.ndarray]:
        """Encode a single text to embedding.

        Args:
            text: Text to encode

        Returns:
            Embedding vector or None if model unavailable
        """
        # Check cache
        if self._cache is not None:
            cache_key = compute_content_hash(text)
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        # Generate embedding
        model = self._get_model()
        if model is None:
            return None

        embedding = model.encode(text, convert_to_numpy=True)

        # Cache result
        if self._cache is not None:
            self._cache.put(cache_key, embedding)

        return embedding

    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
    ) -> List[Optional[np.ndarray]]:
        """Encode multiple texts to embeddings.

        Args:
            texts: List of texts
            batch_size: Batch size for encoding

        Returns:
            List of embeddings (None for failures)
        """
        model = self._get_model()
        if model is None:
            return [None] * len(texts)

        # Check cache for each text
        results = [None] * len(texts)
        to_encode = []
        to_encode_indices = []

        for i, text in enumerate(texts):
            if self._cache is not None:
                cache_key = compute_content_hash(text)
                cached = self._cache.get(cache_key)
                if cached is not None:
                    results[i] = cached
                    continue

            to_encode.append(text)
            to_encode_indices.append(i)

        # Encode uncached texts
        if to_encode:
            embeddings = model.encode(
                to_encode,
                convert_to_numpy=True,
                batch_size=batch_size,
            )

            for text, idx, emb in zip(to_encode, to_encode_indices, embeddings):
                results[idx] = emb
                if self._cache is not None:
                    cache_key = compute_content_hash(text)
                    self._cache.put(cache_key, emb)

        return results


# =============================================================================
# Validation Utilities
# =============================================================================


def validate_embedding_dimension(
    embedding: Union[List[float], np.ndarray],
    expected_dim: int = 768,
) -> bool:
    """Validate embedding has expected dimension.

    Args:
        embedding: Embedding vector
        expected_dim: Expected dimension

    Returns:
        True if valid
    """
    arr = np.array(embedding)
    return arr.shape == (expected_dim,)


def validate_document_content(
    content: str,
    min_length: int = 10,
    max_length: int = 100000,
) -> bool:
    """Validate document content.

    Args:
        content: Document content
        min_length: Minimum length
        max_length: Maximum length

    Returns:
        True if valid
    """
    if not isinstance(content, str):
        return False
    length = len(content)
    return min_length <= length <= max_length


def normalize_embedding(
    embedding: Union[List[float], np.ndarray]
) -> np.ndarray:
    """Normalize embedding to unit length.

    Args:
        embedding: Embedding vector

    Returns:
        Normalized embedding
    """
    arr = np.array(embedding, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm > 0:
        return arr / norm
    return arr


def cosine_similarity(
    a: Union[List[float], np.ndarray],
    b: Union[List[float], np.ndarray],
) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        Cosine similarity (-1 to 1)
    """
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


# =============================================================================
# Statistical Utilities
# =============================================================================


def compute_statistics(values: List[float]) -> Dict[str, float]:
    """Compute basic statistics for a list of values.

    Args:
        values: List of numeric values

    Returns:
        Dictionary with mean, std, min, max, median
    """
    if not values:
        return {
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "median": 0.0,
        }

    arr = np.array(values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr)),
    }


def moving_average(
    values: List[float],
    window_size: int = 10,
) -> List[float]:
    """Compute moving average.

    Args:
        values: List of values
        window_size: Window size for averaging

    Returns:
        List of moving averages
    """
    if len(values) < window_size:
        return [np.mean(values)] * len(values)

    result = []
    for i in range(len(values)):
        start = max(0, i - window_size + 1)
        result.append(np.mean(values[start:i + 1]))

    return result
