import json
import httpx
import difflib
from config import OLLAMA_URL, MODEL_NAME, AI_TIMEOUT, PREFABS, LOCATIONS

class ZeusAIAgent:
    def __init__(self, war_db, command_queue, action_history):
        self.war_db = war_db
        self.queue = command_queue
        self.history = action_history

    async def process_order(self, prompt):
        px, pz, mission = self.war_db.get_pos()
        lista_nombres = list(PREFABS.keys())
        tropas_activas = self.war_db.get_active_troops()
        
        ciudades = list(LOCATIONS.keys())
        
        sys_prompt = f"""Eres Zeus, el Game Master IA de Arma Reforger. 
Jugador en X:{int(px)} Z:{int(pz)}. 

Elige entre 2 ACCIONES:
1. "CREATE": Si el usuario pide CREAR, SPAWNEAR o ENVIAR ALGO NUEVO.
2. "MOVE": Si el usuario pide MOVER, ATACAR o REFORZAR con algo que YA EXISTE en el mapa. 

CIUDADES DISPONIBLES: {ciudades}
TROPAS ACTIVAS EN MAPA (Para MOVE): {tropas_activas}

🛑 REGLAS ESTRICTAS DE VOCABULARIO (Para CREATE) 🛑
El catálogo tiene prefijos importantes. Úsalos correctamente:
- Si el usuario pide "un soldado", "un francotirador", "un médico", "un hombre" (INDIVIDUAL): Busca obligatoriamente nombres que empiecen por "Character ".
- Si el usuario pide "una unidad", "un grupo", "una escuadra", "una patrulla" o "tropas" (MÚLTIPLE): Busca obligatoriamente nombres que empiecen por "Group ".
- Si el usuario pide un vehículo: Busca "BTR", "UAZ", "Ural", "Mi8", "UH1H", etc.

CATALOGO COMPLETO: {lista_nombres}

Responde SOLO en JSON:
- "action": "CREATE" o "MOVE"
- "unit": Nombre exacto del catálogo (si CREATE) o el ID numérico (si MOVE).
- "target_location": Nombre exacto de la ciudad (Ej: "Gravette"). Si dice 'aqui' o 'mi posicion', escribe "player".
- "manned": true o false (Solo para vehiculos en CREATE. true si los quiere con gente dentro).
- "internal_thought": Tu razonamiento corto."""
        
        payload = {'model': MODEL_NAME, 'prompt': prompt, 'system': sys_prompt, 'stream': False, 'format': 'json'}
        
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(OLLAMA_URL, json=payload, timeout=AI_TIMEOUT)
                data = json.loads(r.json()['response'])
                
                action = data.get('action', 'CREATE')
                unit = data.get('unit', '')
                target_loc = data.get('target_location', 'player')
                
                # Resolución de Coordenadas
                if target_loc in LOCATIONS:
                    final_x = LOCATIONS[target_loc]['x']
                    final_z = LOCATIONS[target_loc]['z']
                    nombre_loc = target_loc
                else:
                    final_x = px + 15
                    final_z = pz + 15
                    nombre_loc = "Posicion del Jugador"

                if action == "MOVE":
                    self.queue.append({'action': 'MOVE', 'id': unit, 'x': final_x, 'z': final_z})
                    self.history.append(f"🧠 IA: {data.get('internal_thought')} -> [MOVER ID: {unit} a {nombre_loc}]")
                else:
                    path = PREFABS.get(unit, "")
                    
                    if not path and unit:
                        # Si el auto-corrector entra en acción, intentamos mantener el prefijo que la IA eligió
                        coincidencias = difflib.get_close_matches(unit, lista_nombres, n=1, cutoff=0.4)
                        if coincidencias:
                            unidad_corregida = coincidencias[0]
                            path = PREFABS[unidad_corregida]
                            self.history.append(f"🔧 Autocorreccion: '{unit}' -> '{unidad_corregida}'")
                            unit = unidad_corregida

                    if path:
                        manned = data.get('manned', False)
                        action_type = "SPAWN_MANNED" if ("Vehicles" in path and manned) else "SPAWN"
                        self.queue.append({'action': action_type, 'path': path, 'x': final_x, 'z': final_z})
                        self.history.append(f"🧠 IA: {data.get('internal_thought')} -> [CREAR: {unit} en {nombre_loc}]")
                    else:
                        self.history.append(f"❌ ERROR IA: No reconozco la unidad '{unit}'.")
            except Exception as e:
                self.history.append(f"❌ ERROR IA: {str(e)}")