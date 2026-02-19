FROM python:3.9-slim

# Instala o FFmpeg (necessário para o vídeo)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala as bibliotecas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código
COPY . .

# Comando para iniciar o servidor na porta correta
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
