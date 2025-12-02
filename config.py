"""
Configuración del sistema distribuido
"""
import os

# Configuración del coordinador
COORDINATOR_HOST = "localhost"
COORDINATOR_PORT = 8888

# Configuración de bloques
BLOCK_SIZE = 1024 * 1024  # 1 MB en bytes
MIN_SHARED_SPACE = 50 * 1024 * 1024  # 50 MB mínimo
MAX_SHARED_SPACE = 100 * 1024 * 1024  # 100 MB máximo

# Configuración de replicación
REPLICATION_FACTOR = 2  # Cada bloque tiene 2 copias (original + réplica)

# Directorios
SHARED_DIRECTORY = "espacioCompartido"
COORDINATOR_DATA_DIR = "coordinator_data"

# Directorio compartido del usuario
import os
USER_SHARED_DIRECTORY = os.path.join(f"C:\\Users\\{os.getenv('USERNAME')}", "espacioCompartido")

# Timeout para conexiones (segundos)
CONNECTION_TIMEOUT = 5
HEARTBEAT_INTERVAL = 10  # Intervalo de heartbeat en segundos
NODE_TIMEOUT = 30  # Tiempo sin heartbeat antes de considerar nodo desconectado

# Configuración de la interfaz web
WEB_UPDATE_INTERVAL = 5000  # ms (actualización automática en la web)

