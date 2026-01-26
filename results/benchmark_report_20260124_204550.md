# EmbedGuard Benchmark Results

**Generated:** 2026-01-24T20:45:50.832232
**Detector:** PatternBasedDetector (81 patterns)
**Threshold:** 0.70

---

## Prompt Injection Detection

### Performance Metrics

| Metric | Value |
|--------|-------|
| Detection Rate (Recall) | 100.0% |
| Precision | 100.0% |
| F1 Score | 1.000 |
| False Positive Rate | 0.0% |
| Accuracy | 100.0% |

### Confusion Matrix

- True Positives: 30
- False Positives: 0
- True Negatives: 5
- False Negatives: 0

### Latency

- Mean: 0.09ms
- Median: 0.09ms
- P95: 0.13ms
- P99: 0.14ms

### Detection by Attack Type

| Attack Type | Detection Rate | Count |
|-------------|----------------|-------|
| authority_claim | 100.0% | 1/1 |
| base64_encoding | 100.0% | 1/1 |
| benign_query | 0.0% | 0/5 |
| composite_attack | 100.0% | 2/2 |
| context_manipulation | 100.0% | 1/1 |
| delimiter_confusion | 100.0% | 1/1 |
| developer_mode | 100.0% | 1/1 |
| direct_instruction | 100.0% | 2/2 |
| emotional_manipulation | 100.0% | 1/1 |
| fictional_framing | 100.0% | 1/1 |
| hypothetical_framing | 100.0% | 1/1 |
| indirect_injection | 100.0% | 1/1 |
| instruction_smuggling | 100.0% | 1/1 |
| jailbreak_attempt | 100.0% | 1/1 |
| markdown_injection | 100.0% | 1/1 |
| multi_turn_setup | 100.0% | 1/1 |
| payload_splitting | 100.0% | 1/1 |
| prompt_leaking | 100.0% | 1/1 |
| rag_specific | 100.0% | 3/3 |
| repetition_attack | 100.0% | 1/1 |
| role_manipulation | 100.0% | 1/1 |
| subtle_manipulation | 100.0% | 2/2 |
| translation_attack | 100.0% | 1/1 |
| unicode_obfuscation | 100.0% | 1/1 |
| virtualization | 100.0% | 1/1 |
| xml_injection | 100.0% | 1/1 |

---

## Benign Benchmark: NQ

- Total samples: 50
- False positives: 0
- False positive rate: 0.00%
- Mean latency: 0.02ms

## Benign Benchmark: HOTPOTQA

- Total samples: 25
- False positives: 0
- False positive rate: 0.00%
- Mean latency: 0.05ms

## Benign Benchmark: MSMARCO

- Total samples: 25
- False positives: 0
- False positive rate: 0.00%
- Mean latency: 0.02ms

---

## Aggregate Statistics

- Total samples processed: 135
- Overall mean latency: 0.04ms
- Overall P95 latency: 0.12ms