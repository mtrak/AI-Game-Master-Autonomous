[ComponentEditorProps(category: "AI Game Master", description: "Conecta Arma con Python (Waypoints Agresivos)")]
class SCR_AIGameMasterComponentClass: ScriptComponentClass {}

class SCR_AIGameMaster_RestCallback : RestCallback {
    SCR_AIGameMasterComponent m_Component;
    void SCR_AIGameMaster_RestCallback(SCR_AIGameMasterComponent comp) { m_Component = comp; }
    override void OnSuccess(string data, int dataSize) { if (m_Component) m_Component.ProcessServerResponse(data); }
    override void OnError(int errorCode) {}
}

class SCR_AIGameMasterComponent : ScriptComponent {
    [Attribute("127.0.0.1:8000", desc: "URL del servidor de Python")]
    string m_sBackendAddress;

    protected RestContext m_RestContext;
    protected ref SCR_AIGameMaster_RestCallback m_Callback;
    
    // Mapa de Tropas Activas
    protected ref map<int, IEntity> m_mSpawnedTroops = new map<int, IEntity>();
    protected int m_iNextTroopId = 1;
    protected ref map<string, vector> m_mPendingTeleports = new map<string, vector>();

    override void OnPostInit(IEntity owner) { SetEventMask(owner, EntityEvent.INIT); }

    override void EOnInit(IEntity owner) {
        if (!GetGame().InPlayMode()) return;
        m_RestContext = GetGame().GetRestApi().GetContext(m_sBackendAddress);
        m_Callback = new SCR_AIGameMaster_RestCallback(this);

        GetGame().GetCallqueue().CallLater(SyncRadar, 3000, true);
        GetGame().GetCallqueue().CallLater(SavePersistence, 10000, true);
    }

    void SavePersistence() {
        if (!m_RestContext) return;
        string json = "{\"players\":[],\"troops\":[";
        
        bool firstT = true;
        array<int> keysToRemove = new array<int>();
        
        for (int i = 0; i < m_mSpawnedTroops.Count(); i++) {
            int id = m_mSpawnedTroops.GetKey(i);
            IEntity troop = m_mSpawnedTroops.GetElement(i);
            
            if (!troop) { keysToRemove.Insert(id); continue; }
            
            if (!firstT) json += ",";
            vector pos = troop.GetOrigin();
            EntityPrefabData pData = troop.GetPrefabData();
            string pName = "";
            if (pData) pName = pData.GetPrefabName();
            
            json += string.Format("{\"id\":%1,\"prefab\":\"%2\",\"px\":%3,\"py\":%4,\"pz\":%5}", id, pName, pos[0], pos[1], pos[2]);
            firstT = false;
        }
        json += "]}";
        
        foreach(int deadId : keysToRemove) m_mSpawnedTroops.Remove(deadId);
        m_RestContext.POST(m_Callback, "/save_state", json);
    }

    void SyncRadar() {
        if (!m_RestContext) return;
        vector pos = "4800 0 6300";
        if (GetGame().GetCameraManager() && GetGame().GetCameraManager().CurrentCamera())
            pos = GetGame().GetCameraManager().CurrentCamera().GetOrigin();

        string request = string.Format("/arma_sync?px=%1&pz=%2&m=GameMaster", pos[0], pos[2]);
        m_RestContext.GET(m_Callback, request);
    }

    void ProcessServerResponse(string response) {
        if (response == "NONE" || response == "OK" || response.IsEmpty()) return;

        array<string> data = new array<string>();
        response.Split("|", data, false);
        
        if (data.Count() >= 5) {
            if (data[0] == "SPAWN") {
                SpawnUnit(data[1], data[2].ToFloat(), data[4].ToFloat());
            } else if (data[0] == "SPAWN_MANNED") {
                SpawnMannedVehicle(data[1], data[2].ToFloat(), data[4].ToFloat());
            } else if (data[0] == "MOVE") {
                OrderMoveTo(data[1].ToInt(), data[2].ToFloat(), data[4].ToFloat());
            }
        }
    }

    void RegisterTroop(IEntity entity, int forceId = -1) {
        int newId = forceId;
        if (newId == -1) {
            newId = m_iNextTroopId;
            m_iNextTroopId++;
        } else {
            if (newId >= m_iNextTroopId) m_iNextTroopId = newId + 1;
        }
        m_mSpawnedTroops.Insert(newId, entity);
    }

    void SpawnUnit(ResourceName prefab, float x, float z, int forceId = -1) {
        Resource res = Resource.Load(prefab);
        if (!res || !res.IsValid()) return;
        float y = GetGame().GetWorld().GetSurfaceY(x, z) + 0.5;
        EntitySpawnParams params = new EntitySpawnParams();
        params.TransformMode = ETransformMode.WORLD;
        vector pos = "0 0 0"; pos[0] = x; pos[1] = y; pos[2] = z; params.Transform[3] = pos;
        
        IEntity spawnedEntity = GetGame().SpawnEntityPrefab(res, null, params);
        if (spawnedEntity) RegisterTroop(spawnedEntity, forceId);
    }

