import os
import shutil

print("==============================================")
print("   INICIANDO PROTOCOLO DE REORGANIZACION")
print("==============================================\n")

DIRECTORIO_RAIZ = os.path.dirname(os.path.abspath(__file__))

# 1. Crear las carpetas destino si no existen
carpetas_oficiales = ["Datos", "Logs", "Prompts_Misiones", "Web", "Cerebro_IA"]
print("[+] Verificando estructura base...")
for carpeta in carpetas_oficiales:
    os.makedirs(os.path.join(DIRECTORIO_RAIZ, carpeta), exist_ok=True)

# 2. Lista de movimientos precisos: (Ruta Origen -> Ruta Destino)
movimientos = [
    # Sacar los motores a la raíz
    ("Backend/main.py", "main.py"),
    ("Backend/config_rutas.py", "config_rutas.py"),
    ("Backend/Cerebro_IA", "Cerebro_IA"),
    
    # Agrupar datos y configuraciones
    ("Backend/Datos/coordenadas.json", "Datos/coordenadas.json"),
    ("prefabs.json", "Datos/prefabs.json"),
    
    # Rescatar Logs y Prompts
    ("Backend/Logs/sistema_ia.log", "Logs/sistema_ia.log"),
    ("Backend/Prompts_Misiones/init_mision.txt", "Prompts_Misiones/init_mision.txt"),
    
    # Consolidar Web
    ("Backend/Web/index.html", "Web/index.html"),
    
    # Eliminar instaladores duplicados
    ("Backend/instalar_ia.py", None),
    ("instalar_IA.py", None)
]

print("\n[+] Ejecutando movimientos tácticos...")
for origen, destino in movimientos:
    ruta_origen = os.path.join(DIRECTORIO_RAIZ, origen.replace("/", os.sep))
    
    if os.path.exists(ruta_origen):
        if destino is None:
            if os.path.isdir(ruta_origen):
                shutil.rmtree(ruta_origen)
            else:
                os.remove(ruta_origen)
            print(f"    - Eliminado residual: {origen}")
        else:
            ruta_destino = os.path.join(DIRECTORIO_RAIZ, destino.replace("/", os.sep))
            # Si el destino ya existe y es un archivo, lo borramos para sobreescribir
            if os.path.exists(ruta_destino) and os.path.isfile(ruta_destino):
                os.remove(ruta_destino)
            shutil.move(ruta_origen, ruta_destino)
            print(f"    - Movido: {origen} -> {destino}")

# 3. Eliminar la carpeta Backend si ha quedado vacía
ruta_backend = os.path.join(DIRECTORIO_RAIZ, "Backend")
if os.path.exists(ruta_backend):
    try:
        shutil.rmtree(ruta_backend)
        print("\n[+] Carpeta 'Backend' antigua purgada con éxito.")
    except Exception as e:
        print(f"\n[!] No se pudo borrar 'Backend'. Límpiala manualmente. Error: {e}")

print("\n==============================================")
print("   REORGANIZACION COMPLETADA CON EXITO")
print("==============================================")