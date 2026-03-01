[ComponentEditorProps(category: "AI Game Master", description: "Receptor IA - Parche Anti-Zeus")]
class SCR_AIGameMasterComponentClass: ScriptComponentClass {}

// 1. VOLVEMOS AL SISTEMA CLÁSICO QUE FUNCIONABA
class SCR_AIGameMaster_RestCallback : RestCallback 
{
    SCR_AIGameMasterComponent m_Component;
    void SCR_AIGameMaster_RestCallback(SCR_AIGameMasterComponent comp) { m_Component = comp; }
    
    // Dejamos las advertencias amarillas, no rompen el juego y son seguras.
    override void OnSuccess(string data, int dataSize) { 
        if (m_Component && dataSize > 0) m_Component.ProcessServerResponse(data); 
    }
    override void OnError(int errorCode) {} 
    override void OnTimeout() {}
}

class SCR_AIGameMasterComponent : ScriptComponent 
{
    [Attribute("127.0.0.1:8000", desc: "IP del Backend Python")]
    string m_sBackendAddress;

    protected RestContext m_RestContext;
    protected ref SCR_AIGameMaster_RestCallback m_Callback;

    override void OnPostInit(IEntity owner) { SetEventMask(owner, EntityEvent.INIT); }

    override void EOnInit(IEntity owner) 
    {
        if (!GetGame().InPlayMode() || !Replication.IsServer()) return;

        string finalIP = m_sBackendAddress;
        string configPath = "$profile:AIGameMaster_IP.txt";
        
        if (FileIO.FileExists(configPath)) {
            FileHandle file = FileIO.OpenFile(configPath, FileMode.READ);
            if (file) {
                file.ReadLine(finalIP);
                file = null;
            }
        }

        m_RestContext = GetGame().GetRestApi().GetContext(finalIP);
        m_Callback = new SCR_AIGameMaster_RestCallback(this);

        GetGame().GetCallqueue().CallLater(SyncRadar, 3000, true);
    }

    void SyncRadar() 
    {
        if (!m_RestContext) return;
        
        string url = "/sync";
        IEntity player = SCR_PlayerController.GetLocalMainEntity();
        if (player)
        {
            vector pos = player.GetOrigin();
            url = string.Format("/sync?px=%1&pz=%2", pos[0], pos[2]);
        }
        
        m_RestContext.GET(m_Callback, url);
    }

    void ProcessServerResponse(string data) 
    {
        if (!data || data == "" || data == "null" || data.Contains("status")) return;

        array<string> tokens = new array<string>();
        data.Split("|", tokens, false);

        if (tokens.Count() >= 3) 
        {
            string prefab = tokens.Get(0);
            float x = tokens.Get(1).ToFloat();
            float z = tokens.Get(2).ToFloat();

            vector posFinal = "0 0 0";
            posFinal[0] = x;
            posFinal[2] = z;
            
            float alturaSuelo = GetGame().GetWorld().GetSurfaceY(x, z);
            if (alturaSuelo < 0) alturaSuelo = 0; 
            posFinal[1] = alturaSuelo;

            Print(string.Format("[AI-MASTER] 📥 Orden asimilada. Spawneando en X:%1 Z:%2", x, z));
            SpawnUnit(prefab, posFinal);
        }
    }

    void SpawnUnit(string prefabPath, vector position) 
    {
        Resource res = Resource.Load(prefabPath);
        if (!res || !res.IsValid()) return;

        EntitySpawnParams params = new EntitySpawnParams();
        params.TransformMode = ETransformMode.WORLD; 
        
        // ===============================================
        // 🔧 BLOQUEO DE ROTACIÓN
        // Impide que el motor use la rotación de tu cámara
        // ===============================================
        params.Transform[0] = "1 0 0";
        params.Transform[1] = "0 1 0";
        params.Transform[2] = "0 0 1";
        params.Transform[3] = position;

        IEntity unit = GetGame().SpawnEntityPrefab(res, GetGame().GetWorld(), params);
        
        if (unit) {
            // ===============================================
            // 🚀 PARCHE DE TELETRANSPORTE
            // Fuerza las físicas para anclarlo a la ciudad
            // ===============================================
            vector mat[4];
            unit.GetTransform(mat);  
            mat[3] = position;       
            unit.SetTransform(mat);  
            unit.Update();           
            
            Print(string.Format("[AI-MASTER] ✅ Tropas forzadas a teletransportarse a X:%1 Z:%2", position[0], position[2]));
        }
    }
}