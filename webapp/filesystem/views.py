"""
Vistas para el sistema de archivos distribuido
"""
import socket
import base64
import os
import json
import time
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import sys

# Añadir ruta del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import COORDINATOR_HOST, COORDINATOR_PORT
from common.protocol import MessageType, receive_message, send_message
from common.utils import format_size, combine_blocks_into_file
from coordinator.cache import coordinator_cache

def get_default_coordinator_host():
    """Obtiene la IP del coordinador desde el archivo de configuración o config.py"""
    try:
        config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'webapp', 'coordinator_config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('coordinator_host', COORDINATOR_HOST)
    except:
        pass
    return COORDINATOR_HOST

def get_coordinator_connection(coordinator_host=None):
    """Obtiene una conexión con el coordinador"""
    # Usar IP del request si está disponible, sino usar la del archivo de config, sino la del config.py
    if coordinator_host:
        host = coordinator_host
    else:
        host = get_default_coordinator_host()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, COORDINATOR_PORT))
        return sock
    except Exception as e:
        return None

def index(request):
    """Página principal"""
    return render(request, 'filesystem/index.html')

@require_http_methods(["GET"])
def get_coordinator_host(request):
    """Obtiene la IP del coordinador configurada"""
    coordinator_host = get_default_coordinator_host()
    return JsonResponse({"coordinator_host": coordinator_host})

