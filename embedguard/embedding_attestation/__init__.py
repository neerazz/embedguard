"""Layer 2 software provenance simulator.

This module binds document, model, and embedding hashes with HMAC for development
and certificate-plumbing tests. It does not obtain or validate hardware attestation.
"""

import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from embedguard.types import AttestationResult, Document


@dataclass
class AttestationCertificate:
    """Cryptographic attestation certificate for an embedding.

    Attributes:
        document_hash: SHA-256 hash of the source document
        model_hash: Hash of the embedding model weights
        embedding_hash: Hash of the output embedding vector
        timestamp: Certificate generation timestamp
        validity_period: Certificate validity duration
        signature: Cryptographic signature binding all fields
        pcr_values: Legacy field for optional simulated platform metadata;
            not real TEE evidence
    """

    document_hash: str
    model_hash: str
    embedding_hash: str
    timestamp: str
    validity_period: int  # seconds
    signature: str
    pcr_values: Optional[Dict[str, str]] = None

    def is_expired(self) -> bool:
        """Check if certificate has expired."""
        if (
            not isinstance(self.validity_period, int)
            or isinstance(self.validity_period, bool)
            or self.validity_period <= 0
        ):
            return True
        try:
            cert_time = datetime.fromisoformat(self.timestamp)
        except (TypeError, ValueError):
            return True
        if cert_time.tzinfo is None:
            cert_time = cert_time.replace(tzinfo=timezone.utc)
        try:
            expiry = cert_time + timedelta(seconds=self.validity_period)
        except OverflowError:
            return True
        return datetime.now(timezone.utc) > expiry

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_hash": self.document_hash,
            "model_hash": self.model_hash,
            "embedding_hash": self.embedding_hash,
            "timestamp": self.timestamp,
            "validity_period": self.validity_period,
            "signature": self.signature,
            "pcr_values": self.pcr_values,
        }


