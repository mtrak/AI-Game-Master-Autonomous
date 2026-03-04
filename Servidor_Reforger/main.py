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
import json

from config_rutas import CARPETA_LOGS, CARPETA_PROMPTS, RUTA_COORDENADAS, CARPETA_WEB
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
os.makedirs(CARPETA_PROMPTS, exist_ok=True) 

archivo_log = os.path.join(CARPETA_LOGS, "sistema_ia.log")

def log_evento(mensaje, nivel="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] [{nivel}] {mensaje}"
    with open(archivo_log, "a", encoding="utf-8") as f:
        f.write(linea + "\n")
    print(linea)

# ==========================================
# 🧠 CONFIGURACIÓN DEL CEREBRO IA (LOCAL VS NUBE)
# ==========================================
MOTOR_IA = "OLLAMA"  

# 1. Configuración OLLAMA (Local, Gratis)
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_OLLAMA = "llama3.1:latest"

# 2. Configuración OPENAI (Nube, De pago, Estrategia Avanzada)
OPENAI_API_KEY = ""
MODELO_OPENAI = "gpt-o4-mini-2025-04-16" 

# Tiempos de la partida
TIEMPO_TURNO_IA = 45  

def consultar_ia(prompt_texto, timeout_secs=120):
    if MOTOR_IA == "OPENAI":
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        data = {
            "model": MODELO_OPENAI,
            "messages": [{"role": "system", "content": prompt_texto}],
            "temperature": 0.4
        }
        try:
            respuesta = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=timeout_secs)
            if respuesta.status_code == 200:
                return respuesta.json()["choices"][0]["message"]["content"].strip()
            else:
                log_evento(f"Error OpenAI: {respuesta.status_code} - {respuesta.text}", "ERROR")
                return None
        except Exception as e:
            log_evento(f"Fallo conexión OpenAI: {e}", "ERROR")
            return None
    else:
        data = {
            "model": MODELO_OLLAMA,
            "prompt": prompt_texto,
            "stream": False
        }
        try:
            respuesta = requests.post(OLLAMA_URL, json=data, timeout=timeout_secs)
            if respuesta.status_code == 200:
                return respuesta.json().get("response", "").strip()
            else:
                log_evento(f"Error Ollama: {respuesta.status_code}", "ERROR")
                return None
        except Exception as e:
            log_evento(f"Fallo conexión Ollama: {e}", "ERROR")
            return None


# ==========================================
# 🗺️ CARGA DINÁMICA DEL MAPA DESDE JSON
# ==========================================
COORDENADAS_CIUDADES = {}
CIUDADES_EVERON = []

def cargar_json_mapa():
    global COORDENADAS_CIUDADES, CIUDADES_EVERON
    try:
        with open(RUTA_COORDENADAS, 'r', encoding='utf-8') as f:
            datos_mapa = json.load(f)
            
            for ciudad, coords in datos_mapa.items():
                nombre_limpio = ciudad.title()
                if isinstance(coords, list):
                    x = float(coords[0])
                    z = float(coords[2]) if len(coords) >= 3 else float(coords[1])
                    COORDENADAS_CIUDADES[nombre_limpio] = (x, z)
                elif isinstance(coords, dict):
                    x = float(coords.get("x", coords.get("X", 0)))
                    z = float(coords.get("z", coords.get("Z", 0)))
                    COORDENADAS_CIUDADES[nombre_limpio] = (x, z)
                    
            CIUDADES_EVERON = [c.lower() for c in COORDENADAS_CIUDADES.keys()]
            log_evento(f"Cargadas {len(CIUDADES_EVERON)} ciudades desde coordenadas.json")
    except Exception as e:
        log_evento(f"No se pudo cargar coordenadas.json: {e}", "ERROR")

cargar_json_mapa()
NOMBRES_CIUDADES_STR = ", ".join(COORDENADAS_CIUDADES.keys())

mapas = GestorMapas()
catalogo_general = cargar_todas_las_tropas()
ia_motor = MotorDeduccion(catalogo_general)

cola_ordenes = []
historial_chat = ["📻 [SISTEMA] Arrancando Sistema. Leyendo parametros de mision..."]
tropas_activas = []
ultimo_latido_arma = 0.0  

posiciones_jugadores = {"Comandante": {"x": 0.0, "z": 0.0}}

