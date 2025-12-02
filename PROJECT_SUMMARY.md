# Resumen del Proyecto - Sistema de Archivos Distribuido

## Arquitectura del Sistema

### Componentes Principales

1. **Coordinador (`coordinator/coordinator.py`)**
   - Servidor central que gestiona todo el sistema
   - Mantiene la tabla de bloques (similar a paginación)
   - Coordina la distribución de bloques entre nodos
   - Monitorea el estado de los nodos mediante heartbeat
   - Maneja todas las operaciones de archivos (subir, descargar, eliminar)
   - Notifica cambios a todos los nodos y clientes

2. **Nodos (`node/node.py` y `node/storage.py`)**
   - Almacenan bloques de archivos en su directorio `espacioCompartido`
   - Cada nodo tiene entre 50-100 MB de espacio compartido
   - Mantienen réplicas de bloques para tolerancia a fallos
   - Se comunican con el coordinador mediante heartbeat
   - Escuchan comandos del coordinador en un puerto dedicado

3. **Interfaz Web (`webapp/filesystem/`)**
   - Interfaz web moderna con Django y Bootstrap 5
   - Dashboard con estadísticas en tiempo real
   - Muestra nodos activos en tiempo real
   - Visualiza la tabla de bloques
   - Permite subir archivos con Drag & Drop
   - Permite descargar, eliminar archivos
   - Muestra atributos detallados de archivos
   - Consola de eventos en tiempo real
   - API REST para todas las operaciones

### Módulos Comunes

- **`common/protocol.py`**: Protocolo de comunicación estandarizado
- **`common/utils.py`**: Utilidades para manejo de archivos y bloques
- **`config.py`**: Configuración centralizada del sistema

## Características Implementadas

### ✅ Distribución de Archivos
- Archivos divididos en bloques de 1 MB
- Distribución automática entre nodos disponibles
- Balanceo básico de carga

### ✅ Replicación
- Cada bloque tiene 2 copias (original + réplica)
- Réplicas en nodos diferentes
- Recuperación automática si un nodo falla

### ✅ Tabla de Bloques
- Sistema similar a paginación
- Total de bloques = suma de capacidades de todos los nodos
- Gestión de bloques libres y ocupados
- Rastreo de ubicación de cada bloque

### ✅ Tolerancia a Fallos
- Detección de nodos desconectados mediante heartbeat
- Uso automático de réplicas cuando un nodo falla
- Notificación a todos los clientes de cambios
- Reconstrucción de tabla de bloques al reconectar nodos

### ✅ Interfaz Web
- Dashboard con estadísticas en tiempo real
- Panel de nodos activos con estado visual
- Lista de archivos con información detallada
- Tabla de bloques visualizable
- Consola de eventos estilo terminal
- Operaciones: subir (con Drag & Drop), descargar, eliminar, ver atributos
- Diseño responsive y moderno
- Actualización automática cada 5 segundos

### ✅ Persistencia
- Metadatos guardados en archivos JSON
- Estado del coordinador persistente
- Metadatos de bloques en cada nodo

## Flujo de Operaciones

### Subir Archivo
1. Cliente selecciona archivo y lo envía al coordinador
2. Coordinador divide el archivo en bloques de 1 MB
3. Coordinador asigna bloques libres en la tabla
4. Coordinador distribuye bloques a nodos (original + réplica)
5. Nodos almacenan los bloques
6. Coordinador actualiza tabla de bloques y notifica a clientes

### Descargar Archivo
1. Cliente solicita descarga de archivo
2. Coordinador consulta tabla de bloques para ubicar bloques
3. Coordinador solicita bloques a los nodos (intenta original, luego réplica si falla)
4. Coordinador combina bloques y envía al cliente
5. Cliente guarda archivo completo

### Eliminar Archivo
1. Cliente solicita eliminación
2. Coordinador marca bloques como libres en tabla
3. Coordinador envía comandos de eliminación a nodos
4. Nodos eliminan bloques físicamente
5. Coordinador actualiza estado y notifica

### Detección de Fallos
1. Coordinador monitorea heartbeat de nodos cada 10 segundos
2. Si un nodo no responde en 30 segundos, se marca como desconectado
3. Coordinador notifica a todos los clientes
4. Operaciones futuras usan réplicas automáticamente

