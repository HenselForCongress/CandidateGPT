# tests/test_backend.py
import pytest
from mastermind import backend

@pytest.fixture
def client():
    """Test client for the Flask application."""
    with app.test_client() as client:
        yield client

def test_ask_question(client):
    """Test the question-answer functionality."""
    response = client.post('/api/ask', json={'question': 'What is your stance on environment?'})
    json_data = response.get_json()
    assert response.status_code == 200
    assert 'answer' in json_data
