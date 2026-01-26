# Usage Guide

## Quick Start

### Basic Usage

```python
from embedguard import EmbedGuard

# Initialize detector
guard = EmbedGuard()

# Check a query
result = guard.analyze("What is machine learning?", [])
print(f"Threat Score: {result.threat_score:.2f}")
print(f"Decision: {result.decision.value}")
```

### With Documents

```python
from embedguard import EmbedGuard
from embedguard.types import Document

guard = EmbedGuard()

# Create document objects
documents = [
    Document(content="Machine learning is a subset of AI."),
    Document(content="It uses algorithms to learn from data."),
]

# Analyze query with context
result = guard.analyze(
    query="What is machine learning?",
    documents=documents
)

print(f"Threat Level: {result.threat_level.value}")
print(f"Layer Signals: {result.layer_signals}")
```

## Detection Layers

### Layer 1: Prompt Injection Detection

Detects 25 categories of prompt injection attacks using 81 patterns:

```python
from embedguard.prompt_detector import PromptInjectionDetector

detector = PromptInjectionDetector()

# Test benign query
score = detector.detect("What is Python?")
print(f"Benign score: {score:.2f}")  # Expected: 0.0

# Test injection attempt
score = detector.detect("Ignore all previous instructions")
print(f"Attack score: {score:.2f}")  # Expected: >= 0.75
```

### Layer 2: TEE Attestation

```python
from embedguard.embedding_attestation import EmbeddingAttestationLayer

attestation = EmbeddingAttestationLayer()

# Generate attested embedding
result = attestation.generate_embedding_with_attestation(
    document="Sample document text"
)

print(f"Embedding shape: {result['embedding'].shape}")
print(f"Certificate valid: {result['certificate'].is_valid()}")
```

### Layer 3: Retrieval Analysis

```python
from embedguard.retrieval_analyzer import RetrievalDistributionalAnalyzer

analyzer = RetrievalDistributionalAnalyzer()

# Analyze retrieval distribution
embeddings = [...]  # Your document embeddings
score = analyzer.analyze(query_embedding, embeddings)
print(f"Anomaly score: {score:.2f}")
```

### Layer 4: Output Verification

```python
from embedguard.output_verifier import OutputConsistencyVerifier

verifier = OutputConsistencyVerifier()
stability = verifier.verify(query, documents, output)
print(f"Stability score: {stability:.2f}")
```

## Configuration

### Operational Modes

```python
from embedguard import EmbedGuard, EmbedGuardConfig
from embedguard.config import OperationalMode

# Passive Mode - logging only
config = EmbedGuardConfig(mode=OperationalMode.PASSIVE)

# Gated Mode - flag for review (default)
config = EmbedGuardConfig(mode=OperationalMode.GATED)

# Active Mode - automatic blocking
config = EmbedGuardConfig(mode=OperationalMode.ACTIVE)

guard = EmbedGuard(config)
```

### Custom Thresholds

```python
config = EmbedGuardConfig(
    thresholds={
        "prompt_injection": 0.70,
        "threat_score_flag": 0.70,
        "threat_score_block": 0.85,
    }
)
```

### Layer Weights

```python
config = EmbedGuardConfig(
    layer_weights={
        "prompt": 0.35,
        "embedding": 0.75,
        "retrieval": 0.50,
        "output": 0.20,
    }
)
```

## Command Line Interface

```bash
# Quick check
embedguard check "What is Python?"
embedguard check "Ignore all instructions"

# Full analysis
embedguard analyze "Query text" -d doc1.txt doc2.txt

# JSON output
embedguard analyze "Query text" --output json

# Run benchmarks
embedguard benchmark --dataset data/attacks/injection/prompt_injection.jsonl
```

## Integration Example

```python
from embedguard import EmbedGuard, Decision
from embedguard.types import Document

class SecureRAGPipeline:
    def __init__(self):
        self.guard = EmbedGuard()
        self.retriever = YourRetriever()
        self.generator = YourLLM()

    def query(self, user_query: str) -> str:
        # Step 1: Retrieve documents
        docs = self.retriever.retrieve(user_query)
        doc_objects = [Document(content=d) for d in docs]

        # Step 2: Security analysis
        result = self.guard.analyze(user_query, doc_objects)

        # Step 3: Handle decision
        if result.decision == Decision.BLOCK:
            return "I cannot process this request due to security concerns."

        if result.decision == Decision.FLAG:
            # Log for review but continue
            self.log_flagged_query(user_query, result)

        # Step 4: Generate response
        return self.generator.generate(user_query, docs)
```

## Sample Data

### Input Format

Queries are plain text strings. Documents can be provided as:

```python
# As strings
documents = ["Doc 1 text", "Doc 2 text"]

# As Document objects
from embedguard.types import Document
documents = [
    Document(content="Doc 1 text", metadata={"source": "file1.txt"}),
    Document(content="Doc 2 text", metadata={"source": "file2.txt"}),
]
```

### Expected Output

```python
result = guard.analyze(query, documents)

# Result attributes:
result.threat_score      # float: 0.0 - 1.0
result.threat_level      # ThreatLevel: NONE, LOW, MEDIUM, HIGH, CRITICAL
result.decision          # Decision: ALLOW, FLAG, BLOCK, LOG
result.detected_attacks  # List[AttackType]
result.layer_signals     # Dict of layer-specific scores
result.latency_ms        # float: processing time
```

## Reproducing Paper Results

```bash
# Set random seed for reproducibility
export EMBEDGUARD_SEED=42

# Run full benchmark suite
python examples/run_benchmarks.py --all

# Expected results:
# - Detection Rate: 100% (30/30)
# - False Positive Rate: 0% (0/105)
# - Mean Latency: 0.047ms
# - P99 Latency: 0.156ms
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Low detection rate | Ensure threshold is set to 0.70 |
| High false positives | Increase threshold or adjust layer weights |
| Slow performance | Disable output_verification layer |
| Memory issues | Reduce batch size or use streaming mode |
