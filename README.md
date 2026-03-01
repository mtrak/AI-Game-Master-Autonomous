🤖 AI Game Master - Autonomous (Arma Reforger)
AI Game Master es un sistema avanzado de Inteligencia Artificial y control backend para Arma Reforger. Permite a los jugadores en el rol de Game Master (Zeus) generar unidades, vehículos y escuadrones enteros utilizando lenguaje natural a través de un panel de control web externo, sin necesidad de navegar por los menús del juego.

El sistema comprende contextos, deduce facciones y autocompleta información gracias a un motor de Procesamiento de Lenguaje Natural (NLP) integrado y conectado a Ollama.

✨ Características Principales
🗣️ Procesamiento de Lenguaje Natural (NLP): Pide tropas hablando de forma natural. (Ej: "Manda un pelotón americano médico a Morton", "Despliega un blindado en el aeropuerto").

🌍 Mapas Integrados: Reconoce más de 130 localizaciones de Everon (Pueblos, bases, cabos, valles, etc.).

🪖 Catálogo Masivo: Integración directa con los GUIDs reales del juego. Incluye unidades US, USSR, FIA, Spetsnaz, Boinas Verdes, vehículos terrestres, civiles y helicópteros.

💻 Panel de Control Web: Interfaz gráfica táctica (Dashboard) que muestra el estado de conexión de Arma en tiempo real, un historial de logs y un "radar" de tropas desplegadas.

🚀 Instalador Automatizado (One-Click): Un script inteligente que descarga el código, instala dependencias de Python, instala Ollama (si no lo tienes) y te crea un acceso directo.

🛡️ Parche Anti-Zeus: Sistema de físicas en C++ que impide que el motor Enfusion genere las tropas en la cámara del jugador, teletransportándolas exactamente a las coordenadas solicitadas.

🛠️ Requisitos Previos
Tener Arma Reforger instalado (o Arma Reforger Tools si vas a compilar el mod).

Tener Python 3.10 o superior instalado en tu sistema (Asegúrate de marcar la casilla "Add Python to PATH" al instalarlo).

Conexión a Internet (para descargar Ollama y el modelo de IA en la instalación).

📦 Instalación Rápida (Recomendada)
Hemos diseñado un instalador automático para que no tengas que preocuparte de clonar repositorios ni configurar entornos.

Descarga el archivo Instalar_IA.py de este repositorio.

Colócalo en una carpeta vacía donde quieras guardar tu servidor (Ej: Documentos/AI_GameMaster).

Haz doble clic en Instalar_IA.py (o ejecútalo desde la consola con python Instalar_IA.py).

Sigue las instrucciones en pantalla:

El script descargará automáticamente todo el código fuente.

Instalará librerías como FastAPI y Uvicorn.

Descargará el motor de IA local (Ollama) si no lo tienes.

Generará un archivo llamado Arrancar_IA.bat.

🎮 Cómo jugar (Funcionamiento)
Haz doble clic en el archivo Arrancar_IA.bat.

Se abrirá una consola negra (el Backend) y automáticamente se abrirá tu navegador web en la dirección http://127.0.0.1:8000.

En la web verás un cartel rojo arriba a la derecha que dice 🔴 ARMA: ESPERANDO.

Abre Arma Reforger y entra al modo Game Master (o carga tu mundo en el Workbench).

¡La magia ocurre! En cuanto el juego cargue, la web detectará el latido de Arma y cambiará a 🟢 ARMA: EN LÍNEA.

Usa el chat web para mandar tropas. Ejemplos de uso:

"Despliega un BTR en MontfortCastle"

"Necesito francotiradores rebeldes en Morton"

"Manda spetsnaz a Lamentin"

"Envía un camión al aeropuerto"

⚙️ Arquitectura del Sistema
El proyecto sigue una arquitectura altamente modular (MVC) para facilitar su expansión:

/Cerebro_IA/: Contiene el motor lógico.

gestor_catalogos.py: Devora y asimila los archivos JSON con los GUIDs del juego.

gestor_mapas.py: Cruza las peticiones con las coordenadas geográficas reales.

motor_deduccion.py: El "cerebro" semántico. Usa un sistema de puntuación de etiquetas para traducir palabras comunes ("pelotón", "americano") a clases exactas del juego (Group US RifleSquad).

/Catalogos_IA/: Diccionarios JSON con las referencias a los prefabs del motor Enfusion.

main.py: El controlador principal FastAPI que maneja las rutas web y las peticiones /sync de Arma Reforger.

AIGameMasterComponent.c: El código de Arma Reforger (Enfusion Engine) que hace polling constante al backend en busca de órdenes.

🔄 Últimos Cambios y Actualizaciones
V 2.0 - Arquitectura Modular: Se ha reescrito el backend para separar la lógica de mapas, catálogos y NLP en la carpeta Cerebro_IA.

V 1.9 - NLP Semántico Avanzado: Se ha sustituido el "buscador por palabras" rígido por un sistema de deducción semántica. La IA ahora autocompleta información (ej: si pides un "pelotón" y no dices facción, asume "Soviéticos" por defecto).

V 1.8 - Parche Anti-Zeus (Físicas): Corregido un bug crítico del motor Enfusion donde las unidades aparecían en las coordenadas locales de la cámara del Zeus. Se ha añadido un bloqueo de matriz de identidad (Transform[3]) y un parche post-spawn (SetTransform) en C++ para anclar a las unidades al suelo del mapa.

V 1.7 - Semáforo y Logs: Añadido sistema de logs en Logs/sistema_ia.log y detector de Heartbeat en tiempo real con el cliente web.

V 1.6 - Fix de Compatibilidad Enfusion 1.6+: Actualizado RestCallback en el archivo C++ debido a deprecaciones en la API de Bohemia Interactive. Eliminados argumentos redundantes (dataSize) para evitar crasheos de compilación.

⚠️ Errores Conocidos (Known Issues)
Letras amarillas al compilar en Arma: Al darle a Reload Scripts en el Workbench, Arma mostrará avisos amarillos (Warnings) indicando RestCallback: Function was not set for event: 'OnSuccess'. Esto es un comportamiento normal y seguro. Bohemia ha marcado ciertos eventos antiguos como obsoletos, pero nuestro C++ gestiona los callbacks limpiamente. Ignora la alerta.

Pathfinding de la IA (Enfusion): Si haces spawn de un vehículo pesado dentro de un bosque muy denso, Arma Reforger podría mostrar errores de Pathfinding en la consola del juego. Intenta desplegar vehículos en áreas despejadas, carreteras o ciudades grandes.

WebSockets Warnings (Solucionado): En versiones antiguas el servidor escupía advertencias por falta de WebSockets. Esto se ha solucionado forzando ws="none" en el arranque de Uvicorn en main.py.

🤝 Contribuir y Personalizar
Si quieres que la IA aprenda palabras nuevas o añadir facciones personalizadas de la Workshop de Arma:

Añade tus nuevos prefabs en un archivo .json dentro de la carpeta Catalogos_IA.

Abre Cerebro_IA/motor_deduccion.py y añade tus sinónimos a la lista self.conceptos (Ej: "tanque pesado": "M1A1 Abrams").

Reinicia el servidor. ¡La IA absorberá el conocimiento instantáneamente!
