"""Regression tests for retrieval-layer statistical state."""

import numpy as np
import pytest

from embedguard.retrieval_analyzer import IncrementalPCA, RetrievalDistributionalAnalyzer
from embedguard.types import Document


def _documents(query_index: int) -> list[Document]:
    scores = [0.9, 0.6, 0.2] if query_index % 2 == 0 else [0.2, 0.6, 0.9]
    return [
        Document(
            content=f"document-{index}",
            embedding=[float(index), 0.5, 1.0],
            document_id=f"doc-{index}",
            metadata={"similarity_score": score},
        )
        for index, score in enumerate(scores)
    ]


def test_rank_correlation_becomes_reachable_after_history_warmup():
    analyzer = RetrievalDistributionalAnalyzer(update_frequency=10_000)

    final_details = None
    for query_index in range(11):
        _, _, final_details = analyzer.analyze(
            f"query-{query_index}",
            _documents(query_index),
        )

    assert len(analyzer.score_history) == 11
    assert final_details is not None
    assert final_details["rank_correlation"]["status"] == "evaluated"
    assert final_details["component_scores"]["rank"] is not None


def test_pca_fits_accumulated_rows_when_warmup_threshold_is_reached():
    pca = IncrementalPCA(n_components=2, batch_size=4)

    pca.partial_fit(np.array([[1.0, 0.0], [0.0, 1.0]]))
    assert pca.components is not None
    assert np.count_nonzero(pca.components) == 0

    pca.partial_fit(np.array([[2.0, 0.0], [0.0, 2.0]]))

    assert pca.n_samples_seen == 4
    assert pca.components is not None
    assert np.count_nonzero(pca.components) > 0
    errors = pca.reconstruction_error(np.array([[1.0, 1.0]]))
    assert errors.shape == (1,)


def _disjoint_documents(query_index: int) -> list[Document]:
    return [
        Document(
            content=f"q{query_index}-document-{index}",
            embedding=[float(index), 0.5, 1.0],
            document_id=f"q{query_index}-doc-{index}",
            metadata={"similarity_score": 0.9 - 0.1 * index},
        )
        for index in range(3)
    ]


def test_rank_without_comparable_history_abstains_and_is_excluded_from_fusion():
    analyzer = RetrievalDistributionalAnalyzer(update_frequency=10_000)

    details = None
    for query_index in range(12):
        _, _, details = analyzer.analyze(
            f"query-{query_index}", _disjoint_documents(query_index)
        )

    assert details is not None
    rank = details["rank_correlation"]
    assert rank["status"] == "no_comparable_history"
    assert "rank" not in details["fusion_weights"]
    assert details["component_scores"]["rank"] == 0.0


def test_rank_scores_against_most_recent_overlapping_query():
    analyzer = RetrievalDistributionalAnalyzer(update_frequency=10_000)
    for query_index in range(10):
        analyzer.analyze(f"warm-{query_index}", _disjoint_documents(query_index))

    base = [
        Document(content=f"shared-{i}", embedding=[float(i), 0.5, 1.0],
                 document_id=f"shared-{i}",
                 metadata={"similarity_score": 0.9 - 0.1 * i})
        for i in range(4)
    ]
    analyzer.analyze("base", base)
    analyzer.analyze("unrelated", _disjoint_documents(99))

    reversed_docs = [
        Document(content=d.content, embedding=d.embedding,
                 document_id=d.document_id,
                 metadata={"similarity_score": 0.5 + 0.1 * i})
        for i, d in enumerate(base)
    ]
    _, _, details = analyzer.analyze("base-again", reversed_docs)

    rank = details["rank_correlation"]
    assert rank["status"] == "evaluated"
    assert rank["history_lag"] == 2
    assert rank["shared_documents"] == 4
    assert rank["rank_correlation"] == pytest.approx(-1.0)
    assert details["component_scores"]["rank"] == pytest.approx(1.0)
    assert details["fusion_weights"]["rank"] > 0


