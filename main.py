import asyncio
import edge_tts
import os
import subprocess
import uuid
import requests
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

EXPORT_DIR = "exports"
if not os.path.exists(EXPORT_DIR): os.makedirs(EXPORT_DIR)

def download_imagem(tema, path):
    # Forçamos a busca por imagens bíblicas e históricas para evitar erros como o do palhaço
    search_term = f"biblical,{tema.replace(' ', ',')},historical"
    url = f"https://source.unsplash.com/1280x720/?{search_term}"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            return True
    except: return False
    return False

async def process_video_final(tema, video_id):
    audio_path = f"{EXPORT_DIR}/{video_id}.mp3"
    image_path = f"{EXPORT_DIR}/{video_id}.jpg"
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    
    try:
        # 1. Baixar imagem com filtros rígidos
        download_imagem(tema, image_path)

        # 2. Gerar voz MASCULINA (Donaldo é uma excelente opção masculina)
        texto = f"Refletindo sobre {tema}. Uma mensagem de fé para o seu dia."
        # Mudamos explicitamente para Donaldo para garantir que não volte para Francisca
        communicate = edge_tts.Communicate(texto, "pt-BR-DonaldoNeural")
        await communicate.save(audio_path)

        # 3. Montar vídeo (Exatos 7 segundos como você pediu)
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264', '-t', '7', 
            '-pix_fmt', 'yuv420p', '-vf', 'scale=1280:720',
            '-c:a', 'aac', '-shortest', video_path
        ]
        subprocess.run(cmd, check=True)
        
        # Limpar temporários
        if os.path.exists(audio_path): os.remove(audio_path)
        if os.path.exists(image_path): os.remove(image_path)
    except Exception as e:
        print(f"Erro: {e}")

@app.post("/gerar-video")
async def gerar(tema: str, tasks: BackgroundTasks):
    v_id = str(uuid.uuid4())
    tasks.add_task(process_video_final, tema, v_id)
    return {"id": v_id}

@app.get("/status/{v_id}")
def status(v_id: str):
    if os.path.exists(f"{EXPORT_DIR}/{v_id}.mp4"):
        return {"status": "pronto", "url": f"https://webdark.onrender.com/download/{v_id}"}
    return {"status": "processando"}

@app.get("/download/{v_id}")
def dl(v_id: str):
    return FileResponse(f"{EXPORT_DIR}/{v_id}.mp4", media_type='video/mp4')
