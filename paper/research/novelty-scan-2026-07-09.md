# EmbedGuard Novelty Scan — Literature Review (compiled 2026-07-09)

Search tooling used: arXiv API (~30 queries, ✅ worked), DBLP API (partial, rate-limited after 3 queries),
OpenReview API (✅ worked, no relevant hits), Semantic Scholar API (❌ persistent HTTP 429 rate-limit — NOT searched),
Google Scholar (❌ not scrapeable programmatically — NOT searched).
All URLs below were returned by live API queries; none are invented.

## Category A — Multi-layer / cross-layer RAG or LLM-pipeline defense frameworks

1. **A Layered Security Framework Against Prompt Injection in RAG-Based Chatbots** — Saleem, Ahmed, Zaman, Hassan. arXiv (Jun 2026). https://arxiv.org/abs/2606.19660
   Three-layer middleware (input screening w/ semantic anomaly classifier → provenance-based instruction hierarchy at context assembly → output policy/semantic-drift audit) with a continuous audit loop; reports ASR 71.4%→11.3%, +27.3pp over best single layer, ablations showing layer complementarity.
   **VERDICT: OVERLAPS_CLAIM_1** — a multi-layer RAG defense spanning input/context/output stages with cross-layer complementarity claims and near-identical "+pp over best single layer" framing (though prompt-injection-focused, 3 layers, no embedding-layer attestation).

2. **Securing AI Agents Against Prompt Injection Attacks** — Ramakrishnan, Balaji. arXiv (Nov 2025). https://arxiv.org/abs/2511.15759
   Benchmark of 847 adversarial cases plus a multi-layered defense combining embedding-based anomaly detection, hierarchical prompt guardrails, and multi-stage response verification; 73.2%→8.7% attack success.
   **VERDICT: OVERLAPS_CLAIM_1** — combines embedding-layer anomaly detection with prompt- and output-layer defenses in one framework for RAG agents.

3. **Adaptive Defense Orchestration for RAG: A Sentinel-Strategist Architecture against Multi-Vector Attacks** — Pallerla, Bhukya, Vemula, Kodi. arXiv (Apr 2026). https://arxiv.org/abs/2604.20932
   Context-aware orchestration: a Sentinel detects anomalous retrieval behavior, a Strategist selectively activates defenses (poisoning, membership inference, leakage) per query to reduce the security–utility trade-off.
   **VERDICT: OVERLAPS_CLAIM_1** (partial) — orchestrates multiple defenses across attack vectors/stages, though it selects defenses rather than correlating anomaly signals across layers.

4. **Design and Implementation of a Secure RAG-Enhanced AI Chatbot… (Hsinchu smart tourism)** — Shih, Kang. arXiv (Sep 2025). https://arxiv.org/abs/2509.21367
   Deployed RAG chatbot with multi-layered linguistic analysis (lexical/semantic/pragmatic), gatekeeper intent judgment, and reverse-RAG grounding against injection.
   **VERDICT: ADJACENT** — layered defense engineering for one attack class, no cross-layer signal correlation or embedding-attack focus.