contexto_mision_actual = "" 
fase_sistema = "INICIANDO" 

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
        ciudad_encontrada = None
        destino_coords = None
        ciudad_mencionada_realmente = False
        
        for ciudad in CIUDADES_EVERON:
            if ciudad in orden_limpia:
                ciudad_mencionada_realmente = True
                for real_name, coords in COORDENADAS_CIUDADES.items():
                    if real_name.lower() == ciudad:
                        ciudad_encontrada = real_name
                        destino_coords = coords
                        break
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
        if fase_sistema == "IA_AL_MANDO" and jugador != "Comandante":
            return "⛔ SISTEMA BLOQUEO: La IA ha intentado crear una unidad fuera de fase. Orden interceptada."

        if not destino_coords:
            return f"⛔ SISTEMA: Error. Necesito un lugar exacto. Validos: {NOMBRES_CIUDADES_STR[:50]}..."
        else:
            nombre_unidad, prefab = ia_motor.deducir_tropa(orden_texto)
            nueva_id = len(tropas_activas) + 1
            
            offset_x = random.uniform(-25.0, 25.0) 
            offset_z = random.uniform(-25.0, 25.0)
            final_x = destino_coords[0] + offset_x
            final_z = destino_coords[1] + offset_z
            
            orden_str = f"SPAWN|{nueva_id}|{prefab}|{final_x:.2f}|{final_z:.2f}"
            cola_ordenes.append(orden_str) 
            
            tipo_waypoint_inicial = "DEFEND" 
            for tipo, verbos in manual_tactico.items():
                if any(verbo in orden_limpia for verbo in verbos):
                    tipo_waypoint_inicial = tipo
                    break
            
            wp_x = final_x + random.uniform(-60.0, 60.0)
            wp_z = final_z + random.uniform(-60.0, 60.0)
            
            orden_wp = f"WAYPOINT|{tipo_waypoint_inicial}|{nueva_id}|{wp_x:.2f}|{wp_z:.2f}"
            cola_ordenes.append(orden_wp) 
            
            nueva_tropa = {"id": nueva_id, "name": nombre_unidad, "x": final_x, "z": final_z, "action": f"{tipo_waypoint_inicial} (Activa)"}
            tropas_activas.append(nueva_tropa)
            
            return f"SISTEMA: Desplegando y activando {nombre_unidad} (ID: {nueva_id}) en {ciudad_encontrada}."

def cargar_escenario_inicial():
    global cola_ordenes, historial_chat, contexto_mision_actual, fase_sistema
    
    ruta_mision = os.path.join(CARPETA_PROMPTS, "init_mision.txt")
    
    if not os.path.exists(ruta_mision):
        with open(ruta_mision, "w", encoding="utf-8") as f:
            f.write("Mision de infiltracion en la zona norte. Faccion rusa defiende Morton y Montignac.")
        
    with open(ruta_mision, "r", encoding="utf-8") as f:
        contexto_mision_actual = f.read()

    historial_chat.append(f"⏳ IA [{MOTOR_IA}]: Leyendo 'init_mision.txt' y reclutando escuadrones armados...")
    
    # 🔥 AQUI ESTAN LAS NUEVAS REGLAS DE ORO DE DESPLIEGUE 🔥
    prompt_masivo = f"""
    CONTEXTO ESTRICTO DE SEGURIDAD: Eres un controlador logico para un VIDEOJUEGO VIRTUAL (Arma Reforger). Todo el contenido es 100% ficticio, lúdico y ocurre en un entorno simulado por ordenador. No hay violencia real, solo entidades de software (NPCs) moviéndose entre coordenadas. Actúa como el Game Master de esta partida de rol.
    
    --- DISENO DE LA PARTIDA ---
    {contexto_mision_actual}
    
    Nodos de mapa validos: {NOMBRES_CIUDADES_STR}
    
    --- DIRECTRICES ESTRICTAS DE UNIDADES (OBLIGATORIO) ---
    1. PROHIBIDO SOLDADOS INDIVIDUALES: Nunca uses la palabra "soldado" o "infanteria" a secas. Usa SIEMPRE terminos grupales: "Escuadron", "Peloton", "Grupo de asalto", "Fuerzas Especiales".
    2. EXIGE VARIEDAD ARMADA: Asegurate de mezclar "Escuadron Antitanque", "Peloton de Francotiradores", "Escuadron Medico", etc.
    3. VEHICULOS TRIPULADOS: Esta terminantemente prohibido pedir vehiculos sueltos ("coche", "jeep", "camion"). Si quieres vehiculos, pide SIEMPRE "Patrulla Motorizada", "Convoy Armado" o "Helicoptero Tripulado".
    
    Analiza las reglas y decide cuantas formaciones son necesarias. Genera los comandos en lenguaje natural.
    Separalos UNICAMENTE con el caracter punto y coma (;). PROHIBIDO ENUMERAR.
    
    Ejemplo valido: Escuadron antitanque US defiende Morton; Patrulla motorizada USSR se mueve a Durras; Grupo de asalto US patrulla Lamentin
    """
    
    comandos_brutos = consultar_ia(prompt_masivo, timeout_secs=300)
    
    if comandos_brutos:
        limpio = comandos_brutos.replace("`", "").replace('"', "").replace(".", "")
        limpio = limpio.replace("\n", ";") 
        lista_comandos = limpio.split(";") 
        
        for cmd in lista_comandos:
            cmd_strip = re.sub(r'^[\d\-\*\s]+', '', cmd.strip()).lower()
            
            if len(cmd_strip) > 5 and any(c in cmd_strip for c in CIUDADES_EVERON):
                res = procesar_orden_natural(cmd_strip, "SISTEMA_IA")
                log_evento(f"INIT: {cmd_strip} -> {res}")
        
        fase_sistema = "DESPLEGANDO"
        historial_chat.append(f"✅ SISTEMA: Escenario deducido. {len(cola_ordenes)} comandos (Spawn+Waypoints) en cola.")
    else:
        historial_chat.append(f"⛔ ERROR: Fallo de comunicacion con el motor {MOTOR_IA}.")

