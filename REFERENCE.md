# 📋 Referencia Rápida - Comandos y Endpoints

## 🎯 Limpieza Rápida

### Limpiar TODO (CLI)
```bash
python cleanup.py
# Confirmar: sí
```

### Limpiar TODO (Remota)
```bash
# Terminal 1
python start_coordinator.py

# Terminal 2
python test_cleanup.py
# Seleccionar: s (sí)
```

### Limpiar TODO (Web)
```
http://localhost:8000 
→ Botón 🗑️ "Limpiar" 
→ Confirmar (2 veces)
```

---

## 🔗 Endpoints API

### POST /api/cleanup/
Limpia todos los archivos, bloques y nodos

**Parámetros:**
```
coordinator_host=localhost (opcional)
```

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/api/cleanup/?coordinator_host=localhost"
```

**Respuesta Exitosa:**
```json
{
  "success": true,
  "message": "Sistema limpiado exitosamente",
  "details": {
    "files_deleted": 5,
    "nodes_disconnected": 3,
    "message": "Sistema limpiado exitosamente"
  }
}
```

**Respuesta Error:**
```json
{
  "error": "No se pudo conectar al coordinador"
}
```

---

## 🔌 Protocolo de Limpieza

### Mensaje: CLEANUP_ALL
```python
from common.protocol import MessageType, send_message, receive_message
import socket

# Conectar
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 8888))

# Enviar solicitud
send_message(sock, MessageType.CLEANUP_ALL, {})

# Recibir respuesta
response = receive_message(sock)

# Procesar
if response.get("type") == MessageType.SUCCESS.value:
    print("✓ Limpieza completada")
    data = response.get("data", {})
    print(f"Archivos eliminados: {data.get('files_deleted')}")
else:
    print("✗ Error:", response.get("data", {}).get("message"))

sock.close()
```

---

## 📂 Rutas de Archivos

### Directorio Compartido
```
C:\Users\[usuario]\espacioCompartido\
├── node_id_1\espacioCompartido\
├── node_id_2\espacioCompartido\
└── ...
```

### Datos del Coordinador
```
./coordinator_data/
├── state.json
└── ...
```

### Base de Datos Web
```
./webapp/db.sqlite3
```

---

## 🧪 Pruebas Rápidas

### Test 1: Descubrimiento de Nodos
```bash
# Crear carpeta manualmente
mkdir "C:\Users\$($env:USERNAME)\espacioCompartido\test_node"

# Iniciar nodo
python start_node.py

# Verificar en logs que usó el ID correcto
```

### Test 2: Limpieza Completa
```bash
# Terminal 1
python start_coordinator.py

# Terminal 2
python start_node.py

# Terminal 3
python test_cleanup.py
# Confirmar: s

# Verificar en Terminal 1 y 2 que limpió
```

### Test 3: Limpieza Web
```bash
# Terminal 1
python start_coordinator.py

# Terminal 2
python start_node.py

# Terminal 3
python start_web.py

# Browser: http://localhost:8000
# - Subir archivo
# - Click botón "Limpiar"
# - Confirmar
# - Verificar que desaparece
```

---

## 🐛 Troubleshooting

### "No se puede conectar"
```bash
# Verificar que coordinador está corriendo
python start_coordinator.py
```

### "Permiso denegado"
```bash
# Ejecutar como administrador
# Click derecho PowerShell → Ejecutar como administrador
```

### "Archivo bloqueado"
```bash
# Cerrar aplicaciones que usen la carpeta
# Reintentar limpieza
```

### "Directorio no existe"
```bash
# El directorio se crea automáticamente
# Si aún no existe, se creará al iniciar nodo
```

---

## 📊 Variables de Configuración

### `config.py`
```python
USER_SHARED_DIRECTORY = "C:\\Users\\[usuario]\\espacioCompartido"
COORDINATOR_HOST = "localhost"
COORDINATOR_PORT = 8888
BLOCK_SIZE = 1024 * 1024  # 1 MB
```

---

## 🎯 Uso Programático

### Python
```python
# Limpieza local
import subprocess
subprocess.run(["python", "cleanup.py"], input=b"s\n")

# Limpieza remota
from common.protocol import *
import socket

sock = socket.socket()
sock.connect(('localhost', 8888))
send_message(sock, MessageType.CLEANUP_ALL, {})
response = receive_message(sock)
sock.close()
```

### JavaScript/Fetch
```javascript
async function cleanup() {
    const response = await fetch('/api/cleanup/', {
        method: 'POST'
    });
    const data = await response.json();
    console.log(data);
}
```

### Bash/cURL
```bash
curl -X POST "http://localhost:8000/api/cleanup/"
```

---

## 📝 Archivos de Referencia

| Archivo | Para |
|---------|------|
| CLEANUP_GUIDE.md | Documentación completa |
| IMPLEMENTATION_SUMMARY.md | Resumen técnico |
| QUICK_START_CLEANUP.md | Inicio rápido |
| verify_implementation.py | Validar implementación |
| cleanup.py | Limpieza local |
| test_cleanup.py | Pruebas |

---

## ⌛ Tiempos Aproximados

```
Limpieza local        2-5 segundos
Limpieza remota (3)   10 segundos
Limpieza remota (10)  20 segundos
Reinicio completo     30 segundos
```

---

## ✅ Verificación Rápida

```bash
# 1. Ver archivos nuevos
ls cleanup.py test_cleanup.py CLEANUP_GUIDE.md

# 2. Verificar modificaciones
grep "CLEANUP_ALL" common/protocol.py
grep "USER_SHARED_DIRECTORY" config.py

# 3. Verificar funciones
grep "def cleanup_all" webapp/filesystem/views.py
grep "def handle_cleanup_all" coordinator/coordinator.py

# 4. Verificar directorio usuario
explorer "C:\Users\$($env:USERNAME)\espacioCompartido"
```

---

## 🔐 Seguridad

### ✓ Implementado
- Confirmación en CLI
- Confirmación en Web (doble)
- Validación de entrada
- Manejo de errores

### ⚠️ Recomendado
- Autenticación en API
- Validación de IP
- Rate limiting
- Logs de auditoría

---

## 📞 Referencia Final

```
LIMPIAR: python cleanup.py
PROBAR:  python test_cleanup.py
WEB:     http://localhost:8000 → Botón 🗑️
DOCS:    Ver CLEANUP_GUIDE.md
```

---

**Última actualización:** 2 de diciembre de 2025