def test_calibrate_threshold_uses_clean_quantile():
    clean = list(np.linspace(0.0, 0.99, 100))
    threshold = RetrievalDistributionalAnalyzer.calibrate_threshold(clean, 0.05)
    assert threshold == pytest.approx(0.95)
    assert np.mean(np.array(clean) > threshold) <= 0.05
    with pytest.raises(ValueError):
        RetrievalDistributionalAnalyzer.calibrate_threshold(clean, 0.0)
    with pytest.raises(ValueError):
        RetrievalDistributionalAnalyzer.calibrate_threshold([], 0.05)


def test_default_configuration_is_preserved():
    analyzer = RetrievalDistributionalAnalyzer()
    assert analyzer.anomaly_threshold == 0.5
    assert analyzer.component_weights == {"pca": 0.5, "kl": 0.3, "rank": 0.2}
    _, _, details = analyzer.analyze("q", _documents(0))
    assert details["anomaly_threshold"] == 0.5
    assert details["is_anomalous"] is False


def test_custom_threshold_and_weights_drive_flag():
    analyzer = RetrievalDistributionalAnalyzer(
        anomaly_threshold=-1.0, component_weights={"pca": 0.0}
    )
    _, _, details = analyzer.analyze("q", _documents(0))
    assert details["is_anomalous"] is True
    assert "pca" not in details["fusion_weights"] or details["fusion_weights"]["pca"] == 0
    with pytest.raises(ValueError):
        RetrievalDistributionalAnalyzer(component_weights={"bogus": 1.0})


def _clustered_docs(rng: np.random.Generator, centre: np.ndarray, prefix: str,
                    spread: float = 0.05, k: int = 5) -> list[Document]:
    """Top-k retrieval whose embeddings sit near ``centre`` (unit-normalised)."""
    docs = []
    for i in range(k):
        v = centre + spread * rng.standard_normal(centre.shape[0])
        v = v / np.linalg.norm(v)
        docs.append(Document(content=f"{prefix}-{i}", embedding=v.tolist(),
                             document_id=f"{prefix}-{i}",
                             metadata={"similarity_score": 0.8 - 0.05 * i}))
    return docs


def test_zero_weight_component_is_excluded_from_fusion_and_confidence():
    analyzer = RetrievalDistributionalAnalyzer(
        update_frequency=10_000, component_weights={"pca": 0.0, "kl": 1.0, "rank": 0.0}
    )
    rng = np.random.default_rng(0)
    centre = np.ones(16) / 4.0
    details = {}
    for q in range(40):
        _, _, details = analyzer.analyze(f"q{q}", _clustered_docs(rng, centre, f"c{q}"))
    assert set(details["fusion_weights"]) <= {"kl"}


def _shift_scenario(freeze: bool):
    """Warm up and calibrate on clean traffic, then score held-out clean
    traffic and a sustained run of retrievals from a shifted region."""
    rng = np.random.default_rng(7)
    dim = 16
    clean_centre = np.zeros(dim)
    clean_centre[0] = 1.0
    shifted_centre = np.zeros(dim)
    shifted_centre[1] = 1.0
    analyzer = RetrievalDistributionalAnalyzer(
        update_frequency=10_000, component_weights={"pca": 0.0, "kl": 1.0, "rank": 0.0}
    )

    def clean(tag: str) -> list[Document]:
        return _clustered_docs(rng, clean_centre + 0.1 * rng.standard_normal(dim), tag)

    for q in range(60):
        analyzer.analyze(f"w{q}", clean(f"w{q}"))
    calibration = [analyzer.analyze(f"c{q}", clean(f"c{q}"))[0] for q in range(100)]
    threshold = RetrievalDistributionalAnalyzer.calibrate_threshold(calibration, 0.05)
    if freeze:
        analyzer.freeze_baseline()
    held_out = [analyzer.analyze(f"h{q}", clean(f"h{q}"))[0] for q in range(100)]
    shifted = [
        analyzer.analyze(f"s{q}", _clustered_docs(rng, shifted_centre, f"s{q}", spread=0.02))[0]
        for q in range(200)
    ]
    return threshold, np.array(held_out), np.array(shifted)


