# Iteración 6: Notificación de Desconexiones y Sincronización de Webs

## Problemas Identificados

1. **Nodos desconectados no se notificaban a las webs**: Cuando un nodo se desconectaba, la tabla web no se actualizaba
2. **Webs conectándose/desconectándose repetidamente**: Las conexiones HTTP son efímeras, causando múltiples conexiones por sesión
3. **Falta de comunicación entre Coordinador y Django**: No había forma de que Django notifique a las webs sobre cambios en tiempo real

## Soluciones Implementadas

### 1. ✅ Sistema de Caché de Eventos Global

**Archivo nuevo: `coordinator/cache.py`**
```python
- CoordinatorStateCache: Clase para mantener eventos recientes
- coordinator_cache: Instancia global accessible desde Django
- Métodos:
  - add_event(type, data): Registra un evento
  - get_recent_events(): Obtiene últimos eventos
  - get_events_since(timestamp): Obtiene eventos desde un tiempo específico
```

### 2. ✅ Registro de Clientes Web en Coordinador

**Cambios en `coordinator.py`:**
- Agregada estructura `self.web_clients`: Diccionario de sockets de webs conectadas
- Agregado `self.web_lock`: Lock para sincronización de acceso
- **Registro automático**: Cuando una web hace una solicitud, se registra su socket

```python
# En handle_client():
if not client_type_announced:
    # ... registrar socket
    with self.web_lock:
        self.web_clients[client_address_key] = client_socket
```

### 3. ✅ Función notify_all_webs()

**Agreg en `coordinator.py`:**
```python
def notify_all_webs(self, notification: dict):
    # Envía notificación a todas las webs conectadas
    # Limpia clientes muertos automáticamente
```

### 4. ✅ Sistema de Eventos Persistentes

**Agregadas funciones en `coordinator.py`:**
```python
def add_event(event_type, event_data):
    # Registra evento en memoria y en caché global
    # Mantiene últimos 20 eventos locales + caché global de 50

def get_recent_events():
    # Retorna eventos recientes para consultas de webs
```

### 5. ✅ Notificación en Desconexión de Nodos

**Mejorado `handle_node_disconnection()` en `coordinator.py`:**
```
Ahora hace:
1. Registra el evento en el caché global
2. Intenta notificar a todas las webs conectadas
3. Elimina el nodo del registro

Resultado: [✗ NODO DESCONECTADO] se propaga a todas las webs
```

### 6. ✅ Endpoint de Eventos en Django

**Nuevo endpoint en `views.py`:**
```python
@csrf_exempt
@require_http_methods(["GET"])
def get_recent_events(request):
    # GET /api/events/?since=timestamp
    # Retorna eventos desde un tiempo específico
    # Respuesta:
    {
        "events": [...],
        "count": int,
        "timestamp": float
    }
```

**Ruta agregada en `urls.py`:**
```
path('api/events/', views.get_recent_events)
```

### 7. ✅ Monitoreo Automático en Web Frontend

**Cambios en `index.html`:**

**a) Variables globales:**
```javascript
let lastEventTimestamp = 0;  // Tracking de eventos
let needsRefresh = false;    // Bandera de actualización
```

**b) Nueva función `checkRecentEvents()`:**
```javascript
- Consulta /api/events/ periódicamente
- Procesa eventos de desconexión de nodos
- Actualiza tabla si hay cambios
- Usa timestamps para no repetir eventos
```

**c) Integración con `refreshAll()`:**
```javascript
async function refreshAll() {
    await Promise.all([fetchNodes(), fetchFiles(), fetchBlockTable()]);
    await checkRecentEvents();  // ⭐ NUEVO
}
```

## Flujo de Actualización Ahora Es:

```
1. Nodo se desconecta
    ↓
2. Coordinador detecta timeout
    ↓
3. Llama handle_node_disconnection()
    ↓
4. Registra evento en caché global
    ↓
5. Web hace request a /api/events/
    ↓
6. Obtiene eventos recientes
    ↓
7. JavaScript procesa y actualiza tabla
    ↓
8. Usuario ve [✗ NODO DESCONECTADO] inmediatamente
```

## Solución a Desconexiones Repetidas

**Explicación**: Las conexiones HTTP son efímeras - es normal que haya múltiples conexiones
- Cada request HTTP = nueva conexión
- Django cierra el socket después del request
- Es **correcto comportamiento** en arquitectura REST

**Mejora aplicada**:
- En lugar de intentar mantener socket abierto con webs
- Usamos caché de eventos que las webs consultan
- Más robusto y escalable

## Archivos Modificados

1. **coordinator/cache.py** - ✨ NUEVO
2. **coordinator/coordinator.py** - +60 líneas (caché, eventos, notify_all_webs)
3. **webapp/filesystem/views.py** - +30 líneas (endpoint de eventos, import caché)
4. **webapp/filesystem/urls.py** - +1 ruta
5. **webapp/filesystem/templates/filesystem/index.html** - +60 líneas (monitoreo de eventos)

## Características Principales

✅ **Notificaciones Activas**: Desconexiones se propaganinstantáneamente
✅ **Sin Polling Agresivo**: Usa timestamps para evitar procesar eventos duplicados
✅ **Escalable**: Caché global permite múltiples webs sin sobrecargar
✅ **Robusto**: Limpia automáticamente clientes muertos
✅ **Sincronizado**: Todos ven los cambios al mismo tiempo

## Testing

```bash
# Terminal 1: Iniciar coordinador
python start_coordinator.py

# Terminal 2: Conectar nodo
python start_node.py --space 50MB

# Terminal 3: Abrir web
python start_web.py
# Ir a http://localhost:8000

# Terminal 2: Desconectar nodo (Ctrl+C)
# → Web actualiza tabla automáticamente [✗ NODO DESCONECTADO]
```

## Próximos Pasos Opcionales

1. Implementar WebSocket para comunicación bidireccional real
2. Agregar más tipos de eventos (bloque sincronizado, archivo eliminado, etc)
3. Persistencia de eventos en BD
4. Sistema de alertas para administrador
