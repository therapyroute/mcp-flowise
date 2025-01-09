import pytest
from mcp_flowise.utils import fetch_chatflows, flowise_predict


@pytest.fixture
def mock_flowise_endpoint(monkeypatch):
    """Mock the Flowise API endpoint for fetch_chatflows."""
    def mock_get(*args, **kwargs):
        class MockResponse:
            def raise_for_status(self):
                pass  # Simulate successful HTTP status
            @staticmethod
            def json():
                return [
                    {"id": "mock-id-1", "name": "Mock Chatflow 1"},
                    {"id": "mock-id-2", "name": "Mock Chatflow 2"}
                ]
        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)


def test_fetch_chatflows(mock_flowise_endpoint):
    """Test the fetch_chatflows utility function."""
    result = fetch_chatflows()
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == "mock-id-1"
    assert result[0]["name"] == "Mock Chatflow 1"


def test_flowise_predict(monkeypatch):
    """Test the flowise_predict utility function."""
    def mock_post(*args, **kwargs):
        class MockResponse:
            def raise_for_status(self):
                pass  # Simulate successful HTTP status
            @staticmethod
            def json():
                return {"answer": "Canberra"}
            @property
            def status_code(self):
                return 200
            @property
            def text(self):
                return '{"answer": "Canberra"}'

        return MockResponse()

    monkeypatch.setattr("requests.post", mock_post)

    result = flowise_predict("mock-chatflow-id", "What is the capital of Australia?")
    assert result == '{"answer": "Canberra"}'

