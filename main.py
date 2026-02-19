import asyncio
import edge_tts
import os
import subprocess
import uuid
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- CONFIGURAÇÃO DE SEGURANÇA (CORS) ---
# Isso permite que sua interface index.html fale com o Render
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

# --- FUNÇÃO QUE GERA O VÍDEO ---
async def process_video(tema: str, video_id: str):
    audio_path = f"{EXPORT_DIR}/{video_id}.mp3"
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    
    # Imagem automática baseada no tema (Pollinations AI)
    image_url = f"https://image.pollinations.ai/prompt/cinematic_scene_about_{tema.replace(' ', '_')}?width=1280&height=720&nologo=true"
    
    try:
        # 1. Gerar Áudio Grátis (Voz da Francisca)
        texto_video = f"Olá! Este é um vídeo automático sobre {tema}. Espero que goste do resultado!"
        communicate = edge_tts.Communicate(texto_video, "pt-BR-FranciscaNeural")
        await communicate.save(audio_path)

        # 2. Comando FFmpeg para criar o vídeo 720p com efeito de Zoom
        # O comando baixa a imagem, coloca o áudio e faz o efeito zoompan
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', image_url,
            '-i', audio_path,
            '-vf', "zoompan=z='min(zoom+0.0015,1.5)':d=125:s=1280x720,format=yuv420p",
            '-c:v', 'libx264', '-t', '10', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', video_path
        ]
        
        # Executa a criação do vídeo
        subprocess.run(cmd, check=True)
        print(f"Vídeo {video_id} criado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao processar vídeo: {e}")

# --- ROTAS DA API ---

@app.get("/")
def home():
    return {"status": "Servidor WizardCut Online", "docs": "/docs"}

@app.post("/gerar-video")
async def start_generation(tema: str, background_tasks: BackgroundTasks):
    video_id = str(uuid.uuid4())
    # Roda o processamento em segundo plano para não travar o site
    background_tasks.add_task(process_video, tema, video_id)
    return {
        "status": "processando", 
        "id": video_id, 
        "mensagem": "O vídeo está sendo criado. Verifique os logs do Render."
    }

# Rota para ver se o arquivo já existe
@app.get("/status/{video_id}")
def check_status(video_id: str):
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    if os.path.exists(video_path):
        return {"status": "pronto", "url": f"
