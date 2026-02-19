import os, subprocess, uuid
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

EXPORT_DIR = "exports"
if not os.path.exists(EXPORT_DIR): os.makedirs(EXPORT_DIR)

async def quick_video(tema, video_id):
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    # Usando uma imagem fixa de placeholder para não depender de sites externos que caem
    img = "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1280&h=720&auto=format&fit=crop"
    try:
        # Cria um vídeo super rápido de 5 segundos
        cmd = ['ffmpeg', '-y', '-loop', '1', '-i', img, '-c:v', 'libx264', '-t', '5', '-pix_fmt', 'yuv420p', video_path]
        subprocess.run(cmd, check=True)
    except: pass

@app.post("/gerar-video")
async def gerar(tema: str, tasks: BackgroundTasks):
    v_id = str(uuid.uuid4())
    tasks.add_task(quick_video, tema, v_id)
    return {"id": v_id}

@app.get("/status/{v_id}")
def status(v_id: str):
    if os.path.exists(f"{EXPORT_DIR}/{v_id}.mp4"):
        return {"status": "pronto", "url": f"https://webdark.onrender.com/download/{v_id}"}
    return {"status": "processando"}

@app.get("/download/{v_id}")
def dl(v_id: str): return FileResponse(f"{EXPORT_DIR}/{v_id}.mp4")
