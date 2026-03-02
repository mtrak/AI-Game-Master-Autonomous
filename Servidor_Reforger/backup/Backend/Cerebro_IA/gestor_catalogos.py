import json
import os
import glob
from config_rutas import CARPETA_CATALOGOS

def cargar_todas_las_tropas():
    catalogo_maestro = {}
    if os.path.exists(CARPETA_CATALOGOS):
        archivos_json = glob.glob(os.path.join(CARPETA_CATALOGOS, "*.json"))
        for archivo in archivos_json:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    catalogo_maestro.update(datos)
            except Exception as e:
                print(f"❌ Error leyendo {os.path.basename(archivo)}: {e}")
    else:
        print(f"⚠️ Atención: No se encontró la carpeta {CARPETA_CATALOGOS}")
    
    return catalogo_maestro
