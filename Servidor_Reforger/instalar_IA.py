import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
import time
import platform

print("=====================================================")
print("🚀 INSTALADOR AUTOMÁTICO: AI GAME MASTER REFORGER")
print("=====================================================")

# ==========================================
# ⚙️ CONFIGURACIÓN DEL PROYECTO
# ==========================================
# URL directa del código fuente de tu GitHub
REPO_URL = "https://github.com/mtrak/AI-Game-Master-Autonomous/archive/refs/heads/main.zip"
ZIP_NAME = "repo_descargado.zip"
EXTRACT_DIR = "temp_repo"

# Configuración de IA y Librerías
MODELO_OLLAMA = "llama3" # Cambia esto si usas otro modelo
LIBRERIAS_PYTHON = ["fastapi", "uvicorn[standard]", "websockets", "requests"]

def ejecutar_comando(comando, mensaje_exito, mensaje_error):
    try:
        subprocess.check_call(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ {mensaje_exito}")
        return True
    except Exception:
        print(f"❌ {mensaje_error}")
        return False

# ==========================================
# 1. OBTENER CÓDIGO DESDE GITHUB
# ==========================================
print("\n📥 Paso 1: Clonando el proyecto desde GitHub...")
try:
    print("   -> Descargando la última versión del repositorio...")
    urllib.request.urlretrieve(REPO_URL, ZIP_NAME)
    
    with zipfile.ZipFile(ZIP_NAME, 'r') as zip_ref:
        zip_ref.extractall(EXTRACT_DIR)
        
    # La ruta dentro del zip de GitHub
    ruta_origen = os.path.join(EXTRACT_DIR, "AI-Game-Master-Autonomous-main", "AI_GameMaster")
    
    # Movemos las carpetas (Catalogos_IA, Cerebro_IA, Web, etc.) al directorio actual
    if os.path.exists(ruta_origen):
        for elemento in os.listdir(ruta_origen):
            origen = os.path.join(ruta_origen, elemento)
            destino = os.path.join(os.getcwd(), elemento)
            
            if os.path.exists(destino):
                if os.path.isdir(destino): shutil.rmtree(destino)
                else: os.remove(destino)
                
            shutil.move(origen, destino)
            print(f"   -> Instalado: {elemento}")
            
    # Limpiamos los archivos temporales
    os.remove(ZIP_NAME)
    shutil.rmtree(EXTRACT_DIR)
    print("✅ Sistema de archivos y catálogos creados con éxito.")
except Exception as e:
    print(f"❌ Error al descargar desde GitHub: {e}")
    sys.exit(1)

# ==========================================
# 2. INSTALAR DEPENDENCIAS DE PYTHON
# ==========================================
print("\n🐍 Paso 2: Instalando librerías de red...")
for lib in LIBRERIAS_PYTHON:
    print(f"   -> Instalando {lib}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", lib], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("✅ Entorno de Python preparado.")

# ==========================================
# 3. INSTALAR OLLAMA (Si no existe)
# ==========================================
print("\n🦙 Paso 3: Comprobando motor de IA (Ollama)...")
try:
    subprocess.run(["ollama", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✅ Ollama ya está instalado en tu sistema.")
except (subprocess.CalledProcessError, FileNotFoundError):
    print("⚠️ Ollama no está instalado. Iniciando descarga automática...")
    if platform.system() == "Windows":
        url_ollama = "https://ollama.com/download/OllamaSetup.exe"
        instalador = "OllamaSetup.exe"
        print("   -> Descargando OllamaSetup.exe...")
        urllib.request.urlretrieve(url_ollama, instalador)
        print("   -> Abriendo instalador. Por favor, instálalo y pulsa continuar.")
        subprocess.run([instalador], check=True)
        time.sleep(5) 
    else:
        print("❌ Instala Ollama manualmente desde https://ollama.com")

# ==========================================
# 4. DESCARGAR EL CEREBRO DE LA IA
# ==========================================
print(f"\n🧠 Paso 4: Descargando el modelo de IA ({MODELO_OLLAMA})...")
print("   -> Esto puede tardar unos minutos dependiendo de tu internet. ¡Paciencia!")
ejecutar_comando(
    ["ollama", "pull", MODELO_OLLAMA],
    f"Modelo '{MODELO_OLLAMA}' descargado y listo.",
    "Error al descargar la IA. Asegúrate de tener internet."
)

# ==========================================
# 5. CREAR ACCESO DIRECTO
# ==========================================
print("\n🎮 Paso 5: Generando archivo de lanzamiento...")
contenido_bat = f"""@echo off
title AI Game Master - Servidor Tactico
echo Iniciando motor de IA (Ollama)...
start /b ollama serve
timeout /t 3 /nobreak > NUL
echo Arrancando Servidor de Arma Reforger...
python main.py
pause
"""
with open("Arrancar_IA.bat", "w") as f:
    f.write(contenido_bat)
print("✅ Archivo 'Arrancar_IA.bat' creado.")

print("\n=====================================================")
print("🎉 ¡TODO LISTO! INSTALACIÓN COMPLETADA AL 100% 🎉")
print("=====================================================")
print("Para jugar, simplemente haz doble clic en el archivo:")
print("👉 Arrancar_IA.bat 👈")
print("=====================================================")
os.system("pause")