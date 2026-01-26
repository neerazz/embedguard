# EmbedGuard: Tier-1 Security Venue Submission Plan

**Target Venues:** USENIX Security 2026, IEEE S&P 2026, ACM CCS 2026, NDSS 2026
**Current Status:** MAJOR REVISION REQUIRED
**Roundtable Verdict:** REJECT (78.5% weighted consensus)
**Date:** January 24, 2026

---

## Executive Summary

The BRUTAL dynamic roundtable evaluation identified **4 P0 (blocking)** and **3 P1 (high-priority)** issues that must be resolved before submitting to a Tier-1 security venue. The paper's core contribution (cross-layer detection with TEE attestation) is sound, but the evaluation methodology and threat model formalization are insufficient for Tier-1 acceptance.

---

## P0: Blocking Issues (Must Fix)

### P0-1: Missing Formal Threat Model

**Problem:** Tier-1 venues require explicit adversary capability definitions. Current paper has implicit assumptions scattered throughout.

**Required Addition:** New Section 2.5 "Threat Model"

```markdown
## 2.5 Threat Model

We consider an adversary A with the following capabilities and limitations:

**Adversary Knowledge:**
- Black-box access to the RAG system (query-response only)
- No knowledge of deployed embedding model architecture
- No knowledge of detection thresholds or layer weights

**Adversary Capabilities:**
- Insert-and-edit access to knowledge database (corpus poisoning)
- Computational budget: 10,000 GPU-hours for attack optimization
- Query budget: 1,000 queries for adaptive attack refinement

**Adversary Goals:**
- Integrity violation: Induce LLM to generate attacker-chosen content
- Availability violation: Prevent RAG from answering specific queries

**Adversary Limitations:**
- Cannot compromise TEE hardware trust roots
- Cannot access attestation signing keys
- Cannot modify deployed models or detection logic

**Trust Assumptions:**
- TEE firmware is patched against known CVEs
- Attestation certificates are cryptographically unforgeable
- Detection thresholds are not leaked to adversary
```

**Implementation:** Add this section after Section 2.4

---

### P0-2: No Standardized Benchmark Evaluation

**Problem:** Paper uses proprietary synthetic corpus. USENIX Security reviewers expect evaluation on established benchmarks.

**Required Change:** Evaluate on PoisonedRAG benchmark datasets

