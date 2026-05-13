import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient


@pytest.fixture
def mock_ocr_result():
    return {
        "tests": [
            {
                "name": "Haemoglobin",
                "value": "13.5",
                "unit": "g/dL",
                "reference_range": "12.0 - 16.0",
            }
        ]
    }


@pytest.fixture
def sample_image():
    """Minimal valid PNG bytes for upload testing."""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


async def test_ocr_extract_success(
    client: AsyncClient, mock_ocr_result, sample_image
):
    with patch(
        "app.api.v1.endpoints.ocr.extract_lab_results",
        return_value=mock_ocr_result,
    ):
        response = await client.post(
            "/api/v1/ocr/extract",
            files={"file": ("test.png", sample_image, "image/png")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "tests" in data
    assert len(data["tests"]) == 1
    assert data["tests"][0]["name"] == "Haemoglobin"


async def test_ocr_extract_unsupported_type(client: AsyncClient, sample_image):
    response = await client.post(
        "/api/v1/ocr/extract",
        files={"file": ("test.pdf", sample_image, "application/pdf")},
    )
    assert response.status_code == 415


async def test_ocr_extract_service_failure(client: AsyncClient, sample_image):
    from app.services.ocr import OCRExtractionError

    with patch(
        "app.api.v1.endpoints.ocr.extract_lab_results",
        side_effect=OCRExtractionError("OCR extraction failed. Please try again."),
    ):
        response = await client.post(
            "/api/v1/ocr/extract",
            files={"file": ("test.png", sample_image, "image/png")},
        )
    assert response.status_code == 422