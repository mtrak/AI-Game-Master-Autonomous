import random

class MotorDeduccion:
    def __init__(self, catalogo_general):
        """
        catalogo_general es un diccionario gigante que contiene TODAS las claves
        de los JSON que el Game Master ha metido en la carpeta Catalogos_IA.
        """
        self.catalogo = catalogo_general

    def deducir_tropa(self, texto_orden):
        """
        Analiza el lenguaje natural de Ollama o del jugador y devuelve el 
        (Nombre_Legible, Prefab_Exacto_del_Juego).
        """
        texto = texto_orden.lower()

        # ---------------------------------------------------------
        # 1. VEHÍCULOS AÉREOS
        # ---------------------------------------------------------
        if any(palabra in texto for palabra in ["helicoptero", "pajaro", "apoyo aereo", "extraccion", "transporte aereo"]):
            if "ruso" in texto or "sovietico" in texto or "mi8" in texto:
                if "armado" in texto or "artillado" in texto or "ataque" in texto:
                    return "Helicoptero Mi8 Armado", self.catalogo.get("Mi8MT armed", "{7BD282AF716ED639}Prefabs/Vehicles/Helicopters/Mi8MT/Mi8MT_armed.et")
                return "Helicoptero Mi8 Transporte", self.catalogo.get("Mi8MT base", "{AFF6067A5CE8A853}Prefabs/Vehicles/Helicopters/Mi8MT/Mi8MT_base.et")
            else: 
                if "armado" in texto or "artillado" in texto or "ataque" in texto:
                    return "Helicoptero UH1H Artillado", self.catalogo.get("UH1H armed", "{DDDD9B51F1234DF3}Prefabs/Vehicles/Helicopters/UH1H/UH1H_armed.et")
                return "Helicoptero UH1H Transporte", self.catalogo.get("UH1H", "{70BAEEFC2D3FEE64}Prefabs/Vehicles/Helicopters/UH1H/UH1H.et")

        # ---------------------------------------------------------
        # 2. VEHÍCULOS TERRESTRES (Incluye coches de policía y ambulancias)
        # ---------------------------------------------------------
        if any(palabra in texto for palabra in ["vehiculo", "coche", "camion", "transporte", "blindado", "jeep", "ambulancia", "reparto"]):
            
            # Vehículos de emergencia y civiles
            if "policia" in texto or "patrulla" in texto or "guardia" in texto:
                return "Coche de Policia", self.catalogo.get("UAZ469 uncovered CIV blue", "{9B3A89DD33FF0483}Prefabs/Vehicles/Wheeled/UAZ469/UAZ469_uncovered_CIV_blue.et")
            
            if "ambulancia" in texto or "medico" in texto or "rescate" in texto:
                return "Ambulancia Civil", self.catalogo.get("UAZ452 ambulance", "{43C4AF1EEBD001CE}Prefabs/Vehicles/Wheeled/UAZ452/UAZ452_ambulance.et")
                
            if "civil" in texto or "reparto" in texto or "ciudadano" in texto:
                coches_civiles = ["S105 randomized", "S1203 cargo randomized", "S1203 transport randomized"]
                coche_elegido = random.choice(coches_civiles)
                prefab = self.catalogo.get(coche_elegido, "{128253A267BE9424}Prefabs/Vehicles/Wheeled/S105/S105_randomized.et")
                return "Coche Civil", prefab

            # Militares
            if "ruso" in texto or "sovietico" in texto:
                if "blindado" in texto or "btr" in texto or "brdm" in texto:
                    return "Blindado BTR-70", self.catalogo.get("BTR70", "{C012BB3488BEA0C2}Prefabs/Vehicles/Wheeled/BTR70/BTR70.et")
                if "camion" in texto:
                    return "Camion Ural Ruso", self.catalogo.get("Ural4320", "{4597626AF36C0858}Prefabs/Vehicles/Wheeled/Ural4320/Ural4320.et")
                return "Vehiculo Ligero UAZ", self.catalogo.get("UAZ469", "{259EE7B78C51B624}Prefabs/Vehicles/Wheeled/UAZ469/UAZ469.et")
            else: 
                if "blindado" in texto or "lav" in texto:
                    return "Blindado LAV-25", self.catalogo.get("LAV25", "{0FBF8F010F81A4E5}Prefabs/Vehicles/Wheeled/LAV25/LAV25.et")
                if "camion" in texto:
                    return "Camion M923A1 US", self.catalogo.get("M923A1", "{9A0D72816DFFDB7F}Prefabs/Vehicles/Wheeled/M923A1/M923A1.et")
                return "Vehiculo Humvee", self.catalogo.get("M1025", "{4A71F755A4513227}Prefabs/Vehicles/Wheeled/M998/M1025.et")

        # ---------------------------------------------------------
        # 3. CIVILES Y POLICÍA (Ampliación masiva de vocabulario)
        # ---------------------------------------------------------
        if any(palabra in texto for palabra in ["policia", "policias", "guardia", "guardias", "seguridad", "agente", "urbano", "sheriff", "patrulla"]):
            return "Unidad de Policia Local", self.catalogo.get("Character FIA BaseLoadout", "{DE3786C0C6C978D4}Prefabs/Characters/Factions/INDFOR/FIA/Character_FIA_BaseLoadout.et")
            
        if any(palabra in texto for palabra in ["trabajador", "obrero", "electricista", "mecanico", "limpieza", "bombero", "repartidor"]):
            return "Obrero/Especialista Civil", self.catalogo.get("Character CIV ConstructionWorker Randomized", "{D97EAE64721478F3}Prefabs/Characters/Factions/CIV/ConstructionWorker/Character_CIV_ConstructionWorker_Randomized.et")
            
        if any(palabra in texto for palabra in ["empresario", "traje", "abogado", "comerciante", "vendedor"]):
            return "Empresario Civil", self.catalogo.get("Character CIV Businessman Randomized", "{B3AB6D12D247DDB5}Prefabs/Characters/Factions/CIV/Businessman/Character_CIV_Businessman_Randomized.et")

        if any(palabra in texto for palabra in ["civil", "civiles", "ciudadano", "ciudadanos", "poblacion", "transeunte", "anciano", "ancianos", "niño", "niños", "chico", "chicos", "mujer", "mujeres", "estudiante", "estudiantes", "vecino", "residente"]):
            return "Ciudadano Civil", self.catalogo.get("Character CIV Randomized", "{22E43956740A6794}Prefabs/Characters/Factions/CIV/GenericCivilians/Character_CIV_Randomized.et")

        # ---------------------------------------------------------
        # 4. FACCION FIA (Guerrilla / Rebeldes)
        # ---------------------------------------------------------
        if any(palabra in texto for palabra in ["rebelde", "rebeldes", "fia", "guerrilla", "insurgente"]):
            if "grupo" in texto or "escuadron" in texto or "peloton" in texto:
                return "Escuadron Guerrillero FIA", self.catalogo.get("Group FIA RifleSquad", "{CE41AF625D05D0F0}Prefabs/Groups/INDFOR/Group_FIA_RifleSquad.et")
            elif "francotirador" in texto or "sniper" in texto:
                return "Francotirador FIA", self.catalogo.get("Character FIA Sharpshooter", "{CE33AB22F61F3365}Prefabs/Characters/Factions/INDFOR/FIA/Character_FIA_Sharpshooter.et")
            else:
                return "Rebelde FIA Solitario", self.catalogo.get("Character FIA Randomized", "{8515E8BD26A5D5F8}Prefabs/Characters/Factions/INDFOR/FIA/Character_FIA_Randomized.et")

        # ---------------------------------------------------------
        # 5. FACCION US (Fuerzas Americanas)
        # ---------------------------------------------------------
        if any(palabra in texto for palabra in ["americano", "us", "eeuu", "estados unidos", "otan"]):
            if "fuerzas especiales" in texto or "boina verde" in texto or "sf" in texto:
                return "Escuadron Boinas Verdes US", self.catalogo.get("Group US GreenBeret Squad", "{D0886786634E55AE}Prefabs/Groups/BLUFOR/GreenBerets/Group_US_GreenBeret_Squad.et")
            elif "grupo" in texto or "escuadron" in texto or "peloton" in texto:
                return "Escuadron US Army", self.catalogo.get("Group US RifleSquad", "{DDF3799FA1387848}Prefabs/Groups/BLUFOR/Group_US_RifleSquad.et")
            elif "francotirador" in texto or "sniper" in texto:
                return "Francotirador US", self.catalogo.get("Character US Sniper", "{0F6689B491641155}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Sniper.et")
            else:
                return "Soldado US Solitario", self.catalogo.get("Character US Randomized", "{5EFC243926EE6808}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Randomized.et")

        # ---------------------------------------------------------
        # 6. FACCION USSR (Rusos / Soviéticos) - FALLBACK POR DEFECTO
        # ---------------------------------------------------------
        if "fuerzas especiales" in texto or "spetsnaz" in texto:
            return "Escuadron Spetsnaz", self.catalogo.get("Group USSR Spetsnaz Squad", "{4D3BBEC1A955626A}Prefabs/Groups/OPFOR/Spetsnaz/Group_USSR_Spetsnaz_Squad.et")
        
        if any(palabra in texto for palabra in ["grupo", "escuadron", "peloton", "fuerzas"]):
            return "Escuadron Ruso", self.catalogo.get("Group USSR RifleSquad", "{E552DABF3636C2AD}Prefabs/Groups/OPFOR/Group_USSR_RifleSquad.et")
            
        if "francotirador" in texto or "sniper" in texto:
            return "Francotirador Ruso", self.catalogo.get("Character USSR Sharpshooter", "{976AC400219898FA}Prefabs/Characters/Factions/OPFOR/USSR_Army/Character_USSR_Sharpshooter.et")

        return "Soldado Ruso Genérico", self.catalogo.get("Character USSR Randomized", "{7DE1CBA32A0225EB}Prefabs/Characters/Factions/OPFOR/USSR_Army/Character_USSR_Randomized.et")