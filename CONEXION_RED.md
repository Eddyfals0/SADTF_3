# Guía de Conexión en Red - SADTF

## Cómo Conectar desde Otras Computadoras

Esta guía explica cómo conectar la interfaz web y los nodos desde otras computadoras al coordinador que está ejecutándose en tu computadora principal.

## Requisitos Previos

1. **Todas las computadoras deben estar en la misma red local** (misma red WiFi o mismo switch/router)
2. **El coordinador debe estar ejecutándose** en la computadora principal
3. **Conocer la IP de la computadora principal** donde corre el coordinador

## Paso 1: Encontrar la IP de tu Computadora Principal

### Windows:
```cmd
ipconfig
```
Busca "IPv4 Address" en la sección de tu adaptador de red (WiFi o Ethernet).

Ejemplo: `192.168.1.100`

### Linux/Mac:
```bash
ifconfig
# o
ip addr
```
Busca la IP en tu interfaz de red activa.

## Paso 2: Configurar el Coordinador para Aceptar Conexiones Externas

El coordinador por defecto escucha en todas las interfaces (`0.0.0.0`), así que ya debería aceptar conexiones externas. Solo asegúrate de que:

1. El firewall de Windows permita conexiones en el puerto 8888
2. Si usas un router, no necesitas configuración adicional para red local

### Permitir Puerto en Firewall de Windows:

1. Abre "Firewall de Windows Defender"
2. Click en "Configuración avanzada"
3. Click en "Reglas de entrada" → "Nueva regla"
4. Selecciona "Puerto" → Siguiente
5. TCP → Puerto específico: 8888 → Siguiente
6. Permitir la conexión → Siguiente
7. Marca todos los perfiles → Siguiente
8. Nombre: "SADTF Coordinador" → Finalizar

## Paso 3: Conectar la Interfaz Web desde Otra PC

### Opción A: Usando la Interfaz Web (Recomendado)

1. En la otra computadora, abre un navegador
2. Ve a: `http://IP_DE_LA_PC_PRINCIPAL:8000`
   - Ejemplo: `http://192.168.1.100:8000`
3. En la barra superior de la interfaz, verás un campo "IP Coord:"
4. Cambia la IP de `127.0.0.1` a la IP de tu computadora principal
   - Ejemplo: `192.168.1.100`
5. Haz clic en "Actualizar" o espera a que se actualice automáticamente

### Opción B: Modificar el Servidor Web Django

Si quieres que el servidor web acepte conexiones externas:

1. Edita `start_web.py` o ejecuta manualmente:
```bash
cd webapp
python manage.py runserver 0.0.0.0:8000
```

Esto hará que el servidor escuche en todas las interfaces.

## Paso 4: Conectar un Nodo desde Otra PC

En la otra computadora, ejecuta:

```bash
python start_node.py --node-id node_remoto --space 70MB --coordinator-host 192.168.1.100
```

**Parámetros:**
- `--node-id`: ID único para este nodo (opcional, se genera automáticamente)
- `--space`: Espacio compartido en MB (50-100)
- `--coordinator-host`: **IP de la computadora principal donde corre el coordinador**

### Ejemplo Completo:

```bash
# En PC secundaria (IP: 192.168.1.101)
python start_node.py --node-id nodo_pc2 --space 80MB --coordinator-host 192.168.1.100
```

## Configuración Completa de Ejemplo

### Escenario: 3 Computadoras

**PC Principal (192.168.1.100):**
- Coordinador: `python start_coordinator.py`
- Servidor Web: `python start_web.py` (o `python manage.py runserver 0.0.0.0:8000`)
- Nodo Local: `python start_node.py --node-id nodo_pc1 --space 70MB`

**PC Secundaria 1 (192.168.1.101):**
- Nodo Remoto: `python start_node.py --node-id nodo_pc2 --space 50MB --coordinator-host 192.168.1.100`
- Interfaz Web: Abrir navegador en `http://192.168.1.100:8000` y cambiar IP Coord a `192.168.1.100`

**PC Secundaria 2 (192.168.1.102):**
- Nodo Remoto: `python start_node.py --node-id nodo_pc3 --space 100MB --coordinator-host 192.168.1.100`
- Interfaz Web: Abrir navegador en `http://192.168.1.100:8000` y cambiar IP Coord a `192.168.1.100`

## Verificación de Conexión

### Verificar que el Coordinador Está Escuchando:

En la PC principal:
```bash
netstat -an | findstr 8888
```

Deberías ver algo como:
```
TCP    0.0.0.0:8888           0.0.0.0:0              LISTENING
```

### Verificar desde Otra PC:

```bash
# Linux/Mac
telnet 192.168.1.100 8888

# Windows
Test-NetConnection -ComputerName 192.168.1.100 -Port 8888
```

## Solución de Problemas

### "No se puede conectar al coordinador"

1. **Verifica la IP**: Asegúrate de usar la IP correcta de la PC principal
2. **Verifica el firewall**: El puerto 8888 debe estar abierto
3. **Verifica la red**: Ambas PCs deben estar en la misma red
4. **Ping**: Prueba hacer ping desde la PC secundaria:
   ```bash
   ping 192.168.1.100
   ```

### "Connection refused" o "Connection timeout"

1. Verifica que el coordinador esté ejecutándose
2. Verifica que el coordinador esté escuchando en `0.0.0.0:8888` (no solo `127.0.0.1:8888`)
3. Verifica el firewall de Windows
4. Verifica que no haya un antivirus bloqueando la conexión

### La interfaz web no carga desde otra PC

1. Asegúrate de ejecutar Django con: `python manage.py runserver 0.0.0.0:8000`
2. Verifica que el firewall permita el puerto 8000
3. Usa la IP correcta en el navegador: `http://192.168.1.100:8000`

### El nodo no se conecta

1. Verifica que usaste `--coordinator-host` con la IP correcta
2. Verifica que el coordinador esté ejecutándose
3. Revisa los logs del coordinador para ver si hay intentos de conexión

## Configuración Avanzada

### Cambiar el Puerto del Coordinador

Si necesitas cambiar el puerto (por ejemplo, si 8888 está ocupado):

1. Edita `config.py`:
```python
COORDINATOR_PORT = 8889  # Nuevo puerto
```

2. Actualiza el firewall para el nuevo puerto
3. Usa el nuevo puerto en todas las conexiones

### Usar un Nombre de Host en Lugar de IP

Puedes configurar un nombre de host en `/etc/hosts` (Linux/Mac) o `C:\Windows\System32\drivers\etc\hosts` (Windows):

```
192.168.1.100    coordinador-sadft
```

Luego usa `coordinador-sadft` en lugar de la IP.

## Resumen Rápido

**Para conectar la interfaz web:**
1. Abre `http://IP_PRINCIPAL:8000` en el navegador
2. Cambia "IP Coord:" en la interfaz a la IP de la PC principal

**Para conectar un nodo:**
```bash
python start_node.py --coordinator-host IP_PRINCIPAL --space 70MB
```

**Ejemplo:**
```bash
# Si la PC principal es 192.168.1.100
python start_node.py --coordinator-host 192.168.1.100 --space 70MB
```

¡Listo! Ahora puedes tener nodos y clientes en múltiples computadoras conectados al mismo coordinador.

