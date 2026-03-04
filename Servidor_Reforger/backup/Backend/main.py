from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import webbrowser
import threading
import time
import os
import re
import requests
import json

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
historial_chat = ["📻 [SISTEMA] Motor de Red, Cerebro y Tacticas conectados. Todo listo."]
tropas_activas = []
ultimo_latido_arma = 0.0  

posiciones_jugadores = {
    "Comandante": {"x": 0.0, "z": 0.0}
}

# 🤖 CONFIGURACIÓN DE OLLAMA
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_OLLAMA = "llama3.1:latest" # <--- ¡AHORA SÍ COINCIDE CON TU ORDENADOR!

def solicitar_decision_ollama():
    """Recopila la telemetria y le pide a Ollama que tome una decision tactica."""
    global tropas_activas, posiciones_jugadores
    
    estado_mundo = f"""
    Eres un Game Master hostil de Arma Reforger. Tu objetivo es crear misiones y emboscadas.
    Estado actual de los jugadores humanos: {posiciones_jugadores}
    Tus tropas activas en el mapa: {tropas_activas}
    
    Toma una decision tactica. Puedes:
    1. Crear un escuadron enemigo cerca de un jugador.
    2. Mandar a una tropa activa a atacar (ATTACK) la posicion de un jugador.
    
    Responde EXCLUSIVAMENTE con el comando en este formato, sin texto extra:
    Ejemplo de Ataque: WAYPOINT|ATTACK|1|4500.0|6000.0
    Ejemplo de Creacion: SPAWN|99|US_RifleSquad|4500.0|6000.0
    """
    
    try:
        respuesta = requests.post(OLLAMA_URL, json={
            "model": MODELO_OLLAMA,
            "prompt": estado_mundo,
            "stream": False
        }, timeout=20)
        
        if respuesta.status_code == 200:
            comando_bruto = respuesta.json().get("response", "").strip()
            comando_limpio = comando_bruto.replace("`", "").strip()
            return comando_limpio
        else:
            error_txt = respuesta.json().get("error", "Error HTTP " + str(respuesta.status_code))
            return f"ERROR|Ollama dice: {error_txt}"
            
    except requests.exceptions.ConnectionError:
        return "ERROR|No hay conexion en localhost:11434. Ollama esta cerrado."
    except requests.exceptions.Timeout:
        return "ERROR|Ollama esta pensando demasiado (Timeout de 20s)."
    except Exception as e:
        log_evento(f"Error interno conectando con Ollama: {e}", "ERROR")
        return f"ERROR|Excepcion de Python: {str(e)}"

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
        "troops": tropas_activas,
        "players": posiciones_jugadores
    })

