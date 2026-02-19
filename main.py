import asyncio
import edge_tts
import os
import subprocess
import uuid
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

EXPORT_DIR = "exports"
if not os.path.exists(EXPORT_DIR): os.makedirs(EXPORT_DIR)

async def process_video_real(tema, video_id):
    audio_path = f"{EXPORT_DIR}/{video_id}.mp3"
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    
    # Usando Unsplash para imagem rápida e estável
    image_url = f"https://images.unsplash.com/photo-1509248961158-e54f6934749c?q=80&w=1280&h=720&auto=format&fit=crop"
    
    try:
        # 1. Gera a voz narrativa (Francisca)
        texto = f"Explorando o mistério sobre {tema}. O conhecimento liberta a mente."
        communicate = edge_tts.Communicate(texto, "pt-BR-FranciscaNeural")
        await communicate.save(audio_path)

        # 2. Monta o vídeo (8 segundos, sem efeitos pesados para garantir o sucesso)
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', image_url,
            '-i', audio_path,
            '-c:v', 'libx264', '-t', '8', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', video_path
        ]
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Erro no processamento: {e}")

@app.post("/gerar-video")
async def gerar(tema: str, tasks: BackgroundTasks):
    v_id = str(uuid.uuid4())
    tasks.add_task(process_video_real, tema, v_id)
    return {"id": v_id}

@app.get("/status/{v_id}")
def status(v_id: str):
    if os.path.exists(f"{EXPORT_DIR}/{v_id}.mp4"):
        return {"status": "pronto", "url": f"https://webdark.onrender.com/download/{v_id}"}
    return {"status": "processando"}

@app.get("/download/{v_id}")
def dl(v_id: str):
    return FileResponse(f"{EXPORT_DIR}/{v_id}.mp4", media_type='video/mp4')
