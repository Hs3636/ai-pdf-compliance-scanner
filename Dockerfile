FROM python:3.11-slim

# Install system dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Suppress ONNX GPU discovery warning and heavily optimize memory for 512MB containers
ENV CUDA_VISIBLE_DEVICES=""
ENV ORT_LOGGING_LEVEL=3
ENV MALLOC_ARENA_MAX=2
ENV OMP_NUM_THREADS=1

# Pre-download the GLiNER model during the build phase so it doesn't happen at runtime
RUN python -c "from gliner import GLiNER; GLiNER.from_pretrained('urchade/gliner_small-v2.1')"

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit app
CMD ["python", "-m", "streamlit", "run", "app/ui/main.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