@app.post("/manual_command")
async def manual_command(request: Request):
    global orden_pendiente, historial_chat, tropas_activas, posiciones_jugadores
    try:
        data = await request.json()
        jugador = data.get("player_name", "Comandante")
        orden_texto = data.get("order", "")
        orden_lower = orden_texto.lower()
        
        log_evento(f"WEB: Orden de {jugador}: '{orden_texto}'")
        historial_chat.append(f"👤 {jugador}: {orden_texto}")
        
        # 🤖 MODO AUTÓNOMO (OLLAMA TOMA EL CONTROL)
        if "ia toma el mando" in orden_lower or "decide tu" in orden_lower:
            historial_chat.append("⏳ IA: Evaluando situacion tactica mediante Ollama...")
            comando_ollama = solicitar_decision_ollama()
            
            if "ERROR|" in comando_ollama:
                razon = comando_ollama.split("|")[1]
                historial_chat.append(f"⛔ IA FALLO CRITICO: {razon}")
                return JSONResponse(content={"status": "error"})
                
            orden_pendiente = comando_ollama
            log_evento(f"OLLAMA DECIDE: {comando_ollama}")
            
            if comando_ollama.startswith("SPAWN"):
                partes = comando_ollama.split("|")
                if len(partes) >= 5:
                    nueva_id = int(partes[1])
                    nombre_prefab = partes[2]
                    x_sp = float(partes[3])
                    z_sp = float(partes[4])
                    tropas_activas.append({"id": nueva_id, "name": "Fuerzas Hostiles (IA)", "x": x_sp, "z": z_sp, "action": "IDLE"})
            
            historial_chat.append(f"🧠 GAME MASTER OLLAMA: He analizado la telemetria y ejecutado mi propia estrategia.")
            return JSONResponse(content={"status": "success"})

        # --- MODO MANUAL CLÁSICO ---
        es_posicion_jugador = re.search(r'\b(mi posicion|aqui|donde estoy|mi ubicacion)\b', orden_lower)
        
        if es_posicion_jugador:
            if jugador in posiciones_jugadores:
                destino_coords = (posiciones_jugadores[jugador]["x"], posiciones_jugadores[jugador]["z"])
                ciudad_encontrada = f"la posicion de {jugador}"
            else:
                destino_coords = (posiciones_jugadores["Comandante"]["x"], posiciones_jugadores["Comandante"]["z"])
                ciudad_encontrada = "tu posicion (Zeus)"
        else:
            ciudad_encontrada, destino_coords = mapas.buscar_destino(orden_texto)
            ciudad_mencionada_realmente = False
            if ciudad_encontrada:
                ciudad_lower = ciudad_encontrada.lower()
                if ciudad_lower in orden_lower:
                    ciudad_mencionada_realmente = True
                else:
                    for palabra in ciudad_lower.split():
                        if len(palabra) > 3 and palabra in orden_lower:
                            ciudad_mencionada_realmente = True
                            break
            
            if not ciudad_mencionada_realmente:
                destino_coords = None
                ciudad_encontrada = "su posicion actual"

        manual_tactico = {
            "MOVE": ["mueve", "mover", "ve a", "desplaza", "dirigete", "avanza"],
            "PATROL": ["patrulla", "ronda", "vigila", "explora"],
            "DEFEND": ["defiende", "protege", "asegura", "atrincherate", "manten", "refugiate", "cubrete", "escondete"],
            "ATTACK": ["ataca", "asalta", "toma", "invade", "carga contra"],
            "SAD": ["busca y destruye", "limpia", "aniquila", "elimina"],
            "GETIN": ["embarca", "sube", "monta", "ocupa", "al vehiculo", "a los vehiculos"],
            "GETOUT": ["desembarca", "baja", "sal del", "salid del"],
            "SUPPRESS": ["suprime", "fuego de supresion", "dispara hacia", "fuego a discrecion"]
        }

        match_numero = re.search(r'\d+', orden_lower) 
        
        if match_numero:
            id_tropa = int(match_numero.group())
            tropa_encontrada = next((t for t in tropas_activas if t["id"] == id_tropa), None)
            
            if tropa_encontrada:
                if not destino_coords:
                    destino_coords = (tropa_encontrada["x"], tropa_encontrada["z"])

                tipo_waypoint = "MOVE"
                for tipo, verbos in manual_tactico.items():
                    if any(verbo in orden_lower for verbo in verbos):
                        tipo_waypoint = tipo
                        break

                log_evento(f"IA: Intencion -> {tipo_waypoint} Unidad {id_tropa} en {ciudad_encontrada}")
                
                tropa_encontrada["x"] = destino_coords[0]
                tropa_encontrada["z"] = destino_coords[1]
                tropa_encontrada["action"] = tipo_waypoint
                
                orden_pendiente = f"WAYPOINT|{tipo_waypoint}|{id_tropa}|{destino_coords[0]}|{destino_coords[1]}"
                
                diccionario_respuestas = {
                    "MOVE": "Moviendo la", "PATROL": "Iniciando ruta de patrulla para la",
                    "DEFEND": "Atrincherando y buscando refugio para la", "ATTACK": "Lanzando asalto con la", "SAD": "Iniciando operacion de limpieza con la",
                    "GETIN": "Buscando vehiculos cercanos para embarcar a la", "GETOUT": "Ordenando desembarco a la", "SUPPRESS": "Abriendo fuego de supresion con la"
                }
                
                respuesta_ia = f"🧠 IA: Entendido. {diccionario_respuestas[tipo_waypoint]} unidad {id_tropa} en {ciudad_encontrada}."
            else:
                respuesta_ia = f"⛔ IA: Error. No existe la unidad {id_tropa} en el radar."
        else:
            if not destino_coords:
                respuesta_ia = f"⛔ IA: Error. Para solicitar tropas nuevas necesito un lugar exacto (Ej: 'despliega un tanque en Morton' o 'en mi posicion')."
            else:
                nombre_unidad, prefab = ia_motor.deducir_tropa(orden_texto)
                nueva_id = len(tropas_activas) + 1
                
                log_evento(f"IA: Intencion -> CREAR {nombre_unidad} en {ciudad_encontrada}")
                
                orden_pendiente = f"SPAWN|{nueva_id}|{prefab}|{destino_coords[0]}|{destino_coords[1]}"
                respuesta_ia = f"🧠 IA: Entendido. Desplegando {nombre_unidad} (ID: {nueva_id}) en {ciudad_encontrada}."
                
                tropas_activas.append({"id": nueva_id, "name": nombre_unidad, "x": destino_coords[0], "z": destino_coords[1], "action": "IDLE"})
            
        historial_chat.append(respuesta_ia)
        return JSONResponse(content={"status": "success"})
    except Exception as e:
        log_evento(f"Error procesando comando: {str(e)}", "ERROR")
        return JSONResponse(content={"status": "error"})

# ==========================================
# 📡 CONEXION CON ARMA 
# ==========================================
@app.get("/sync", response_class=PlainTextResponse)
async def sync(px: float = 0.0, pz: float = 0.0, player: str = "Comandante"):
    global orden_pendiente, ultimo_latido_arma, posiciones_jugadores
    ultimo_latido_arma = time.time()
    
    posiciones_jugadores[player] = {"x": px, "z": pz}
    
    print(f"📡 [LATIDO ARMA] {player} en X:{px:.1f} Z:{pz:.1f}         ", end="\r")

    if orden_pendiente != "":
        orden_a_enviar = orden_pendiente
        orden_pendiente = "" 
        print("\n") 
        log_evento("ARMA: Orden interceptada y enviada a Enfusion Engine.")
        return orden_a_enviar
        
    return "null"

if __name__ == "__main__":
    print("===============================================")
    print("🚀 SERVIDOR IA INICIADO (OLLAMA AUTÓNOMO V5.2)")
    print("===============================================")
    threading.Thread(target=lambda: (time.sleep(1.5), webbrowser.open("http://127.0.0.1:8000"))).start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error", ws="none")