@require_http_methods(["GET"])
def get_active_nodes(request):
    """Obtiene lista de nodos activos"""
    coordinator_host = request.GET.get('coordinator_host', None)
    sock = get_coordinator_connection(coordinator_host)
    if not sock:
        return JsonResponse({"error": f"No se pudo conectar al coordinador en {coordinator_host or COORDINATOR_HOST}"}, status=500)
    
    try:
        send_message(sock, MessageType.GET_ACTIVE_NODES)
        response = receive_message(sock)
        
        if response and response.get("type") == MessageType.ACTIVE_NODES_DATA.value:
            return JsonResponse(response.get("data", {}))
        else:
            return JsonResponse({"error": "Error obteniendo nodos"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        sock.close()

@require_http_methods(["GET"])
def list_files(request):
    """Lista todos los archivos"""
    coordinator_host = request.GET.get('coordinator_host', None)
    sock = get_coordinator_connection(coordinator_host)
    if not sock:
        return JsonResponse({"error": f"No se pudo conectar al coordinador en {coordinator_host or COORDINATOR_HOST}"}, status=500)
    
    try:
        send_message(sock, MessageType.LIST_FILES)
        response = receive_message(sock)
        
        if response and response.get("type") == MessageType.FILE_LIST.value:
            return JsonResponse(response.get("data", {}))
        else:
            return JsonResponse({"error": "Error obteniendo archivos"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        sock.close()

@require_http_methods(["GET"])
def get_block_table(request):
    """Obtiene la tabla de bloques"""
    coordinator_host = request.GET.get('coordinator_host', None)
    sock = get_coordinator_connection(coordinator_host)
    if not sock:
        return JsonResponse({"error": f"No se pudo conectar al coordinador en {coordinator_host or COORDINATOR_HOST}"}, status=500)
    
    try:
        send_message(sock, MessageType.GET_BLOCK_TABLE)
        response = receive_message(sock)
        
        if response and response.get("type") == MessageType.BLOCK_TABLE_DATA.value:
            return JsonResponse(response.get("data", {}))
        else:
            return JsonResponse({"error": "Error obteniendo tabla de bloques"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        sock.close()

@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    """Sube un archivo"""
    if 'file' not in request.FILES:
        return JsonResponse({"error": "No se proporcionó archivo"}, status=400)
    
    file = request.FILES['file']
    filename = file.name
    file_data = file.read()
    file_size = len(file_data)
    
    # Codificar en base64
    file_data_b64 = base64.b64encode(file_data).decode('utf-8')
    
    coordinator_host = request.POST.get('coordinator_host', None)
    sock = get_coordinator_connection(coordinator_host)
    if not sock:
        return JsonResponse({"error": f"No se pudo conectar al coordinador en {coordinator_host or COORDINATOR_HOST}"}, status=500)
    
    try:
        send_message(sock, MessageType.UPLOAD_FILE, {
            "filename": filename,
            "size": file_size,
            "file_data": file_data_b64
        })
        
        response = receive_message(sock)
        
        if response and response.get("type") == MessageType.UPLOAD_RESPONSE.value:
            data = response.get("data", {})
            if data.get("success"):
                return JsonResponse({"success": True, "message": "Archivo subido exitosamente", "file_id": data.get("file_id")})
            else:
                return JsonResponse({"error": data.get("message", "Error desconocido")}, status=500)
        elif response and response.get("type") == MessageType.ERROR.value:
            return JsonResponse({"error": response.get("data", {}).get("message", "Error desconocido")}, status=500)
        else:
            return JsonResponse({"error": "Respuesta inválida del coordinador"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        sock.close()

@require_http_methods(["GET"])
def download_file(request):
    """Descarga un archivo"""
    file_id = request.GET.get('file_id')
    if not file_id:
        return JsonResponse({"error": "No se proporcionó file_id"}, status=400)
    
    coordinator_host = request.GET.get('coordinator_host', None)
    sock = get_coordinator_connection(coordinator_host)
    if not sock:
        return JsonResponse({"error": f"No se pudo conectar al coordinador en {coordinator_host or COORDINATOR_HOST}"}, status=500)
    
    try:
        send_message(sock, MessageType.DOWNLOAD_FILE, {"file_id": file_id})
        response = receive_message(sock)
        
        if response and response.get("type") == MessageType.DOWNLOAD_RESPONSE.value:
            data = response.get("data", {})
            if data.get("success"):
                blocks_data = data.get("blocks", {})
                
                # Combinar bloques (ordenar por número de bloque)
                blocks = [(int(k), base64.b64decode(v)) for k, v in blocks_data.items()]
                blocks.sort(key=lambda x: x[0])  # Ordenar por número de bloque
                
                # Crear archivo temporal
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    combine_blocks_into_file(blocks, tmp_file.name)
                    file_content = open(tmp_file.name, 'rb').read()
                    os.unlink(tmp_file.name)
                
                filename = data.get("filename", "archivo")
                http_response = HttpResponse(file_content, content_type='application/octet-stream')
                http_response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return http_response
            else:
                return JsonResponse({"error": data.get("message", "Error desconocido")}, status=500)
        else:
            return JsonResponse({"error": "Error descargando archivo"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        sock.close()

@csrf_exempt
@require_http_methods(["POST"])
def delete_file(request):
    """Elimina un archivo"""
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        coordinator_host = data.get('coordinator_host', None)
    except:
        return JsonResponse({"error": "Datos inválidos"}, status=400)
    
    if not file_id:
        return JsonResponse({"error": "No se proporcionó file_id"}, status=400)
    sock = get_coordinator_connection(coordinator_host)
    if not sock:
        return JsonResponse({"error": f"No se pudo conectar al coordinador en {coordinator_host or COORDINATOR_HOST}"}, status=500)
    
    try:
        send_message(sock, MessageType.DELETE_FILE, {"file_id": file_id})
        response = receive_message(sock)
        
        if response and response.get("type") == MessageType.DELETE_RESPONSE.value:
            data = response.get("data", {})
            if data.get("success"):
                return JsonResponse({"success": True, "message": "Archivo eliminado exitosamente"})
            else:
                return JsonResponse({"error": data.get("message", "Error desconocido")}, status=500)
        else:
            return JsonResponse({"error": "Error eliminando archivo"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        sock.close()

@require_http_methods(["GET"])
def get_file_info(request):
    """Obtiene información detallada de un archivo"""
    file_id = request.GET.get('file_id')
    if not file_id:
        return JsonResponse({"error": "No se proporcionó file_id"}, status=400)
    
    coordinator_host = request.GET.get('coordinator_host', None)
    sock = get_coordinator_connection(coordinator_host)
    if not sock:
        return JsonResponse({"error": f"No se pudo conectar al coordinador en {coordinator_host or COORDINATOR_HOST}"}, status=500)
    
    try:
        send_message(sock, MessageType.GET_FILE_INFO, {"file_id": file_id})
        response = receive_message(sock)
        
        if response and response.get("type") == MessageType.FILE_INFO.value:
            return JsonResponse(response.get("data", {}))
        else:
            return JsonResponse({"error": "Error obteniendo información del archivo"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        sock.close()

@csrf_exempt
@require_http_methods(["POST"])
def cleanup_all(request):
    """Limpia todos los archivos, bloques y nodos del sistema"""
    coordinator_host = request.GET.get('coordinator_host', None)
    sock = get_coordinator_connection(coordinator_host)
    if not sock:
        return JsonResponse({"error": f"No se pudo conectar al coordinador en {coordinator_host or COORDINATOR_HOST}"}, status=500)
    
    try:
        print("[WEB] Solicitando limpieza completa del sistema...")
        send_message(sock, MessageType.CLEANUP_ALL, {})
        response = receive_message(sock)
        
        if response and response.get("type") == MessageType.SUCCESS.value:
            return JsonResponse({
                "success": True,
                "message": "Sistema limpiado exitosamente",
                "details": response.get("data", {})
            })
        else:
            error_msg = response.get("data", {}).get("message", "Error desconocido") if response else "Sin respuesta del coordinador"
            return JsonResponse({"error": error_msg}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        sock.close()

@csrf_exempt
@require_http_methods(["GET"])
def get_recent_events(request):
    """Obtiene los eventos recientes (desconexiones de nodos, etc)"""
    try:
        # Obtener timestamp desde request si existe
        timestamp_str = request.GET.get('since', '0')
        try:
            timestamp = float(timestamp_str)
        except:
            timestamp = 0
        
        # Obtener eventos desde el caché
        if timestamp > 0:
            events = coordinator_cache.get_events_since(timestamp)
        else:
            events = coordinator_cache.get_recent_events()
        
        return JsonResponse({
            "events": events,
            "count": len(events),
            "timestamp": time.time()
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)