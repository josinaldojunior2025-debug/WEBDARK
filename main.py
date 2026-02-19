import asyncio
import edge_tts
import os
import subprocess
import uuid
import requests
import google.generativeai as genai
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Configuração da sua API Key do Gemini
genai.configure(api_key="AIzaSyDuAHwVxGDHauu1XU-m8HPy-48mDdrhyeM")
gemini = genai.GenerativeModel('gemini-1.5-flash')

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

EXPORT_DIR = "exports"
if not os.path.exists(EXPORT_DIR): os.makedirs(EXPORT_DIR)

def buscar_imagem_otimizada(prompt_melhorado, path):
    """Usa o prompt gerado pela IA para buscar uma imagem precisa"""
    # Adicionamos 'cinematic' e 'high resolution' para garantir qualidade
    url = f"https://loremflickr.com/1280/720/{prompt_melhorado.replace(' ', ',')}"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            return True
    except: return False
    return False

async def process_video_gemini(tema, video_id):
    audio_path = f"{EXPORT_DIR}/{video_id}.mp3"
    image_path = f"{EXPORT_DIR}/{video_id}.jpg"
    video_path = f"{EXPORT_DIR}/{video_id}.mp4"
    
    try:
        # 1. IA cria o Roteiro e o Prompt de busca
        response = gemini.generate_content(
            f"Para o tema '{tema}', responda em duas linhas separadas por '|': "
            f"Linha 1: Uma frase curta e impactante para narração (máximo 10 palavras). "
            f"Linha 2: Três palavras-chave em inglês para busca de imagem cinematográfica."
        )
        
        # Divide a resposta da IA
        conteudo = response.text.split('|')
        roteiro_ia = conteudo[0].strip()
        tags_imagem = conteudo[1].strip() if len(conteudo) > 1 else tema

        # 2. IA define a imagem e fazemos o download
        buscar_imagem_otimizada(tags_imagem, image_path)

        # 3. Gerar voz MASCULINA (Donaldo) com o roteiro da IA
        communicate = edge_tts.Communicate(roteiro_ia, "pt-BR-DonaldoNeural")
        await communicate.save(audio_path)

        # 4. Montar vídeo (7 segundos)
        # Adicionei um fundo musical de suspense leve direto no FFmpeg
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', image_path,
            '-i', audio_path,
            '-f', 'lavfi', '-i', 'sine=frequency=100:duration=7', # Tom grave de fundo
            '-filter_complex', "[1:a][2:a]amix=inputs=2:duration=first[aout]",
            '-c:v', 'libx264', '-t', '7', 
            '-pix_fmt', 'yuv420p', '-vf', 'scale=1280:720',
            '-map', '0:v', '-map', '[aout]', '-c:a', 'aac', '-shortest', video_path
        ]
        subprocess.run(cmd, check=True)
        
        # Limpar temporários
        if os.path.exists(audio_path): os.remove(audio_path)
        if os.path.exists(image_path): os.remove(image_path)

    except Exception as e:
        print(f"Erro no processamento IA: {e}")

@app.post("/gerar-video")
async def gerar(tema: str, tasks: BackgroundTasks):
    v_id = str(uuid.uuid4())
    tasks.add_task(process_video_gemini, tema, v_id)
    return {"id": v_id}

@app.get("/status/{v_id}")
def status(v_id: str):
    if os.path.exists(f"{EXPORT_DIR}/{v_id}.mp4"):
        return {"status": "pronto", "url": f"https://webdark.onrender.com/download/{v_id}"}
    return {"status": "processando"}

@app.get("/download/{v_id}")
def dl(v_id: str):
    return FileResponse(f"{EXPORT_DIR}/{v_id}.mp4", media_type='video/mp4')
