import os
import json

print("=========================================")
print("🤖 ACTUALIZANDO ARQUITECTURA + LOGS + WEB")
print("=========================================")

# 1. CONTENIDOS DE LOS ARCHIVOS
# =======================================================
CONFIG_RUTAS = """import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

CARPETA_WEB = os.path.join(RAIZ_DIR, "Web")
if not os.path.exists(CARPETA_WEB):
    CARPETA_WEB = os.path.join(BASE_DIR, "Web")

CARPETA_DATOS = os.path.join(BASE_DIR, "Datos")
CARPETA_CATALOGOS = os.path.join(BASE_DIR, "Catalogos_IA")
if not os.path.exists(CARPETA_CATALOGOS):
    CARPETA_CATALOGOS = os.path.join(RAIZ_DIR, "Catalogos_IA")

ARCHIVO_MAPA = os.path.join(CARPETA_DATOS, "coordenadas.json")
CARPETA_LOGS = os.path.join(BASE_DIR, "Logs")
"""

MAIN_CODE = """from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import webbrowser
import threading
import time
import os

from config_rutas import CARPETA_WEB, CARPETA_LOGS
from Cerebro_IA.gestor_catalogos import cargar_todas_las_tropas
from Cerebro_IA.gestor_mapas import GestorMapas
from Cerebro_IA.motor_deduccion import MotorDeduccion

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SISTEMA DE LOGS ---
os.makedirs(CARPETA_LOGS, exist_ok=True)
archivo_log = os.path.join(CARPETA_LOGS, "sistema_ia.log")

def log_evento(mensaje, nivel="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] [{nivel}] {mensaje}"
    # Guardamos en el archivo
    with open(archivo_log, "a", encoding="utf-8") as f:
        f.write(linea + "\\n")
    # Imprimimos en consola también
    print(linea)

# --- INICIALIZAMOS LOS SISTEMAS ---
mapas = GestorMapas()
catalogo_general = cargar_todas_las_tropas()
ia_motor = MotorDeduccion(catalogo_general)

orden_pendiente = ""
historial_chat = ["📻 [SISTEMA] Motor de Red y Cerebro conectados. Todo listo."]
tropas_activas = []
ultimo_latido_arma = 0.0  # Para saber si Arma está conectado

log_evento("Servidor iniciado correctamente. Cargados mapas y catálogos.")

# ==========================================
# 🌐 RUTAS WEB 
# ==========================================
@app.get("/")
async def read_root():
    ruta_index = os.path.join(CARPETA_WEB, "index.html")
    if os.path.exists(ruta_index):
        return FileResponse(ruta_index)
    return HTMLResponse(content=f"<h1>Error</h1><p>Falta index.html en {CARPETA_WEB}</p>", status_code=404)

@app.get("/status")
async def status():
    # Comprobamos si Arma nos ha hablado en los últimos 6 segundos
    arma_online = (time.time() - ultimo_latido_arma) < 6.0
    
    return JSONResponse(content={
        "status": "online", 
        "ia_ready": True,
        "arma_connected": arma_online,
        "history": historial_chat[-20:], # Enviamos solo los últimos 20 mensajes
        "troops": tropas_activas
    })

@app.post("/manual_command")
async def manual_command(request: Request):
    global orden_pendiente, historial_chat, tropas_activas
    try:
        data = await request.json()
        jugador = data.get("player_name", "Comandante")
        orden_texto = data.get("order", "")
        
        log_evento(f"WEB: Orden recibida de {jugador}: '{orden_texto}'")
        historial_chat.append(f"👤 {jugador}: {orden_texto}")
        
        # 🧠 LA IA DELEGA EL TRABAJO
        nombre_unidad, prefab = ia_motor.deducir_tropa(orden_texto)
        ciudad_encontrada, destino_coords = mapas.buscar_destino(orden_texto)
        
        log_evento(f"IA: Deducido -> Unidad: {nombre_unidad} | Destino: {ciudad_encontrada}")
            
        # 📦 PREPARAR ENVÍO
        orden_pendiente = f"{prefab}|{destino_coords[0]}|{destino_coords[1]}"
        
        respuesta_ia = f"🧠 IA: Entendido. Desplegando {nombre_unidad} en {ciudad_encontrada}."
        historial_chat.append(respuesta_ia)
        
        nueva_id = len(tropas_activas) + 1
        tropas_activas.append({"id": nueva_id, "name": nombre_unidad, "x": destino_coords[0], "z": destino_coords[1]})
        
        return JSONResponse(content={"status": "success"})
    except Exception as e:
        log_evento(f"Error procesando comando: {str(e)}", "ERROR")
        return JSONResponse(content={"status": "error"})

# ==========================================
# 📡 CONEXIÓN CON ARMA 
# ==========================================
@app.get("/sync", response_class=PlainTextResponse)
async def sync(px: float = 0.0, pz: float = 0.0):
    global orden_pendiente, ultimo_latido_arma
    
    # Registramos que Arma sigue vivo
    ultimo_latido_arma = time.time()
    
    # El radar se imprime en consola con \r para no saturar la pantalla, y NO se guarda en el log
    print(f"📡 [LATIDO ARMA] Zeus en X:{px:.1f} Z:{pz:.1f}         ", end="\\r")

    if orden_pendiente != "":
        orden_a_enviar = orden_pendiente
        orden_pendiente = "" 
        print("\\n") # Salto de línea para no pisar el radar
        log_evento(f"ARMA: Orden interceptada y enviada a Enfusion Engine.")
        return orden_a_enviar
        
    return "null"

def abrir_navegador():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("===============================================")
    print("🚀 SERVIDOR IA INICIADO (SISTEMA DE LOGS ACTIVO)")
    print("===============================================")
    threading.Thread(target=abrir_navegador).start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning") # Ocultamos logs inútiles de Uvicorn
"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Arma Reforger - IA Zeus</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #121212; color: #00ff00; margin: 0; padding: 20px; }
        .dashboard { display: flex; gap: 20px; max-width: 1200px; margin: 0 auto; }
        .panel { background-color: #1e1e1e; padding: 20px; border-radius: 8px; border: 1px solid #00ff00; box-shadow: 0 4px 6px rgba(0,255,0,0.1); }
        .chat-panel { flex: 2; position: relative; }
        .radar-panel { flex: 1; }
        .log-box { background-color: #000; padding: 15px; height: 350px; overflow-y: auto; border: 1px solid #333; margin-bottom: 20px; font-family: monospace; }
        .troop-box { background-color: #000; padding: 10px; height: 385px; overflow-y: auto; border: 1px solid #333; font-family: monospace; font-size: 14px; }
        .log-entry { margin: 5px 0; border-bottom: 1px dashed #222; padding-bottom: 5px; }
        .troop-entry { margin: 5px 0; color: #ffb800; border-bottom: 1px solid #333; padding-bottom: 5px; }
        input[type="text"] { padding: 12px; background: #000; border: 1px solid #00ff00; color: #0f0; font-size: 16px; box-sizing: border-box; }
        button { padding: 12px 20px; background-color: #00ff00; color: #000; border: none; cursor: pointer; font-weight: bold; font-size: 16px; }
        button:hover { background-color: #33ff33; }
        h1, h2 { text-align: center; margin-top: 0;}
        .status-badge { position: absolute; top: 25px; right: 20px; padding: 5px 10px; border-radius: 5px; font-weight: bold; font-size: 14px; background: #000; border: 1px solid #333; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="panel chat-panel">
            <h1>📻 Centro de Mando Zeus</h1>
            <div id="arma-status" class="status-badge" style="color: #ff4444;">🔴 ARMA: ESPERANDO</div>
            <div class="log-box" id="logs"></div>
            <div style="display: flex; gap: 10px;">
                <input type="text" id="playerName" placeholder="Nombre..." style="width: 25%;" value="Raulote">
                <input type="text" id="order-input" placeholder="Ej: Crea un peloton americano en Morton..." style="width: 60%;" onkeypress="if(event.key==='Enter') sendOrder()">
                <button onclick="sendOrder()">Enviar</button>
            </div>
        </div>

        <div class="panel radar-panel">
            <h2 style="color: #00ffff;">🛰️ Radar Activo</h2>
            <div class="troop-box" id="troops">
                Cargando satélite...
            </div>
        </div>
    </div>

    <script>
        let lastLength = 0;

        async function fetchLogs() {
            try {
                const res = await fetch('http://127.0.0.1:8000/status');
                const data = await res.json();
                
                // Actualizar Semáforo de Arma
                const statusBadge = document.getElementById('arma-status');
                if (data.arma_connected) {
                    statusBadge.innerHTML = '🟢 ARMA: EN LÍNEA';
                    statusBadge.style.color = '#00ff00';
                    statusBadge.style.borderColor = '#00ff00';
                } else {
                    statusBadge.innerHTML = '🔴 ARMA: ESPERANDO';
                    statusBadge.style.color = '#ff4444';
                    statusBadge.style.borderColor = '#ff4444';
                }

                // Actualizar Logs de Chat
                if (data.history.length !== lastLength) {
                    const box = document.getElementById('logs');
                    box.innerHTML = '';
                    data.history.forEach(msg => {
                        const div = document.createElement('div');
                        div.className = 'log-entry';
                        if(msg.includes('❌') || msg.includes('⛔')) div.style.color = '#ff4444';
                        else if(msg.includes('👤') || msg.includes('📻')) div.style.color = '#aaaaaa';
                        else if(msg.includes('🧠')) div.style.color = '#00ffff';
                        div.textContent = msg;
                        box.appendChild(div);
                    });
                    lastLength = data.history.length;
                    box.scrollTop = box.scrollHeight; 
                }

                // Actualizar Radar de Tropas
                const tBox = document.getElementById('troops');
                tBox.innerHTML = '';
                if(data.troops.length === 0) {
                    tBox.innerHTML = '<span style="color:#555;">No hay fuerzas en el área.</span>';
                } else {
                    data.troops.forEach(t => {
                        const tDiv = document.createElement('div');
                        tDiv.className = 'troop-entry';
                        tDiv.innerHTML = `<strong>[ID: ${t.id}]</strong> ${t.name}<br><span style="color:#888;">Pos: X:${Math.round(t.x)} Z:${Math.round(t.z)}</span>`;
                        tBox.appendChild(tDiv);
                    });
                }
            } catch (e) {}
        }

        async function sendOrder() {
            const input = document.getElementById('order-input');
            const nameInput = document.getElementById('playerName');
            if (!input.value.trim() || !nameInput.value.trim()) return;
            
            const text = input.value.trim(); 
            const pName = nameInput.value.trim();
            input.value = '';
            
            await fetch('http://127.0.0.1:8000/manual_command', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify({ player_name: pName, order: text }) 
            });
            fetchLogs(); 
        }

        setInterval(fetchLogs, 1000); 
        fetchLogs();
    </script>
</body>
</html>
"""

# 2. DEFINICIÓN DE ARCHIVOS Y CARPETAS
# =======================================================
archivos_a_crear = {
    "config_rutas.py": CONFIG_RUTAS,
    "main.py": MAIN_CODE,
    "Web/index.html": INDEX_HTML # Sobrescribe el index.html con la nueva versión del semáforo
}

# 3. LÓGICA DE INSTALACIÓN
# =======================================================
for ruta_relativa, contenido in archivos_a_crear.items():
    directorio = os.path.dirname(ruta_relativa)
    if directorio and not os.path.exists(directorio):
        os.makedirs(directorio)
    
    with open(ruta_relativa, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)
    print(f"📄 Actualizado archivo: {ruta_relativa}")

print("\n=========================================")
print("✅ ¡SISTEMA DE LOGS Y SEMÁFORO INSTALADOS!")
print("=========================================")