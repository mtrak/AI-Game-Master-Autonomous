import os

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
