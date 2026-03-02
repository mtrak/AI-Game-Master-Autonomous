from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
import time
import os
import re
import requests
import random
import math

from config_rutas import CARPETA_LOGS
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

os.makedirs(CARPETA_LOGS, exist_ok=True)
CARPETA_PROMPTS = "Prompts_Misiones"
os.makedirs(CARPETA_PROMPTS, exist_ok=True) 

archivo_log = os.path.join(CARPETA_LOGS, "sistema_ia.log")

def log_evento(mensaje, nivel="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] [{nivel}] {mensaje}"
    with open(archivo_log, "a", encoding="utf-8") as f:
        f.write(linea + "\n")
    print(linea)

mapas = GestorMapas()
catalogo_general = cargar_todas_las_tropas()
ia_motor = MotorDeduccion(catalogo_general)

cola_ordenes = []
historial_chat = ["📻 [SISTEMA] Arrancando Sistema. Leyendo parametros de mision..."]
tropas_activas = []
ultimo_latido_arma = 0.0  

posiciones_jugadores = {
    "Comandante": {"x": 0.0, "z": 0.0}
}

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_OLLAMA = "llama3.1:latest"
contexto_mision_actual = "" 
fase_sistema = "INICIANDO" 

CIUDADES_EVERON = ["morton", "montignac", "durras", "saint pierre", "le moule", "lamentin", "tyrone"]

COORDENADAS_CIUDADES = {
    "Morton": (4364, 6450),
    "Montignac": (4520, 5880),
    "Durras": (5250, 6120),
    "Saint Pierre": (6140, 6420),
    "Le Moule": (6830, 5910),
    "Lamentin": (1450, 2430),
    "Tyrone": (4830, 3120)
}

def obtener_ciudad_cercana(x, z):
    if x == 0.0 and z == 0.0:
        return "Desplegando..."
        
    ciudad_cercana = "Zona Salvaje"
    distancia_min = 999999
    
    for nombre_ciudad, coords in COORDENADAS_CIUDADES.items():
        dist = math.sqrt((x - coords[0])**2 + (z - coords[1])**2)
        if dist < distancia_min:
            distancia_min = dist
            ciudad_cercana = nombre_ciudad
            
    if distancia_min > 1200:
        return "Zona Salvaje"
        
    return ciudad_cercana

def desencadenar_refuerzos(id_solicitante):
    global cola_ordenes, tropas_activas, historial_chat
    
    tropa_solicitante = next((t for t in tropas_activas if t["id"] == id_solicitante), None)
    if not tropa_solicitante:
        log_evento(f"Falsa alarma. La unidad {id_solicitante} no existe.", "WARN")
        return
        
    tx = tropa_solicitante["x"]
    tz = tropa_solicitante["z"]
    unidades_enviadas = 0
    
    for t in tropas_activas:
        if t["id"] != id_solicitante:
            distancia = math.sqrt((t["x"] - tx)**2 + (t["z"] - tz)**2)
            if distancia <= 2000: 
                # 🛠️ BUGFIX: Forzamos orden MOVE directo a la coordenada para que dejen lo que están haciendo y corran.
                orden_str = f"WAYPOINT|MOVE|{t['id']}|{tx:.2f}|{tz:.2f}"
                cola_ordenes.append(orden_str)
                t["action"] = f"AL RESCATE DE #{id_solicitante}"
                unidades_enviadas += 1
                
    if unidades_enviadas > 0:
        historial_chat.append(f"🚨 RADIO: Unidad {id_solicitante} bajo fuego. ¡{unidades_enviadas} unidades movilizadas al rescate!")
        log_evento(f"Refuerzos enviados a la unidad {id_solicitante}. Movilizadas: {unidades_enviadas}")
    else:
        historial_chat.append(f"⚠️ RADIO: Unidad {id_solicitante} pide apoyo, pero no hay aliados a menos de 2km.")

def procesar_orden_natural(orden_texto, jugador="SISTEMA"):
    global cola_ordenes, tropas_activas, posiciones_jugadores, historial_chat, fase_sistema
    
    orden_lower = orden_texto.lower()
    orden_limpia = orden_lower.replace(".", "").replace(",", "").replace("!", "").replace("?", "")
    
    if "refuerzo" in orden_limpia or "refuerzos" in orden_limpia:
        match_num_refuerzo = re.search(r'\d+', orden_limpia)
        if match_num_refuerzo:
            return desencadenar_refuerzos(int(match_num_refuerzo.group()))

    es_posicion_jugador = re.search(r'\b(mi posicion|aqui|donde estoy|mi ubicacion)\b', orden_limpia)
    
    if es_posicion_jugador:
        if jugador in posiciones_jugadores:
            destino_coords = (posiciones_jugadores[jugador]["x"], posiciones_jugadores[jugador]["z"])
            ciudad_encontrada = f"la posicion de {jugador}"
        else:
            coord_x = posiciones_jugadores.get("Comandante", {"x":0,"z":0})["x"]
            coord_z = posiciones_jugadores.get("Comandante", {"x":0,"z":0})["z"]
            destino_coords = (coord_x, coord_z)
            ciudad_encontrada = "tu posicion (Zeus)"
    else:
        ciudad_encontrada, destino_coords = mapas.buscar_destino(orden_limpia)
        ciudad_mencionada_realmente = False
        
        for ciudad in CIUDADES_EVERON:
            if ciudad in orden_limpia:
                ciudad_mencionada_realmente = True
                ciudad_encontrada = ciudad.title()
                break
                
        if not ciudad_mencionada_realmente:
            destino_coords = None
            ciudad_encontrada = "su posicion actual"

    manual_tactico = {
        "MOVE": ["mueve", "mover", "ve a", "desplaza", "dirigete", "avanza"],
        "PATROL": ["patrulla", "ronda", "vigila", "explora"],
        "DEFEND": ["defiende", "protege", "asegura", "atrincherate", "manten", "refugiate", "cubrete"],
        "ATTACK": ["ataca", "asalta", "toma", "invade", "carga contra"],
        "SAD": ["busca y destruye", "limpia", "aniquila", "elimina"],
        "GETIN": ["embarca", "sube", "monta", "ocupa", "al vehiculo", "a los vehiculos"],
        "GETOUT": ["desembarca", "baja", "sal del", "salid del"],
        "SUPPRESS": ["suprime", "fuego de supresion", "dispara hacia", "fuego a discrecion"]
    }

    match_numero = re.search(r'\b(?:unidad|tropa|escuadron|grupo|id|numero|#)\s*(\d+)\b', orden_limpia) 
    
    if match_numero:
        id_tropa = int(match_numero.group(1))
        tropa_encontrada = next((t for t in tropas_activas if t["id"] == id_tropa), None)
        
        if tropa_encontrada:
            if not destino_coords:
                destino_coords = (tropa_encontrada["x"], tropa_encontrada["z"])
            tipo_waypoint = "MOVE"
            for tipo, verbos in manual_tactico.items():
                if any(verbo in orden_limpia for verbo in verbos):
                    tipo_waypoint = tipo
                    break
            tropa_encontrada["x"] = destino_coords[0]
            tropa_encontrada["z"] = destino_coords[1]
            tropa_encontrada["action"] = f"{tipo_waypoint} a {ciudad_encontrada}"
            
            orden_str = f"WAYPOINT|{tipo_waypoint}|{id_tropa}|{destino_coords[0]:.2f}|{destino_coords[1]:.2f}"
            cola_ordenes.append(orden_str) 
            return f"SISTEMA: Moviendo Unidad {id_tropa} a {ciudad_encontrada} ({tipo_waypoint})."
        else:
            return f"⛔ SISTEMA: No existe la unidad {id_tropa}."
    else:
        # 🛠️ BUGFIX DE SEGURIDAD: Prohibir a la IA crear tropas si el despliegue ya terminó.
        if fase_sistema == "IA_AL_MANDO" and jugador != "Comandante":
            return "⛔ SISTEMA BLOQUEO: La IA ha intentado crear una unidad fuera de fase. Orden interceptada y cancelada."

        if not destino_coords:
            return f"⛔ SISTEMA: Error. Necesito un lugar exacto (Ej: Morton, Montignac)."
        else:
            nombre_unidad, prefab = ia_motor.deducir_tropa(orden_texto)
            nueva_id = len(tropas_activas) + 1
            
            offset_x = random.uniform(-25.0, 25.0) 
            offset_z = random.uniform(-25.0, 25.0)
            final_x = destino_coords[0] + offset_x
            final_z = destino_coords[1] + offset_z
            
            orden_str = f"SPAWN|{nueva_id}|{prefab}|{final_x:.2f}|{final_z:.2f}"
            cola_ordenes.append(orden_str) 
            
            nueva_tropa = {"id": nueva_id, "name": nombre_unidad, "x": final_x, "z": final_z, "action": "ESPERANDO ORDENES"}
            tropas_activas.append(nueva_tropa)
            
            return f"SISTEMA: Desplegando {nombre_unidad} (ID: {nueva_id}) en {ciudad_encontrada}."

def cargar_escenario_inicial():
    global cola_ordenes, historial_chat, contexto_mision_actual, fase_sistema
    
    ruta_mision = os.path.join(CARPETA_PROMPTS, "init_mision.txt")
    
    if not os.path.exists(ruta_mision):
        with open(ruta_mision, "w", encoding="utf-8") as f:
            f.write("Mision de infiltracion en la zona norte. Faccion rusa defiende Morton y Montignac.")
        
    with open(ruta_mision, "r", encoding="utf-8") as f:
        contexto_mision_actual = f.read()

    historial_chat.append("⏳ IA: Leyendo 'init_mision.txt' y construyendo el mapa inicial...")
    
    prompt_masivo = f"""
    Eres el motor de generacion de escenarios de Arma Reforger.
    Tu objetivo es generar las ordenes de despliegue inicial.
    
    --- DISENO DE MISION ---
    {contexto_mision_actual}
    
    Pueblos validos: Morton, Montignac, Durras, Saint Pierre, Le Moule, Lamentin, Tyrone.
    
    Genera 10 ordenes en lenguaje natural para poblar el mapa.
    Separalas UNICAMENTE con el caracter punto y coma (;). 
    PROHIBIDO ENUMERAR. SOLO LAS ORDENES PURAS.
    """
    
    try:
        respuesta = requests.post(OLLAMA_URL, json={
            "model": MODELO_OLLAMA,
            "prompt": prompt_masivo,
            "stream": False
        }, timeout=60) 
        
        if respuesta.status_code == 200:
            comandos_brutos = respuesta.json().get("response", "").strip()
            
            limpio = comandos_brutos.replace("`", "").replace('"', "").replace(".", "")
            limpio = limpio.replace("\n", ";") 
            lista_comandos = limpio.split(";") 
            
            for cmd in lista_comandos:
                cmd_strip = re.sub(r'^[\d\-\*\s]+', '', cmd.strip()).lower()
                
                if len(cmd_strip) > 5 and any(c in cmd_strip for c in CIUDADES_EVERON):
                    res = procesar_orden_natural(cmd_strip, "Ollama")
                    log_evento(f"INIT: {cmd_strip} -> {res}")
            
            fase_sistema = "DESPLEGANDO"
            historial_chat.append(f"✅ SISTEMA: Mision generada. {len(cola_ordenes)} entidades esperando al jugador.")
        else:
            historial_chat.append(f"⛔ IA FALLO HTTP: {respuesta.status_code}")
    except Exception as e:
        historial_chat.append(f"⛔ ERROR GENERANDO MISION: {str(e)}")

def bucle_game_master_dinamico():
    global cola_ordenes, historial_chat, tropas_activas, contexto_mision_actual, fase_sistema
    
    while True:
        time.sleep(60) 
        arma_online = (time.time() - ultimo_latido_arma) < 6.0
        
        if arma_online and len(cola_ordenes) == 0 and fase_sistema in ["DESPLEGANDO", "IA_AL_MANDO"]:
            
            if fase_sistema == "DESPLEGANDO":
                fase_sistema = "IA_AL_MANDO"
                historial_chat.append("🚀 SISTEMA: Despliegue completado. IA Mantiene el ecosistema vivo.")
            
            # Formateamos las tropas para que la IA sepa EXACTAMENTE qué ID puede mover
            tropas_disponibles = ", ".join([f"Unidad {t['id']} (en {obtener_ciudad_cercana(t['x'], t['z'])})" for t in tropas_activas])

            # 🛠️ BUGFIX: Reglas militares súper estrictas para la IA de mando
            estado_mundo = f"""
            Eres un Comandante de Arma Reforger operando en la isla de EVERON.
            
            --- TUS REGLAS ESTRICTAS E INQUEBRANTABLES ---
            1. TIENES TOTALMENTE PROHIBIDO crear o desplegar nuevas tropas.
            2. SOLO puedes mover de pueblo a las unidades que ya tienes activas en el mapa.
            3. LOS ÚNICOS PUEBLOS QUE EXISTEN SON: Morton, Montignac, Durras, Saint Pierre, Le Moule, Lamentin, Tyrone.
            4. PROHIBIDO mencionar Chernarus, Chernogorsk, Kostanay o cualquier otra ciudad inventada.
            
            --- TUS TROPAS ACTUALES Y SUS POSICIONES ---
            {tropas_disponibles}
            
            --- TU TURNO ---
            Da UNA SOLA ORDEN para mover a UNA de tus unidades existentes a otro pueblo para patrullar o defender.
            Ejemplo 1: la Unidad 2 patrulla en Durras
            Ejemplo 2: la Unidad 5 defiende en Morton
            
            Responde UNICAMENTE con la orden directa.
            """
            
            try:
                respuesta = requests.post(OLLAMA_URL, json={
                    "model": MODELO_OLLAMA,
                    "prompt": estado_mundo,
                    "stream": False
                }, timeout=30)
                
                if respuesta.status_code == 200:
                    comando_bruto = respuesta.json().get("response", "").strip()
                    limpio = comando_bruto.replace("`", "").replace('"', '').replace(".", "")
                    
                    if len(limpio) > 5:
                        historial_chat.append(f"🧠 IA (Comandante): '{limpio}'")
                        resultado_ia = procesar_orden_natural(limpio, "IA_AUTO")
                        if "⛔" in resultado_ia:
                            log_evento(f"La IA cometió un error y fue bloqueada: {resultado_ia}")
            except Exception:
                pass

threading.Thread(target=cargar_escenario_inicial, daemon=True).start()
threading.Thread(target=bucle_game_master_dinamico, daemon=True).start()

@app.get("/status")
async def status():
    arma_online = (time.time() - ultimo_latido_arma) < 6.0
    
    tropas_para_web = []
    for t in tropas_activas:
        t_web = t.copy()
        t_web["city"] = obtener_ciudad_cercana(t["x"], t["z"])
        tropas_para_web.append(t_web)
        
    return JSONResponse(content={
        "status": "online", 
        "ia_ready": True,
        "arma_connected": arma_online,
        "history": historial_chat[-15:], 
        "troops": tropas_para_web,
        "queue_size": len(cola_ordenes),
        "fase": fase_sistema
    })

@app.get("/combat_alert")
async def combat_alert(unit_id: int):
    log_evento(f"MOTOR ENFUSION: La unidad {unit_id} reporta combate en curso.")
    desencadenar_refuerzos(unit_id)
    return PlainTextResponse("OK_REFUERZOS_EN_CAMINO")

@app.post("/manual_command")
async def manual_command(request: Request):
    global historial_chat
    try:
        data = await request.json()
        jugador = data.get("player_name", "Comandante")
        orden_texto = data.get("order", "")
        
        log_evento(f"WEB: Orden manual de {jugador}: '{orden_texto}'")
        historial_chat.append(f"👤 Zeus: {orden_texto}")
        
        resultado_humano = procesar_orden_natural(orden_texto, jugador)
        if "SISTEMA" in str(resultado_humano):
            historial_chat.append(resultado_humano)
        
        return JSONResponse(content={"status": "success"})
        
    except Exception as e:
        log_evento(f"Error procesando comando manual: {str(e)}", "ERROR")
        return JSONResponse(content={"status": "error"})

@app.get("/sync", response_class=PlainTextResponse)
async def sync(px: float = 0.0, pz: float = 0.0, player: str = "Comandante"):
    global cola_ordenes, ultimo_latido_arma, posiciones_jugadores
    ultimo_latido_arma = time.time()
    posiciones_jugadores[player] = {"x": px, "z": pz}
    
    if len(cola_ordenes) > 0:
        orden_a_enviar = cola_ordenes.pop(0) 
        return orden_a_enviar
        
    return "null"

if __name__ == "__main__":
    print("===============================================")
    print("🚀 SERVIDOR IA INICIADO (REGLAS ESTRICTAS EVERON)")
    print("===============================================")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error", ws="none")