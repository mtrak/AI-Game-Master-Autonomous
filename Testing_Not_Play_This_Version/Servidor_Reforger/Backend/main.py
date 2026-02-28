import uvicorn
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from config import HOST, PORT
from database import WarDatabase
from ai_agent import ZeusAIAgent

# No olvides poner aquí tu nombre real del juego
WHITELIST = ["Raulote", "ComandanteAlfa"]

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

command_queue = []
action_history = []
war_db = WarDatabase()
zeus_ai = ZeusAIAgent(war_db, command_queue, action_history)

class ManualOrder(BaseModel): 
    player_name: str
    order: str

@app.post('/manual_command')
async def manual_command(o: ManualOrder):
    if o.player_name not in WHITELIST:
        action_history.append(f"⛔ DENEGADO: '{o.player_name}' intentó dar una orden.")
        return {'status': 'denied'}

    action_history.append(f"👤 ORDEN ({o.player_name}): {o.order}")
    await zeus_ai.process_order(o.order)
    return {'status': 'ok'}

# ¡Fíjate que ya no dice "async def"! Esto soluciona los bloqueos
@app.get('/arma_sync', response_class=PlainTextResponse)
def arma_sync(px: float = 0, pz: float = 0, m: str = "Game Master"):
    war_db.update_telemetry(px, pz, m)
    if command_queue:
        c = command_queue.pop(0)
        if c['action'] == "MOVE":
            return f"MOVE|{c['id']}|{c['x']}|0|{c['z']}"
        else:
            return f"{c['action']}|{c['path']}|{c['x']}|0|{c['z']}"
    return 'NONE'

@app.get('/status')
def status():
    return {
        'history': action_history[-15:],
        'troops': war_db.get_active_troops()
    }

@app.post('/save_state')
async def save_state(request: Request):
    try:
        data = await request.json()
        players = data.get('players', [])
        troops = data.get('troops', [])
        # Mandamos el guardado a un hilo secundario para que no atasque
        await asyncio.to_thread(war_db.save_state, players, troops)
        return {"status": "saved"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get('/load_state', response_class=PlainTextResponse)
def load_state():
    troops, players = war_db.load_state()
    response_parts = []
    for t in troops:
        response_parts.append(f"LOAD|TROOP|{t[0]}|{t[1]}|{t[2]}|{t[3]}")
    for p in players:
        response_parts.append(f"LOAD|PLAYER|{p[0]}|{p[1]}|{p[2]}|{p[3]}")
    
    if not response_parts:
        return "NONE"
    return "#".join(response_parts)

if __name__ == '__main__':
    print(f"🚀 Servidor Python Iniciado en puerto {PORT}...")
    uvicorn.run(app, host=HOST, port=PORT)