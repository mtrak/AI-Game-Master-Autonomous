import os

# Al estar en la raíz, este es nuestro centro de mando
DIRECTORIO_RAIZ = os.path.dirname(os.path.abspath(__file__))

# Rutas directas a las carpetas oficiales
CARPETA_CATALOGOS = os.path.join(DIRECTORIO_RAIZ, "Catalogos_IA")
CARPETA_DATOS = os.path.join(DIRECTORIO_RAIZ, "Datos")
CARPETA_WEB = os.path.join(DIRECTORIO_RAIZ, "Web")
CARPETA_LOGS = os.path.join(DIRECTORIO_RAIZ, "Logs")
CARPETA_PROMPTS = os.path.join(DIRECTORIO_RAIZ, "Prompts_Misiones")

# 📍 Archivos clave (con los nombres exactos que buscan tus submódulos)
RUTA_COORDENADAS = os.path.join(CARPETA_DATOS, "coordenadas.json")
ARCHIVO_MAPA = RUTA_COORDENADAS  # <--- Esto soluciona el error del gestor de mapas

# Añado esta por precaución, por si gestor_catalogos.py la necesita
ARCHIVO_PREFABS = os.path.join(CARPETA_DATOS, "prefabs.json")