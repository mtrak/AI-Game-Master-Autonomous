import os
import sys
import subprocess
import importlib.util
import traceback
import shutil

def print_header(text):
    print(f"\n{'='*75}\n{text}\n{'='*75}")

def check_dependencies():
    print_header("🔍 VERIFICANDO DEPENDENCIAS DEL SISTEMA")
    print(f"[OK] Python detectado: Version {sys.version.split()[0]}")

    if shutil.which("ollama"):
        print("[OK] Ollama detectado en el PATH del sistema.")
    else:
        print("[!] ADVERTENCIA: No se detecto 'ollama'. Debes instalarlo para que la IA funcione.")

    docs_path = os.path.expanduser("~/Documents")
    if os.path.exists(os.path.join(docs_path, "My Games", "ArmaReforgerWorkbench")):
        print("[OK] Carpeta de Arma Reforger Workbench detectada.")
    if os.path.exists(os.path.join(docs_path, "My Games", "ArmaReforger")):
        print("[OK] Perfil de Arma Reforger detectado.")

def install_python_packages():
    print_header("📦 VERIFICANDO PAQUETES DE PYTHON")
    required_packages = ["fastapi", "uvicorn", "httpx", "pydantic"]
    missing_packages = [pkg for pkg in required_packages if importlib.util.find_spec(pkg) is None]

    if missing_packages:
        print(f"[-] Instalando paquetes faltantes: {missing_packages}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
    else:
        print("[OK] Todas las librerias de Python estan listas.")

def main():
    print_header("🚀 INSTALADOR MAESTRO V15: ARCHIVOS ORIGINALES + HOST IN-GAME")
    
    check_dependencies()
    install_python_packages()

    docs_dir = os.path.expanduser("~/Documents")
    server_dir = os.path.join(docs_dir, "ArmaAI_Server")
    
    workbench_mod_dir = os.path.join(docs_dir, "My Games", "ArmaReforgerWorkbench", "addons", "AI_GameMaster")
    
    old_unpacked_game_mod = os.path.join(docs_dir, "My Games", "ArmaReforger", "addons", "AI_GameMaster")
    if os.path.exists(old_unpacked_game_mod):
        print("[-] Limpiando restos de mods en la carpeta del juego base...")
        shutil.rmtree(old_unpacked_game_mod)

    print_header("📂 CREANDO ESTRUCTURA DE DIRECTORIOS")
    os.makedirs(os.path.join(server_dir, "Backend"), exist_ok=True)
    os.makedirs(os.path.join(server_dir, "Web"), exist_ok=True)
    
    os.makedirs(os.path.join(workbench_mod_dir, "Missions"), exist_ok=True)
    os.makedirs(os.path.join(workbench_mod_dir, "Scripts", "Game"), exist_ok=True)
    os.makedirs(os.path.join(workbench_mod_dir, "worlds", "GameMaster"), exist_ok=True)

    server_files = {}

    server_files["LANZAR_IA.bat"] = "\n".join([
        "@echo off",
        "title Cerebro IA - AI Game Master",
        "color 0B",
        "echo ===================================================",
        "echo        INICIANDO CEREBRO DE LA IA (PYTHON)",
        "echo ===================================================",
        "echo.",
        "echo Iniciando servidor en segundo plano...",
        "start \"Cerebro IA\" cmd /c \"cd Backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000\"",
        "",
        "echo Abriendo panel de mando web...",
        "timeout /t 2 >nul",
        "start \"\" \"Web\\index.html\"",
        "",
        "echo.",
        "echo [LISTO] La IA esta escuchando en el puerto 8000.",
        "echo Ya puedes abrir Arma Reforger y alojar tu partida.",
        "echo ===================================================",
        "pause"
    ])

    server_files["prefabs.json"] = "\n".join([
        "{",
        "  \"US Asistente de Ametrallador (AMG)\": \"{6058AB54781A0C52}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_AMG.et\",",
        "  \"US Portador de Municion (Ammo)\": \"{CD28EE7C5690D3BB}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Ammo.et\",",
        "  \"US Fusilero Automatico (AR)\": \"{5B1996C05B1E51A4}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_AR.et\",",
        "  \"US Base\": \"{836E7E39AAC5888B}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Base.et\",",
        "  \"US Base Loadout\": \"{284E735C6C70DAD2}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_BaseLoadout.et\",",
        "  \"US Comandante de Compania (CC)\": \"{F35F145D4A3F75EF}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_CC.et\",",
        "  \"US Tripulacion de Vehiculo (Crew)\": \"{E1CB513B8B9B08F4}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Crew.et\",",
        "  \"US Ingeniero (Engineer)\": \"{36CCDB4556ECDA06}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Engineer.et\",",
        "  \"US Granadero (GL)\": \"{84029128FA6F6BB9}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_GL.et\",",
        "  \"US Tripulacion de Helicoptero (HeliCrew)\": \"{15CD521098748195}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_HeliCrew.et\",",
        "  \"US Piloto de Helicoptero (HeliPilot)\": \"{42A502E3BB727CEB}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_HeliPilot.et\",",
        "  \"US Antitanque Ligero (LAT)\": \"{27BF1FF235DD6036}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_LAT.et\",",
        "  \"US Medico (Medic)\": \"{C9E4FEAF5AAC8D8C}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Medic.et\",",
        "  \"US Ametrallador Pesado (MG)\": \"{1623EA3AEFACA0E4}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_MG.et\",",
        "  \"US Oficial (Officer)\": \"{DE15FB5FAFC3E63F}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Officer.et\",",
        "  \"US Lider de Peloton (PL)\": \"{0B3167BB0FB68110}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_PL.et\",",
        "  \"US Soldado Aleatorio (Randomized)\": \"{5EFC243926EE6808}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Randomized.et\",",
        "  \"US Fusilero Estandar (Rifleman)\": \"{26A9756790131354}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Rifleman.et\",",
        "  \"US Fusilero Variante 1\": \"{EA158B6EB6A24B4B}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Rifleman_Variant_1.et\",",
        "  \"US Operador de Radio (RTO)\": \"{3726077BE60962FF}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_RTO.et\",",
        "  \"US Zapador de Combate (Sapper)\": \"{AE63E4B79FB45DD1}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Sapper.et\",",
        "  \"US Explorador (Scout)\": \"{371FD0F920B600DD}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Scout.et\",",
        "  \"US Explorador Radio (Scout RTO)\": \"{E94CD0D20A63909E}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Scout_RTO.et\",",
        "  \"US Sargento (Sergeant)\": \"{4FBA24F7BB43E17D}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Sergeant.et\",",
        "  \"US Lider de Escuadra (SL)\": \"{E45F1E163F5CA080}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_SL.et\",",
        "  \"US Francotirador (Sniper)\": \"{0F6689B491641155}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Sniper.et\",",
        "  \"US Observador de Francotirador (Spotter)\": \"{1CA3D30464EE4674}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Spotter.et\",",
        "  \"US Lider de Equipo (TL)\": \"{E398E44759DA1A43}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_TL.et\",",
        "  \"US Desarmado (Unarmed)\": \"{2F912ED6E399FF47}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Unarmed.et\"",
        "}"
    ])

    server_files[os.path.join("Backend", "main.py")] = "\n".join([
        "import json",
        "import httpx",
        "from fastapi import FastAPI, Request",
        "from fastapi.middleware.cors import CORSMiddleware",
        "from fastapi.responses import PlainTextResponse",
        "from pydantic import BaseModel",
        "",
        "app = FastAPI()",
        "app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])",
        "",
        "command_queue = []",
        "action_history = []",
        "",
        "try:",
        "    with open('../prefabs.json', 'r') as f:",
        "        PREFABS = json.load(f)",
        "except FileNotFoundError:",
        "    PREFABS = {}",
        "AVAILABLE_UNITS = list(PREFABS.keys())",
        "",
        "SYSTEM_PROMPT = \"\"\"",
        "Eres el Game Master tactico de Arma Reforger. Genera eventos tacticos realistas.",
        "SISTEMA DE COORDENADAS: Si dan 4 digitos (ej: '057 069'), multiplica por 100.",
        "UNIDADES DISPONIBLES: \"\"\" + str(AVAILABLE_UNITS) + \"\"\"",
        "Responde SOLO con JSON exacto:",
        "{\"action\": \"spawn\", \"unit_id\": \"<unidad>\", \"spawn_x\": 6400, \"spawn_y\": 0, \"spawn_z\": 6400, \"intensity\": 1, \"internal_thought\": \"Motivo\"}",
        "IMPORTANTE: 'spawn_y' debe ser SIEMPRE 0.",
        "\"\"\"",
        "",
        "class ManualOrder(BaseModel):",
        "    order: str",
        "",
        "async def ask_ollama(prompt_text):",
        "    payload = {'model': 'llama3.1', 'system': SYSTEM_PROMPT, 'prompt': prompt_text, 'stream': False, 'format': 'json'}",
        "    async with httpx.AsyncClient() as client:",
        "        try:",
        "            response = await client.post('http://localhost:11434/api/generate', json=payload, timeout=60.0)",
        "            data = json.loads(response.json()['response'])",
        "            unit_id = data.get('unit_id')",
        "            if unit_id in PREFABS:",
        "                data['prefab_path'] = PREFABS[unit_id]",
        "                command_queue.append(data)",
        "                msg = \"🧠 IA: \" + data.get('internal_thought', 'Despliegue tactico') + \" -> \" + str(unit_id) + \" a X:\" + str(data.get('spawn_x')) + \" Z:\" + str(data.get('spawn_z'))",
        "                action_history.append(msg)",
        "        except Exception as e:",
        "            action_history.append(\"❌ ERROR IA: \" + str(e))",
        "",
        "@app.post('/manual_command')",
        "async def manual_command(order: ManualOrder):",
        "    action_history.append(\"👤 ORDEN: \" + order.order)",
        "    await ask_ollama(\"ORDEN HUMANA: '\" + order.order + \"'.\")",
        "    return {'status': 'ok'}",
        "",
        "@app.get('/arma_sync', response_class=PlainTextResponse)",
        "async def arma_sync():",
        "    if command_queue:",
        "        cmd = command_queue.pop(0)",
        "        return \"SPAWN|\" + cmd['prefab_path'] + \"|\" + str(cmd.get('spawn_x',6400)) + \"|\" + str(cmd.get('spawn_y',0)) + \"|\" + str(cmd.get('spawn_z',6400))",
        "    return 'NONE'",
        "",
        "@app.post('/arma_log')",
        "async def receive_arma_log(request: Request):",
        "    body = await request.body()",
        "    action_history.append(\"🎮 ARMA: \" + body.decode('utf-8'))",
        "    return PlainTextResponse('OK')",
        "",
        "@app.get('/status')",
        "async def get_status():",
        "    return {'history': action_history[-15:]}",
        "",
        "if __name__ == '__main__':",
        "    import uvicorn",
        "    uvicorn.run(app, host='0.0.0.0', port=8000)"
    ])

    server_files[os.path.join("Web", "index.html")] = "\n".join([
        "<!DOCTYPE html>",
        "<html lang=\"es\">",
        "<head>",
        "    <meta charset=\"UTF-8\">",
        "    <title>Panel de Mando - AI Game Master</title>",
        "    <style>",
        "        body { font-family: 'Segoe UI', sans-serif; background-color: #1e1e24; color: #fff; margin: 0; padding: 20px; }",
        "        .container { max-width: 800px; margin: 0 auto; background: #2b2b36; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }",
        "        h1 { color: #4CAF50; text-align: center; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }",
        "        .log-box { background: #111; padding: 15px; height: 350px; overflow-y: scroll; border-radius: 5px; font-family: monospace; font-size: 14px; margin-bottom: 20px; border: 1px solid #444; }",
        "        .log-entry { margin-bottom: 8px; padding: 8px; border-left: 4px solid #4CAF50; background: #1a1a1a; border-radius: 3px; }",
        "        .input-group { display: flex; gap: 10px; }",
        "        input[type=\"text\"] { flex: 1; padding: 12px; border-radius: 5px; border: none; background: #3c3c4a; color: #fff; font-size: 16px; }",
        "        button { padding: 12px 24px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; transition: background 0.3s; }",
        "        button:hover { background: #45a049; }",
        "    </style>",
        "</head>",
        "<body>",
        "    <div class=\"container\">",
        "        <h1>📡 AI Game Master - Centro de Mando</h1>",
        "        <div class=\"log-box\" id=\"logBox\"><div style=\"color: #888;\">Iniciando conexion...</div></div>",
        "        <div class=\"input-group\">",
        "            <input type=\"text\" id=\"orderInput\" placeholder=\"Ej: Envia infanteria a la coordenada 045 067...\" onkeypress=\"if(event.key === 'Enter') sendOrder()\">",
        "            <button onclick=\"sendOrder()\">TRANSMITIR</button>",
        "        </div>",
        "    </div>",
        "    <script>",
        "        const logBox = document.getElementById('logBox');",
        "        let lastLength = 0;",
        "        async function fetchLogs() {",
        "            try {",
        "                const res = await fetch('http://localhost:8000/status');",
        "                const data = await res.json();",
        "                if (data.history.length !== lastLength) {",
        "                    logBox.innerHTML = '';",
        "                    data.history.forEach(msg => {",
        "                        const div = document.createElement('div');",
        "                        div.className = 'log-entry';",
        "                        if (msg.includes('🎮 ARMA')) div.style.borderLeftColor = '#2196F3';",
        "                        else if (msg.includes('🧠 IA')) div.style.borderLeftColor = '#9C27B0';",
        "                        else if (msg.includes('👤 ORDEN')) div.style.borderLeftColor = '#FFC107';",
        "                        div.textContent = msg;",
        "                        logBox.appendChild(div);",
        "                    });",
        "                    lastLength = data.history.length;",
        "                    logBox.scrollTop = logBox.scrollHeight;",
        "                }",
        "            } catch (e) {}",
        "        }",
        "        async function sendOrder() {",
        "            const input = document.getElementById('orderInput');",
        "            if (!input.value.trim()) return;",
        "            const text = input.value.trim(); input.value = '';",
        "            await fetch('http://localhost:8000/manual_command', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ order: text }) });",
        "        }",
        "        setInterval(fetchLogs, 1000); fetchLogs();",
        "    </script>",
        "</body>",
        "</html>"
    ])

    mod_files = {}
    
    # -------------------------------------------------------------
    # TUS ARCHIVOS EXACTOS (Copiados y pegados)
    # -------------------------------------------------------------
    
    mod_files["addon.gproj"] = "\n".join([
        "GameProject {",
        " ID \"AIGameMasterMod\"",
        " GUID \"5A1B2C3D4E5F6789\"",
        " TITLE \"AI Game Master Autonomous\"",
        " Dependencies {",
        "  \"58D0FB3206B6F859\"",
        " }",
        " Configurations {",
        "  GameProjectConfig PC {",
        "   WorldFile \"{6389AA54E6CCA0AF}worlds/GameMaster/GM_Eden_IA.ent\"",
        "  }",
        "  GameProjectConfig XBOX_ONE {",
        "   PlatformHardware XBOX_ONE",
        "  }",
        "  GameProjectConfig XBOX_SERIES {",
        "   PlatformHardware XBOX_SERIES",
        "  }",
        "  GameProjectConfig PS4 {",
        "   PlatformHardware PS4",
        "  }",
        "  GameProjectConfig PS5 {",
        "   PlatformHardware PS5",
        "  }",
        "  GameProjectConfig HEADLESS {",
        "  }",
        " }",
        "}"
    ])

    mod_files[os.path.join("Missions", "Operacion_Zeus.conf")] = "\n".join([
        "SCR_MissionHeader {",
        " World \"{6389AA54E6CCA0AF}worlds/GameMaster/GM_Eden_IA.ent\"",
        " m_sName \"GM_Eden_IA\"",
        " m_sAuthor \"mtrakm@gmail.com\"",
        " m_sPath \"{0E4F4092E2B1380D}Missions/Operacion_Zeus.conf\"",
        " m_sGameMode \"GameMaster\"",
        " m_iPlayerCount 16",
        "}"
    ])

    mod_files[os.path.join("Scripts", "Game", "AIGameMasterComponent.c")] = "\n".join([
        "[ComponentEditorProps(category: \"AI Game Master\", description: \"Conecta Arma Reforger con el backend de Python AI.\")]",
        "class SCR_AIGameMasterComponentClass: ScriptComponentClass",
        "{",
        "}",
        "",
        "// 1. CLASE DEDICADA PARA ESCUCHAR A PYTHON (Requisito de Reforger)",
        "class AI_RestCallback : RestCallback",
        "{",
        "    SCR_AIGameMasterComponent m_Component;",
        "    ",
        "    void AI_RestCallback(SCR_AIGameMasterComponent comp)",
        "    {",
        "        m_Component = comp;",
        "    }",
        "    ",
        "    override void OnSuccess(string data, int dataSize)",
        "    {",
        "        if (m_Component)",
        "            m_Component.OnSyncResponse(data);",
        "    }",
        "    ",
        "    override void OnError(int errorCode)",
        "    {",
        "        if (m_Component)",
        "            m_Component.OnSyncError(errorCode);",
        "    }",
        "}",
        "",
        "// 2. COMPONENTE PRINCIPAL",
        "class SCR_AIGameMasterComponent : ScriptComponent",
        "{",
        "    [Attribute(\"127.0.0.1\", desc: \"IP del Backend Python\")]",
        "    string m_sBackendIP;",
        "",
        "    [Attribute(\"8000\", desc: \"Puerto del Backend Python\")]",
        "    string m_sBackendPort;",
        "",
        "    protected RestContext m_RestContext;",
        "    protected const float SYNC_INTERVAL = 2.0; // Pide ordenes cada 2 segundos",
        "    protected float m_fTimer = 0;",
        "",
        "    override void OnPostInit(IEntity owner)",
        "    {",
        "        SetEventMask(owner, EntityEvent.INIT | EntityEvent.FRAME);",
        "    }",
        "",
        "    override void EOnInit(IEntity owner)",
        "    {",
        "        // Solo ejecutar en modo juego, no en el editor principal",
        "        if (!GetGame().InPlayMode())",
        "            return;",
        "",
        "        // Configurar la conexion HTTP con FastAPI (Python)",
        "        m_RestContext = GetGame().GetRestApi().GetContext(string.Format(\"http://%1:%2\", m_sBackendIP, m_sBackendPort));",
        "        Print(\"[AI-MASTER] Sistema Iniciado. Esperando ordenes de la IA...\");",
        "    }",
        "",
        "    override void EOnFrame(IEntity owner, float timeSlice)",
        "    {",
        "        if (!m_RestContext) return;",
        "",
        "        m_fTimer += timeSlice;",
        "        if (m_fTimer >= SYNC_INTERVAL)",
        "        {",
        "            m_fTimer = 0;",
        "            PollBackend();",
        "        }",
        "    }",
        "",
        "    void PollBackend()",
        "    {",
        "        // Usamos la clase de Callback para hacer el GET",
        "        AI_RestCallback cb = new AI_RestCallback(this);",
        "        m_RestContext.GET(cb, \"/arma_sync\");",
        "    }",
        "",
        "    void OnSyncResponse(string response)",
        "    {",
        "        // Si Python dice \"NONE\", no hay ordenes nuevas",
        "        if (response == \"NONE\" || response.IsEmpty())",
        "            return;",
        "",
        "        Print(\"[AI-MASTER] Orden descifrada: \" + response);",
        "",
        "        // Separar el string usando el delimitador \"|\"",
        "        array<string> data = new array<string>();",
        "        response.Split(\"|\", data, false);",
        "",
        "        if (data.Count() >= 5 && data[0] == \"SPAWN\")",
        "        {",
        "            ResourceName prefabPath = data[1];",
        "            float posX = data[2].ToFloat();",
        "            float posZ = data[4].ToFloat();",
        "            ",
        "            // ---------------------------------------------------------",
        "            // ¡LA MAGIA DE LA ALTITUD! (Eje Y)",
        "            // Calculamos la altura real del terreno en las coordenadas X y Z",
        "            // ---------------------------------------------------------",
        "            float posY = GetGame().GetWorld().GetSurfaceY(posX, posZ);",
        "",
        "            SpawnUnit(prefabPath, posX, posY, posZ);",
        "        }",
        "    }",
        "",
        "    void OnSyncError(int errorCode)",
        "    {",
        "        // Mantenemos esto comentado para que no sature el log si apagas Python",
        "        // Print(string.Format(\"[AI-MASTER] Error de red. Codigo HTTP: %1\", errorCode), LogLevel.WARNING);",
        "    }",
        "",
        "    void SpawnUnit(ResourceName prefab, float x, float y, float z)",
        "    {",
        "        Resource res = Resource.Load(prefab);",
        "        if (!res || !res.IsValid())",
        "        {",
        "            Print(string.Format(\"[AI-MASTER] Error: No se pudo cargar el prefab %1\", prefab), LogLevel.ERROR);",
        "            return;",
        "        }",
        "",
        "        // Configurar los parametros de aparicion",
        "        EntitySpawnParams spawnParams = new EntitySpawnParams();",
        "        spawnParams.TransformMode = ETransformMode.WORLD;",
        "        ",
        "        // Asignar las coordenadas (X, Y ajustada al suelo, Z)",
        "        vector pos = \"0 0 0\";",
        "        pos[0] = x;",
        "        pos[1] = y;",
        "        pos[2] = z;",
        "        spawnParams.Transform[3] = pos;",
        "",
        "        // Generar la entidad en el mundo",
        "        IEntity entity = GetGame().SpawnEntityPrefab(res, GetGame().GetWorld(), spawnParams);",
        "        ",
        "        if (entity)",
        "        {",
        "            Print(string.Format(\"[AI-MASTER] EXITO TOTAL: Unidad desplegada en X:%1 Y:%2 Z:%3\", x, y, z));",
        "        }",
        "        else",
        "        {",
        "            Print(\"[AI-MASTER] Error al generar la entidad en el mundo.\", LogLevel.ERROR);",
        "        }",
        "    }",
        "}"
    ])

    print("[-] Escribiendo archivos en el disco...")
    
    for rel_path, content in server_files.items():
        with open(os.path.join(server_dir, rel_path), "w", encoding="utf-8") as f:
            f.write(content)

    for rel_path, content in mod_files.items():
        with open(os.path.join(workbench_mod_dir, rel_path), "w", encoding="utf-8") as f:
            f.write(content)

    print_header("✅ INSTALACIÓN COMPLETADA CON ÉXITO")
    print("\n👉 NUEVO FLUJO DE TRABAJO:")
    print("   1. Entra a Arma Reforger Tools (Workbench), carga el mod y dale a 'Pack for Local Testing'.")
    print("   2. Ejecuta 'LANZAR_IA.bat' en tu carpeta ArmaAI_Server.")
    print("   3. Entra a Arma Reforger normal, dale a Multijugador -> Alojar.")
    print("   4. Activa tu mod en la lista de addons y arranca la partida.")
    print("="*75)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_header("❌ OCURRIO UN ERROR DURANTE LA INSTALACION")
        traceback.print_exc()
    finally:
        input("\nPresiona ENTER para cerrar esta ventana...")