class EmbeddingAttestationLayer:
    """Software HMAC simulator for embedding provenance certificates.

    This development implementation binds document, model, and embedding hashes.
    It does not generate or verify TEE evidence, even when ``tee_available`` is
    true; that compatibility flag only adds simulated platform metadata.

    Attributes:
        model_name: Name of the embedding model
        device: Device for embedding generation
        secret_key: Key for signing simulated certificates
        validity_period: Certificate validity in seconds

    Example:
        >>> attestation = EmbeddingAttestationLayer()
        >>> cert = attestation.generate_attestation(document, embedding)
        >>> is_valid = attestation.verify_attestation(document, embedding, cert)
    """

    # Simulated model hash (in production, computed from actual model weights)
    MODEL_HASH = "sha256:a1b2c3d4e5f6789012345678901234567890abcdef"

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        device: str = "cpu",
        secret_key: Optional[bytes] = None,
        validity_period: int = 86400,  # 24 hours
        tee_available: bool = False,
    ):
        """Initialize attestation layer.

        Args:
            model_name: Embedding model name
            device: Device for inference
            secret_key: HMAC key for signing (auto-generated if None)
            validity_period: Certificate validity in seconds
            tee_available: Whether to include simulated platform metadata;
                this does not enable hardware attestation
        """
        self.model_name = model_name
        self.device = device
        if (
            not isinstance(validity_period, int)
            or isinstance(validity_period, bool)
            or validity_period <= 0
        ):
            raise ValueError("validity_period must be a positive integer")
        self.validity_period = validity_period
        self.tee_available = tee_available

        # The simulator uses an ephemeral key unless the caller supplies one.
        self.secret_key = secret_key or self._generate_secret_key()

        # Load embedding model lazily
        self._embedding_model = None

        logger.debug(
            f"EmbeddingAttestationLayer initialized (tee={tee_available})"
        )

    def _generate_secret_key(self) -> bytes:
        """Generate an ephemeral development key for HMAC signing.

        Callers that need certificates to survive process restarts must provide
        ``secret_key`` explicitly and manage it outside this simulator.
        """
        logger.debug("Generated ephemeral HMAC provenance key")
        return secrets.token_bytes(32)

    def _get_embedding_model(self):
        """Lazily load embedding model."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(
                    self.model_name, device=self.device
                )
                logger.debug("Embedding model loaded")
            except ImportError:
                logger.warning("sentence-transformers not available")
                self._embedding_model = None
        return self._embedding_model

    def _compute_document_hash(self, content: str) -> str:
        """Compute SHA-256 hash of document content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _compute_embedding_hash(self, embedding: List[float]) -> str:
        """Compute hash of embedding vector."""
        # Convert to bytes and hash
        arr = np.array(embedding, dtype=np.float32)
        return hashlib.sha256(arr.tobytes()).hexdigest()

    def _sign_certificate(self, data: str) -> str:
        """Sign certificate data with secret key."""
        signature = hmac.new(
            self.secret_key,
            data.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    @staticmethod
    def _certificate_payload(
        document_hash: str,
        model_hash: str,
        embedding_hash: str,
        timestamp: str,
        validity_period: int,
        pcr_values: Optional[Dict[str, str]],
    ) -> str:
        """Serialize every mutable certificate field into the signed payload."""
        return json.dumps(
            {
                "document_hash": document_hash,
                "embedding_hash": embedding_hash,
                "model_hash": model_hash,
                "pcr_values": pcr_values,
                "timestamp": timestamp,
                "validity_period": validity_period,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def _verify_signature(self, data: str, signature: str) -> bool:
        """Verify signature."""
        expected = self._sign_certificate(data)
        return hmac.compare_digest(expected, signature)

    def generate_embedding_with_attestation(
        self, document: str
    ) -> Tuple[List[float], AttestationCertificate]:
        """Generate an embedding and a software HMAC provenance certificate.

        This method does not execute inside a TEE and does not produce a hardware
        attestation report.

        Args:
            document: Document content to embed

        Returns:
            Tuple of (embedding vector, attestation certificate)
        """
        # Generate embedding
        model = self._get_embedding_model()
        if model is None:
            raise RuntimeError(
                "No embedding model is available; refusing to attest a random vector"
            )
        embedding = model.encode(document, convert_to_numpy=True).tolist()

        # Create attestation certificate
        document_hash = self._compute_document_hash(document)
        embedding_hash = self._compute_embedding_hash(embedding)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Legacy compatibility metadata only; not an attestation report.
        pcr_values = {
            "simulated_firmware": hashlib.sha256(b"firmware").hexdigest()[:16],
            "simulated_boot_state": hashlib.sha256(b"secureboot").hexdigest()[:16],
        } if self.tee_available else None

        # Bind every mutable field that verification or callers can observe.
        sign_data = self._certificate_payload(
            document_hash,
            self.MODEL_HASH,
            embedding_hash,
            timestamp,
            self.validity_period,
            pcr_values,
        )
        signature = self._sign_certificate(sign_data)

        certificate = AttestationCertificate(
            document_hash=document_hash,
            model_hash=self.MODEL_HASH,
            embedding_hash=embedding_hash,
            timestamp=timestamp,
            validity_period=self.validity_period,
            signature=signature,
            pcr_values=pcr_values,
        )

        return embedding, certificate

    def verify_attestation(
        self,
        document: str,
        embedding: List[float],
        certificate: AttestationCertificate,
    ) -> AttestationResult:
        """Verify embedding attestation certificate.

        Args:
            document: Original document content
            embedding: Embedding vector to verify
            certificate: Attestation certificate

        Returns:
            AttestationResult with verification status
        """
        errors = []

        # Check expiration
        if certificate.is_expired():
            errors.append("Certificate expired")

        # Verify document hash
        doc_hash = self._compute_document_hash(document)
        if doc_hash != certificate.document_hash:
            errors.append("Document hash mismatch")

        # Verify embedding hash
        emb_hash = self._compute_embedding_hash(embedding)
        if emb_hash != certificate.embedding_hash:
            errors.append("Embedding hash mismatch")

        # Verify model hash
        if certificate.model_hash != self.MODEL_HASH:
            errors.append("Model hash mismatch")

        # Verify signature
        try:
            sign_data = self._certificate_payload(
                certificate.document_hash,
                certificate.model_hash,
                certificate.embedding_hash,
                certificate.timestamp,
                certificate.validity_period,
                certificate.pcr_values,
            )
            if not self._verify_signature(sign_data, certificate.signature):
                errors.append("Invalid signature")
        except (TypeError, ValueError):
            errors.append("Malformed certificate payload")

        is_valid = len(errors) == 0

        return AttestationResult(
            is_valid=is_valid,
            document_hash=certificate.document_hash,
            model_hash=certificate.model_hash,
            timestamp=certificate.timestamp,
            signature=certificate.signature,
            error="; ".join(errors) if errors else None,
        )

    def verify_batch(
        self, documents: List[Document]
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Verify attestation for a batch of documents.

        Documents without attestation certificates are flagged as unverified.

        Args:
            documents: List of Document objects

        Returns:
            Tuple of (score, confidence, details) where:
                - score: 0.0 to 1.0, higher = more unverified documents
                - confidence: 0.0 to 1.0
                - details: Verification details
        """
        if not documents:
            return 0.0, 0.0, {"error": "No documents provided"}

        verified_count = 0
        unverified_count = 0
        failed_count = 0
        results = []

        for doc in documents:
            if doc.attestation is None:
                # No attestation - count as unverified
                unverified_count += 1
                results.append({"doc_id": doc.document_id, "status": "unverified"})
            else:
                # Has attestation - verify it
                if doc.embedding is not None:
                    result = self.verify_attestation(
                        doc.content, doc.embedding,
                        AttestationCertificate(**doc.attestation.__dict__)
                        if hasattr(doc.attestation, '__dict__')
                        else doc.attestation
                    )
                    if result.is_valid:
                        verified_count += 1
                        results.append({"doc_id": doc.document_id, "status": "verified"})
                    else:
                        failed_count += 1
                        results.append({
                            "doc_id": doc.document_id,
                            "status": "failed",
                            "error": result.error,
                        })
                else:
                    unverified_count += 1
                    results.append({"doc_id": doc.document_id, "status": "no_embedding"})

        total = len(documents)
        # Score: proportion of unverified/failed documents
        score = (unverified_count + failed_count) / total
        # Confidence: higher if we have clear results
        confidence = verified_count / total if verified_count > 0 else 0.5

        details = {
            "total_documents": total,
            "verified": verified_count,
            "unverified": unverified_count,
            "failed": failed_count,
            "results": results,
        }

        return score, confidence, details


# Convenience function for creating attested embeddings
def create_attested_embedding(
    document: str,
    model_name: str = "sentence-transformers/all-mpnet-base-v2",
) -> Tuple[List[float], Dict[str, Any]]:
    """Create an embedding with attestation certificate.

    Args:
        document: Document content
        model_name: Embedding model name

    Returns:
        Tuple of (embedding, certificate_dict)
    """
    layer = EmbeddingAttestationLayer(model_name=model_name)
    embedding, cert = layer.generate_embedding_with_attestation(document)
    return embedding, cert.to_dict()
