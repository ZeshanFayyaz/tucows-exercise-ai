# 1. Use a lightweight Python image
FROM python:3.12-slim

# 2. Set working directory
WORKDIR /app

# 3. Install system dependencies for numpy and faiss
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements
COPY requirements.txt .

# 5. Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy project code
COPY src/ src/
COPY data/ data/
COPY tests/ tests/
COPY ask.sh .
COPY README.md .

# 7. Expose FastAPI port
EXPOSE 8000

# 8. Run FastAPI server
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
