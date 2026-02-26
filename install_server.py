@echo off
chcp 65001 >nul
title CREADOR Y COMPILADOR - ARMA AI COMMANDER
color 0B

echo ====================================================
echo   1. CREANDO ESTRUCTURA DE DIRECTORIOS...
echo ====================================================
if not exist "Backend" mkdir Backend
if not exist "Web" mkdir Web
echo [OK] Carpetas Backend y Web creadas.

echo.
echo ====================================================
echo   2. GENERANDO ARCHIVOS DEL SERVIDOR...
echo ====================================================

echo [~] Escribiendo prefabs.json...
powershell -Command "$text = @'
{
  \"US Escuadra de Fusileros\": \"{DDF3799FA1387848}Prefabs/Groups/BLUFOR/Group_US_RifleSquad.et\",
  \"US Equipo de Francotiradores\": \"{D807C7047E818488}Prefabs/Groups/BLUFOR/Group_US_SniperTeam.et\",
  \"US Equipo de Ametralladoras\": \"{958039B857396B7B}Prefabs/Groups/BLUFOR/Group_US_MachineGunTeam.et\",
  \"US Equipo Medico\": \"{EF62027CC75A7459}Prefabs/Groups/BLUFOR/Group_US_MedicalSection.et\"
}
'@; Set-Content -Path 'prefabs.json' -Value $text -Encoding UTF8"

echo [~] Escribiendo Backend\main.py...
powershell -Command "$text = @'
import json, httpx, sqlite3, uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

class WarDatabase:
    def __init__(self):
        self.db_path = 'war_room.db'
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS telemetry (id INTEGER PRIMARY KEY CHECK (id=1), px REAL, pz REAL, mission TEXT)')
        c.execute('INSERT OR IGNORE INTO telemetry (id, px, pz, mission) VALUES (1, 4800.0, 6300.0, \"Game Master\")')
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
        return res if res else (4800.0, 6300.0, \"Game Master\")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
command_queue = []
action_history = []
war_db = WarDatabase()

try:
    with open('../prefabs.json', 'r') as f: PREFABS = json.load(f)
except:
    PREFABS = {\"US Escuadra de Fusileros\": \"{DDF3799FA1387848}Prefabs/Groups/BLUFOR/Group_US_RifleSquad.et\"}

class ManualOrder(BaseModel): order: str

async def ask_ollama(prompt):
    px, pz, mission = war_db.get_pos()
    sys_prompt = f\"Eres Zeus de Arma Reforger. Jugador en X:{int(px)} Z:{int(pz)}. Responde SOLO JSON con unit_id ({list(PREFABS.keys())}), grid_x, grid_z e internal_thought.\"
    payload = {'model': 'llama3.1', 'prompt': prompt, 'system': sys_prompt, 'stream': False, 'format': 'json'}
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post('http://localhost:11434/api/generate', json=payload, timeout=30.0)
            data = json.loads(r.json()['response'])
            uid = data.get('unit_id')
            gx, gz = data.get('grid_x', -1), data.get('grid_z', -1)
            
            final_x = px + 15 if gx <= 0 else (gx * 100 if gx < 1000 else gx)
            final_z = pz + 15 if gz <= 0 else (gz * 100 if gz < 1000 else gz)

            if uid in PREFABS:
                command_queue.append({'path': PREFABS[uid], 'x': final_x, 'z': final_z})
                action_history.append(f\"🧠 IA: {data.get('internal_thought', 'Despliegue tactico')} -> {uid}\")
        except Exception as e:
            action_history.append(f\"❌ ERROR IA: {str(e)}\")

@app.post('/manual_command')
async def manual_command(o: ManualOrder):
    action_history.append(f\"👤 ORDEN: {o.order}\")
    await ask_ollama(o.order)
    return {'status': 'ok'}

@app.get('/arma_sync', response_class=PlainTextResponse)
async def arma_sync(px: float = 0, pz: float = 0, m: str = \"GM\"):
    war_db.update_telemetry(px, pz, m)
    if command_queue:
        c = command_queue.pop(0)
        return f\"SPAWN|{c['path']}|{c['x']}|0|{c['z']}\"
    return 'NONE'

@app.get('/status')
async def status():
    return {'history': action_history[-15:]}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
'@; Set-Content -Path 'Backend\main.py' -Value $text -Encoding UTF8"

echo [~] Escribiendo Web\index.html...
powershell -Command "$text = @'
<!DOCTYPE html>
<html lang=\"es\">
<head>
    <meta charset=\"UTF-8\">
    <title>Panel de Mando - AI Game Master</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #1e1e24; color: #fff; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: #2b2b36; padding: 20px; border-radius: 10px; }
        h1 { color: #4CAF50; text-align: center; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        .log-box { background: #111; padding: 15px; height: 350px; overflow-y: scroll; font-family: monospace; border: 1px solid #444; }
        .log-entry { margin-bottom: 8px; padding: 8px; border-left: 4px solid #4CAF50; background: #1a1a1a; }
        input[type=\"text\"] { width: 80%; padding: 10px; background: #000; border: 1px solid #4CAF50; color: #0f0; }
        button { padding: 10px; background: #4CAF50; color: #fff; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>Zeus AI Commander</h1>
        <div class=\"log-box\" id=\"logs\"></div>
        <div style=\"display:flex; gap:10px; margin-top:10px;\">
            <input type=\"text\" id=\"orderInput\" placeholder=\"Orden para la IA...\" onkeypress=\"if(event.key==='Enter') sendOrder()\">
            <button onclick=\"sendOrder()\">Enviar</button>
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
                        if(msg.includes('❌')) div.style.borderLeftColor = '#ff4444';
                        else if(msg.includes('👤')) div.style.borderLeftColor = '#aaaaaa';
                        else if(msg.includes('🧠')) div.style.borderLeftColor = '#00ffff';
                        div.textContent = msg;
                        box.appendChild(div);
                    });
                    lastLength = data.history.length;
                    box.scrollTop = box.scrollHeight;
                }
            } catch (e) {}
        }
        async function sendOrder() {
            const input = document.getElementById('orderInput');
            if (!input.value.trim()) return;
            const text = input.value.trim(); input.value = '';
            await fetch('http://127.0.0.1:8000/manual_command', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ order: text }) });
            fetchLogs();
        }
        setInterval(fetchLogs, 1000); fetchLogs();
    </script>
</body>
</html>
'@; Set-Content -Path 'Web\index.html' -Value $text -Encoding UTF8"

echo [~] Escribiendo LANZAR_IA.bat...
powershell -Command "$text = @'
@echo off
title Arma Reforger IA - MODO COMANDANTE
setlocal
cd /d `\"%~dp0`\"
echo [+] Abriendo Panel de Control...
if exist `"Web\index.html`" start `"`" `"Web\index.html`"
echo [+] Entrando en la carpeta Backend...
cd Backend
echo [+] Iniciando Servidor Uvicorn...
python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
'@; Set-Content -Path 'LANZAR_IA.bat' -Value $text -Encoding UTF8"

echo [OK] Todos los archivos generados con exito.

echo.
echo ====================================================
echo   3. INSTALANDO DEPENDENCIAS DE PYTHON...
echo ====================================================
python -m pip install fastapi uvicorn httpx pydantic

echo.
echo ====================================================
echo   4. VERIFICANDO OLLAMA Y MODELO...
echo ====================================================
ollama pull llama3.1



echo.
echo ====================================================
echo   ¡TODO LISTO!
echo   Se ha creado el archivo LANZAR_IA.bat
echo   Ejecutalo para iniciar el sistema.
echo ====================================================
pause
