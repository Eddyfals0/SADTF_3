# Guía de Inicio Rápido

## Inicio Rápido del Sistema

### 1. Iniciar el Coordinador

```bash
python start_coordinator.py
```

Deberías ver:
```
============================================================
SISTEMA DE ARCHIVOS DISTRIBUIDO - COORDINADOR
============================================================
Iniciando coordinador en puerto 8888...
Presione Ctrl+C para detener
============================================================
Coordinador iniciado en puerto 8888
```

### 2. Iniciar al menos 2 Nodos

**Terminal 2:**
```bash
python start_node.py --node-id node1 --space 70MB
```

**Terminal 3:**
```bash
python start_node.py --node-id node2 --space 50MB
```

**Terminal 4 (Opcional):**
```bash
python start_node.py --node-id node3 --space 100MB
```

### 3. Iniciar el Cliente GUI

**Terminal 5:**
```bash
python start_client.py
```

## Verificación Rápida

1. En el cliente GUI, verifica que aparezcan los nodos en el panel izquierdo
2. Intenta subir un archivo pequeño (menos de 1 MB)
3. Verifica que aparezca en la lista de archivos
4. Descarga el archivo para verificar que funciona
5. Verifica la tabla de bloques para ver cómo se distribuyeron los bloques

## Ejemplo de Sesión Completa

```bash
# Terminal 1 - Coordinador
$ python start_coordinator.py
Coordinador iniciado en puerto 8888
Nodo node1 registrado desde 192.168.1.100:54321 con 73400320 bytes
Nodo node2 registrado desde 192.168.1.100:54322 con 52428800 bytes

# Terminal 2 - Nodo 1
$ python start_node.py --node-id node1 --space 70MB
Nodo node1 iniciado
Espacio compartido: 70.00 MB
Puerto listener: 54321
Nodo registrado exitosamente. Total de bloques: 120

# Terminal 3 - Nodo 2
$ python start_node.py --node-id node2 --space 50MB
Nodo node2 iniciado
Espacio compartido: 50.00 MB
Puerto listener: 54322
Nodo registrado exitosamente. Total de bloques: 120

# Terminal 4 - Cliente GUI
$ python start_client.py
# Se abre la ventana de la GUI
```

## Solución de Problemas Comunes

### "No se puede conectar al coordinador"
- Verifica que el coordinador esté ejecutándose
- Verifica que el puerto 8888 no esté bloqueado por firewall

### "Se necesitan al menos 2 nodos activos"
- Asegúrate de tener al menos 2 nodos ejecutándose
- Verifica que los nodos se hayan registrado correctamente en el coordinador

### "No hay suficientes bloques libres"
- El archivo es demasiado grande para el espacio disponible
- Elimina archivos antiguos o añade más nodos

### La GUI no muestra nodos
- Presiona el botón "Actualizar" en el panel de nodos
- Verifica la consola para ver mensajes de error

## Comandos Útiles

### Ver espacio disponible
- En la GUI, revisa el panel de "Nodos Activos"
- La tabla de bloques muestra bloques libres vs usados

### Verificar distribución de bloques
- Selecciona un archivo
- Haz clic en "Ver Atributos"
- Verás dónde está cada bloque y su réplica

### Monitorear el sistema
- La consola en la parte inferior muestra todos los eventos
- Los nodos muestran mensajes en sus terminales

