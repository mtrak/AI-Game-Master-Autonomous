import json
import os

print("====================================================")
print("  CLASIFICANDO CATÁLOGO DE ARMA REFORGER...")
print("====================================================")

# Crear carpeta para guardar los JSONs limpios
os.makedirs("Catalogos_IA", exist_ok=True)

# Diccionarios para cada categoría
categorias = {
    "grupos_us": {},
    "grupos_ussr": {},
    "grupos_fia": {},
    "personajes_us": {},
    "personajes_ussr": {},
    "personajes_fia": {},
    "civiles": {},
    "vehiculos_terrestres": {},
    "helicopteros": {}
}

try:
    with open("unidades.txt", "r", encoding="utf-8") as f:
        lineas = f.readlines()
        
    for linea in lineas:
        linea = linea.strip()
        # Ignorar líneas vacías o que no empiecen por un GUID {
        if not linea or not linea.startswith("{"): 
            continue
        
        # Extraer un nombre legible para la IA (Ej: "Group US AmmoTeam")
        nombre_crudo = linea.split('/')[-1].replace('.et', '')
        nombre_limpio = nombre_crudo.replace('_', ' ')
        
        # Clasificador automático basado en la ruta
        if "Groups/BLUFOR" in linea: categorias["grupos_us"][nombre_limpio] = linea
        elif "Groups/OPFOR" in linea: categorias["grupos_ussr"][nombre_limpio] = linea
        elif "Groups/INDFOR" in linea: categorias["grupos_fia"][nombre_limpio] = linea
        elif "Characters/Factions/BLUFOR" in linea: categorias["personajes_us"][nombre_limpio] = linea
        elif "Characters/Factions/OPFOR" in linea: categorias["personajes_ussr"][nombre_limpio] = linea
        elif "Characters/Factions/INDFOR" in linea: categorias["personajes_fia"][nombre_limpio] = linea
        elif "Characters/Factions/CIV" in linea: categorias["civiles"][nombre_limpio] = linea
        elif "Vehicles/Wheeled" in linea: categorias["vehiculos_terrestres"][nombre_limpio] = linea
        elif "Vehicles/Helicopters" in linea: categorias["helicopteros"][nombre_limpio] = linea

    # Guardar cada diccionario en un archivo JSON independiente
    for nombre_cat, datos in categorias.items():
        if datos: # Solo creamos el archivo si hay datos dentro
            ruta = f"Catalogos_IA/prefabs_{nombre_cat}.json"
            with open(ruta, "w", encoding="utf-8") as json_file:
                json.dump(datos, json_file, indent=4)
            print(f"[+] Generado: {ruta} ({len(datos)} unidades)")

    print("====================================================")
    print(" ✅ ¡Todos los JSON han sido generados con éxito!")
    print("====================================================")
    
except FileNotFoundError:
    print("❌ Error: No se encontró el archivo 'unidades.txt'.")