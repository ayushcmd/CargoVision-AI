# CargoVision AI — Production Linux CPU Container
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    HOST=0.0.0.0 \
    ENV=production \
    MAX_UPLOAD_SIZE_MB=35 \
    MAX_CONCURRENT_JOBS=1

# Install system dependencies for OpenCV, FFmpeg, and health probes
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up non-root user (UID 1000 matches Hugging Face Spaces and standard security practices)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python requirements
COPY deployment/requirements.txt /app/deployment/requirements.txt
RUN pip install --no-cache-dir -r /app/deployment/requirements.txt

# Pre-warm EasyOCR weights so they are baked into the image (prevents download on every cold-start)
USER appuser
RUN python -c "import easyocr; easyocr.Reader(['en'], gpu=False)"
USER root

# Copy application source code and models
COPY --chown=appuser:appuser "full model" /app/"full model"
COPY --chown=appuser:appuser "wagon number detection" /app/"wagon number detection"
COPY --chown=appuser:appuser evaluation /app/evaluation
COPY --chown=appuser:appuser run.py /app/run.py

# Create data directories with appropriate permissions
RUN mkdir -p /app/data/Video /app/data/detection /app/data/reports \
    && chown -R appuser:appuser /app/data

USER appuser

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start FastAPI server via run.py
CMD ["python", "run.py"]
