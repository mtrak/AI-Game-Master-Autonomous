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
REPO_URL = "https://github.com/mtrak/AI-Game-Master-Autonomous/archive/refs/heads/main.zip"
ZIP_NAME = "repo_descargado.zip"
EXTRACT_DIR = "temp_repo"

MODELO_OLLAMA = "llama3" 
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
# 1. OBTENER CÓDIGO Y SEPARAR CARPETAS
# ==========================================
print("\n📥 Paso 1: Descargando e instalando el proyecto...")
try:
    print("   -> Clonando la última versión del repositorio...")
    urllib.request.urlretrieve(REPO_URL, ZIP_NAME)
    
    with zipfile.ZipFile(ZIP_NAME, 'r') as zip_ref:
        zip_ref.extractall(EXTRACT_DIR)
        
    # Identificar la carpeta raíz extraída (ej: AI-Game-Master-Autonomous-main)
    carpeta_raiz_zip = os.listdir(EXTRACT_DIR)[0]
    
    ruta_servidor = os.path.join(EXTRACT_DIR, carpeta_raiz_zip, "Servidor_Reforger")
    ruta_addon = os.path.join(EXTRACT_DIR, carpeta_raiz_zip, "AI_GameMaster")

    # --- 1A. INSTALAR EL SERVIDOR PYTHON ---
    if os.path.exists(ruta_servidor):
        for elemento in os.listdir(ruta_servidor):
            origen = os.path.join(ruta_servidor, elemento)
            destino = os.path.join(os.getcwd(), elemento)
            
            if os.path.exists(destino):
                if os.path.isdir(destino): shutil.rmtree(destino)
                else: os.remove(destino)
                
            shutil.move(origen, destino)
        print("   ✅ Backend (Servidor Python) instalado en la carpeta actual.")
    else:
        print("   ❌ Error: No se encontró la carpeta 'Servidor_Reforger' en GitHub.")

    # --- 1B. INSTALAR EL ADDON EN EL WORKBENCH DE ARMA ---
    if os.path.exists(ruta_addon):
        # Buscamos la ruta de Documentos estándar de Windows
        ruta_docs = os.path.join(os.path.expanduser('~'), 'Documents')
        ruta_workbench = os.path.join(ruta_docs, 'My Games', 'ArmaReforgerWorkbench', 'addons', 'AI_GameMaster')
        
        try:
            os.makedirs(os.path.dirname(ruta_workbench), exist_ok=True)
            if os.path.exists(ruta_workbench):
                shutil.rmtree(ruta_workbench) # Borra la versión vieja
            
            shutil.move(ruta_addon, ruta_workbench)
            print(f"   ✅ Addon C++ instalado automáticamente en: ArmaReforgerWorkbench/addons/")
        except Exception as e:
            # Si falla por permisos, lo extraemos aquí para que el usuario lo mueva a mano
            destino_alt = os.path.join(os.getcwd(), "AI_GameMaster_Addon")
            if os.path.exists(destino_alt): shutil.rmtree(destino_alt)
            shutil.move(ruta_addon, destino_alt)
            print("   ⚠️ No se pudo instalar el Addon en el Workbench automáticamente.")
            print(f"   -> El Addon se ha guardado en la carpeta local: {destino_alt}")
            print("   -> Por favor, cópialo a mano a tu carpeta de addons del juego.")

    # Limpiamos basura
    if os.path.exists(ZIP_NAME): os.remove(ZIP_NAME)
    if os.path.exists(EXTRACT_DIR): shutil.rmtree(EXTRACT_DIR)
    
except Exception as e:
    print(f"❌ Error crítico al descargar desde GitHub: {e}")
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
# 3. INSTALAR OLLAMA
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
# 5. CREAR ACCESO DIRECTO (.BAT)
# ==========================================
print("\n🎮 Paso 5: Generando archivo de lanzamiento...")
contenido_bat = f"""@echo off
title AI Game Master - Servidor Tactico
cd /d "%~dp0"
echo Iniciando motor de IA (Ollama)...
start /b ollama serve >NUL 2>NUL
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
print("1. El Addon se ha enviado a tu Workbench de Arma.")
print("2. Para encender el panel de control web, haz doble clic en:")
print("👉 Arrancar_IA.bat 👈")
print("=====================================================")
os.system("pause")