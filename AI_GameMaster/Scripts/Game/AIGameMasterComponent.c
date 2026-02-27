[ComponentEditorProps(category: "AI Game Master", description: "Conecta Arma con Python (Todo-en-Uno)")]
class SCR_AIGameMasterComponentClass: ScriptComponentClass {}

// 1. GESTOR DE CONEXION (Usamos clase dedicada para evitar el error de delegados)
class SCR_AIGameMaster_RestCallback : RestCallback {
    SCR_AIGameMasterComponent m_Component;

    void SCR_AIGameMaster_RestCallback(SCR_AIGameMasterComponent comp) {
        m_Component = comp;
    }

    override void OnSuccess(string data, int dataSize) {
        if (m_Component) m_Component.ProcessServerResponse(data);
    }

    override void OnError(int errorCode) {
        Print("[AI-MASTER] ❌ Error de red: " + errorCode.ToString(), LogLevel.ERROR);
    }
}

// 2. COMPONENTE PRINCIPAL Y CREADOR DE TROPAS
class SCR_AIGameMasterComponent : ScriptComponent {
    [Attribute("127.0.0.1:8000", desc: "URL del servidor de Python")]
    string m_sBackendAddress;

    protected RestContext m_RestContext;
    protected ref SCR_AIGameMaster_RestCallback m_Callback;

    override void OnPostInit(IEntity owner) {
        SetEventMask(owner, EntityEvent.INIT);
    }

    override void EOnInit(IEntity owner) {
        if (!GetGame().InPlayMode()) return;

        m_RestContext = GetGame().GetRestApi().GetContext(m_sBackendAddress);
        m_Callback = new SCR_AIGameMaster_RestCallback(this);

        GetGame().GetCallqueue().CallLater(SyncRadar, 3000, true);
        Print("[AI-MASTER] 🚀 Sistema Iniciado (Version Unificada).");
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

        if (data.Count() >= 5 && data[0] == "SPAWN") {
            ResourceName prefabPath = data[1];
            float posX = data[2].ToFloat();
            float posZ = data[4].ToFloat();

            // Llamamos a nuestra funcion interna
            SpawnUnit(prefabPath, posX, posZ);
        }
    }

    void SpawnUnit(ResourceName prefab, float x, float z) {
        Resource res = Resource.Load(prefab);
        if (!res || !res.IsValid()) {
            Print("[AI-MASTER] ❌ Prefab invalido: " + prefab, LogLevel.ERROR);
            return;
        }

        // Calculo inteligente de altura para no caer bajo el mapa
        float y = GetGame().GetWorld().GetSurfaceY(x, z) + 0.5;

        EntitySpawnParams spawnParams = new EntitySpawnParams();
        spawnParams.TransformMode = ETransformMode.WORLD;

        vector pos = "0 0 0"; pos[0] = x; pos[1] = y; pos[2] = z;
        spawnParams.Transform[3] = pos;

        IEntity spawnedEntity = GetGame().SpawnEntityPrefab(res, null, spawnParams);
        Print("[AI-MASTER] ✅ Unidad desplegada en X:" + x.ToString() + " Z:" + z.ToString());
    }
}