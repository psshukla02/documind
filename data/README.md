# Data Directory

Runtime artifacts live here. Nothing in this directory is checked in except
this README.

- `vector_store/` — FAISS index + metadata, created on first ingest.

To clear everything, either use the UI ("Clear All" button in the Knowledge
Base page) or delete the `vector_store/` directory and restart the server.
