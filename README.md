# Sistema de Archivos Distribuido Tolerante a Fallas (SADTF)

## Descripción

Sistema distribuido tolerante a fallas que permite almacenar y administrar archivos grandes aprovechando la capacidad en disco duro de múltiples computadoras (n > 1). El sistema divide archivos en bloques de 1 MB, los distribuye entre nodos y mantiene réplicas para garantizar la disponibilidad incluso ante fallos de nodos.

## Características Principales

- **Distribución de Archivos**: Los archivos se dividen en bloques de 1 MB y se distribuyen entre múltiples nodos
- **Replicación**: Cada bloque tiene al menos 2 copias (original + réplica) en nodos diferentes
- **Tolerancia a Fallos**: Si un nodo falla, los archivos siguen siendo accesibles desde sus réplicas
- **Tabla de Bloques**: Sistema similar a paginación para gestionar el espacio disponible
- **Interfaz Gráfica**: GUI moderna y completa para gestionar archivos y monitorear el sistema
- **Monitoreo en Tiempo Real**: Visualización de nodos activos, tabla de bloques y consola de eventos

## Arquitectura del Sistema

El sistema está compuesto por tres componentes principales:

1. **Coordinador**: Servidor central que gestiona la tabla de bloques, coordina los nodos y maneja las solicitudes de los clientes
2. **Nodos**: Computadoras que almacenan bloques de archivos en su directorio `espacioCompartido` (50-100 MB cada uno)
3. **Cliente GUI**: Interfaz gráfica que permite a los usuarios interactuar con el sistema

## Estructura del Proyecto

```
SADTF_3/
├── coordinator/          # Módulo del coordinador
│   ├── __init__.py
│   ├── coordinator.py    # Servidor coordinador principal
│   └── block_table.py    # Gestión de la tabla de bloques
├── node/                 # Módulo de nodos
│   ├── __init__.py
│   ├── node.py          # Nodo del sistema distribuido
│   └── storage.py       # Gestión de almacenamiento de bloques
├── client/               # Módulo del cliente
│   ├── __init__.py
│   └── gui.py           # Interfaz gráfica del cliente
├── common/               # Módulos comunes
│   ├── __init__.py
│   ├── protocol.py      # Protocolo de comunicación
│   └── utils.py         # Utilidades comunes
├── config.py            # Configuración del sistema
├── start_coordinator.py # Script para iniciar el coordinador
├── start_node.py        # Script para iniciar un nodo
├── start_client.py      # Script para iniciar el cliente GUI
├── requirements.txt     # Dependencias (ninguna externa requerida)
└── README.md           # Este archivo
```

## Requisitos

- Python 3.7 o superior
- tkinter (interfaz gráfica)
  - Windows/macOS: Viene incluido con Python
  - Linux: `sudo apt-get install python3-tk`

## Instalación

1. Clonar o descargar el proyecto
2. No se requieren dependencias externas (solo librerías estándar de Python)
3. Si tkinter no está disponible en Linux, instalarlo:
   ```bash
   sudo apt-get install python3-tk
   ```

## Configuración

El archivo `config.py` contiene todas las configuraciones del sistema:

- `COORDINATOR_HOST`: Dirección del coordinador (default: "localhost")
- `COORDINATOR_PORT`: Puerto del coordinador (default: 8888)
- `BLOCK_SIZE`: Tamaño de bloque en bytes (default: 1 MB)
- `MIN_SHARED_SPACE`: Espacio mínimo por nodo (default: 50 MB)
- `MAX_SHARED_SPACE`: Espacio máximo por nodo (default: 100 MB)
- `HEARTBEAT_INTERVAL`: Intervalo de heartbeat en segundos (default: 10)
- `NODE_TIMEOUT`: Tiempo sin heartbeat antes de considerar nodo desconectado (default: 30 segundos)

## Cómo Ejecutar el Sistema

### Paso 1: Iniciar el Coordinador

En una terminal, ejecutar:

```bash
python start_coordinator.py
```

El coordinador se iniciará en el puerto 8888 (por defecto). Verás un mensaje confirmando que está escuchando conexiones.

**Importante**: El coordinador debe estar ejecutándose antes de iniciar los nodos.

### Paso 2: Iniciar los Nodos

En terminales separadas (una por cada nodo), ejecutar:

```bash
# Nodo 1 con 70 MB de espacio
python start_node.py --node-id node1 --space 70MB

# Nodo 2 con 50 MB de espacio
python start_node.py --node-id node2 --space 50MB

# Nodo 3 con 100 MB de espacio
python start_node.py --node-id node3 --space 100MB
```

**Notas**:
- Cada nodo debe tener un ID único
- El espacio debe estar entre 50 y 100 MB
- Puedes iniciar tantos nodos como desees (mínimo 2 para replicación)
- Si no especificas `--node-id`, se generará uno automáticamente
- Si no especificas `--space`, se usará el mínimo (50 MB)

### Paso 3: Iniciar el Cliente GUI

En otra terminal, ejecutar:

```bash
python start_client.py
```

Se abrirá la interfaz gráfica del cliente.

## Uso de la Interfaz Gráfica

La interfaz gráfica está dividida en varias secciones:

### Panel Izquierdo: Nodos Activos
- Muestra todos los nodos registrados en el sistema
- Indica el espacio disponible de cada nodo
- Muestra el estado (Activo/Inactivo) de cada nodo
- Se actualiza automáticamente cada segundo

