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

def download_imagem(url, path):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            return True
    except:
        return False
    return False

async def process_video_final(tema, video_id):
    audio_path = f"{EXPORT_DIR}/{video_id}.mp3"
    image_path = f"{EXPORT_DIR}/{video_id}.jpg"
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    
    # URL de imagem mais estável
    img_url = f"https://loremflickr.com/1280/720/dark,{tema.replace(' ', '')}"
    
    try:
        # 1. Baixar a imagem primeiro (Garante que ela exista)
        if not download_imagem(img_url, image_path):
            # Imagem de backup caso a busca falhe
            download_imagem("https://images.unsplash.com/photo-1516339901601-2e1b62dc0c45?q=80&w=1280&h=720&auto=format&fit=crop", image_path)

        # 2. Gerar a voz
        texto = f"Iniciando relato sobre {tema}. O mistério se revela agora."
        communicate = edge_tts.Communicate(texto, "pt-BR-FranciscaNeural")
        await communicate.save(audio_path)

        # 3. Montar o vídeo usando a imagem local (Acaba com o problema da tela preta)
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264', '-t', '7', 
            '-pix_fmt', 'yuv420p', '-vf', 'scale=1280:720',
            '-c:a', 'aac', '-shortest', video_path
        ]
        subprocess.run(cmd, check=True)
        
        # Limpar arquivos temporários para economizar espaço no Render
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
