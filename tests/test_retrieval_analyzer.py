"""Regression tests for retrieval-layer statistical state."""

import numpy as np

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
