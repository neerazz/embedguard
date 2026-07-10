"""Integrity tests for the software attestation simulator."""

from dataclasses import replace
from unittest.mock import patch

import numpy as np
import pytest

from embedguard.embedding_attestation import EmbeddingAttestationLayer


class _FixedEmbeddingModel:
    def encode(self, document: str, convert_to_numpy: bool = True):
        assert convert_to_numpy is True
        return np.array([0.1, 0.2, 0.3], dtype=np.float32)


def test_embedding_generation_fails_closed_without_model():
    layer = EmbeddingAttestationLayer(secret_key=b"x" * 32)

    with patch.object(layer, "_get_embedding_model", return_value=None):
        with pytest.raises(RuntimeError, match="embedding model"):
            layer.generate_embedding_with_attestation("source document")


@pytest.mark.parametrize("validity_period", [0, -1, True, "60"])
def test_software_certificate_rejects_invalid_validity_period(validity_period):
    with pytest.raises(ValueError, match="positive integer"):
        EmbeddingAttestationLayer(
            secret_key=b"x" * 32,
            validity_period=validity_period,
        )


def test_software_certificate_detects_embedding_tampering():
    layer = EmbeddingAttestationLayer(secret_key=b"x" * 32)
    with patch.object(layer, "_get_embedding_model", return_value=_FixedEmbeddingModel()):
        embedding, certificate = layer.generate_embedding_with_attestation(
            "source document"
        )

    tampered = embedding.copy()
    tampered[0] += 1.0
    result = layer.verify_attestation("source document", tampered, certificate)

    assert result.is_valid is False
    assert result.error is not None
    assert "Embedding hash mismatch" in result.error


def test_software_certificate_signs_validity_period():
    """Extending expiry after issuance must invalidate the certificate HMAC."""
    layer = EmbeddingAttestationLayer(
        secret_key=b"x" * 32,
        validity_period=60,
    )
    with patch.object(layer, "_get_embedding_model", return_value=_FixedEmbeddingModel()):
        embedding, certificate = layer.generate_embedding_with_attestation(
            "source document"
        )

    tampered = replace(certificate, validity_period=86400)
    result = layer.verify_attestation("source document", embedding, tampered)

    assert result.is_valid is False
    assert result.error is not None
    assert "Invalid signature" in result.error


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("timestamp", "not-a-timestamp"),
        ("validity_period", "not-an-integer"),
        ("pcr_values", {"bad": object()}),
    ],
)
def test_software_certificate_fails_closed_on_malformed_fields(field, value):
    layer = EmbeddingAttestationLayer(secret_key=b"x" * 32)
    with patch.object(layer, "_get_embedding_model", return_value=_FixedEmbeddingModel()):
        embedding, certificate = layer.generate_embedding_with_attestation(
            "source document"
        )

    malformed = replace(certificate, **{field: value})
    result = layer.verify_attestation("source document", embedding, malformed)

    assert result.is_valid is False
    assert result.error is not None
