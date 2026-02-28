import os
import json
import sys

print("====================================================")
print("  CONSTRUYENDO ARMA AI COMMANDER (MODULAR)...")
print("====================================================")

# 1. Crear carpetas
os.makedirs("Backend", exist_ok=True)
os.makedirs("Web", exist_ok=True)
print("[+] Carpetas 'Backend' y 'Web' creadas.")

# 2. Generar prefabs.json
prefabs = {
    "US Equipo de Municion": "{F72EF3429D8C8DF5}Prefabs/Groups/BLUFOR/Group_US_AmmoTeam.et",
    "US Equipo de Ingenieros": "{6B2A6EE5002D200F}Prefabs/Groups/BLUFOR/Group_US_EngineerTeam.et",
    "US Escuadra de Fuego": "{84E5BBAB25EA23E5}Prefabs/Groups/BLUFOR/Group_US_FireTeam.et",
    "US Equipo de Ametralladoras": "{958039B857396B7B}Prefabs/Groups/BLUFOR/Group_US_MachineGunTeam.et",
    "US Equipo de Guardia": "{0A8E20F50DA233E1}Prefabs/Groups/BLUFOR/Group_US_FireTeam_Guard.et",
    "US Seccion Medica": "{EF62027CC75A7459}Prefabs/Groups/BLUFOR/Group_US_MedicalSection.et",
    "US Equipo de Reconocimiento": "{F65B7BB712F46FEE}Prefabs/Groups/BLUFOR/Group_US_ReconTeam.et",
    "US Equipo de Centinelas": "{3BF36BDEEB33AEC9}Prefabs/Groups/BLUFOR/Group_US_SentryTeam.et",
    "US Escuadra de Fusileros": "{DDF3799FA1387848}Prefabs/Groups/BLUFOR/Group_US_RifleSquad.et",
    "US Equipo de Francotiradores": "{D807C7047E818488}Prefabs/Groups/BLUFOR/Group_US_SniperTeam.et",
    "US Equipo de Fuego Ligero": "{FCF7F5DC4F83955C}Prefabs/Groups/BLUFOR/Group_US_LightFireTeam.et",
    "US Cuartel de Peloton": "{B7AB5D3F8A7ADAE4}Prefabs/Groups/BLUFOR/Group_US_PlatoonHQ.et",
    "US Equipo de Zapadores": "{9624D2B39397E148}Prefabs/Groups/BLUFOR/Group_US_SapperTeam.et",
    "US Equipo de Lanzagranadas": "{DE747BC9217D383C}Prefabs/Groups/BLUFOR/Group_US_Team_GL.et",
    "US Equipo Antitanque Ligero": "{FAEA8B9E1252F56E}Prefabs/Groups/BLUFOR/Group_US_Team_LAT.et",
    "US Equipo de Supresion": "{81B6DBF2B88545F5}Prefabs/Groups/BLUFOR/Group_US_Team_Suppress.et",
    "US Equipo de Transporte": "{727C134094032B1F}Prefabs/Groups/BLUFOR/Group_US_Transport.et"
}
with open("prefabs.json", "w", encoding="utf-8") as f:
    json.dump(prefabs, f, indent=4)
print("[+] prefabs.json generado (17 unidades).")

# 3. Generar Backend/config.py
config_py = """import json
HOST = '0.0.0.0'
PORT = 8000
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL_NAME = 'llama3.1'
AI_TIMEOUT = 40.0
DB_PATH = 'war_room.db'
PREFABS_PATH = '../prefabs.json'

def load_prefabs():
    try:
        with open(PREFABS_PATH, 'r', encoding='utf-8') as f: return json.load(f)
    except:
        return {'US Escuadra de Fusileros': '{DDF3799FA1387848}Prefabs/Groups/BLUFOR/Group_US_RifleSquad.et'}

PREFABS = load_prefabs()
"""
with open("Backend/config.py", "w", encoding="utf-8") as f: f.write(config_py)

# 4. Generar Backend/database.py
database_py = """import sqlite3
from config import DB_PATH

class WarDatabase:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS telemetry (id INTEGER PRIMARY KEY CHECK (id=1), px REAL, pz REAL, mission TEXT)')
        c.execute('INSERT OR IGNORE INTO telemetry (id, px, pz, mission) VALUES (1, 4800.0, 6300.0, "Game Master")')
        conn.commit()
        conn.close()

    def update_telemetry(self, px, pz, m):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('UPDATE telemetry SET px=?, pz=?, mission=? WHERE id=1', (px, pz, m))
        conn.commit()
        conn.close()

    def get_pos(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT px, pz, mission FROM telemetry WHERE id=1')
        res = c.fetchone()
        conn.close()
        return res if res else (4800.0, 6300.0, "Game Master")
"""
with open("Backend/database.py", "w", encoding="utf-8") as f: f.write(database_py)

# 5. Generar Backend/ai_agent.py
ai_agent_py = """import json, httpx
from config import OLLAMA_URL, MODEL_NAME, AI_TIMEOUT, PREFABS

class ZeusAIAgent:
    def __init__(self, war_db, command_queue, action_history):
        self.war_db = war_db
        self.queue = command_queue
        self.history = action_history

    async def process_order(self, prompt):
        px, pz, mission = self.war_db.get_pos()
        sys_prompt = f"Eres Zeus de Arma Reforger. Jugador en X:{int(px)} Z:{int(pz)}. Mision: {mission}. Responde SOLO JSON con unit_id ({list(PREFABS.keys())}), grid_x, grid_z e internal_thought."
        
        payload = {'model': MODEL_NAME, 'prompt': prompt, 'system': sys_prompt, 'stream': False, 'format': 'json'}
        
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(OLLAMA_URL, json=payload, timeout=AI_TIMEOUT)
                data = json.loads(r.json()['response'])
                uid = data.get('unit_id')
                gx, gz = data.get('grid_x', -1), data.get('grid_z', -1)
                
                final_x = px + 15 if gx <= 0 else (gx * 100 if gx < 1000 else gx)
                final_z = pz + 15 if gz <= 0 else (gz * 100 if gz < 1000 else gz)

                if uid in PREFABS:
                    self.queue.append({'path': PREFABS[uid], 'x': final_x, 'z': final_z})
                    self.history.append(f"🧠 IA: {data.get('internal_thought', 'Despliegue tactico')} -> {uid}")
            except Exception as e:
                self.history.append(f"❌ ERROR IA: {str(e)}")
"""
with open("Backend/ai_agent.py", "w", encoding="utf-8") as f: f.write(ai_agent_py)

