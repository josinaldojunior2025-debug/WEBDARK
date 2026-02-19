import asyncio
import edge_tts
import os
import subprocess
import uuid
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()

# LIBERAÇÃO DE ACESSO (CORS) - ESSENCIAL PARA A VERCEL FUNCIONAR
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite que o link da Vercel fale com o Render
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXPORT_DIR = "exports"
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)

async def process_video(tema: str, video_id: str):
    audio_path = f"{EXPORT_DIR}/{video_id}.mp3"
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    image_url = f"https://image.pollinations.ai/prompt/dark_cinematic_scene_about_{tema.replace(' ', '_')}?width=1280&height=720&nologo=true"
    
    try:
        texto = f"Iniciando relato sobre {tema}. Prepare-se para o que vem a seguir."
        communicate = edge_tts.Communicate(texto, "pt-BR-FranciscaNeural")
        await communicate.save(audio_path)

        # Comando FFmpeg para criar o vídeo
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', image_url,
            '-i', audio_path,
            '-vf', "zoompan=z='min(zoom+0.0015,1.5)':d=125:s=1280x720,format=yuv420p",
            '-c:v', 'libx264', '-t', '10', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', video_path
        ]
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Erro: {e}")

@app.get("/")
def home():
    return {"status": "WEBDARK ONLINE"}

@app.post("/gerar-video")
async def start_generation(tema: str, background_tasks: BackgroundTasks):
    video_id = str(uuid.uuid4())
    background_tasks.add_task(process_video, tema, video_id)
    return {"status": "processando", "id": video_id}

@app.get("/status/{video_id}")
def check_status(video_id: str):
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    if os.path.exists(video_path):
        return {"status": "pronto", "url": f"https://webdark.onrender.com/download/{video_id}"}
    return {"status": "ainda_processando"}

@app.get("/download/{video_id}")
def download_file(video_id: str):
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    return FileResponse(video_path, media_type='video/mp4')
