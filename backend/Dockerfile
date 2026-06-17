FROM python:3.11-slim

WORKDIR /app
ARG ENV_MODE=development
ENV ENV_MODE=${ENV_MODE}
ENV PORT=8000
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System deps for whisper (ffmpeg required for audio)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install PyTorch CPU-only first (smaller, faster download)
RUN pip install --no-cache-dir torch==2.3.0 torchaudio==2.3.0 \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir 'setuptools<81' 'wheel<0.46'

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "if [ \"$ENV_MODE\" = \"production\" ]; then exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1; else exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --reload; fi"]