    void SpawnMannedVehicle(ResourceName vehPrefab, float x, float z, int forceId = -1) {
        Resource res = Resource.Load(vehPrefab);
        if (!res || !res.IsValid()) return;
        
        float y = GetGame().GetWorld().GetSurfaceY(x, z) + 3.0;
        EntitySpawnParams params = new EntitySpawnParams();
        params.TransformMode = ETransformMode.WORLD;
        vector pos = "0 0 0"; pos[0] = x; pos[1] = y; pos[2] = z; params.Transform[3] = pos;
        
        IEntity vehicle = GetGame().SpawnEntityPrefab(res, null, params);
        if (!vehicle) return;
        RegisterTroop(vehicle, forceId); 
        
        string path = vehPrefab;
        path.ToLower();
        ResourceName crewRes = "{DCB41B3746FDD1BE}Prefabs/Characters/Factions/OPFOR/USSR_Army/Character_USSR_Rifleman.et"; 
        
        if (path.Contains("us_") || path.Contains("m998") || path.Contains("m151") || path.Contains("m923") || path.Contains("lav25") || path.Contains("uh1h")) {
            crewRes = "{26A9756790131354}Prefabs/Characters/Factions/BLUFOR/US_Army/Character_US_Rifleman.et";
        } else if (path.Contains("fia")) {
            crewRes = "{84B40583F4D1B7A3}Prefabs/Characters/Factions/INDFOR/FIA/Character_FIA_Rifleman.et";
        } else if (path.Contains("civ")) {
            crewRes = "{99F600AD4C6BA6A4}Prefabs/Characters/Factions/CIV/Character_CIV_base.et";
        }

        EntitySpawnParams crewParams = new EntitySpawnParams();
        crewParams.TransformMode = ETransformMode.WORLD;
        vector crewPos = "0 0 0"; crewPos[0] = x; crewPos[1] = y + 100.0; crewPos[2] = z; 
        crewParams.Transform[3] = crewPos;

        SCR_BaseCompartmentManagerComponent compMgr = SCR_BaseCompartmentManagerComponent.Cast(vehicle.FindComponent(SCR_BaseCompartmentManagerComponent));
        if (compMgr) {
            array<BaseCompartmentSlot> compartments = new array<BaseCompartmentSlot>();
            compMgr.GetCompartments(compartments);
            
            for (int i = 0; i < compartments.Count(); i++) {
                IEntity crew = GetGame().SpawnEntityPrefab(Resource.Load(crewRes), null, crewParams);
                if (crew) {
                    SCR_CompartmentAccessComponent access = SCR_CompartmentAccessComponent.Cast(crew.FindComponent(SCR_CompartmentAccessComponent));
                    if (access) {
                        int seatType = 2; 
                        if (i == 0) seatType = 0;      
                        else if (i == 1) seatType = 1; 
                        
                        access.MoveInVehicle(vehicle, seatType);
                    }
                    RegisterTroop(crew); 
                }
            }
        }
    }

    // ==========================================
    // 🧠 SISTEMA AGRESIVO DE WAYPOINTS
    // ==========================================
    SCR_AIGroup GetEntityGroup(IEntity entity) {
        SCR_AIGroup group = SCR_AIGroup.Cast(entity);
        if (group) return group;

        SCR_BaseCompartmentManagerComponent compMgr = SCR_BaseCompartmentManagerComponent.Cast(entity.FindComponent(SCR_BaseCompartmentManagerComponent));
        if (compMgr) {
            array<IEntity> occupants = new array<IEntity>();
            compMgr.GetOccupants(occupants);
            foreach (IEntity occ : occupants) {
                AIControlComponent aiComp = AIControlComponent.Cast(occ.FindComponent(AIControlComponent));
                if (aiComp && aiComp.GetAIAgent()) return SCR_AIGroup.Cast(aiComp.GetAIAgent().GetParentGroup());
            }
        }
        return null;
    }

    void OrderMoveTo(int id, float x, float z) {
        Print("[AI-MASTER] ⚡ Intentando mover ID " + id.ToString(), LogLevel.WARNING);
        
        IEntity entity;
        if (!m_mSpawnedTroops.Find(id, entity)) {
            Print("[AI-MASTER] ❌ Error: El ID " + id.ToString() + " no esta en la memoria.", LogLevel.ERROR);
            return;
        }

        if (!entity) {
            m_mSpawnedTroops.Remove(id);
            return;
        }

        SCR_AIGroup group = GetEntityGroup(entity);
        if (!group) {
            Print("[AI-MASTER] ❌ Error: El ID " + id.ToString() + " no tiene Cerebro de Grupo.", LogLevel.ERROR);
            return;
        }

        array<AIWaypoint> wps = new array<AIWaypoint>();
        group.GetWaypoints(wps);
        foreach (AIWaypoint w : wps) group.RemoveWaypoint(w);

        Resource wpRes = Resource.Load("{93291E72AC23930F}Prefabs/AI/Waypoints/AIWaypoint_Move.et");
        if (!wpRes || !wpRes.IsValid()) return;

        EntitySpawnParams wpParams = new EntitySpawnParams();
        wpParams.TransformMode = ETransformMode.WORLD;
        vector pos = "0 0 0"; 
        pos[0] = x; 
        pos[1] = GetGame().GetWorld().GetSurfaceY(x, z) + 1.0; 
        pos[2] = z;
        wpParams.Transform[3] = pos;

        IEntity wpEnt = GetGame().SpawnEntityPrefab(wpRes, null, wpParams);
        AIWaypoint wp = AIWaypoint.Cast(wpEnt);
        
        if (wp) {
            wp.SetCompletionRadius(10.0);
            group.AddWaypoint(wp);
            Print("[AI-MASTER] ✅ ORDEN RECIBIDA: Moviendo ID " + id.ToString() + " a X:" + x.ToString() + " Z:" + z.ToString(), LogLevel.NORMAL);
        }
    }
}