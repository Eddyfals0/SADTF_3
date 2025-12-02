# Lógica de Bloques - Sistema de Paginación

## Nueva Estructura de Bloques

### IDs de Bloques

Los bloques ahora tienen IDs que identifican el nodo y el número de bloque:

**Formato:** `nodo{numero_nodo}{numero_bloque}`

**Ejemplos:**
- Nodo 1 con 50 bloques: `nodo1001`, `nodo1002`, ..., `nodo1050`
- Nodo 2 con 60 bloques: `nodo2001`, `nodo2002`, ..., `nodo2060`
- Nodo 3 con 100 bloques: `nodo3001`, `nodo3002`, ..., `nodo3100`

**Total de bloques:** Suma de todos los bloques de todos los nodos activos

### Estructura Tipo Lista Ligada

Cada bloque tiene un puntero al siguiente bloque del mismo archivo:

```
Bloque 1 (nodo1001) → PRIMARY en nodo1, REPLICA en nodo2 → next: nodo2001
Bloque 2 (nodo2001) → PRIMARY en nodo2, REPLICA en nodo3 → next: nodo3001
Bloque 3 (nodo3001) → PRIMARY en nodo3, REPLICA en nodo1 → next: null
```

### Asignación de Bloques

1. **Cada bloque pertenece a un nodo específico** (tipo paginación)
   - El bloque `nodo1001` siempre pertenece al nodo1
   - El bloque `nodo2001` siempre pertenece al nodo2

2. **Cada bloque tiene una réplica en otro nodo**
   - El bloque original se almacena en su nodo asignado
   - La réplica se almacena en un nodo diferente (rotación circular)

3. **Distribución automática**
   - Los bloques se distribuyen entre todos los nodos disponibles
   - La réplica siempre va a un nodo diferente al original

### Ejemplo de Distribución

**Sistema con 3 nodos:**
- Nodo1: 50 bloques (nodo1001 - nodo1050)
- Nodo2: 60 bloques (nodo2001 - nodo2060)
- Nodo3: 100 bloques (nodo3001 - nodo3100)
- **Total: 210 bloques**

**Archivo de 3 bloques:**
- Bloque 1: `nodo1001` → PRIMARY: nodo1, REPLICA: nodo2
- Bloque 2: `nodo2001` → PRIMARY: nodo2, REPLICA: nodo3
- Bloque 3: `nodo3001` → PRIMARY: nodo3, REPLICA: nodo1

### Visualización en la Interfaz

Al pasar el mouse sobre un bloque en la tabla de bloques, verás:

**Bloque Libre:**
```
ID: nodo1001
Nodo Primario: nodo1
Estado: Libre
```

**Bloque Ocupado:**
```
ID: nodo1001
Nodo Primario: nodo1
Estado: Ocupado (Original)
Archivo: archivo.pdf_1234567890
Réplica en: nodo2
```

### Validaciones

1. **Tamaño de nodo:** 50-100 MB (validado al iniciar el nodo)
2. **Mínimo de nodos:** Se necesitan al menos 2 nodos para replicación
3. **Espacio disponible:** Se verifica antes de asignar bloques

### Persistencia

- El coordinador guarda el registro de nodos y sus bloques
- Si un nodo se desconecta y reconecta, recupera su ID y sus bloques
- La tabla de bloques se reconstruye automáticamente cuando cambian los nodos

### Ventajas de esta Estructura

1. **Tipo Paginación:** Cada bloque tiene una ubicación fija en un nodo específico
2. **Fácil Identificación:** El ID del bloque indica inmediatamente a qué nodo pertenece
3. **Replicación Garantizada:** Cada bloque tiene una réplica en otro nodo
4. **Lista Ligada:** Fácil seguir la secuencia de bloques de un archivo
5. **Tolerancia a Fallos:** Si un nodo falla, los bloques están disponibles en sus réplicas

