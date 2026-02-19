import asyncio, edge_tts, os, subprocess, uuid, requests
import google.generativeai as genai
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Sua chave de API
genai.configure(api_key="AIzaSyDuAHwVxGDHauu1XU-m8HPy-48mDdrhyeM")
model = genai.GenerativeModel('gemini-1.5-flash')

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

EXPORT_DIR = "exports"
if not os.path.exists(EXPORT_DIR): os.makedirs(EXPORT_DIR)

async def gerar_video_blindado(tema, video_id):
    audio_path = f"{EXPORT_DIR}/{video_id}.mp3"
    image_path = f"{EXPORT_DIR}/{video_id}.jpg"
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    
    try:
        # 1. Gemini cria o roteiro e tags de busca
        prompt = f"Tema: {tema}. Responda apenas: FRASE_CURTA | 3_TAGS_INGLES"
        response = model.generate_content(prompt)
        res_text = response.text.split('|')
        
        texto = res_text[0].strip() if len(res_text) > 0 else f"Sobre {tema}"
        tags = res_text[1].strip() if len(res_text) > 1 else f"{tema},cinematic"

        # 2. Busca de imagem mais rígida para evitar erros (como o do gato/palhaço)
        img_url = f"https://source.unsplash.com/1280x720/?{tags.replace(' ', '')},religion,historical"
        img_data = requests.get(img_url, timeout=15).content
        with open(image_path, 'wb') as f: f.write(img_data)

        # 3. Voz MASCULINA (Antonio) - Garantindo a mudança
        communicate = edge_tts.Communicate(texto, "pt-BR-AntonioNeural")
        await communicate.save(audio_path)

        # 4. FFmpeg rápido (7 segundos)
        cmd = ['ffmpeg', '-y', '-loop', '1', '-i', image_path, '-i', audio_path, 
               '-c:v', 'libx264', '-t', '7', '-pix_fmt', 'yuv420p', '-vf', 'scale=1280:720', 
               '-c:a', 'aac', '-shortest', video_path]
        subprocess.run(cmd, check=True)
    except: pass

@app.post("/gerar-video")
async def gerar(tema: str, tasks: BackgroundTasks):
    v_id = str(uuid.uuid4())
    tasks.add_task(gerar_video_blindado, tema, v_id)
    return {"id": v_id}

@app.get("/status/{v_id}")
def status(v_id: str):
    if os.path.exists(f"{EXPORT_DIR}/{v_id}.mp4"):
        return {"status": "pronto", "url": f"https://webdark.onrender.com/download/{v_id}"}
    return {"status": "processando"}

@app.get("/download/{v_id}")
def dl(v_id: str): return FileResponse(f"{EXPORT_DIR}/{v_id}.mp4")
