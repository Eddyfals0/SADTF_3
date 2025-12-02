# Interfaz Web - Sistema de Archivos Distribuido

## Nueva Interfaz Web Moderna con Django

Se ha creado una interfaz web moderna y elegante usando Django y Bootstrap 5 que reemplaza la interfaz de escritorio (tkinter).

## Características de la Interfaz Web

### 🎨 Diseño Moderno
- **Gradientes modernos** y diseño atractivo
- **Responsive**: Funciona en desktop, tablet y móvil
- **Bootstrap 5** para componentes modernos
- **Iconos Bootstrap Icons** para mejor UX
- **Tema oscuro** con colores vibrantes

### 📊 Dashboard en Tiempo Real
- **Estadísticas en tiempo real**: Nodos activos, archivos, bloques
- **Actualización automática** cada 5 segundos
- **Tarjetas informativas** con gradientes

### 🖥️ Paneles Interactivos

#### Panel de Nodos
- Lista de nodos activos/inactivos
- Estado visual con badges de colores
- Actualización en tiempo real

#### Panel de Archivos
- **Drag & Drop**: Arrastra archivos para subirlos
- Tabla interactiva con selección
- Operaciones: Subir, Descargar, Eliminar, Ver Atributos
- Información detallada de cada archivo

#### Panel de Tabla de Bloques
- Visualización de bloques en uso
- Estado de cada bloque (Libre/Usado)
- Información de nodos donde están almacenados

#### Consola
- Logs en tiempo real con timestamps
- Estilo terminal moderno
- Scroll automático

## Instalación

### 1. Instalar Django

```bash
pip install Django
```

O instalar todas las dependencias:

```bash
pip install -r requirements.txt
```

### 2. Configurar Django (solo primera vez)

```bash
cd webapp
python manage.py migrate
```

## Uso

### 1. Iniciar el Coordinador

En una terminal:

```bash
python start_coordinator.py
```

### 2. Iniciar los Nodos

En terminales separadas:

```bash
python start_node.py --node-id node1 --space 70MB
python start_node.py --node-id node2 --space 50MB
```

### 3. Iniciar el Servidor Web

En otra terminal:

```bash
python start_web.py
```

O manualmente:

```bash
cd webapp
python manage.py runserver
```

### 4. Abrir en el Navegador

Abre tu navegador y ve a:

```
http://127.0.0.1:8000
```

## Funcionalidades de la Interfaz

### Subir Archivos
1. **Método 1**: Arrastra un archivo al área de carga
2. **Método 2**: Haz clic en el área de carga y selecciona un archivo
3. Haz clic en "Subir"
4. El archivo se dividirá en bloques y se distribuirá automáticamente

### Descargar Archivos
1. Selecciona un archivo de la tabla (haz clic en la fila)
2. Haz clic en "Descargar"
3. El archivo se descargará completo

### Eliminar Archivos
1. Selecciona un archivo
2. Haz clic en "Eliminar"
3. Confirma la eliminación
4. Los bloques se liberarán automáticamente

### Ver Atributos
1. Selecciona un archivo
2. Haz clic en "Atributos"
3. Verás:
   - Información del archivo (nombre, tamaño, bloques, fecha)
   - Distribución de bloques (qué nodo tiene cada bloque y su réplica)

## API Endpoints

La interfaz web usa una API REST:

- `GET /api/nodes/` - Obtener nodos activos
- `GET /api/files/` - Listar archivos
- `POST /api/files/upload/` - Subir archivo
- `GET /api/files/download/?file_id=X` - Descargar archivo
- `POST /api/files/delete/` - Eliminar archivo
- `GET /api/files/info/?file_id=X` - Información del archivo
- `GET /api/blocks/` - Tabla de bloques

## Características Técnicas

### Frontend
- **HTML5** semántico
- **Bootstrap 5.3** para componentes
- **JavaScript vanilla** (sin dependencias externas)
- **CSS3** con gradientes y animaciones
- **Drag & Drop API** nativa

### Backend
- **Django 4.2+** como framework web
- **Comunicación con coordinador** mediante sockets
- **API REST** para todas las operaciones
- **Manejo de archivos** con FormData

### Actualizaciones en Tiempo Real
- **Polling automático** cada 5 segundos
- **Actualización de estadísticas** en tiempo real
- **Consola con logs** en tiempo real

## Comparación con Interfaz Desktop

| Característica | Desktop (tkinter) | Web (Django) |
|---------------|-------------------|--------------|
| Diseño | Básico | Moderno y atractivo |
| Responsive | No | Sí |
| Acceso remoto | No | Sí (con configuración) |
| Actualizaciones | Manual | Automática |
| Drag & Drop | No | Sí |
| Estadísticas | Básicas | Dashboard completo |

## Solución de Problemas

### "No se pudo conectar al coordinador"
- Verifica que el coordinador esté ejecutándose
- Verifica que el puerto 8888 esté disponible
- Revisa `config.py` para la configuración

### Django no se instala
```bash
pip install --upgrade pip
pip install Django
```

### Error al migrar
```bash
cd webapp
python manage.py makemigrations
python manage.py migrate
```

### El servidor no inicia
- Verifica que estés en el directorio `webapp`
- Verifica que Django esté instalado
- Revisa los logs de error

## Personalización

### Cambiar Colores
Edita el CSS en `webapp/filesystem/templates/filesystem/index.html`:

```css
:root {
    --primary-color: #6366f1;  /* Cambia estos valores */
    --secondary-color: #8b5cf6;
    --success-color: #10b981;
    --danger-color: #ef4444;
}
```

### Cambiar Puerto
Edita `start_web.py` o ejecuta:

```bash
cd webapp
python manage.py runserver 8001  # Puerto diferente
```

## Próximas Mejoras

- [ ] WebSockets para actualizaciones en tiempo real (sin polling)
- [ ] Autenticación de usuarios
- [ ] Múltiples usuarios simultáneos
- [ ] Historial de operaciones
- [ ] Gráficos de uso de espacio
- [ ] Notificaciones push

## Notas

- La interfaz web se comunica directamente con el coordinador
- No requiere base de datos (usa SQLite solo para Django admin)
- Compatible con todos los navegadores modernos
- Funciona en localhost por defecto (configurable para red)

