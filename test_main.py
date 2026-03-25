from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "random_joke" in data
    assert isinstance(data["random_joke"], str)
