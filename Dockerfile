FROM python:3.11-slim

WORKDIR /app

# Install dependencies first so this layer is cached across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY server.py retrieve.py recommend.py embeddings.py deepseek_client.py ./

# Static, pre-built knowledge base data (kb_corpus.json, kb_index.npz).
COPY out/ ./out/

EXPOSE 8420

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8420"]