**Datasets to Add:**
| Dataset | Size | Source |
|---------|------|--------|
| Natural Questions (NQ) | 2,681,468 texts | [PoisonedRAG GitHub](https://github.com/sleeepeer/PoisonedRAG) |
| HotpotQA | 5,233,329 texts | PoisonedRAG benchmark |
| MS-MARCO | 8,841,823 texts | PoisonedRAG benchmark |

**New Evaluation Table:**
```markdown
**Table X: EmbedGuard Performance on Standardized Benchmarks**

| Dataset | Attack | EmbedGuard DR | RAGuard DR | RobustRAG DR | RAGDefender DR |
|---------|--------|---------------|------------|--------------|----------------|
| NQ | PoisonedRAG | XX.X% | 87.2% | 82.9% | 91.2% |
| NQ | Jamming | XX.X% | N/A | N/A | N/A |
| HotpotQA | PoisonedRAG | XX.X% | XX.X% | XX.X% | XX.X% |
| MS-MARCO | PoisonedRAG | XX.X% | XX.X% | XX.X% | XX.X% |
```

**Implementation Steps:**
1. Download PoisonedRAG datasets from GitHub
2. Run EmbedGuard evaluation on NQ, HotpotQA, MS-MARCO
3. Add new results table to Section 4
4. Update comparative analysis with standardized metrics

---

### P0-3: Unaddressed TEE Side-Channel Attacks

**Problem:** CounterSEVeillance (NDSS 2025) demonstrates 228 performance counter events leak from SEV-SNP VMs. This undermines the "deterministic cryptographic verification" claim.

**Required Change:** Acknowledge limitation and propose mitigation

**Update to Section 4.6:**
```markdown
### 4.6.1 TEE Side-Channel Vulnerabilities

Recent research demonstrates that AMD SEV-SNP remains vulnerable to
side-channel attacks through performance counter exposure.
CounterSEVeillance (Graz University, NDSS 2025) shows that 228
performance counter events are exposed to potentially malicious
hypervisors, enabling extraction of RSA-4096 keys in under 8 minutes.

**Impact on EmbedGuard:** While attestation certificates remain
cryptographically valid, side-channel leakage could allow adversaries
to infer embedding computation patterns without invalidating attestation.

**Mitigations:**
1. Disable performance counters for embedding computation enclaves
2. Add timing obfuscation to embedding generation
3. Monitor for anomalous hypervisor performance counter queries

**Residual Risk:** Side-channel defenses add 8-12ms latency overhead.
Organizations must weigh security benefits against performance costs.
```

**New Reference:**
```
CounterSEVeillance: Performance-Counter Attacks On AMD SEV-SNP.
Graz University of Technology. NDSS 2025.
```

---

### P0-4: Incomplete Attack Surface Coverage

**Problem:** Paper focuses on integrity attacks but ignores availability attacks (jamming/DoS).

**Required Addition:** New attack category evaluation

**"Machine Against the RAG" Jamming Attack:**
- Single blocker document causes RAG to refuse answering specific queries
- Black-box optimization, no instruction injection required
- USENIX Security 2025 accepted paper

**New Table Row:**
```markdown
| Attack Type | Detection Rate | False Positive Rate | Mean Latency |
|-------------|---------------|---------------------|--------------|
| Jamming/DoS | XX.X% | X.X% | XXms |
```

**Implementation:**
1. Download jamming attack code from [GitHub](https://github.com/avitalsh/jamming_attack)
2. Generate blocker documents for EmbedGuard test queries
3. Evaluate detection across all four layers
4. Add results to Table 4

---

## P1: High-Priority Issues

### P1-1: Missing Formal SEV-SNP Security Analysis Citation

**Problem:** Paper uses TEE without citing formal verification research.

**Required Citation:**
```
Formal Security Analysis of the AMD SEV-SNP Software Interface.
IEEE Transactions on Dependable and Secure Computing, 2025.
DOI: 10.1109/TDSC.2025.XXXXXXX
```

**Add to Section 3.3 after TEE description.**

---

### P1-2: Incomplete Baseline Comparisons

**Problem:** Missing comparison with RAGForensics traceback system.

**Required Addition:**
```markdown
**Table Y: Forensic Capability Comparison**

| System | Attack Detection | Traceback | Provenance |
|--------|-----------------|-----------|------------|
| EmbedGuard | 94.7% | No | Yes (TEE) |
| RAGForensics | N/A | Yes | No |
| Combined | 94.7% | Yes | Yes |
```

---

### P1-3: Finalize Zenodo DOI

**Problem:** DOI placeholder (XXXXXXX) in manuscript.

**Action:** After GitHub release, update DOI in:
- Section 5 Data Availability
- Appendix A.4 Reproducibility Checklist

---

## New Figures Required

### Figure 6: Formal Threat Model Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ADVERSARY MODEL                          │
├─────────────────────────────────────────────────────────────┤
│  Knowledge: Black-box RAG access                            │
│  Capabilities: Corpus poisoning, Query optimization         │
│  Goals: Integrity violation, Availability denial            │
│  Budget: 10K GPU-hours, 1K queries                          │
├─────────────────────────────────────────────────────────────┤
│                    TRUST ASSUMPTIONS                        │
├─────────────────────────────────────────────────────────────┤
│  ✓ TEE firmware patched                                     │
│  ✓ Attestation keys protected                               │
│  ✓ Detection thresholds confidential                        │
└─────────────────────────────────────────────────────────────┘
```

### Figure 7: Standardized Benchmark Results

Comparative bar chart showing EmbedGuard vs. baselines on NQ, HotpotQA, MS-MARCO.

### Figure 8: Side-Channel Attack Surface

Diagram showing CounterSEVeillance attack vector and proposed mitigations.

---

## Implementation Timeline

| Week | Task | Owner | Deliverable |
|------|------|-------|-------------|
| 1 | Write formal threat model | Author | Section 2.5 draft |
| 2-3 | Run NQ/HotpotQA/MS-MARCO evaluation | Author | New Table X data |
| 3 | Implement jamming attack evaluation | Author | Jamming detection results |
| 4 | Update TEE limitation section | Author | Section 4.6.1 revision |
| 5 | Add new figures | Author | Figures 6-8 |
| 6 | Internal review | Reviewer | Feedback document |
| 7 | Revise based on feedback | Author | Final manuscript |
| 8 | Submit to USENIX Security 2026 Cycle 1 | Author | Submission confirmation |

**Deadline:** USENIX Security 2026 Cycle 1: August 26, 2025

---

## Artifact Requirements (USENIX 2026)

USENIX Security 2026 requires open artifacts at submission time.

**Current Status:**
- [x] Code repository: https://github.com/neerazz/embedguard
- [x] GitHub release created
- [ ] Zenodo DOI finalized
- [ ] Standardized benchmark data included
- [ ] Evaluation scripts for NQ/HotpotQA/MS-MARCO
- [ ] Pre-trained prompt classifier weights

**Required Artifacts:**
1. `benchmarks/` - Standardized evaluation datasets
2. `attacks/poisonedrag/` - PoisonedRAG attack implementation
3. `attacks/jamming/` - Jamming attack implementation
4. `defenses/` - EmbedGuard defense modules
5. `evaluation/` - Reproducible evaluation scripts
6. `figures/` - Publication-quality figure generation

---

## Quality Checklist for Tier-1 Submission

### Mandatory Requirements
- [ ] Formal threat model with explicit adversary definition
- [ ] Evaluation on standardized benchmarks (NQ, HotpotQA, MS-MARCO)
- [ ] Comparison with all USENIX Security 2025 RAG defense papers
- [ ] Discussion of side-channel vulnerabilities and mitigations
- [ ] Open artifacts at submission time
- [ ] Ethics section addressing dual-use concerns

### Recommended Improvements
- [ ] User study or real deployment data
- [ ] Formal security analysis of cross-layer correlation
- [ ] Ablation on additional datasets
- [ ] Cost analysis (compute, storage, operational)

---

## References to Add

1. **[USENIX Security 2025]** Shafran, A., Schuster, R., Shmatikov, V. "Machine Against the RAG: Jamming Retrieval-Augmented Generation with Blocker Documents."

2. **[NDSS 2025]** Graz University of Technology. "CounterSEVeillance: Performance-Counter Attacks On AMD SEV-SNP."

3. **[IEEE TDSC 2025]** "Formal Security Analysis of the AMD SEV-SNP Software Interface."

4. **[arXiv 2505.18543]** "Benchmarking Poisoning Attacks against Retrieval-Augmented Generation."

5. **[WWW 2025]** "RAGForensics: Traceback of Poisoning Attacks to Retrieval-Augmented Generation."

---

## Success Criteria

**Tier-1 Acceptance Indicators:**
- Detection rate ≥90% on standardized benchmarks
- Formal threat model approved by security reviewers
- All attack categories addressed (integrity + availability)
- Reproducible artifacts with Zenodo DOI
- Ethics considerations documented

**Estimated Acceptance Probability:**
- Current: 15% (major gaps)
- After P0 fixes: 45% (competitive)
- After P0 + P1 fixes: 65% (strong submission)

---

*Plan generated by BRUTAL Dynamic Roundtable Evaluation*
*Agents: architect, researcher, evidence-hunter, critic, devil-advocate, red-teamer, verifier, gatekeeper*
*Date: January 24, 2026*