# 6. Generar Backend/main.py
main_py = """import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from config import HOST, PORT
from database import WarDatabase
from ai_agent import ZeusAIAgent

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

command_queue = []
action_history = []
war_db = WarDatabase()
zeus_ai = ZeusAIAgent(war_db, command_queue, action_history)

class ManualOrder(BaseModel): order: str

@app.post('/manual_command')
async def manual_command(o: ManualOrder):
    action_history.append(f"👤 ORDEN: {o.order}")
    await zeus_ai.process_order(o.order)
    return {'status': 'ok'}

@app.get('/arma_sync', response_class=PlainTextResponse)
async def arma_sync(px: float = 0, pz: float = 0, m: str = "GM"):
    war_db.update_telemetry(px, pz, m)
    if command_queue:
        c = command_queue.pop(0)
        return f"SPAWN|{c['path']}|{c['x']}|0|{c['z']}"
    return 'NONE'

@app.get('/status')
async def status():
    return {'history': action_history[-15:]}

if __name__ == '__main__':
    uvicorn.run(app, host=HOST, port=PORT)
"""
with open("Backend/main.py", "w", encoding="utf-8") as f: f.write(main_py)

# 7. Generar Web/index.html
index_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Arma Reforger - IA Zeus</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #00ff00; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background-color: #1e1e1e; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,255,0,0.1); border: 1px solid #00ff00; }
        h1 { text-align: center; font-size: 24px; letter-spacing: 2px; }
        .log-box { background-color: #000; padding: 15px; height: 350px; overflow-y: auto; border: 1px solid #333; margin-bottom: 20px; font-family: monospace; }
        .log-entry { margin: 5px 0; border-bottom: 1px dashed #222; padding-bottom: 5px;}
        input[type="text"] { width: calc(100% - 130px); padding: 12px; background: #000; border: 1px solid #00ff00; color: #0f0; font-size: 16px; }
        button { padding: 12px 20px; background-color: #00ff00; color: #000; border: none; cursor: pointer; font-weight: bold; font-size: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Zeus AI Commander</h1>
        <div class="log-box" id="logs"></div>
        <div>
            <input type="text" id="order-input" placeholder="Orden para la IA..." onkeypress="if(event.key==='Enter') sendOrder()">
            <button onclick="sendOrder()">Enviar</button>
        </div>
    </div>
    <script>
        let lastLength = 0;
        async function fetchLogs() {
            try {
                const res = await fetch('http://127.0.0.1:8000/status');
                const data = await res.json();
                if (data.history.length !== lastLength) {
                    const box = document.getElementById('logs');
                    box.innerHTML = '';
                    data.history.forEach(msg => {
                        const div = document.createElement('div');
                        div.className = 'log-entry';
                        if(msg.includes('❌')) div.style.color = '#ff4444';
                        else if(msg.includes('👤')) div.style.color = '#aaaaaa';
                        else if(msg.includes('🧠')) div.style.color = '#00ffff';
                        div.textContent = msg;
                        box.appendChild(div);
                    });
                    lastLength = data.history.length;
                    box.scrollTop = box.scrollHeight;
                }
            } catch (e) {}
        }
        async function sendOrder() {
            const input = document.getElementById('order-input');
            if (!input.value.trim()) return;
            const text = input.value.trim(); input.value = '';
            await fetch('http://127.0.0.1:8000/manual_command', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ order: text }) });
            fetchLogs();
        }
        setInterval(fetchLogs, 1000); fetchLogs();
    </script>
</body>
</html>
"""
with open("Web/index.html", "w", encoding="utf-8") as f: f.write(index_html)
print("[+] Archivos de Backend y Web creados correctamente.")

# 8. Generar LANZAR_IA.bat
lanzar_bat = """@echo off
title Arma Reforger IA - MODO COMANDANTE
cd /d "%~dp0"
echo ==============================================
echo    SISTEMA TACTICO IA - ARMA REFORGER
echo ==============================================
echo.
echo [+] Abriendo Panel de Control...
if exist "Web\\index.html" ( start "" "Web\\index.html" )
echo [+] Entrando en la carpeta Backend...
cd Backend
echo [+] Iniciando Servidor Modular...
python3-64.exe main.py
pause
"""
with open("LANZAR_IA.bat", "w", encoding="utf-8") as f: f.write(lanzar_bat)
print("[+] LANZAR_IA.bat creado.")

print("====================================================")
print("  INSTALANDO LIBRERÍAS DE PYTHON...")
print("====================================================")
# Usamos exactamente el mismo ejecutable de Python que estás utilizando ahora
os.system(f'"{sys.executable}" -m pip install fastapi uvicorn httpx pydantic')

print("====================================================")
print(" ✅ ¡TODO LISTO! La arquitectura modular se ha creado.")
print(" Solo tienes que ejecutar LANZAR_IA.bat para arrancar.")
print("====================================================")