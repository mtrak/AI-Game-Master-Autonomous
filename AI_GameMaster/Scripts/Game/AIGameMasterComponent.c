[ComponentEditorProps(category: "AI Game Master", description: "Conecta Arma Reforger con el backend de Python AI.")]
class SCR_AIGameMasterComponentClass: ScriptComponentClass {}

class AI_RestCallback : RestCallback {
    SCR_AIGameMasterComponent m_Component;
    void AI_RestCallback(SCR_AIGameMasterComponent comp) { m_Component = comp; }
    override void OnSuccess(string data, int dataSize) { 
        if (m_Component) {
            m_Component.OnSyncResponse(data); 
        }
    }
    override void OnError(int errorCode) { }
}

class SCR_AIGameMasterComponent : ScriptComponent {
    [Attribute("127.0.0.1:8000", desc: "IP y Puerto del Backend Python")] 
    string m_sBackendAddress;

    protected RestContext m_RestContext;
    protected ref AI_RestCallback m_Callback; 
    protected ref map<int, IEntity> m_Squads = new map<int, IEntity>();

    override void OnPostInit(IEntity owner) {
        SetEventMask(owner, EntityEvent.INIT);
    }

    override void EOnInit(IEntity owner) {
        if (!GetGame().InPlayMode()) return;
        m_RestContext = GetGame().GetRestApi().GetContext(m_sBackendAddress);
        m_Callback = new AI_RestCallback(this);

        if (m_RestContext) {
            Print("[AI-MASTER] Modulo COMANDANTE Iniciado. Escuchando base de datos...", LogLevel.WARNING);
            GetGame().GetCallqueue().CallLater(PollBackend, 2000, true);
        }
    }

    void PollBackend() {
        if (!m_RestContext || !m_Callback) return;

        float pX = 4800; float pZ = 6300;
        PlayerManager playerMgr = GetGame().GetPlayerManager();
        if (playerMgr) {
            array<int> players = new array<int>();
            playerMgr.GetPlayers(players);
            if (players.Count() > 0) {
                IEntity playerEnt = playerMgr.GetPlayerControlledEntity(players[0]);
                if (playerEnt) {
                    vector pos = playerEnt.GetOrigin();
                    pX = pos[0]; pZ = pos[2];
                }
            }
        }
        
        if (pX == 4800) {
            CameraManager camMgr = GetGame().GetCameraManager();
            if (camMgr) {
                CameraBase currentCam = camMgr.CurrentCamera();
                if (currentCam) {
                    vector mat[4]; currentCam.GetTransform(mat);
                    pX = mat[3][0]; pZ = mat[3][2];
                }
            }
        }

        int intX = Math.Round(pX);
        int intZ = Math.Round(pZ);
        string request = string.Format("/arma_sync?px=%1&pz=%2&m=GameMaster", intX, intZ);
        m_RestContext.GET(m_Callback, request);
    }

    void OnSyncResponse(string response) {
        if (response == "NONE" || response == "OK" || response.IsEmpty()) return;

        array<string> data = new array<string>();
        response.Split("|", data, false);

        if (data.Count() >= 6 && data[0] == "SPAWN") {
            int squadId = data[1].ToInt();
            ResourceName prefabPath = data[2];
            float posX = data[3].ToFloat();
            float posZ = data[5].ToFloat();
            float posY = GetGame().GetWorld().GetSurfaceY(posX, posZ) + 0.5;
            SpawnUnit(squadId, prefabPath, posX, posY, posZ);
        }
        else if (data.Count() >= 4 && data[0] == "MOVE") {
            int squadId = data[1].ToInt();
            float moveX = data[2].ToFloat();
            float moveZ = data[3].ToFloat();
            MoveSquad(squadId, moveX, moveZ);
        }
    }

    void SpawnUnit(int id, ResourceName prefab, float x, float y, float z) {
        Resource res = Resource.Load(prefab);
        if (!res || !res.IsValid()) return;

        EntitySpawnParams spawnParams = new EntitySpawnParams();
        spawnParams.TransformMode = ETransformMode.WORLD;
        vector pos = "0 0 0"; pos[0] = x; pos[1] = y; pos[2] = z;
        spawnParams.Transform[3] = pos;

        IEntity entity = GetGame().SpawnEntityPrefab(res, GetGame().GetWorld(), spawnParams);
        if (entity) {
            m_Squads.Insert(id, entity);
            Print(string.Format("[AI-MASTER] ✅ Escuadra %1 desplegada", id), LogLevel.NORMAL);
        }
    }

    void MoveSquad(int id, float destX, float destZ) {
        IEntity squadEntity = m_Squads.Get(id);
        if (!squadEntity) return;

        SCR_AIGroup group = SCR_AIGroup.Cast(squadEntity);
        if (!group) {
            AIControlComponent aiComp = AIControlComponent.Cast(squadEntity.FindComponent(AIControlComponent));
            if (aiComp) {
                AIAgent agent = aiComp.GetAIAgent();
                if (agent) {
                    group = SCR_AIGroup.Cast(agent.GetParentGroup());
                }
            }
        }

        if (group) {
            array<AIWaypoint> existingWps = new array<AIWaypoint>();
            group.GetWaypoints(existingWps);
            foreach (AIWaypoint oldWp : existingWps) {
                group.RemoveWaypoint(oldWp);
            }

            Resource wpRes = Resource.Load("{93291E72AC23930F}Prefabs/AI/Waypoints/AIWaypoint_Move.et");
            EntitySpawnParams wpParams = new EntitySpawnParams();
            wpParams.TransformMode = ETransformMode.WORLD;
            vector pos = "0 0 0"; 
            pos[0] = destX; 
            pos[1] = GetGame().GetWorld().GetSurfaceY(destX, destZ); 
            pos[2] = destZ;
            wpParams.Transform[3] = pos;

            AIWaypoint wp = AIWaypoint.Cast(GetGame().SpawnEntityPrefab(wpRes, GetGame().GetWorld(), wpParams));
            if (wp) {
                wp.SetCompletionRadius(10.0);
                group.AddWaypoint(wp);
                Print(string.Format("[AI-MASTER] 🏃‍♂️ Escuadra %1 moviendose", id), LogLevel.NORMAL);
            }
        }
    }
}