5. **Cordon-MAS: Defending RAG against Knowledge Poisoning via Information-Flow Control** — Yu et al. arXiv (May 2026). https://arxiv.org/abs/2605.26754
   Identifies a "monitoring–control gap" (detection alone doesn't prevent harm) and enforces information-flow control across the RAG pipeline in a multi-agent setting.
   **VERDICT: ADJACENT** — pipeline-wide defense philosophy but IFC-based, not multi-layer anomaly-signal correlation.

6. **Towards Secure Retrieval-Augmented Generation: A Comprehensive Review of Threats, Defenses and Benchmarks** — Mu et al. arXiv (Mar 2026). https://arxiv.org/abs/2603.21654
   Survey organizing RAG vulnerabilities and defenses stage-by-stage along the RAG workflow (system-level, multi-module view).
   **VERDICT: ADJACENT** — establishes the per-stage taxonomy EmbedGuard builds on; a reviewer may cite it against "first" claims framed too broadly.

7. **Security and Privacy in RAG: Architectures, Threats, Defenses, and Future Directions** — Palanisamy, Chalapathi, Hassija, Buyya. arXiv (Jun 2026). https://arxiv.org/abs/2606.25533
   Survey of RAG security/privacy across the retrieval-generation pipeline.
   **VERDICT: NOT_THREATENING** — survey, no framework contribution.

8. **SoK: The Attack Surface of Agentic AI** — Dehghantanha, Homayoun. arXiv (Mar 2026). https://arxiv.org/abs/2603.22928
   SoK mapping trust boundaries across LLM+RAG+agent stacks.
   **VERDICT: NOT_THREATENING** — taxonomy only.

## Category B — TEE / confidential computing / cryptographic attestation for embeddings, vector DBs, RAG

9. **VectorSmuggle: Steganographic Exfiltration in Embedding Stores and a Cryptographic Provenance Defense** — Jascha Wanger. arXiv (May 2026). https://arxiv.org/abs/2605.13764
   Shows embedding-store exfiltration attacks, then proposes **VectorPin**: a cryptographic provenance protocol pinning each embedding to its source content AND producing model via Ed25519 signatures; any post-embedding modification breaks verification. Explicitly notes vector stores lack "embedding integrity, ingestion-time distributional anomaly detection, or cryptographic provenance attestation."
   **VERDICT: OVERLAPS_CLAIM_2** — this is cryptographic attestation of embedding generation/provenance for RAG vector stores; EmbedGuard's differentiator narrows to the *hardware TEE* root of trust (VectorPin is software signature-based).

10. **Fortify Your Foundations: Practical Privacy and Security for Foundation Model Deployments in the Cloud** — Chrapek, Vahldiek-Oberwagner, Spoczynski, Constable, Vij, Hoefler (Intel/ETH). arXiv (Oct 2024). https://arxiv.org/abs/2410.05930
   Runs full Llama-2 inference pipelines (explicitly motivated by RAG deployments on private data) inside Intel SGX and TDX with <10% overhead; argues TEEs are the practical security mechanism for FM/RAG stacks.
   **VERDICT: OVERLAPS_CLAIM_2** (partial) — TEEs applied to RAG-relevant pipelines with SGX/TDX; does not do per-embedding attestation/provenance, but kills any claim that TEE-for-RAG is itself new.

11. **Confidential LLM Inference: Performance and Cost Across CPU and GPU TEEs** — Chrapek, Copik, Mettaz, Hoefler. arXiv (Sep 2025). https://arxiv.org/abs/2509.18886
    Systematic performance study of LLM inference in CPU/GPU TEEs. **VERDICT: ADJACENT** — confidential inference, no embedding attestation.

12. **EnclaveX: End-to-End Confidential AI with CPU/GPU TEEs** — Schambach, Le, Arnautov, Fetzer. arXiv (Jun 2026). https://arxiv.org/abs/2606.31408
    End-to-end confidential AI platform spanning CPU+GPU TEEs for LLM workloads. **VERDICT: ADJACENT** — platform-level confidentiality, not RAG-layer attestation of embeddings.

13. **AgenTEE: Confidential LLM Agent Execution on Edge Devices** — Abdollahi et al. arXiv (Apr 2026). https://arxiv.org/abs/2604.18231
    TEE-protected LLM-agent execution on edge. **VERDICT: ADJACENT**.

14. **When Agents Handle Secrets: A Survey of Confidential Computing for Agentic AI** — Forough, Kogias, Haddadi. arXiv (May 2026). https://arxiv.org/abs/2605.03213
    Survey of confidential computing across agent pipelines (incl. RAG memory/tools). **VERDICT: ADJACENT** — survey; useful related-work cite; signals the space is active.

15. **Toward provably private analytics and insights into GenAI use** — Cheu et al. (Google). arXiv (Oct 2025). https://arxiv.org/abs/2510.21684
    Federated analytics with AMD SEV-SNP / Intel TDX attestation for verifiable privacy. **VERDICT: NOT_THREATENING** — different domain (federated analytics), but shows SEV-SNP attestation patterns are established.

16. **Confidential Prompting: Privacy-preserving LLM Inference on Cloud** — Li, Gim, Zhong (Yale). arXiv (Sep 2024). https://arxiv.org/abs/2409.19134
    Confidential-computing-based protection of user prompts during cloud LLM inference. **VERDICT: NOT_THREATENING** — prompt confidentiality, not embedding integrity.

17. **Transform Before You Query: Privacy-Preserving Vector Retrieval with Embedding Space Alignment** — He et al. arXiv (Jul 2025). https://arxiv.org/abs/2507.18518
    Privacy for queries against vector DBs via embedding-space transforms. **VERDICT: NOT_THREATENING** — privacy, not integrity/attestation.

## Category C — Poisoning DETECTION methods post-PoisonedRAG (beyond those already cited)

18. **Safeguarding RAG Pipelines with GMTP** — Kim, Kim, Jeon, Lee. **Findings of ACL 2025**. DOI 10.18653/v1/2025.findings-acl.1263 / https://arxiv.org/abs/2507.18202
    Gradient-based masked-token-probability detection of poisoned documents in retrieved sets.
    **VERDICT: ADJACENT** — strong single-layer (retrieval-stage) detector; a baseline EmbedGuard should compare against.

19. **Traceback of Poisoning Attacks to Retrieval-Augmented Generation (RAGForensics)** — Zhang et al. **WWW 2025**. DOI 10.1145/3696410.3714756 / https://arxiv.org/abs/2504.21668
    First traceback system identifying poisoned texts responsible for attacker-desired outputs.
    **VERDICT: ADJACENT** — post-hoc forensics, not multi-layer online detection.

20. **Through the Stealth Lens: Attention-Aware Defenses Against Poisoning in RAG** — Choudhary, Palumbo, Hooda, Dvijotham, Jha. arXiv (Jun 2025). https://arxiv.org/abs/2506.04390
    Formalizes stealth via a distinguishability game; attention-signal-based detection of poisoned passages.
    **VERDICT: ADJACENT** — generation-layer signal only; also warns detectors are evadable by stealthy adaptive attacks (relevant to EmbedGuard's 89.3% adaptive claim).

21. **TRACE: Tracing Target Answers in Poisoned Retrieval Corpora via Token Influence Attribution** — Chen, Chen (Pin-Yu), Yu, Lin, Wu, Lee. arXiv (Jun 2026). https://arxiv.org/abs/2606.25721
    Lightweight token-influence attribution for corpus-poisoning detection without auxiliary classifiers.
    **VERDICT: ADJACENT** — single-mechanism detector, natural baseline.

22. **EcoSafeRAG: Efficient Security through Context Analysis in RAG** — Yao et al. arXiv (May 2025). https://arxiv.org/abs/2505.13506
    Sentence-level context analysis (bait-guided diversity) detecting corpus poisoning without model internals. **VERDICT: ADJACENT**.

23. **Rescuing the Unpoisoned: Efficient Defense against Knowledge Corruption Attacks on RAG** — Kim, Lee, Koo. arXiv (Nov 2025). https://arxiv.org/abs/2511.01268
    Efficient filtering defense recovering clean passages under knowledge-corruption attacks. **VERDICT: ADJACENT**.

24. **Adversarial Hubness Detector: Detecting Hubness Poisoning in RAG Systems** — Habler, Narajala, Koren, Chang, Saade. arXiv (Feb 2026). https://arxiv.org/abs/2602.22427
    Detects adversarial hubs (embedding-space geometry) in vector stores — an *embedding-layer* detection signal. **VERDICT: ADJACENT** (leaning threatening to any "first embedding-layer detection" sub-claim).

25. **When Global Gating Is Enough: Admission-Time Hubness Control in Vector Retrieval** — Pathak, Sharma. arXiv (Jun 2026). https://arxiv.org/abs/2606.19692
    Ingestion/admission-time scoring against sentinel queries to quarantine poisoning candidates in vector stores. **VERDICT: ADJACENT** — embedding/ingestion-layer defense.

26. **BiRD: Bidirectional Ranking Defense for RAG** — Gao et al. arXiv (May 2026). https://arxiv.org/abs/2605.20123
    Retrieval-context-aware ranking defense against poisoning. **VERDICT: ADJACENT**.

27. **PRA-RAG: Provably Robust Aggregation against Retrieval Corruption** — Tan et al. arXiv (May 2026). https://arxiv.org/abs/2607.00012
    Certified-robustness aggregation defense. **VERDICT: ADJACENT**.

28. **Needle-in-RAG: Character-Level Traceback of Poisoned Spans** — Cui, Liu. arXiv (May 2026). https://arxiv.org/abs/2605.01782
    Span-level traceback of poisoned evidence. **VERDICT: ADJACENT**.

29. **Addressing Corpus Knowledge Poisoning on RAG Using Sparse Attention** — Dekel, Tennenholtz, Kurland. arXiv (Feb 2026). https://arxiv.org/abs/2602.04711 — **ADJACENT** (generation-layer mitigation).

30. **Defending Against Knowledge Poisoning Attacks During RAG** — Edemacu et al. arXiv (Aug 2025). https://arxiv.org/abs/2508.02835 — **ADJACENT** (explicitly counters PoisonedRAG).

31. **ControlNET: A Firewall for RAG-based LLM System** — Yao, Shi, Chen, Jiang, Wang, Qin. arXiv (Apr 2025). https://arxiv.org/abs/2504.09593
    "Firewall" governing query/response flows in RAG for privacy+security risks, incl. detection of anomalous flows.
    **VERDICT: ADJACENT** (leaning OVERLAPS_CLAIM_1 in spirit — a system-level control point spanning ingress and egress of the RAG pipeline).

32. **Zero-Shot Embedding Drift Detection** — Sekar et al. arXiv (Jan 2026). https://arxiv.org/abs/2601.12359
    Embedding-drift signal to detect prompt injections. **VERDICT: ADJACENT** — embedding-layer anomaly signal, single-layer.

Attack papers confirming adaptive-evasion pressure (context, not threats): RefineRAG (2604.07403), Confundo (2602.06616), SilentRetrieval (2605.28074), DiscourseFlip (2606.01212), Semantic Chameleon (2603.18034), PIDP-Attack, PR-Attack (2504.07717 — coordinated prompt+RAG bilevel attack).
Already-cited prior art confirmed at real venues: RevPRAG (Findings of EMNLP 2025, DOI 10.18653/v1/2025.findings-emnlp.698), TrustRAG (arXiv 2501.00879).
