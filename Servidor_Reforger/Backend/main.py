from fastapi import FastAPI, Request
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
    with open(archivo_log, "a", encoding="utf-8") as f:
        f.write(linea + "\n")
    print(linea)

# --- INICIALIZAMOS LOS SISTEMAS ---
mapas = GestorMapas()
catalogo_general = cargar_todas_las_tropas()
ia_motor = MotorDeduccion(catalogo_general)

orden_pendiente = ""
historial_chat = ["📻 [SISTEMA] Motor de Red y Cerebro conectados. Todo listo."]
tropas_activas = []
ultimo_latido_arma = 0.0  

log_evento("Servidor iniciado correctamente. Cargados mapas y catalogos.")

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
    arma_online = (time.time() - ultimo_latido_arma) < 6.0
    
    return JSONResponse(content={
        "status": "online", 
        "ia_ready": True,
        "arma_connected": arma_online,
        "history": historial_chat[-20:],
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
        
        nombre_unidad, prefab = ia_motor.deducir_tropa(orden_texto)
        ciudad_encontrada, destino_coords = mapas.buscar_destino(orden_texto)
        
        log_evento(f"IA: Deducido -> Unidad: {nombre_unidad} | Destino: {ciudad_encontrada}")
            
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
# 📡 CONEXION CON ARMA 
# ==========================================
@app.get("/sync", response_class=PlainTextResponse)
async def sync(px: float = 0.0, pz: float = 0.0):
    global orden_pendiente, ultimo_latido_arma
    
    ultimo_latido_arma = time.time()
    
    # Imprimimos el radar de forma limpia en consola
    print(f"📡 [LATIDO ARMA] Zeus en X:{px:.1f} Z:{pz:.1f}         ", end="\r")

    if orden_pendiente != "":
        orden_a_enviar = orden_pendiente
        orden_pendiente = "" 
        print("\n") 
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
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error", ws="none")