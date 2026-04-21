SAMPLE = """
FastAPI is a modern, fast (high-performance), web framework for building APIs
with Python based on standard Python type hints.

Key features include:
- Automatic interactive API documentation (Swagger UI and ReDoc).
- Data validation via Pydantic.
- Async support built in on top of Starlette.

Common pitfalls:
- Forgetting to declare a response_model when you want schema validation.
- Using synchronous blocking calls inside async endpoints.
"""


def test_ingest_text_and_list_kb(client):
    r = client.post(
        "/api/ingest/text",
        json={"title": "FastAPI intro", "text": SAMPLE, "source": "unit-test"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["chunks"] >= 1
    assert data["title"] == "FastAPI intro"

    r2 = client.get("/api/knowledge-base")
    assert r2.status_code == 200
    kb = r2.json()
    assert kb["total_chunks"] == data["chunks"]
    assert kb["documents"][0]["title"] == "FastAPI intro"


def test_chat_returns_answer_and_citations(client):
    client.post(
        "/api/ingest/text",
        json={"title": "FastAPI intro", "text": SAMPLE, "source": "unit-test"},
    )
    r = client.post("/api/chat", json={"query": "What features does FastAPI provide?"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "answer" in data and len(data["answer"]) > 0
    assert isinstance(data["citations"], list)
    assert data["citations"], "expected at least one citation after ingest"
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["latency_ms"] >= 0.0


def test_chat_rejects_empty_query(client):
    r = client.post("/api/chat", json={"query": ""})
    assert r.status_code == 422  # Pydantic min_length


def test_reset_kb(client):
    client.post(
        "/api/ingest/text",
        json={"title": "FastAPI intro", "text": SAMPLE, "source": "unit-test"},
    )
    r = client.delete("/api/knowledge-base")
    assert r.status_code == 200
    kb = client.get("/api/knowledge-base").json()
    assert kb["total_chunks"] == 0
    assert kb["documents"] == []
