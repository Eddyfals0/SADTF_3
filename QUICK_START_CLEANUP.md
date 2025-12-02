# 🚀 QUICK START - Limpieza y Gestión de Nodos

## ⚡ Inicio Rápido

### 1️⃣ Limpiar TODO el Sistema (Local)

```powershell
python cleanup.py
```

**Lo que hace:**
- ❌ Elimina todos los nodos
- ❌ Elimina datos del coordinador
- ❌ Elimina archivos almacenados
- ❌ Limpia carpeta: `C:\Users\[usuario]\espacioCompartido\`

**Confirmación requerida:** SÍ/NO

---

### 2️⃣ Limpiar Sistema Remoto (desde Web)

```
1. Abrir: http://localhost:8000
2. Click en botón 🗑️ "Limpiar" (esquina superior derecha)
3. Confirmar advertencias (2 veces)
4. ✓ Completado automáticamente
```

---

### 3️⃣ Limpiar Sistema Remoto (desde CLI)

```powershell
# Terminal 1
python start_coordinator.py

# Terminal 2
python test_cleanup.py
```

---

## 📂 Nodos Automáticos

### Ubicación
```
C:\Users\[usuario]\espacioCompartido\
├── node_id_1\espacioCompartido\
├── node_id_2\espacioCompartido\
└── ...
```

### Uso
```python
# SIN especificar ID (descubre automáticamente)
node = Node()

# CON ID específico
node = Node(node_id="node_abc123")
```

---

## 📊 Archivos Nuevos

| Archivo | Propósito |
|---------|-----------|
| `cleanup.py` | Limpieza local completa |
| `test_cleanup.py` | Pruebas de limpieza remota |
| `CLEANUP_GUIDE.md` | Documentación completa |
| `IMPLEMENTATION_SUMMARY.md` | Resumen técnico |

---

## ✅ Verificación

```powershell
# 1. Verificar que cleanup.py existe
Test-Path cleanup.py

# 2. Ejecutar pruebas
python test_cleanup.py

# 3. Verificar directorio compartido
explorer "C:\Users\$($env:USERNAME)\espacioCompartido"
```

---

## 🆘 Problemas Comunes

### ❌ "No se puede conectar al coordinador"
```powershell
# Solución: Asegúrate que el coordinador esté ejecutándose
python start_coordinator.py
```

### ❌ "Error al limpiar directorio"
```powershell
# Solución: Cierra archivos abiertos en esa carpeta
# Luego intenta nuevamente
```

### ❌ "Permiso denegado"
```powershell
# Solución: Ejecuta con permisos de administrador
# Click derecho en PowerShell > "Ejecutar como administrador"
```

---

## 📝 Cambios Implementados

### Archivos Modificados
- ✅ `config.py` - Ruta del directorio compartido
- ✅ `node/node.py` - Descubrimiento de nodos
- ✅ `coordinator/coordinator.py` - Limpieza remota
- ✅ `webapp/filesystem/views.py` - Endpoint de limpieza
- ✅ `webapp/filesystem/urls.py` - Ruta de limpieza
- ✅ `webapp/filesystem/templates/filesystem/index.html` - Botón web
- ✅ `common/protocol.py` - Mensaje CLEANUP_ALL

### Archivos Nuevos
- ✅ `cleanup.py` - 182 líneas
- ✅ `test_cleanup.py` - 115 líneas
- ✅ `CLEANUP_GUIDE.md` - 312 líneas
- ✅ `IMPLEMENTATION_SUMMARY.md` - 350+ líneas

---

## 🎯 Casos de Uso

### Caso 1: Iniciar de Cero
```powershell
python cleanup.py  # Confirmar
python start_coordinator.py
python start_node.py
python start_web.py
```

### Caso 2: Eliminar Archivo y sus Réplicas
```
1. Acceder a http://localhost:8000
2. Click en 🗑️ del archivo
3. ✓ Archivo y réplicas eliminados
```

### Caso 3: Limpieza Total desde Código
```python
from common.protocol import send_message, MessageType
import socket

sock = socket.socket()
sock.connect(('localhost', 8888))
send_message(sock, MessageType.CLEANUP_ALL, {})
response = receive_message(sock)
print(response)  # {"type": "SUCCESS", "data": {...}}
```

---

## 🔍 Estructura Final

```
SADTF_3/
├── cleanup.py ⭐ NUEVO
├── test_cleanup.py ⭐ NUEVO
├── CLEANUP_GUIDE.md ⭐ NUEVO
├── IMPLEMENTATION_SUMMARY.md ⭐ NUEVO
├── config.py ✏️ MODIFICADO
├── common/protocol.py ✏️ MODIFICADO
├── node/node.py ✏️ MODIFICADO
├── coordinator/coordinator.py ✏️ MODIFICADO
├── webapp/filesystem/views.py ✏️ MODIFICADO
├── webapp/filesystem/urls.py ✏️ MODIFICADO
├── webapp/filesystem/templates/filesystem/index.html ✏️ MODIFICADO
└── ...
```

---

## 📞 Referencia Rápida

```powershell
# Limpiar
python cleanup.py

# Pruebas
python test_cleanup.py

# Documentación
Start-Process CLEANUP_GUIDE.md
Start-Process IMPLEMENTATION_SUMMARY.md
```

---

## ⏰ Tiempo Estimado

| Operación | Tiempo |
|-----------|--------|
| Limpieza local | 2-5 segundos |
| Limpieza remota (3 nodos) | 5-10 segundos |
| Reinicio completo | 15-30 segundos |

---

**Última actualización:** 2 de diciembre de 2025
**Estado:** ✅ Completado
