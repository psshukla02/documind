SAMPLE = """
Pydantic is a data validation library for Python. You define models by
subclassing BaseModel and declaring typed attributes.

Common edge cases:
- Optional fields must have a default value to avoid "field required" errors.
- Validators run in the order they are defined.
"""


def test_generate_docs(client):
    r = client.post(
        "/api/generate-docs",
        json={"topic": "How to define a Pydantic model", "use_retrieval": False},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["markdown"]) > 0
    assert "latency_ms" in data


def test_synthetic_requires_ingest(client):
    r = client.post("/api/synthetic-data", json={"n_pairs": 3})
    assert r.status_code == 400


def test_synthetic_after_ingest(client):
    client.post(
        "/api/ingest/text",
        json={"title": "Pydantic basics", "text": SAMPLE, "source": "unit-test"},
    )
    r = client.post("/api/synthetic-data", json={"n_pairs": 3})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["title"] == "Pydantic basics"
    # In stub mode the model returns non-JSON, so pairs may be empty —
    # but the endpoint must still succeed and return a well-formed response.
    assert isinstance(data["pairs"], list)


def test_metrics_endpoint(client):
    client.post(
        "/api/ingest/text",
        json={"title": "Pydantic basics", "text": SAMPLE, "source": "unit-test"},
    )
    client.post("/api/chat", json={"query": "What is Pydantic?"})
    r = client.get("/api/metrics")
    assert r.status_code == 200
    data = r.json()
    assert data["counters"]["ingest_requests"] >= 1
    assert data["counters"]["chat_requests"] >= 1
    assert data["chat"]["count"] >= 1
