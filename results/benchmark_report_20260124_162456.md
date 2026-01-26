# EmbedGuard Benchmark Results

**Generated:** 2026-01-24T16:24:56.922492
**Detector:** PatternBasedDetector (24 patterns)
**Threshold:** 0.70

---

## Prompt Injection Detection

### Performance Metrics

| Metric | Value |
|--------|-------|
| Detection Rate (Recall) | 6.7% |
| Precision | 100.0% |
| F1 Score | 0.125 |
| False Positive Rate | 0.0% |
| Accuracy | 20.0% |

### Confusion Matrix

- True Positives: 2
- False Positives: 0
- True Negatives: 5
- False Negatives: 28

### Latency

- Mean: 0.02ms
- Median: 0.03ms
- P95: 0.03ms
- P99: 0.04ms

### Detection by Attack Type

| Attack Type | Detection Rate | Count |
|-------------|----------------|-------|
| authority_claim | 0.0% | 0/1 |
| base64_encoding | 0.0% | 0/1 |
| benign_query | 0.0% | 0/5 |
| composite_attack | 0.0% | 0/2 |
| context_manipulation | 0.0% | 0/1 |
| delimiter_confusion | 0.0% | 0/1 |
| developer_mode | 100.0% | 1/1 |
| direct_instruction | 0.0% | 0/2 |
| emotional_manipulation | 0.0% | 0/1 |
| fictional_framing | 0.0% | 0/1 |
| hypothetical_framing | 0.0% | 0/1 |
| indirect_injection | 0.0% | 0/1 |
| instruction_smuggling | 0.0% | 0/1 |
| jailbreak_attempt | 0.0% | 0/1 |
| markdown_injection | 0.0% | 0/1 |
| multi_turn_setup | 0.0% | 0/1 |
| payload_splitting | 0.0% | 0/1 |
| prompt_leaking | 0.0% | 0/1 |
| rag_specific | 0.0% | 0/3 |
| repetition_attack | 0.0% | 0/1 |
| role_manipulation | 0.0% | 0/1 |
| subtle_manipulation | 0.0% | 0/2 |
| translation_attack | 0.0% | 0/1 |
| unicode_obfuscation | 0.0% | 0/1 |
| virtualization | 100.0% | 1/1 |
| xml_injection | 0.0% | 0/1 |

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
- Mean latency: 0.01ms

## Benign Benchmark: MSMARCO

- Total samples: 25
- False positives: 0
- False positive rate: 0.00%
- Mean latency: 0.01ms

---

## Aggregate Statistics

- Total samples processed: 135
- Overall mean latency: 0.02ms
- Overall P95 latency: 0.04ms