## Estructura de Datos

### Tabla de Bloques
```python
BlockEntry {
    block_id: int          # ID único del bloque
    status: BlockStatus    # FREE, USED, REPLICATED
    file_id: str          # ID del archivo que usa el bloque
    block_number: int     # Número de bloque dentro del archivo
    node_id: str          # Nodo que almacena el bloque original
    replica_node_id: str  # Nodo que almacena la réplica
}
```

### Información de Archivo
```python
FileInfo {
    file_id: str          # ID único del archivo
    filename: str         # Nombre original del archivo
    size: int            # Tamaño en bytes
    upload_date: str     # Fecha de subida (ISO format)
    num_blocks: int      # Número de bloques
}
```

### Información de Nodo
```python
NodeInfo {
    node_id: str          # ID único del nodo
    address: str         # Dirección IP
    port: int           # Puerto listener
    shared_space_size: int  # Espacio disponible en bytes
    last_heartbeat: float  # Timestamp del último heartbeat
    is_alive: bool      # Estado del nodo
}
```

## Protocolo de Comunicación

El sistema usa un protocolo basado en mensajes JSON con prefijo de longitud:

1. **Mensaje**: `[4 bytes longitud][JSON mensaje]`
2. **Tipos de mensajes**:
   - `NODE_REGISTER`: Registro de nodo
   - `NODE_HEARTBEAT`: Latido de nodo
   - `STORE_BLOCK`: Almacenar bloque
   - `RETRIEVE_BLOCK`: Recuperar bloque
   - `DELETE_BLOCK`: Eliminar bloque
   - `UPLOAD_FILE`: Subir archivo
   - `DOWNLOAD_FILE`: Descargar archivo
   - Y más...

## Configuración

Todas las configuraciones están en `config.py`:
- Puerto del coordinador: 8888
- Tamaño de bloque: 1 MB
- Espacio por nodo: 50-100 MB
- Intervalo de heartbeat: 10 segundos
- Timeout de nodo: 30 segundos

## Limitaciones Conocidas

1. **Tamaño de archivo**: Limitado por capacidad total del sistema
2. **Red**: Diseñado para red local (localhost o LAN)
3. **Seguridad**: No incluye autenticación ni cifrado
4. **Archivos grandes**: Carga completa en memoria (mejorable con streaming)
5. **Reconstrucción**: La tabla de bloques se reconstruye completamente al añadir nodos

## Mejoras Futuras Posibles

1. Streaming de archivos grandes
2. Autenticación y autorización
3. Cifrado de datos
4. Compresión de bloques
5. Balanceo de carga más sofisticado
6. Interfaz web
7. Métricas y estadísticas avanzadas
8. Soporte para redes distribuidas (no solo localhost)

## Archivos del Proyecto

```
SADTF_3/
├── coordinator/          # Módulo coordinador
│   ├── coordinator.py    # Servidor principal
│   └── block_table.py    # Gestión tabla de bloques
├── node/                 # Módulo nodos
│   ├── node.py          # Nodo principal
│   └── storage.py        # Almacenamiento
├── webapp/               # Aplicación web Django
│   ├── filesystem/      # App Django
│   │   ├── views.py     # Vistas y API REST
│   │   ├── urls.py      # URLs
│   │   └── templates/   # Templates HTML
│   └── sadft_web/       # Configuración Django
├── common/               # Módulos comunes
│   ├── protocol.py      # Protocolo comunicación
│   └── utils.py         # Utilidades
├── config.py            # Configuración
├── start_*.py           # Scripts de inicio
├── README.md            # Documentación completa
├── QUICK_START.md       # Guía rápida
└── requirements.txt     # Dependencias (Django)
```

## Conclusión

El sistema implementa exitosamente un sistema de archivos distribuido tolerante a fallos con:
- ✅ Distribución de archivos en bloques
- ✅ Replicación para tolerancia a fallos
- ✅ Tabla de bloques tipo paginación
- ✅ Interfaz web moderna y completa
- ✅ Monitoreo en tiempo real
- ✅ Manejo de desconexiones
- ✅ Operaciones CRUD completas

El sistema está listo para uso y demostración.