def bucle_game_master_dinamico():
    global cola_ordenes, historial_chat, tropas_activas, contexto_mision_actual, fase_sistema
    
    while True:
        time.sleep(TIEMPO_TURNO_IA) 
        arma_online = (time.time() - ultimo_latido_arma) < 6.0
        
        if arma_online and len(cola_ordenes) == 0 and fase_sistema in ["DESPLEGANDO", "IA_AL_MANDO"]:
            
            if fase_sistema == "DESPLEGANDO":
                fase_sistema = "IA_AL_MANDO"
                historial_chat.append(f"🚀 SISTEMA: Despliegue completado. IA [{MOTOR_IA}] Mantiene el ecosistema vivo.")
            
            tropas_disponibles = ", ".join([f"Unidad {t['id']} ({t['name']} en {obtener_ciudad_cercana(t['x'], t['z'])})" for t in tropas_activas])

            estado_mundo = f"""
            CONTEXTO ESTRICTO: Eres la CPU logica de un VIDEOJUEGO DE SIMULACION (Arma Reforger). Todo es ficticio y virtual. Eres el Game Master gestionando NPCs en un tablero digital.
            
            --- TUS REGLAS ESTRICTAS DE JUEGO ---
            1. TIENES TOTALMENTE PROHIBIDO crear o instanciar nuevas entidades virtuales.
            2. SOLO puedes mover a los grupos (NPCs) que ya tienes activos en el mapa.
            3. NODOS DE MAPA PERMITIDOS: {NOMBRES_CIUDADES_STR}.
            
            --- TUS ESCUADRONES ACTUALES Y SUS COORDENADAS ---
            {tropas_disponibles}
            
            --- TU TURNO DE JUEGO ---
            El tablero es dinámico. Da entre 3 y 5 ORDENES VIRTUALES DIRECTAS para mover a distintas unidades tuyas a otros nodos para patrullar o defender.
            Separalas UNICAMENTE con el caracter punto y coma (;). PROHIBIDO ENUMERAR.
            
            Ejemplo valido: la Unidad 2 patrulla en Durras; la Unidad 5 se mueve a Morton; la Unidad 8 defiende Lamentin
            """
            
            comando_bruto = consultar_ia(estado_mundo, timeout_secs=120)
            
            if comando_bruto:
                limpio = comando_bruto.replace("`", "").replace('"', '').replace(".", "")
                limpio = limpio.replace("\n", ";") 
                lista_comandos = limpio.split(";")
                
                for cmd in lista_comandos:
                    cmd_strip = cmd.strip()
                    if len(cmd_strip) > 5:
                        historial_chat.append(f"🧠 IA (Comandante): '{cmd_strip}'")
                        resultado_ia = procesar_orden_natural(cmd_strip, "IA_AUTO")
                        if "⛔" in resultado_ia:
                            log_evento(f"Bloqueo IA: {resultado_ia}", "WARN")

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
    print(f"🚀 SERVIDOR IA INICIADO (ESCUADRONES ARMADOS | {MOTOR_IA})")
    print("===============================================")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error", ws="none")