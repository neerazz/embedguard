"""Regression tests for output-consistency evaluation modes."""

from embedguard.output_verifier import OutputConsistencyVerifier
from embedguard.types import Document


def _documents() -> list[Document]:
    return [
        Document(content="alpha beta gamma", document_id="a"),
        Document(content="delta epsilon zeta", document_id="b"),
    ]


def test_real_output_without_generator_is_not_compared_to_synthetic_outputs():
    verifier = OutputConsistencyVerifier(k_perturbations=2)

    score, confidence, details = verifier.verify(
        "query",
        _documents(),
        generated_output="real deployed model output",
    )

    assert score == 0.0
    assert confidence == 0.0
    assert details["status"] == "not_evaluated"
    assert details["evaluation_mode"] == "real_output_requires_generator"


def test_generator_callback_is_used_for_baseline_and_every_perturbation():
    verifier = OutputConsistencyVerifier(k_perturbations=3)
    calls: list[list[str]] = []

    def generator(query: str, documents: list[Document]) -> str:
        assert query == "query"
        calls.append([document.content for document in documents])
        return "stable generator output"

    score, confidence, details = verifier.verify(
        "query",
        _documents(),
        output_generator=generator,
    )

    assert len(calls) == 4
    assert score == 0.0
    assert confidence == 1.0
    assert details["evaluation_mode"] == "generator_callback"
