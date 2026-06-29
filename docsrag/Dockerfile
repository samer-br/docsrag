FROM python:3.11-slim

WORKDIR /app

# System deps kept minimal; sentence-transformers pulls torch (CPU) as a wheel.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build the index at image build time so the container starts ready to serve.
# (For a real corpus you'd mount data and build at deploy time instead.)
RUN python -m app.ingest

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
