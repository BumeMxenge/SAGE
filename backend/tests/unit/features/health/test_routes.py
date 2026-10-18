# Checks the /health route answers and names the running commit, so CI proves the app boots
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    # "dev" on a laptop, the commit SHA in a deployed image
    assert response.json()["commit"]
