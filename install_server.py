import os
import sys
import subprocess
import shutil
import importlib.util
import time

def print_header(text):
    print(f"\n{'='*60}\n{text}\n{'='*60}")

print_header("🌐 ARMA REFORGER AI GAME MASTER - SMART INSTALLER")

# ==========================================
# 1. VERIFICAR DEPENDENCIAS DE PYTHON
# ==========================================
print("[EN] Checking Python dependencies...")
print("[ES] Verificando dependencias de Python...")

required_packages = ["fastapi", "uvicorn", "httpx", "pydantic"]
missing_packages = []

for package in required_packages:
    if importlib.util.find_spec(package) is None:
        missing_packages.append(package)

if missing_packages:
    print(f"[-] Missing packages detected / Paquetes faltantes: {missing_packages}. Installing...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
        print("✔ Libraries installed successfully / Librerías instaladas.")
    except Exception as e:
        print(f"❌ Error installing libraries / Error instalando librerías: {e}")
        sys.exit(1)
else:
    print("✔ All Python libraries are already installed. Skipping. / Todas las librerías ya están instaladas. Omitiendo.")

# ==========================================
# 2. VERIFICAR E INSTALAR OLLAMA
# ==========================================
print("\n[EN] Checking Ollama installation...")
print("[ES] Verificando instalación de Ollama...")

if shutil.which("ollama") is None:
    print("[-] Ollama not found. Installing via PowerShell... / Ollama no encontrado. Instalando...")
    try:
        subprocess.run(["powershell", "-Command", "irm https://ollama.com/install.ps1 | iex"], check=True)
        print("✔ Ollama installed successfully / Ollama instalado.")
    except Exception as e:
        print(f"❌ Error installing Ollama / Error instalando Ollama: {e}")
else:
    print("✔ Ollama is already installed. Skipping. / Ollama ya está instalado. Omitiendo.")

# ==========================================
# 3. ASEGURAR QUE OLLAMA ESTÁ ACTIVO Y CARGAR MODELO
# ==========================================
print("\n[EN] Ensuring Ollama service is running and loading 'llama3.1'...")
print("[ES] Asegurando que el servicio Ollama está activo y cargando 'llama3.1'...")

try:
    # Intenta listar los modelos para ver si el servidor responde
    subprocess.run(["ollama", "list"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except subprocess.CalledProcessError:
    # Si falla, significa que el servicio no está corriendo en segundo plano
    print("[-] Starting Ollama background service... / Iniciando servicio en segundo plano...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5) # Esperamos 5 segundos a que arranque

print("[-] Pulling model 'llama3.1' (~4.7GB if not downloaded) / Descargando modelo 'llama3.1'...")
try:
    subprocess.run(["ollama", "pull", "llama3.1"], check=True)
    print("✔ Model 'llama3.1' is loaded and ready / Modelo cargado y listo.")
except Exception as e:
    print(f"❌ Error pulling model / Error descargando modelo: {e}")

# ==========================================
# 4. CREAR ESTRUCTURA DE CARPETAS Y ARCHIVOS
# ==========================================
base_dir = os.path.join(os.getcwd(), "ArmaAI_Server")
folders = ["Backend", "Web"]

print(f"\n[+] Generating server files at / Generando archivos en: {base_dir}")
for folder in folders:
    os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

files = {
    r"Backend\prefabs.json": """{
  "ussr_infantry": "{318DF1CC3A26DCE3}Prefabs/Characters/Factions/OPFOR/USSR_Army/Character_USSR_Rifleman.et",
  "us_infantry": "{26A9756790E31D6E}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Rifleman.et",
  "fia_infantry": "{84B40583F4D1B7A3}Prefabs/Characters/Factions/INDFOR/FIA/Character_FIA_Rifleman.et",
  "ussr_btr70": "{C012BB3488BEA3C2}Prefabs/Vehicles/Wheeled/BTR70/BTR70.et"
}""",

    r"Backend\main.py": """import json
import asyncio
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

command_queue = []
action_history = []

try:
    with open("prefabs.json", "r") as f:
        PREFABS = json.load(f)
except FileNotFoundError:
    PREFABS = {}
AVAILABLE_UNITS = list(PREFABS.keys())

SYSTEM_PROMPT = f\"\"\"
Eres el Game Master táctico de Arma Reforger. Genera eventos realistas.
LIMITES: X y Z entre 3000 y 9000. Centro: X:6400, Z:6400.
UNIDADES: {AVAILABLE_UNITS}

Responde SOLO con JSON:
{{
  "action": "spawn",
  "unit_id": "<unidad>",
  "spawn_x": 6400,
  "spawn_y": 500,
  "spawn_z": 6400,
  "intensity": 1,
  "internal_thought": "Motivo"
}}
IMPORTANTE: "spawn_y" debe ser SIEMPRE 500. Si no actúas, usa "action": "idle".
\"\"\"

class ManualOrder(BaseModel):
    order: str

async def ask_ollama(prompt_text):
    payload = {"model": "llama3.1", "system": SYSTEM_PROMPT, "prompt": prompt_text, "stream": False, "format": "json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://localhost:11434/api/generate", json=payload, timeout=60.0)
            data = json.loads(response.json()["response"])
            
            unit_id = data.get("unit_id")
            if unit_id in PREFABS:
                data["prefab_path"] = PREFABS[unit_id]
                command_queue.append(data)
                msg = f"IA: {data.get('internal_thought', 'Accion')} -> {unit_id} en X:{data.get('spawn_x')}|Y:{data.get('spawn_y')}|Z:{data.get('spawn_z')}"
                action_history.append(msg)
                print(f"[NUEVA ORDEN] {msg}")
        except Exception as e:
            print(f"Error con Ollama: {e}")

async def autonomous_loop():
    while True:
        await asyncio.sleep(60)
        await ask_ollama("Analiza y decide si enviar tropas. Varía las posiciones y usa spawn_y en 500.")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(autonomous_loop())

@app.post("/manual_command")
async def manual_command(order: ManualOrder):
    await ask_ollama(f"ORDEN HUMANA: '{order.order}'. (spawn_y en 500).")
    return {"status": "ok"}

@app.get("/arma_sync", response_class=PlainTextResponse)
async def arma_sync():
    if command_queue:
        cmd = command_queue.pop(0)
        if cmd.get("action") == "spawn" and "prefab_path" in cmd:
            return f"SPAWN|{cmd['prefab_path']}|{cmd.get('spawn_x',6400)}|{cmd.get('spawn_y',500)}|{cmd.get('spawn_z',6400)}"
    return "NONE"

@app.get("/status")
async def get_status():
    return {"history": action_history[-15:]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",

    r"Web\index.html": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><title>Arma AI Game Master</title>
    <style>
        body { background-color: #0d1117; color: #58a6ff; font-family: monospace; padding: 20px; }
        .panel { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 8px; margin-bottom: 20px;}
        input, button { padding: 10px; font-family: monospace; }
        input { width: 60%; background: #010409; color: #c9d1d9; border: 1px solid #30363d; }
        button { background: #238636; color: white; border: none; cursor: pointer; font-weight: bold; }
        li { padding: 8px 0; border-bottom: 1px solid #30363d; font-size: 0.9em; }
        .ia-prefix { color: #ff7b72; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🌐 ARMA REFORGER - AI COMMANDER</h1>
    <div class="panel">
        <h3>Manual Order</h3>
        <input type="text" id="orderInput" placeholder="Ej: Ataca la base norte con un BTR">
        <button onclick="sendOrder()">SEND ORDER</button>
    </div>
    <div class="panel">
        <h3>Server Log & AI Thoughts</h3>
        <ul id="historyList"></ul>
    </div>
    <script>
        async function sendOrder() {
            const input = document.getElementById('orderInput');
            await fetch('http://127.0.0.1:8000/manual_command', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ order: input.value })
            });
            input.value = '';
        }
        async function updateLog() {
            try {
                const res = await fetch('http://127.0.0.1:8000/status');
                const data = await res.json();
                const list = document.getElementById('historyList');
                list.innerHTML = '';
                data.history.reverse().forEach(item => {
                    let li = document.createElement('li');
                    li.innerHTML = `<span class="ia-prefix">[SERVER]</span> ${item}`;
                    list.appendChild(li);
                });
            } catch(e) {}
        }
        setInterval(updateLog, 2000);
    </script>
</body>
</html>""",

    r"START_SERVER.bat": """@echo off
title Arma Reforger AI - Master Server
color 0A
echo [1/3] Starting AI Engine (Ollama)...
start "Ollama Server" cmd /c "ollama serve"
timeout /t 3 /nobreak >nul

echo [2/3] Starting Python Backend...
start "Backend Python AI" cmd /k "cd Backend && python main.py"
timeout /t 4 /nobreak >nul

echo [3/3] Opening Web Control Panel...
start Web\index.html
echo  ALL SYSTEMS ONLINE! Start your Arma server.
pause
"""
}

# Crear archivos
for relative_path, content in files.items():
    absolute_path = os.path.join(base_dir, relative_path)
    with open(absolute_path, "w", encoding="utf-8") as f:
        f.write(content)

print_header("✅ INSTALLATION COMPLETE / INSTALACIÓN COMPLETADA")
print(f"Server files generated at / Archivos generados en: {base_dir}")
print("Double click 'START_SERVER.bat' to run the system!")