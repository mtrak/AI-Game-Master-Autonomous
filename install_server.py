import os

def crear_instalador():
    base_dir = "ArmaAI_Server"
    backend_dir = os.path.join(base_dir, "Backend")
    panel_dir = os.path.join(base_dir, "Panel")

    os.makedirs(backend_dir, exist_ok=True)
    os.makedirs(panel_dir, exist_ok=True)

    # 1. EL CEREBRO DE LA IA (main.py)
    main_py_content = r"""import json
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

command_queue = []
action_history = []

live_telemetry = {
    "player_x": 4800.0,
    "player_z": 6300.0,
    "mission_name": "Game Master"
}

try:
    with open('../prefabs.json', 'r') as f:
        PREFABS = json.load(f)
except FileNotFoundError:
    PREFABS = {}
AVAILABLE_UNITS = list(PREFABS.keys())

class ManualOrder(BaseModel):
    order: str

async def ask_ollama(prompt_text):
    dynamic_prompt = f'''
    Eres el Game Master tactico de Arma Reforger.
    DATOS DEL RADAR EN TIEMPO REAL:
    - Mision actual: {live_telemetry['mission_name']}
    - Coordenadas exactas del jugador: X:{int(live_telemetry['player_x'])} Z:{int(live_telemetry['player_z'])}
    
    REGLA DE COORDENADAS: 
    1. Si el jugador te da un numero de cuadricula (ejemplo: '086 030' o '86 30'), TU SOLAMENTE pones esos numeros exactos en 'grid_x' y 'grid_z'. Ej: "grid_x": 86, "grid_z": 30. No multipliques nada.
    2. Si el jugador dice "a mi posicion", "aqui", "cerca de mi", o NO da coordenadas exactas, DEBES poner "grid_x": -1, "grid_z": -1. El sistema usara el Radar del jugador.
    
    UNIDADES DISPONIBLES: {AVAILABLE_UNITS}
    
    Responde SOLO con un JSON valido y exacto:
    {{"action": "spawn", "unit_id": "US Fusilero", "grid_x": 86, "grid_z": 30, "internal_thought": "Motivo tactico"}}
    '''
    
    payload = {'model': 'llama3.1', 'system': dynamic_prompt, 'prompt': prompt_text, 'stream': False, 'format': 'json'}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post('http://localhost:11434/api/generate', json=payload, timeout=60.0)
            data = json.loads(response.json()['response'])
            unit_id = data.get('unit_id')
            
            gx = data.get('grid_x', -1)
            gz = data.get('grid_z', -1)
            
            try:
                gx = int(gx)
                gz = int(gz)
            except:
                gx, gz = -1, -1

            if gx <= 0 or gz <= 0:
                final_x = live_telemetry['player_x'] + 15
                final_z = live_telemetry['player_z'] + 15
                coord_info = "TU POSICION VISUAL"
            else:
                final_x = gx * 100 if gx < 1000 else gx
                final_z = gz * 100 if gz < 1000 else gz
                coord_info = f"X:{final_x} Z:{final_z}"

            if unit_id in PREFABS:
                spawn_data = {
                    'prefab_path': PREFABS[unit_id],
                    'spawn_x': final_x,
                    'spawn_z': final_z
                }
                command_queue.append(spawn_data)
                
                msg = f"🧠 IA: {data.get('internal_thought', 'Despliegue tactico')} -> {unit_id} a {coord_info}"
                action_history.append(msg)
            else:
                action_history.append(f"❌ ERROR: La IA intento spawnear '{unit_id}', que no esta en prefabs.json")
        except Exception as e:
            action_history.append(f"❌ ERROR IA: {str(e)}")

@app.post('/manual_command')
async def manual_command(order: ManualOrder):
    action_history.append(f"👤 ORDEN: {order.order}")
    await ask_ollama(f"ORDEN HUMANA: '{order.order}'.")
    return {'status': 'ok'}

@app.get('/arma_sync', response_class=PlainTextResponse)
async def arma_sync(px: float = 4800.0, pz: float = 6300.0, m: str = "Game Master"):
    live_telemetry['player_x'] = px
    live_telemetry['player_z'] = pz
    live_telemetry['mission_name'] = m
    
    if command_queue:
        cmd = command_queue.pop(0)
        return f"SPAWN|{cmd['prefab_path']}|{cmd.get('spawn_x')}|0|{cmd.get('spawn_z')}"
    return 'NONE'

@app.get('/status')
async def get_status():
    return {'history': action_history[-15:]}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
"""
    with open(os.path.join(backend_dir, "main.py"), "w", encoding="utf-8") as f:
        f.write(main_py_content)

    # 2. EL DICCIONARIO DE PREFABS (prefabs.json)
    prefabs_content = r"""{
    "US Fusilero": "{26A9756790131354}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Rifleman.et",
    "US Lider de Escuadra": "{E45F1E163F5CA080}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_SL.et",
    "US Francotirador": "{0F6689B491641155}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Sniper.et",
    "US Lanzagranadas": "{84029128FA6F6BB9}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_GL.et",
    "URSS Fusilero": "{84455E5B84EEB54}Prefabs/Characters/Factions/OPFOR/USSR_Army/Character_USSR_Rifleman.et"
}"""
    with open(os.path.join(base_dir, "prefabs.json"), "w", encoding="utf-8") as f:
        f.write(prefabs_content)

    # 3. EL PANEL DE CONTROL WEB (index.html)
    html_content = r"""<!DOCTYPE html>
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
        input[type="text"] { width: calc(100% - 130px); padding: 12px; background: #000; border: 1px solid #00ff00; color: #00ff00; font-size: 16px; outline: none;}
        button { width: 100px; padding: 12px; background: #00ff00; color: #000; border: none; font-weight: bold; cursor: pointer; font-size: 16px;}
        button:hover { background: #00cc00; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ZEUS A.I. AUTÓNOMO</h1>
        <div class="log-box" id="log-box">Esperando conexion con el servidor Python...</div>
        <div>
            <input type="text" id="order-input" placeholder="Ej: Manda un francotirador a mi posicion..." onkeypress="if(event.key === 'Enter') sendOrder()">
            <button onclick="sendOrder()">ENVIAR</button>
        </div>
    </div>
    <script>
        async function fetchLogs() {
            try {
                let res = await fetch('http://localhost:8000/status');
                let data = await res.json();
                let box = document.getElementById('log-box');
                box.innerHTML = '';
                data.history.forEach(msg => {
                    let div = document.createElement('div');
                    div.className = 'log-entry';
                    div.textContent = msg;
                    if(msg.includes('❌')) div.style.color = '#ff4444';
                    else if(msg.includes('👤')) div.style.color = '#aaaaaa';
                    else if(msg.includes('🧠')) div.style.color = '#00ffff';
                    box.appendChild(div);
                });
                box.scrollTop = box.scrollHeight;
            } catch (e) {}
        }
        async function sendOrder() {
            let input = document.getElementById('order-input');
            let order = input.value.trim();
            if (!order) return;
            input.value = '';
            await fetch('http://localhost:8000/manual_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order: order })
            });
            fetchLogs();
        }
        setInterval(fetchLogs, 1000);
    </script>
</body>
</html>"""
    with open(os.path.join(panel_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    # 4. EL LANZADOR AUTOMATICO (LANZAR_IA.bat)
    bat_content = r"""@echo off
title Arma Reforger IA Server
echo Instalando dependencias necesarias (si faltan)...
pip install fastapi uvicorn httpx pydantic >nul 2>&1
echo.
echo ==============================================
echo    SISTEMA TACTICO IA INICIADO CON EXITO
echo ==============================================
echo.
echo Abriendo el panel de control en tu navegador...
start "" "%~dp0Panel\index.html"
cd Backend
python main.py
pause
"""
    with open(os.path.join(base_dir, "LANZAR_IA.bat"), "w", encoding="utf-8") as f:
        f.write(bat_content)

    print(f"✅ ¡Instalador completado! Se ha creado la carpeta '{base_dir}'.")
    print("Entra en esa carpeta y haz doble click en 'LANZAR_IA.bat' para empezar.")

if __name__ == "__main__":
    crear_instalador()