### Panel Central: Archivos
- Lista todos los archivos almacenados en el sistema
- Muestra nombre, tamaño, número de bloques y fecha de subida
- Botones de operaciones:
  - **Subir Archivo**: Selecciona y sube un archivo al sistema
  - **Descargar**: Descarga el archivo seleccionado
  - **Eliminar**: Elimina el archivo seleccionado
  - **Ver Atributos**: Muestra información detallada del archivo y dónde están sus bloques
  - **Actualizar**: Refresca la lista de archivos

### Panel Derecho: Tabla de Bloques
- Muestra la tabla de bloques del sistema
- Indica qué bloques están libres o en uso
- Muestra en qué nodos están almacenados los bloques
- Muestra información de réplicas
- Botón **Actualizar Tabla** para refrescar la información

### Consola (Inferior)
- Muestra eventos y mensajes del sistema en tiempo real
- Incluye timestamps para cada mensaje
- Útil para debugging y monitoreo

### Barra de Estado
- Indica el estado de conexión con el coordinador
- Verde: Conectado
- Rojo: Desconectado

## Operaciones del Sistema

### Subir un Archivo

1. Hacer clic en **Subir Archivo**
2. Seleccionar el archivo deseado
3. El sistema:
   - Divide el archivo en bloques de 1 MB
   - Asigna bloques libres en la tabla de bloques
   - Distribuye los bloques entre los nodos disponibles
   - Crea réplicas en nodos diferentes
   - Actualiza la tabla de bloques

### Descargar un Archivo

1. Seleccionar un archivo de la lista
2. Hacer clic en **Descargar**
3. Seleccionar la ubicación donde guardar el archivo
4. El sistema:
   - Recupera todos los bloques del archivo desde los nodos
   - Si un nodo falló, usa la réplica
   - Combina los bloques en el archivo completo
   - Guarda el archivo en la ubicación seleccionada

### Eliminar un Archivo

1. Seleccionar un archivo de la lista
2. Hacer clic en **Eliminar**
3. Confirmar la eliminación
4. El sistema:
   - Marca los bloques como libres en la tabla de bloques
   - Elimina los bloques de todos los nodos (original y réplicas)
   - Actualiza la información del sistema

### Ver Atributos de un Archivo

1. Seleccionar un archivo de la lista
2. Hacer clic en **Ver Atributos**
3. Se abrirá una ventana mostrando:
   - Información del archivo (nombre, tamaño, bloques, fecha)
   - Distribución de bloques (qué nodo tiene cada bloque y su réplica)

## Tolerancia a Fallos

El sistema está diseñado para ser tolerante a fallos:

1. **Replicación**: Cada bloque tiene al menos 2 copias en nodos diferentes
2. **Detección de Fallos**: El coordinador monitorea los nodos mediante heartbeat
3. **Recuperación Automática**: Si un nodo falla:
   - El coordinador lo marca como desconectado
   - Los archivos siguen siendo accesibles desde las réplicas
   - La tabla de bloques se actualiza para reflejar el estado
   - Todos los clientes son notificados del cambio

4. **Reconstrucción**: Cuando un nodo se reconecta:
   - Se registra nuevamente en el coordinador
   - La tabla de bloques se reconstruye si es necesario

## Ejemplo de Uso Completo

```bash
# Terminal 1: Coordinador
python start_coordinator.py

# Terminal 2: Nodo 1
python start_node.py --node-id node1 --space 70MB

# Terminal 3: Nodo 2
python start_node.py --node-id node2 --space 50MB

# Terminal 4: Nodo 3
python start_node.py --node-id node3 --space 100MB

# Terminal 5: Cliente GUI
python start_client.py
```

**Capacidad Total del Sistema**: 70 + 50 + 100 = 220 MB
**Total de Bloques**: 220 bloques (cada uno de 1 MB)

## Solución de Problemas

### El coordinador no inicia
- Verificar que el puerto 8888 no esté en uso
- Cambiar `COORDINATOR_PORT` en `config.py` si es necesario

### Los nodos no se conectan al coordinador
- Verificar que el coordinador esté ejecutándose
- Verificar que `COORDINATOR_HOST` en `config.py` sea correcto
- Verificar la conectividad de red

### Error al subir archivos grandes
- Verificar que haya suficiente espacio disponible en los nodos
- Verificar que haya al menos 2 nodos activos (necesario para replicación)

### La GUI no se abre
- Verificar que tkinter esté instalado
- En Linux: `sudo apt-get install python3-tk`

### Los archivos no se descargan correctamente
- Verificar que al menos una copia de cada bloque esté disponible
- Verificar la conectividad con los nodos que almacenan los bloques

## Limitaciones y Consideraciones

1. **Tamaño de Archivo**: Limitado por la capacidad total del sistema
2. **Número de Nodos**: Mínimo 2 nodos para replicación efectiva
3. **Red Local**: El sistema está diseñado para funcionar en red local
4. **Persistencia**: Los metadatos se guardan en archivos JSON
5. **Seguridad**: El sistema actual no incluye autenticación ni cifrado (adecuado para entornos controlados)

## Mejoras Futuras

- Autenticación y autorización de usuarios
- Cifrado de datos en tránsito y en reposo
- Compresión de bloques
- Balanceo de carga más sofisticado
- Interfaz web además de GUI de escritorio
- Métricas y estadísticas avanzadas
- Soporte para redes distribuidas (no solo localhost)

## Autor

Sistema desarrollado como proyecto final para Sistemas Operativos 2

## Licencia

Este proyecto es de uso educativo.

