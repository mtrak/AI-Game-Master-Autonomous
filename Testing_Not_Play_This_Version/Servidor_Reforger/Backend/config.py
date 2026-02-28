import json
import os
import glob

# ==========================================
# CONFIGURACIÓN DEL SERVIDOR
# ==========================================
HOST = "0.0.0.0"
PORT = 8000

# ==========================================
# CONFIGURACIÓN DE IA
# ==========================================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1"
AI_TIMEOUT = 60.0 

# ==========================================
# RUTAS
# ==========================================
DB_PATH = "war_room.db"
CATALOGOS_PATH = "../Catalogos_IA" 
COORDENADAS_PATH = "coordenadas.json"

# ==========================================
# CARGADORES MODULARES
# ==========================================
def load_all_prefabs():
    all_prefabs = {}
    if os.path.exists(CATALOGOS_PATH):
        archivos_json = glob.glob(f"{CATALOGOS_PATH}/*.json")
        for archivo in archivos_json:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    all_prefabs.update(datos)
            except Exception as e:
                pass
    return all_prefabs

def load_locations():
    if os.path.exists(COORDENADAS_PATH):
        try:
            with open(COORDENADAS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando mapa: {e}")
    return {}

PREFABS = load_all_prefabs()
LOCATIONS = load_locations()