class MotorDeduccion:
    def __init__(self, catalogo_tropas):
        self.catalogo = catalogo_tropas
        
        self.conceptos = {
            "rus": "USSR", "sovietic": "USSR", "american": "US", "usa": "US", 
            "fia": "FIA", "rebelde": "FIA", "guerrilla": "FIA",
            "grupo": "Group", "escuadra": "Group", "peloton": "Group", "equipo": "Group",
            "soldado": "Character", "individuo": "Character", "hombre": "Character",
            "medic": "Medic", "sanitario": "Medic", "hospital": "Medical",
            "francotirador": "Sniper", "sniper": "Sniper", "tirador": "Sharpshooter",
            "supresion": "Suppress", "ametralladora": "MachineGun", "pesada": "MG",
            "at ": "AT", "antitanque": "AT", "misil": "LAT", "lanzacohetes": "LAT",
            "spetsnaz": "Spetsnaz", "especial": "SF", "boina verde": "GreenBeret",
            "ingeniero": "Engineer", "zapador": "Sapper",
            "btr": "BTR70", "blindado": "BTR70", "tanque": "BTR70",
            "uaz": "UAZ469", "jeep": "M151A2", "coche": "UAZ469", "humvee": "M1025",
            "ural": "Ural4320", "camion": "Ural4320", "logistica": "Ural4320",
            "helicoptero": "Mi8MT", "pajaro": "Mi8MT", "huey": "UH1H"
        }

    def deducir_tropa(self, orden_texto):
        orden_lower = orden_texto.lower()
        etiquetas_encontradas = []

        for palabra_clave, etiqueta_tecnica in self.conceptos.items():
            if palabra_clave in orden_lower:
                etiquetas_encontradas.append(etiqueta_tecnica)

        if not any(f in etiquetas_encontradas for f in ["USSR", "US", "FIA"]):
            etiquetas_encontradas.append("USSR")
            
        vehiculos = ["BTR70", "UAZ469", "M151A2", "Ural4320", "Mi8MT", "UH1H", "M1025"]
        es_vehiculo = any(v in etiquetas_encontradas for v in vehiculos)
        
        if not es_vehiculo and not any(t in etiquetas_encontradas for t in ["Group", "Character"]):
            etiquetas_encontradas.append("Group")
            
        roles_detectados = [r for r in etiquetas_encontradas if r not in ["USSR", "US", "FIA", "Group", "Character"] + vehiculos]
        if not es_vehiculo and not roles_detectados:
            etiquetas_encontradas.append("RifleSquad")

        print(f"🤖 [MOTOR NLP] Pensando... Conceptos extraídos: {etiquetas_encontradas}")

        mejor_puntaje = 0
        mejor_nombre = "Group USSR RifleSquad" 
        mejor_prefab = self.catalogo.get("Group USSR RifleSquad", "{E552DABF3636C2AD}Prefabs/Groups/OPFOR/Group_USSR_RifleSquad.et")

        for nombre_catalogo, prefab in self.catalogo.items():
            puntaje_actual = 0
            nombre_test = nombre_catalogo.lower()
            
            for etiqueta in etiquetas_encontradas:
                if etiqueta.lower() in nombre_test:
                    puntaje_actual += 1
                    
            if puntaje_actual > mejor_puntaje:
                mejor_puntaje = puntaje_actual
                mejor_nombre = nombre_catalogo
                mejor_prefab = prefab

        return mejor_nombre, mejor_prefab