def test_frozen_baseline_flags_sustained_shift_without_firing_on_clean():
    threshold, held_out, shifted = _shift_scenario(freeze=True)
    assert np.mean(held_out > threshold) <= 0.15  # must not fire on clean
    assert np.mean(shifted > threshold) == 1.0    # must fire on every shifted request
    assert shifted[-1] == pytest.approx(shifted[0], rel=0.05)


def test_adaptive_baseline_is_desensitised_by_a_sustained_shift():
    """Documents why EmbedGuard.calibrate() freezes the baseline.

    With adaptive updates every scored batch joins the covariance estimate it
    is scored against, so a sustained run of shifted retrievals inflates the
    covariance along the shift and the distance collapses (about 29 -> 1.4
    after 50 requests in this scenario). A frozen baseline stays flat."""

    def distances(freeze: bool) -> list[float]:
        rng = np.random.default_rng(7)
        dim = 16
        clean_centre = np.zeros(dim)
        clean_centre[0] = 1.0
        shifted_centre = np.zeros(dim)
        shifted_centre[1] = 1.0
        analyzer = RetrievalDistributionalAnalyzer(
            update_frequency=10_000, component_weights={"pca": 0.0, "kl": 1.0, "rank": 0.0}
        )
        for q in range(160):
            analyzer.analyze(
                f"w{q}", _clustered_docs(rng, clean_centre + 0.1 * rng.standard_normal(dim), f"w{q}")
            )
        if freeze:
            analyzer.freeze_baseline()
        return [
            analyzer.analyze(f"s{q}", _clustered_docs(rng, shifted_centre, f"s{q}", spread=0.02))[2][
                "kl_divergence"
            ]["mahalanobis_distance"]
            for q in range(50)
        ]

    frozen, adaptive = distances(True), distances(False)
    assert frozen[-1] == pytest.approx(frozen[0], rel=0.1)
    assert adaptive[-1] < 0.25 * frozen[-1]


def test_frozen_baseline_stops_state_updates_and_reset_restores_adaptation():
    rng = np.random.default_rng(1)
    analyzer = RetrievalDistributionalAnalyzer(update_frequency=10_000)
    centre = np.ones(8) / np.sqrt(8)
    for q in range(20):
        analyzer.analyze(f"q{q}", _clustered_docs(rng, centre, f"q{q}"))
    analyzer.freeze_baseline()
    mean_before = analyzer.baseline_mean.copy()
    buffer_before = len(analyzer._embedding_buffer)
    far = np.zeros(8)
    far[3] = 1.0
    analyzer.analyze("far", _clustered_docs(rng, far, "far"))
    assert np.array_equal(analyzer.baseline_mean, mean_before)
    assert len(analyzer._embedding_buffer) == buffer_before
    analyzer.reset()
    assert analyzer.adapt_baseline is True


def test_frozen_before_warmup_abstains_instead_of_learning_from_scored_traffic():
    analyzer = RetrievalDistributionalAnalyzer(update_frequency=10_000)
    analyzer.freeze_baseline()
    rng = np.random.default_rng(3)
    score, confidence, details = analyzer.analyze("q", _clustered_docs(rng, np.ones(8), "a"))
    assert analyzer.baseline_mean is None
    assert analyzer.pca.n_samples_seen == 0
    assert details["kl_divergence"]["status"] == "frozen_before_warmup"
    assert score == 0.0 and confidence == 0.0


def test_ranking_orders_by_similarity_and_falls_back_to_caller_order_on_nan():
    docs = [
        Document(content="a", document_id="a", metadata={"similarity_score": 0.2}),
        Document(content="b", document_id="b", metadata={"similarity_score": 0.9}),
        Document(content="c", document_id="c", metadata={"similarity_score": 0.8}),
    ]
    assert RetrievalDistributionalAnalyzer._document_ranking(docs) == ["b", "c", "a"]
    docs[2].metadata["similarity_score"] = float("nan")
    assert RetrievalDistributionalAnalyzer._document_ranking(docs) == ["a", "b", "c"]


def test_all_zero_component_weights_are_rejected():
    with pytest.raises(ValueError):
        RetrievalDistributionalAnalyzer(component_weights={"pca": 0.0, "kl": 0.0, "rank": 0.0})
