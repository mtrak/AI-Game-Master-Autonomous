import os
import json
import re

print("=====================================================")
print("🕵️‍♂️ EXTRACTOR AUTOMÁTICO DE GUIDs - ARMA REFORGER")
print("=====================================================")

# ==========================================
# ⚙️ CONFIGURACIÓN DE RUTAS
# ==========================================
# Cambia esta ruta si tienes el Arma Reforger Tools instalado en otro disco
RUTA_ARMA_TOOLS = r"C:\Program Files (x86)\Steam\steamapps\common\Arma Reforger Tools\projects"

CARPETA_SALIDA = "Catalogos_Generados"

def extraer_guids(ruta_base):
    if not os.path.exists(ruta_base):
        print(f"❌ Error: No se encuentra la ruta de Arma Reforger Tools: {ruta_base}")
        print("Asegurate de poner la ruta correcta en la variable RUTA_ARMA_TOOLS.")
        return

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    
    diccionario_guids = {
        "Vehiculos": {},
        "Personajes": {},
        "Waypoints": {},
        "Armas": {},
        "Otros": {}
    }

    print(f"\n🔍 Escaneando miles de archivos en: {ruta_base}")
    print("⏳ Esto puede tardar unos segundos, paciencia...\n")

    archivos_procesados = 0
    guids_encontrados = 0

    # Rastrear recursivamente todas las carpetas
    for root, dirs, files in os.walk(ruta_base):
        for file in files:
            if file.endswith(".meta"):
                archivos_procesados += 1
                ruta_completa = os.path.join(root, file)
                nombre_archivo = file.replace(".meta", "") # Le quitamos el .meta para tener el nombre real (ej: AIWaypoint_Defend.et)
                
                try:
                    with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                        contenido = f.read()
                        # Buscar el patrón del GUID dentro del archivo .meta (ej: id {FAEB1F46A94E271F})
                        match = re.search(r'id\s*\{([A-F0-9]+)\}', contenido, re.IGNORECASE)
                        
                        if match:
                            guid = match.group(1)
                            guids_encontrados += 1
                            
                            # Reconstruir la ruta relativa al estilo Arma Reforger (ej: Prefabs/AI/Waypoints/...)
                            ruta_relativa = os.path.relpath(ruta_completa, ruta_base).replace("\\", "/")
                            ruta_relativa = ruta_relativa.replace(".meta", "")
                            
                            formato_arma = f"{{{guid}}}{ruta_relativa}"
                            
                            # Clasificar automáticamente según la carpeta en la que esté
                            if "Vehicles" in ruta_relativa:
                                diccionario_guids["Vehiculos"][nombre_archivo] = formato_arma
                            elif "Characters" in ruta_relativa:
                                diccionario_guids["Personajes"][nombre_archivo] = formato_arma
                            elif "Waypoints" in ruta_relativa:
                                diccionario_guids["Waypoints"][nombre_archivo] = formato_arma
                            elif "Weapons" in ruta_relativa:
                                diccionario_guids["Armas"][nombre_archivo] = formato_arma
                            else:
                                diccionario_guids["Otros"][nombre_archivo] = formato_arma

                except Exception as e:
                    pass # Ignoramos archivos corruptos o bloqueados

    # Guardar los resultados en archivos JSON separados
    for categoria, datos in diccionario_guids.items():
        if len(datos) > 0:
            ruta_json = os.path.join(CARPETA_SALIDA, f"{categoria.lower()}.json")
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            print(f"✅ Catálogo creado: {categoria}.json ({len(datos)} elementos encontrados)")

    print("\n=====================================================")
    print(f"🎉 EXTRACCIÓN COMPLETADA")
    print(f"Archivos analizados: {archivos_procesados}")
    print(f"GUIDs extraídos: {guids_encontrados}")
    print(f"Los diccionarios se han guardado en la carpeta '{CARPETA_SALIDA}'")
    print("=====================================================")

if __name__ == "__main__":
    extraer_guids(RUTA_ARMA_TOOLS)
    os.system("pause")