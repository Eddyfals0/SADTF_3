# Arreglo: Reconocimiento Correcto de Nodos Persistentes

## Problema Identificado

**Síntoma**: 
```
PC del usuario:
- Primera conexión: me conecta como "nodo1"
- Desconexión
- Segunda conexión: me conecta como "nodo2"
(Debería ser nodo1 nuevamente)
```

**Causa Raíz**: 
El coordinador usaba `address:port` como clave única en `node_registry`, pero el puerto cambia en cada conexión porque el nodo usa:
```python
self.listener_socket.bind(('', 0))  # Puerto aleatorio
self.listener_port = self.listener_socket.getsockname()[1]  # Cada conexión diferente
```

**Flujo Incorrecto**:
```
Conexión 1: 172.31.10.37:57433 → node_registry["172.31.10.37:57433"] = "nodo1"
Desconexión

Conexión 2: 172.31.10.37:57434 (PUERTO DIFERENTE) 
→ node_registry["172.31.10.37:57434"] = NO EXISTE
→ Asignar nuevo: "nodo2" ✗
```

## Solución Implementada

**Nueva Clave**: `address#node_id` (en lugar de `address:port`)

```python
# ANTES (incorrecto):
node_key = f"{address}:{port}"  # Cambia cada conexión
# "172.31.10.37:57433"
# "172.31.10.37:57434"

# AHORA (correcto):
node_key = f"{address}#{requested_node_id}"  # Persistente
# "172.31.10.37#node_3eac6ec3"
# "172.31.10.37#node_3eac6ec3" (mismo)
```

**Por qué funciona**:
- `address` es la IP del nodo (persistente)
- `node_id` (ej: `node_3eac6ec3`) es el ID del filesystem (persistente)
- `port` es el puerto del listener (cambia en cada conexión)

**Nuevo Flujo**:
```
Conexión 1: 172.31.10.37:57433
  node_key = "172.31.10.37#node_3eac6ec3"
  node_registry["172.31.10.37#node_3eac6ec3"] = "nodo1" ✓
  
Desconexión

Conexión 2: 172.31.10.37:57434
  node_key = "172.31.10.37#node_3eac6ec3" (MISMO)
  node_registry["172.31.10.37#node_3eac6ec3"] = "nodo1" (reutiliza) ✓
```

## Cambios en coordinator.py

### handle_node_register()

**Antes**:
```python
node_key = f"{address}:{port}"
if node_key in self.node_registry:
    node_id = self.node_registry[node_key]
    print(f"[✓ NODO CONECTADO] ID: {node_id}")
```

**Ahora**:
```python
node_key = f"{address}#{requested_node_id}"
if node_key in self.node_registry:
    assigned_nodo = self.node_registry[node_key]
    print(f"[✓ NODO RECONECTADO] node_id: {requested_node_id} → {assigned_nodo}")
```

## Flujo de Información

```
┌─────────────────────────────────────────────────────────┐
│                      NODO (Persistente)                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  File: C:\Users\Eduar\espacioCompartido\node_3eac6ec3   │
│  ↓                                                       │
│  self.node_id = "node_3eac6ec3" (siempre igual)         │
│                                                          │
│  Conexión 1: puerto 57433  }                            │
│  Conexión 2: puerto 57434  } (puertos diferentes)       │
│  Conexión 3: puerto 57435  }                            │
│                                                          │
└────────────────┬────────────────────────────────────────┘
                 │ send NODE_REGISTER
                 │ {node_id: "node_3eac6ec3"}
                 ↓
┌─────────────────────────────────────────────────────────┐
│                  COORDINADOR (Inteligente)               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  node_registry = {                                      │
│    "172.31.10.37#node_3eac6ec3": "nodo1"               │
│  }                                                       │
│                                                          │
│  Reconexión: Same key → Same nodo1                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Impacto

✅ **Usuario conecta PC**: `nodo1` → bloques persistentes
✅ **Usuario desconecta**: Bloques en `nodo1`
✅ **Usuario reconecta**: Misma `nodo1` → accede a sus bloques
✅ **Usuario agrega otra máquina**: Nueva `nodo2` con nuevo `node_id`

## Persistencia de Datos

Con este cambio:
- Los bloques se almacenan en `nodo1`, `nodo2`, etc (asignado por coordinador)
- Si el usuario desconecta y reconecta, sigue siendo `nodo1`
- Los archivos permanecen accesibles bajo el mismo nodo
- No hay pérdida de datos por cambio de puerto

## Testing

```bash
# Terminal 1: Coordinador
python start_coordinator.py

# Terminal 2: Nodo (primera vez)
python start_node.py --space 100MB --coordinator-host 172.31.10.37
# Verás: [✓ NODO NUEVO] node_id: node_3eac6ec3 → nodo1

# Cargar archivo...

# Ctrl+C para desconectar

# Terminal 2: Nodo (segunda vez)
python start_node.py --space 100MB --coordinator-host 172.31.10.37
# Verás: [✓ NODO RECONECTADO] node_id: node_3eac6ec3 → nodo1
# Los archivos siguen disponibles en nodo1 ✓
```

## Resumen Técnico

| Aspecto | Antes | Después |
|---------|-------|---------|
| Clave de identificación | `address:port` | `address#node_id` |
| Reconocimiento | No (puerto cambia) | Sí (ambos persistentes) |
| Pérdida de datos | Posible (nodo diferente) | No (mismo nodo) |
| Blocks persistentes | No | Sí |
| Reuso de nodo_n | No | Sí |
