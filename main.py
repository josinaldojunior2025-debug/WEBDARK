import asyncio
import edge_tts
import os
import subprocess
import uuid
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()

# --- CONFIGURAÇÃO DE SEGURANÇA (CORS) ---
# Essencial para que a Vercel consiga conversar com o Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pasta para salvar os vídeos
EXPORT_DIR = "exports"
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)

# --- LOGICA DE GERAÇÃO DO VÍDEO ---
async def process_video(tema: str, video_id: str):
    audio_path = f"{EXPORT_DIR}/{video_id}.mp3"
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    
    # Imagem gerada automaticamente via IA (Pollinations)
    image_url = f"https://image.pollinations.ai/prompt/dark_cinematic_scene_about_{tema.replace(' ', '_')}?width=1280&height=720&nologo=true"
    
    try:
        # 1. Gerar Áudio (Voz Narrativa Francisca)
        texto = f"Iniciando relato sobre {tema}. Prepare-se para o que vem a seguir."
        communicate = edge_tts.Communicate(texto, "pt-BR-FranciscaNeural")
        await communicate.save(audio_path)

        # 2. Comando FFmpeg (Zoom Pan + Qualidade 720p)
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', image_url,
            '-i', audio_path,
            '-vf', "zoompan=z='min(zoom+0.0015,1.5)':d=125:s=1280x720,format=yuv420p",
            '-c:v', 'libx264', '-t', '10', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', video_path
        ]
        
        subprocess.run(cmd, check=True)
        print(f"Vídeo {video_id} finalizado com sucesso.")
        
    except Exception as e:
        print(f"Erro no processamento: {e}")

# --- ROTAS DA API ---

@app.get("/")
def home():
    return {"message": "Servidor WEBDARK Ativo", "status": "Online"}

@app.post("/gerar-video")
async def start_generation(tema: str, background_tasks: BackgroundTasks):
    video_id = str(uuid.uuid4())
    # O processamento roda em segundo plano para o site não travar
    background_tasks.add_task(process_video, tema, video_id)
    return {"status": "processando", "id": video_id}

@app.get("/status/{video_id}")
def check_status(video_id: str):
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    if os.path.exists(video_path):
        # Retorna o link direto para download (ajuste para sua URL do Render)
        return {"status": "pronto", "url": f"https://webdark.onrender.com/download/{video_id}"}
    return {"status": "ainda_processando"}

@app.get("/download/{video_id}")
def download_file(video_id: str):
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    if os.path.exists(video_path
