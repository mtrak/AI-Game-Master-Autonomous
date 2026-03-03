import json
import os
from config_rutas import ARCHIVO_MAPA

class GestorMapas:
    def __init__(self):
        self.mapa = self._cargar_coordenadas()
        self.ciudades_planas = self._aplanar_mapa()

    def _cargar_coordenadas(self):
        if os.path.exists(ARCHIVO_MAPA):
            try:
                with open(ARCHIVO_MAPA, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Error JSON Mapa: {e}")
        return {}

    def _aplanar_mapa(self):
        planas = {}
        for k, v in self.mapa.items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    planas[sub_k] = sub_v
            elif isinstance(v, list):
                planas[k] = v
        return planas

    def buscar_destino(self, texto_orden):
        texto_orden = texto_orden.lower()
        palabras = texto_orden.split()
        
        for ciudad, coords in self.ciudades_planas.items():
            if ciudad.lower() in texto_orden:
                return ciudad, coords
                
        for palabra in palabras:
            if len(palabra) > 3: 
                for ciudad, coords in self.ciudades_planas.items():
                    if palabra in ciudad.lower():
                        nombre_limpio = ciudad.replace("C_Location", "").replace("G_", "")
                        return nombre_limpio, coords
                        
        return "Montignac", [4773, 7094] # Fallback
