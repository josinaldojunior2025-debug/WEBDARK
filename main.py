import os, subprocess, uuid
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

EXPORT_DIR = "exports"
if not os.path.exists(EXPORT_DIR): os.makedirs(EXPORT_DIR)

async def video_ultra_rapido(video_id):
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    try:
        # Cria um vídeo de 3 segundos com uma cor sólida (preto) - SEM DEPENDER DE INTERNET
        cmd = [
            'ffmpeg', '-y', 
            '-f', 'lavfi', '-i', 'color=c=black:s=1280x720:d=3', 
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', 
            video_path
        ]
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Erro: {e}")

@app.post("/gerar-video")
async def gerar(tema: str, tasks: BackgroundTasks):
    v_id = str(uuid.uuid4())
    tasks.add_task(video_ultra_rapido, v_id)
    return {"id": v_id}

@app.get("/status/{v_id}")
def status(v_id: str):
    if os.path.exists(f"{EXPORT_DIR}/{v_id}.mp4"):
        return {"status": "pronto", "url": f"https://webdark.onrender.com/download/{v_id}"}
    return {"status": "processando"}

@app.get("/download/{v_id}")
def dl(v_id: str): 
    return FileResponse(f"{EXPORT_DIR}/{v_id}.mp4", media_type='video/mp4')
