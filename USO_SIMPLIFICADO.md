# Guía de Uso Simplificado - SADTF

## Cambios Realizados

El sistema ahora es más simple de usar:

1. **Los nodos ya no necesitan especificar su ID** - El coordinador lo asigna automáticamente (nodo1, nodo2, nodo3, etc.)
2. **El coordinador mantiene registro persistente** - Si un nodo se desconecta y reconecta, recupera su ID anterior
3. **La interfaz web puede configurarse con la IP del coordinador** al iniciar

## Uso Simplificado

### En la PC Principal (Coordinador)

```bash
# Terminal 1: Iniciar coordinador
python start_coordinator.py

# Terminal 2: Iniciar servidor web (opcional, si quieres acceso local)
python start_web.py
```

### En Otra PC (Interfaz Web)

```bash
# Iniciar servidor web especificando la IP del coordinador
python start_web.py --coordinator-host 192.168.1.100
```

Luego abre el navegador en `http://127.0.0.1:8000` o `http://TU_IP:8000`

La interfaz web cargará automáticamente la IP del coordinador que especificaste.

### En Otra PC (Nodo)

```bash
# Comando simplificado - sin --node-id
python start_node.py --space 70MB --coordinator-host 192.168.1.100
```

**El coordinador asignará automáticamente:**
- Primer nodo: `nodo1`
- Segundo nodo: `nodo2`
- Tercer nodo: `nodo3`
- Y así sucesivamente...

## Ejemplo Completo

### PC Principal (192.168.1.100)

```bash
# Terminal 1
python start_coordinator.py

# Terminal 2 (opcional)
python start_node.py --space 70MB
# El coordinador asignará: nodo1
```

### PC Secundaria 1 (192.168.1.101)

```bash
# Terminal 1: Interfaz Web
python start_web.py --coordinator-host 192.168.1.100
# Abre navegador en http://127.0.0.1:8000

# Terminal 2: Nodo
python start_node.py --space 50MB --coordinator-host 192.168.1.100
# El coordinador asignará: nodo2
```

### PC Secundaria 2 (192.168.1.102)

```bash
# Terminal: Nodo
python start_node.py --space 100MB --coordinator-host 192.168.1.100
# El coordinador asignará: nodo3
```

## Reconexión de Nodos

Si un nodo se desconecta y luego se reconecta:

1. El coordinador detecta que es el mismo nodo (por su dirección IP:puerto)
2. Le asigna el mismo ID que tenía antes
3. El nodo recupera su identidad automáticamente

**Ejemplo:**
- Nodo `nodo2` se desconecta
- Se vuelve a conectar desde la misma PC
- El coordinador le asigna nuevamente `nodo2` (no `nodo4`)

## Parámetros del Comando

### start_web.py

```bash
python start_web.py [--coordinator-host IP]
```

- `--coordinator-host`: IP del coordinador (ej: 192.168.1.100)
  - Si no se especifica, usa `127.0.0.1` (localhost)

### start_node.py

```bash
python start_node.py --space TAMAÑO [--coordinator-host IP]
```

- `--space`: **REQUERIDO** - Espacio compartido (50-100 MB)
  - Ejemplos: `70MB`, `50MB`, `100MB`
- `--coordinator-host`: IP del coordinador (ej: 192.168.1.100)
  - Si no se especifica, usa `localhost`

**Ya NO necesitas:**
- `--node-id` (eliminado - el coordinador lo asigna)

## Ventajas

1. **Más simple**: Menos parámetros que recordar
2. **Automático**: El coordinador gestiona los IDs
3. **Persistente**: Los nodos mantienen su identidad
4. **Escalable**: Fácil agregar más nodos sin preocuparse por IDs

## Notas

- El coordinador guarda el registro de nodos en `coordinator_data/state.json`
- Si eliminas este archivo, los nodos recibirán nuevos IDs
- Los IDs se asignan secuencialmente: nodo1, nodo2, nodo3...
- Si un nodo con ID ya asignado se desconecta, ese ID queda "reservado" para cuando se reconecte

