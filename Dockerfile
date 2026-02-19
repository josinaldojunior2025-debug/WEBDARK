FROM python:3.9-slim

# Instala o FFmpeg no sistema Linux do servidor
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . .

RUN pip install fastapi uvicorn edge_tts requests

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
