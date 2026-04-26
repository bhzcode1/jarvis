FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# System deps:
# - ffmpeg: faster-whisper
# - portaudio + libsndfile: sounddevice/soundfile
# - espeak-ng: pyttsx3 (linux driver)
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
      portaudio19-dev \
      libsndfile1 \
      espeak-ng \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt /workspace/requirements.txt
RUN python -m pip install -r /workspace/requirements.txt

COPY . /workspace

CMD ["python", "-m", "app.main"]
