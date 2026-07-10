"""Regression tests for public integration examples."""

from types import SimpleNamespace

from embedguard import Decision
from examples import integration_example


def _passive_log_analysis():
    return SimpleNamespace(
        decision=Decision.LOG,
        threat_score=0.8,
        detected_attacks=[],
        to_dict=lambda: {"decision": Decision.LOG.value},
    )


def test_passive_log_middleware_invokes_callback(monkeypatch):
    """Passive LOG observes the request without intervening."""
    middleware = integration_example.EmbedGuardMiddleware()
    monkeypatch.setattr(
        middleware,
        "guard",
        SimpleNamespace(analyze=lambda query, documents: _passive_log_analysis()),
    )
    calls = []

    def proceed(query, documents):
        calls.append((query, documents))
        return "generated"

    assert middleware("query", ["document"], proceed) == "generated"
    assert calls == [("query", ["document"])]


def test_passive_log_decorator_invokes_wrapped_function(monkeypatch):
    """The decorator must not turn passive observation into an error response."""

    class _FakeGuard:
        def __init__(self, config):
            self.config = config

        def analyze(self, query, documents):
            return _passive_log_analysis()

    monkeypatch.setattr(integration_example, "EmbedGuard", _FakeGuard)
    calls = []

    @integration_example.protected_by_embedguard(mode="passive")
    def generate(query, documents):
        calls.append((query, documents))
        return "generated"

    result = generate("query", ["document"])

    assert result["result"] == "generated"
    assert result["security_analysis"]["decision"] == "log"
    assert calls == [("query", ["document"])]
