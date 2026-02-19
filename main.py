from fastapi import FastAPI, BackgroundTasks
import edge_tts
import subprocess
import os
import uuid

app = FastAPI()

# Configuração de pastas
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

async def process_video(tema: str, video_id: str):
    audio_path = f"{EXPORT_DIR}/{video_id}.mp3"
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    # Link de imagem grátis (exemplo com Pollinations)
    image_url = f"https://image.pollinations.ai/prompt/cinematic_scene_about_{tema.replace(' ', '_')}?width=1280&height=720&nologo=true"
    
    # 1. Gerar Áudio (Grátis via Edge-TTS)
    communicate = edge_tts.Communicate(f"Hoje vamos falar sobre {tema}", "pt-BR-AntonioNeural")
    await communicate.save(audio_path)

    # 2. Comando FFmpeg (Zoom In + 720p)
    # Baixamos a imagem e aplicamos o zoom em um único comando
    cmd = [
        'ffmpeg', '-y',
        '-loop', '1', '-i', image_url,
        '-i', audio_path,
        '-vf', "zoompan=z='min(zoom+0.0015,1.5)':d=125:s=1280x720,format=yuv420p",
        '-c:v', 'libx264', '-t', '10', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', video_path
    ]
    subprocess.run(cmd)
    print(f"Vídeo {video_id} finalizado!")

@app.post("/gerar-video")
async def start_generation(tema: str, background_tasks: BackgroundTasks):
    video_id = str(uuid.uuid4())
    background_tasks.add_task(process_video, tema, video_id)
    return {"status": "processando", "id": video_id, "url": f"/download/{video_id}"}

@app.get("/download/{video_id}")
def download_video(video_id: str):
    return {"file_link": f"https://seu-dominio.com/exports/{video_id}.mp4"}
