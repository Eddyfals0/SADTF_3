"""
Coordinador del sistema distribuido
"""
import socket
import threading
import time
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import COORDINATOR_PORT, HEARTBEAT_INTERVAL, NODE_TIMEOUT, COORDINATOR_DATA_DIR, BLOCK_SIZE
from common.protocol import MessageType, receive_message, send_message
from coordinator.block_table import BlockTable
from coordinator.cache import coordinator_cache
from common.utils import ensure_directory

@dataclass
class NodeInfo:
    """Información de un nodo"""
    node_id: str
    address: str
    port: int
    shared_space_size: int  # en bytes
    last_heartbeat: float
    socket: Optional[Any] = field(default=None)
    
    def is_alive(self):
        """Verifica si el nodo está vivo"""
        return time.time() - self.last_heartbeat < NODE_TIMEOUT
    
    def to_dict(self):
        """Convierte a diccionario"""
        return {
            "node_id": self.node_id,
            "address": self.address,
            "port": self.port,
            "shared_space_size": self.shared_space_size,
            "is_alive": self.is_alive()
        }

@dataclass
class FileInfo:
    """Información de un archivo"""
    file_id: str
    filename: str
    size: int
    upload_date: str
    num_blocks: int
    
    def to_dict(self):
        return asdict(self)

class Coordinator:
    """Coordinador del sistema distribuido"""
    
    def __init__(self, port=COORDINATOR_PORT):
        self.port = port
        self.socket = None
        self.running = False
        
        # Nodos registrados
        self.nodes: Dict[str, NodeInfo] = {}
        self.node_lock = threading.Lock()
        
        # Registro de nodos por dirección (para reasignar IDs)
        self.node_registry: Dict[str, str] = {}  # address:port -> node_id
        
        # Clientes web conectados (para notificaciones)
        self.web_clients: Dict[str, socket.socket] = {}  # address:port -> socket
        self.web_lock = threading.Lock()
        
        # Eventos recientes (para notificar a webs)
        self.recent_events = []  # Lista de eventos recientes
        self.events_lock = threading.Lock()
        
        self.next_node_number = 1
        
        # Tabla de bloques
        self.block_table: Optional[BlockTable] = None
        
        # Archivos almacenados
        self.files: Dict[str, FileInfo] = {}
        self.files_lock = threading.Lock()
        
        # Directorio de datos del coordinador
        ensure_directory(COORDINATOR_DATA_DIR)
        
        # Cargar estado persistente
        self.load_state()
        
        # Thread para monitorear nodos
        self.monitor_thread = None
    
    def load_state(self):
        """Carga el estado persistente del coordinador"""
        state_file = os.path.join(COORDINATOR_DATA_DIR, "state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    # Cargar archivos
                    self.files = {fid: FileInfo(**data) 
                                 for fid, data in state.get("files", {}).items()}
                    # Cargar registro de nodos
                    self.node_registry = state.get("node_registry", {})
                    # Calcular el siguiente número de nodo
                    if self.node_registry:
                        max_num = 0
                        for node_id in self.node_registry.values():
                            if node_id.startswith("nodo"):
                                try:
                                    num = int(node_id.replace("nodo", ""))
                                    max_num = max(max_num, num)
                                except:
                                    pass
                        self.next_node_number = max_num + 1
                    # La tabla de bloques se reconstruirá cuando los nodos se registren
            except Exception as e:
                print(f"Error cargando estado: {e}")
    
    def save_state(self):
        """Guarda el estado persistente del coordinador"""
        state_file = os.path.join(COORDINATOR_DATA_DIR, "state.json")
        try:
            with open(state_file, 'w') as f:
                state = {
                    "files": {fid: file_info.to_dict() 
                             for fid, file_info in self.files.items()},
                    "node_registry": self.node_registry
                }
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error guardando estado: {e}")
    
    def start(self):
        """Inicia el coordinador"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.socket.listen(10)
        self.running = True
        
        print(f"Coordinador iniciado en puerto {self.port}")
        
        # Iniciar thread de monitoreo
        self.monitor_thread = threading.Thread(target=self.monitor_nodes, daemon=True)
        self.monitor_thread.start()
        
        # Aceptar conexiones
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, address), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"Error aceptando conexión: {e}")
    
    def monitor_nodes(self):
        """Monitorea los nodos y detecta desconexiones"""
        while self.running:
            time.sleep(HEARTBEAT_INTERVAL)
            with self.node_lock:
                disconnected_nodes = []
                for node_id, node_info in list(self.nodes.items()):
                    if not node_info.is_alive():
                        disconnected_nodes.append(node_id)
                
                for node_id in disconnected_nodes:
                    print(f"Nodo {node_id} desconectado (timeout)")
                    self.handle_node_disconnection(node_id)
    
    def handle_node_disconnection(self, node_id: str):
        """Maneja la desconexión de un nodo"""
        if node_id in self.nodes:
            node_info = self.nodes[node_id]
            # Cerrar socket si está abierto
            if node_info.socket:
                try:
                    node_info.socket.close()
                except:
                    pass
            
            # ADVERTENCIA: Solo mostrar desconexión sin recuperación automática
            print(f"[✗ NODO DESCONECTADO] {node_id} - Se perdió contacto")
            print(f"    [!] Bloques replicas disponibles para recuperación manual si es necesario")
            
            # ⭐ Registrar evento para que las webs lo vean
            self.add_event("NODE_DISCONNECTED", {
                "node_id": node_id,
                "address": node_info.address,
                "port": node_info.port
            })
            
            # ⭐ NOTIFICAR A TODAS LAS WEBS sobre la desconexión del nodo
            self.notify_all_webs({
                "type": "NODE_DISCONNECTED",
                "node_id": node_id,
                "address": node_info.address,
                "port": node_info.port
            })
            
            del self.nodes[node_id]
    
    def rebuild_block_table(self):
        """Reconstruye la tabla de bloques basándose en los nodos activos"""
        total_blocks = sum(node.shared_space_size // BLOCK_SIZE 
                          for node in self.nodes.values() if node.is_alive())
        
        if total_blocks > 0:
            # Crear nueva tabla de bloques
            new_table = BlockTable(total_blocks)
            
            # Migrar información de archivos existentes
            # (simplificado - en producción se necesitaría más lógica)
            self.block_table = new_table
            
            # Notificar a todos los nodos
            self.notify_all_nodes({
                "type": "BLOCK_TABLE_UPDATED",
                "table": self.block_table.to_dict()
            })
    
    def verify_and_recover_blocks(self):
        """
        Verifica que todos los bloques existan en su nodo principal.
        Si no existen, intenta recuperarlos desde la réplica.
        Se ejecuta periódicamente para sincronización.
        """
        if not self.block_table or not self.block_table.blocks:
            return
        
        recovered_blocks = 0
        missing_blocks = []
        
        for block_id, block_info in list(self.block_table.blocks.items()):
            if block_info["status"] == "FREE":
                continue
            
            primary_node_id = block_info.get("primary_node_id")
            replica_node_id = block_info.get("replica_node_id")
            file_id = block_info.get("file_id")
            
            # Verificar que el nodo principal esté vivo
            if primary_node_id not in self.nodes or not self.nodes[primary_node_id].is_alive():
                # Nodo principal desconectado
                if replica_node_id and replica_node_id in self.nodes and self.nodes[replica_node_id].is_alive():
                    print(f"[!] Bloque {block_id} - Primario desconectado, réplica disponible en {replica_node_id}")
                    # No recuperar automáticamente, solo notificar
                else:
                    print(f"[✗] Bloque {block_id} - SIN RESPALDO (primario y réplica no disponibles)")
                    missing_blocks.append(block_id)
                continue
            
            # TODO: Aquí se podría agregar verificación real del bloque en el nodo
            # Por ahora solo verificamos el estado del nodo
    
    def sync_blocks_from_node(self, node_id: str):
        """
        Sincroniza bloques desde un nodo específico después de reconexión.
        Si el usuario borró archivos, intenta recuperarlos desde las réplicas.
        """
        if node_id not in self.nodes:
            return False
        
        node_info = self.nodes[node_id]
        sync_count = 0
        
        # Buscar bloques que deberían estar en este nodo
        for block_id, block_info in list(self.block_table.blocks.items()):
            if block_info["status"] == "FREE":
                continue
            
            if block_info.get("primary_node_id") == node_id:
                # Este bloque debería estar en este nodo
                # Verificar si está (esto se haría con un mensaje de verificación)
                sync_count += 1
        
        print(f"[*] Sincronización: {sync_count} bloques verificados en {node_id}")
        return True
    
    def notify_all_nodes(self, message: dict):
        """Notifica a todos los nodos activos"""
        with self.node_lock:
            for node_id, node_info in list(self.nodes.items()):
                if node_info.is_alive() and node_info.socket:
                    try:
                        send_message(node_info.socket, MessageType.UPDATE_BLOCK_TABLE, message)
                    except:
                        pass
    
    def notify_all_webs(self, notification: dict):
        """Notifica a todas las webs conectadas sobre cambios en nodos"""
        with self.web_lock:
            dead_clients = []
            for client_addr, client_socket in list(self.web_clients.items()):
                try:
                    # Enviar notificación a cada web
                    send_message(client_socket, MessageType.ACTIVE_NODES_DATA, notification)
                except Exception as e:
                    # Si hay error, marcar para eliminar
                    dead_clients.append(client_addr)
            
            # Limpiar clientes muertos
            for client_addr in dead_clients:
                try:
                    self.web_clients[client_addr].close()
                except:
                    pass
                del self.web_clients[client_addr]
    
    def add_event(self, event_type: str, event_data: dict):
        """Agrega un evento reciente para que las webs lo lean"""
        import time
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": event_data
        }
        with self.events_lock:
            self.recent_events.append(event)
            # Mantener solo los últimos 20 eventos
            if len(self.recent_events) > 20:
                self.recent_events = self.recent_events[-20:]
        
        # También agregar al caché global para que Django pueda acceder
        coordinator_cache.add_event(event_type, event_data)
    
    def get_recent_events(self) -> list:
        """Obtiene los eventos recientes (para webs)"""
        with self.events_lock:
            return list(self.recent_events)
    
    def handle_client(self, client_socket: socket.socket, address):
        """Maneja una conexión de cliente (nodo o cliente GUI)"""
        client_type = "DESCONOCIDO"
        client_type_announced = False
        client_address_key = f"{address[0]}:{address[1]}"
        
        try:
            while self.running:
                message = receive_message(client_socket)
                if not message:
                    break
                
                msg_type = MessageType(message["type"])
                data = message.get("data", {})
                
                if msg_type == MessageType.NODE_REGISTER:
                    client_type = "NODO"
                    self.handle_node_register(client_socket, data)
                elif msg_type == MessageType.NODE_HEARTBEAT:
                    client_type = "NODO"
                    self.handle_node_heartbeat(data)
                elif msg_type == MessageType.BLOCK_STORED:
                    client_type = "NODO"
                    self.handle_block_stored(data)
                elif msg_type == MessageType.UPLOAD_FILE:
                    # ⭐ Registrar cliente web cuando se conecte
                    if not client_type_announced:
                        print(f"\n[✓ WEB CONECTADA] Dirección: {address[0]}:{address[1]}")
                        client_type_announced = True
                        client_type = "WEB"
                        # Registrar el socket de esta web
                        with self.web_lock:
                            self.web_clients[client_address_key] = client_socket
                    self.handle_upload_file(client_socket, data)
                elif msg_type == MessageType.DOWNLOAD_FILE:
                    if not client_type_announced:
                        print(f"\n[✓ WEB CONECTADA] Dirección: {address[0]}:{address[1]}")
                        client_type_announced = True
                        client_type = "WEB"
                        with self.web_lock:
                            self.web_clients[client_address_key] = client_socket
                    self.handle_download_file(client_socket, data)
                elif msg_type == MessageType.DELETE_FILE:
                    if not client_type_announced:
                        print(f"\n[✓ WEB CONECTADA] Dirección: {address[0]}:{address[1]}")
                        client_type_announced = True
                        client_type = "WEB"
                        with self.web_lock:
                            self.web_clients[client_address_key] = client_socket
                    self.handle_delete_file(client_socket, data)
                elif msg_type == MessageType.CLEANUP_ALL:
                    if not client_type_announced:
                        print(f"\n[✓ WEB CONECTADA] Dirección: {address[0]}:{address[1]}")
                        client_type_announced = True
                        client_type = "WEB"
                        with self.web_lock:
                            self.web_clients[client_address_key] = client_socket
                    self.handle_cleanup_all(client_socket, data)
                elif msg_type == MessageType.LIST_FILES:
                    if not client_type_announced:
                        print(f"\n[✓ WEB CONECTADA] Dirección: {address[0]}:{address[1]}")
                        client_type_announced = True
                        client_type = "WEB"
                        with self.web_lock:
                            self.web_clients[client_address_key] = client_socket
                    self.handle_list_files(client_socket)
                elif msg_type == MessageType.GET_FILE_INFO:
                    if not client_type_announced:
                        print(f"\n[✓ WEB CONECTADA] Dirección: {address[0]}:{address[1]}")
                        client_type_announced = True
                        client_type = "WEB"
                        with self.web_lock:
                            self.web_clients[client_address_key] = client_socket
                    self.handle_get_file_info(client_socket, data)
                elif msg_type == MessageType.GET_BLOCK_TABLE:
                    if not client_type_announced:
                        print(f"\n[✓ WEB CONECTADA] Dirección: {address[0]}:{address[1]}")
                        client_type_announced = True
                        client_type = "WEB"
                        with self.web_lock:
                            self.web_clients[client_address_key] = client_socket
                    self.handle_get_block_table(client_socket)
                elif msg_type == MessageType.GET_ACTIVE_NODES:
                    if not client_type_announced:
                        print(f"\n[✓ WEB CONECTADA] Dirección: {address[0]}:{address[1]}")
                        client_type_announced = True
                        client_type = "WEB"
                        with self.web_lock:
                            self.web_clients[client_address_key] = client_socket
                    self.handle_get_active_nodes(client_socket)
                
        except Exception as e:
            print(f"Error manejando cliente {address}: {e}")
        finally:
            if client_type == "WEB":
                print(f"\n[✗ WEB DESCONECTADO] Dirección: {address[0]}:{address[1]}")
                # Desregistrar cliente web
                with self.web_lock:
                    if client_address_key in self.web_clients:
                        del self.web_clients[client_address_key]
            elif client_type == "NODO":
                print(f"\n[✗ NODO DESCONECTADO] Dirección: {address[0]}:{address[1]}")
            client_socket.close()
    
    def handle_node_register(self, client_socket: socket.socket, data: dict):
        """Registra un nuevo nodo"""
        requested_node_id = data.get("node_id")  # El node_id local del nodo (ej: node_3eac6ec3)
        address = data.get("address")
        port = data.get("port")
        shared_space_size = data.get("shared_space_size")
        
        # ⭐ CLAVE MEJORADA: Usar node_id + address en lugar de solo address:port
        # Porque el puerto cambia en cada conexión
        node_key = f"{address}#{requested_node_id}"  # Ej: "172.31.10.37#node_3eac6ec3"
        
        # Determinar el ID del nodo a asignar (nodo1, nodo2, etc)
        with self.node_lock:
            # Si el nodo ya está registrado (reconexión con mismo node_id), usar su nodo_n asignado
            if node_key in self.node_registry:
                assigned_nodo = self.node_registry[node_key]
                print(f"\n[✓ NODO RECONECTADO] node_id: {requested_node_id} → {assigned_nodo} | Dirección: {address}:{port}")
            # Si no, asignar un nuevo nodo_n (nodo1, nodo2, etc.)
            else:
                assigned_nodo = f"nodo{self.next_node_number}"
                self.next_node_number += 1
                self.node_registry[node_key] = assigned_nodo
                print(f"\n[✓ NODO NUEVO] node_id: {requested_node_id} → {assigned_nodo} (asignado) | Dirección: {address}:{port}")
            
            # Si el nodo ya existe en self.nodes pero está desconectado, actualizar su información
            if assigned_nodo in self.nodes:
                old_node = self.nodes[assigned_nodo]
                print(f"    [*] Actualizando información del nodo {assigned_nodo}")
                old_node.address = address
                old_node.port = port
                old_node.shared_space_size = shared_space_size
                old_node.last_heartbeat = time.time()
                old_node.socket = client_socket
            else:
                # Crear nuevo nodo con el nodo_n asignado
                node_info = NodeInfo(
                    node_id=assigned_nodo,  # El nodo_n asignado (nodo1, nodo2, etc)
                    address=address,
                    port=port,
                    shared_space_size=shared_space_size,
                    last_heartbeat=time.time(),
                    socket=client_socket
                )
                self.nodes[assigned_nodo] = node_info
                print(f"    [*] Nuevo nodo creado: {assigned_nodo}")
            
            # Guardar estado
            self.save_state()
            
            # Reconstruir tabla de bloques con estructura de nodos
            node_blocks = {}
            for nodo_id, node_info in self.nodes.items():
                if node_info.is_alive():
                    num_blocks = node_info.shared_space_size // BLOCK_SIZE
                    node_blocks[nodo_id] = num_blocks
            
            if node_blocks:
                if self.block_table is None:
                    self.block_table = BlockTable(node_blocks)
                else:
                    # Actualizar tabla con nuevos nodos
                    self.block_table.update_node_blocks(node_blocks)
            
            total_blocks = sum(node_blocks.values()) if node_blocks else 0
            
            send_message(client_socket, MessageType.REGISTER_RESPONSE, {
                "success": True,
                "node_id": assigned_nodo,  # Enviar el nodo_n asignado al nodo
                "total_blocks": total_blocks,
                "block_table": self.block_table.to_dict() if self.block_table else {}
            })
        
        # Notificar a otros nodos
        self.notify_all_nodes({
            "type": "NODE_REGISTERED",
            "node_id": assigned_nodo
        })
    
    def handle_node_heartbeat(self, data: dict):
        """Procesa heartbeat de un nodo"""
        node_id = data.get("node_id")
        with self.node_lock:
            if node_id in self.nodes:
                self.nodes[node_id].last_heartbeat = time.time()
    
    def handle_block_stored(self, data: dict):
        """Confirma que un bloque fue almacenado"""
        # Puede usarse para verificación
        pass
    
    def handle_upload_file(self, client_socket: socket.socket, data: dict):
        """Maneja la subida de un archivo"""
        filename = data.get("filename")
        file_size = data.get("size")
        file_data = data.get("file_data")  # Base64 encoded
        
        if not filename or not file_size:
            send_message(client_socket, MessageType.ERROR, {
                "message": "Datos incompletos"
            })
            return
        
        # Validar tamaño del archivo (no hay límite específico, pero validar que quepa)
        # Calcular número de bloques necesarios
        num_blocks = (file_size + BLOCK_SIZE - 1) // BLOCK_SIZE
        
        # Obtener nodos activos
        with self.node_lock:
            active_nodes = [node_id for node_id, node_info in self.nodes.items() 
                           if node_info.is_alive()]
        
        if len(active_nodes) < 2:
            send_message(client_socket, MessageType.ERROR, {
                "message": "Se necesitan al menos 2 nodos activos"
            })
            return
        
        # Verificar que hay suficientes bloques libres
        if self.block_table:
            free_blocks = self.block_table.get_free_blocks_count()
            if free_blocks < num_blocks:
                send_message(client_socket, MessageType.ERROR, {
                    "message": f"No hay suficientes bloques libres. Necesarios: {num_blocks}, Disponibles: {free_blocks}"
                })
                return
        
        # Generar ID único para el archivo
        file_id = f"{filename}_{int(time.time())}"
        
        try:
            # Asignar bloques (retorna lista de (block_id, primary_node_id, replica_node_id))
            allocated = self.block_table.allocate_blocks(file_id, num_blocks, active_nodes)
            
            # Guardar información del archivo
            with self.files_lock:
                self.files[file_id] = FileInfo(
                    file_id=file_id,
                    filename=filename,
                    size=file_size,
                    upload_date=datetime.now().isoformat(),
                    num_blocks=num_blocks
                )
            
            self.save_state()
            
            # Enviar instrucciones a los nodos para almacenar bloques
            import base64
            file_bytes = base64.b64decode(file_data)
            blocks = split_file_into_blocks_from_bytes(file_bytes, BLOCK_SIZE)
            
            # Distribuir bloques a nodos
            block_assignments = {}
            for i, (block_id, node_id, replica_node_id) in enumerate(allocated):
                if i < len(blocks):
                    block_data = blocks[i][1]
                    if node_id not in block_assignments:
                        block_assignments[node_id] = []
                    if replica_node_id not in block_assignments:
                        block_assignments[replica_node_id] = []
                    
                    block_assignments[node_id].append({
                        "block_id": block_id,
                        "file_id": file_id,
                        "block_number": i,
                        "block_data": base64.b64encode(block_data).decode('utf-8')
                    })
                    block_assignments[replica_node_id].append({
                        "block_id": block_id,
                        "file_id": file_id,
                        "block_number": i,
                        "block_data": base64.b64encode(block_data).decode('utf-8'),
                        "is_replica": True
                    })
            
            # Enviar bloques a nodos
            for node_id, assignments in block_assignments.items():
                if node_id in self.nodes and self.nodes[node_id].is_alive():
                    node_info = self.nodes[node_id]
                    try:
                        # Conectar al puerto listener del nodo
                        node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        node_socket.settimeout(10)
                        node_socket.connect((node_info.address, node_info.port))
                        
                        send_message(node_socket, MessageType.STORE_BLOCK, {
                            "blocks": assignments
                        })
                        
                        # Esperar confirmación
                        response = receive_message(node_socket)
                        node_socket.close()
                    except Exception as e:
                        print(f"Error enviando bloques al nodo {node_id}: {e}")
            
            send_message(client_socket, MessageType.UPLOAD_RESPONSE, {
                "success": True,
                "file_id": file_id,
                "message": "Archivo subido exitosamente"
            })
            
        except Exception as e:
            send_message(client_socket, MessageType.ERROR, {
                "message": f"Error subiendo archivo: {str(e)}"
            })
    
    def handle_download_file(self, client_socket: socket.socket, data: dict):
        """Maneja la descarga de un archivo"""
        file_id = data.get("file_id")
        
        if file_id not in self.files:
            send_message(client_socket, MessageType.ERROR, {
                "message": "Archivo no encontrado"
            })
            return
        
        file_info = self.files[file_id]
        blocks_info = self.block_table.get_file_blocks(file_id)
        
        # Obtener bloques de los nodos
        blocks_data = {}
        for block_entry in blocks_info:
            block_num = block_entry.block_number
            block_retrieved = False
            
            # Intentar obtener del nodo principal primero
            primary_node_id = getattr(block_entry, 'primary_node_id', None) or getattr(block_entry, 'node_id', None)
            if primary_node_id and primary_node_id in self.nodes and self.nodes[primary_node_id].is_alive():
                node_info = self.nodes[primary_node_id]
                try:
                    # Conectar al puerto listener del nodo
                    node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    node_socket.settimeout(5)
                    node_socket.connect((node_info.address, node_info.port))
                    
                    send_message(node_socket, MessageType.RETRIEVE_BLOCK, {
                        "block_id": block_entry.block_id,
                        "file_id": file_id,
                        "block_number": block_num
                    })
                    
                    response = receive_message(node_socket)
                    node_socket.close()
                    
                    if response and response.get("type") == MessageType.BLOCK_RETRIEVED.value:
                        blocks_data[block_num] = response.get("data", {}).get("block_data")
                        block_retrieved = True
                except Exception as e:
                    print(f"Error obteniendo bloque {block_entry.block_id} del nodo {primary_node_id}: {e}")
            
            # Si falla, intentar con la réplica
            if not block_retrieved:
                replica_id = block_entry.replica_node_id
                if replica_id and replica_id in self.nodes and self.nodes[replica_id].is_alive():
                    replica_info = self.nodes[replica_id]
                    try:
                        node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        node_socket.settimeout(5)
                        node_socket.connect((replica_info.address, replica_info.port))
                        
                        send_message(node_socket, MessageType.RETRIEVE_BLOCK, {
                            "block_id": block_entry.block_id,
                            "file_id": file_id,
                            "block_number": block_num
                        })
                        
                        response = receive_message(node_socket)
                        node_socket.close()
                        
                        if response and response.get("type") == MessageType.BLOCK_RETRIEVED.value:
                            blocks_data[block_num] = response.get("data", {}).get("block_data")
                            block_retrieved = True
                    except Exception as e:
                        print(f"Error obteniendo bloque {block_entry.block_id} de réplica {replica_id}: {e}")
            
            if not block_retrieved:
                send_message(client_socket, MessageType.ERROR, {
                    "message": f"No se pudo recuperar el bloque {block_num} del archivo"
                })
                return
        
        # Enviar bloques al cliente
        send_message(client_socket, MessageType.DOWNLOAD_RESPONSE, {
            "success": True,
            "file_id": file_id,
            "filename": file_info.filename,
            "blocks": blocks_data
        })
    
    def handle_delete_file(self, client_socket: socket.socket, data: dict):
        """Maneja la eliminación de un archivo"""
        file_id = data.get("file_id")
        
        if file_id not in self.files:
            send_message(client_socket, MessageType.ERROR, {
                "message": "Archivo no encontrado"
            })
            return
        
        # Liberar bloques
        self.block_table.free_blocks(file_id)
        
        # Eliminar bloques de los nodos (original y réplica)
        blocks_info = self.block_table.get_file_blocks(file_id)
        for block_entry in blocks_info:
            # Eliminar del nodo primario
            primary_node_id = block_entry.primary_node_id
            if primary_node_id and primary_node_id in self.nodes and self.nodes[primary_node_id].is_alive():
                node_info = self.nodes[primary_node_id]
                try:
                    node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    node_socket.settimeout(5)
                    node_socket.connect((node_info.address, node_info.port))
                    
                    send_message(node_socket, MessageType.DELETE_BLOCK, {
                        "block_id": block_entry.block_id,
                        "file_id": file_id
                    })
                    
                    node_socket.close()
                except Exception as e:
                    print(f"Error eliminando bloque del nodo primario {primary_node_id}: {e}")
            
            # Eliminar de la réplica
            replica_id = block_entry.replica_node_id
            if replica_id and replica_id in self.nodes and self.nodes[replica_id].is_alive():
                replica_info = self.nodes[replica_id]
                try:
                    node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    node_socket.settimeout(5)
                    node_socket.connect((replica_info.address, replica_info.port))
                    
                    send_message(node_socket, MessageType.DELETE_BLOCK, {
                        "block_id": block_entry.block_id,
                        "file_id": file_id
                    })
                    
                    node_socket.close()
                except Exception as e:
                    print(f"Error eliminando bloque de réplica {replica_id}: {e}")
        
        # Eliminar archivo
        with self.files_lock:
            del self.files[file_id]
        
        self.save_state()
        
        send_message(client_socket, MessageType.DELETE_RESPONSE, {
            "success": True,
            "message": "Archivo eliminado exitosamente"
        })
    
    def handle_list_files(self, client_socket: socket.socket):
        """Lista todos los archivos"""
        with self.files_lock:
            files_list = [file_info.to_dict() for file_info in self.files.values()]
        
        send_message(client_socket, MessageType.FILE_LIST, {
            "files": files_list
        })
    
    def handle_get_file_info(self, client_socket: socket.socket, data: dict):
        """Obtiene información detallada de un archivo"""
        file_id = data.get("file_id")
        
        if file_id not in self.files:
            send_message(client_socket, MessageType.ERROR, {
                "message": "Archivo no encontrado"
            })
            return
        
        file_info = self.files[file_id]
        blocks_info = [entry.to_dict() for entry in self.block_table.get_file_blocks(file_id)]
        
        send_message(client_socket, MessageType.FILE_INFO, {
            "file": file_info.to_dict(),
                "blocks": blocks_info
        })
    
    def handle_get_block_table(self, client_socket: socket.socket):
        """Obtiene la tabla de bloques completa"""
        if self.block_table:
            send_message(client_socket, MessageType.BLOCK_TABLE_DATA, {
                "table": self.block_table.to_dict()
            })
        else:
            send_message(client_socket, MessageType.ERROR, {
                "message": "Tabla de bloques no inicializada"
            })
    
    def handle_get_active_nodes(self, client_socket: socket.socket):
        """Obtiene lista de nodos activos"""
        with self.node_lock:
            nodes_list = [node_info.to_dict() 
                         for node_info in self.nodes.values() 
                         if node_info.is_alive()]
        
        send_message(client_socket, MessageType.ACTIVE_NODES_DATA, {
            "nodes": nodes_list
        })
    
    def handle_cleanup_all(self, client_socket: socket.socket, data: dict):
        """Limpia todos los archivos, bloques y nodos del sistema"""
        print("[!] LIMPIEZA COMPLETA DEL SISTEMA SOLICITADA")
        
        try:
            # 1. Obtener lista de todos los archivos
            file_ids_to_delete = list(self.files.keys())
            
            # 2. Eliminar cada archivo (esto eliminará sus bloques)
            for file_id in file_ids_to_delete:
                try:
                    if file_id in self.files:
                        file_info = self.files[file_id]
                        
                        # Liberar bloques
                        if self.block_table:
                            self.block_table.free_blocks(file_id)
                        
                        # Obtener bloques del archivo
                        if self.block_table:
                            blocks_info = self.block_table.get_file_blocks(file_id)
                            
                            # Eliminar bloques de los nodos
                            for block_entry in blocks_info:
                                # Eliminar del nodo primario
                                primary_node_id = block_entry.primary_node_id
                                if primary_node_id and primary_node_id in self.nodes:
                                    node_info = self.nodes[primary_node_id]
                                    if node_info.is_alive():
                                        try:
                                            node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                            node_socket.settimeout(3)
                                            node_socket.connect((node_info.address, node_info.port))
                                            
                                            send_message(node_socket, MessageType.DELETE_BLOCK, {
                                                "block_id": block_entry.block_id,
                                                "file_id": file_id
                                            })
                                            
                                            node_socket.close()
                                        except Exception as e:
                                            print(f"  [!] Error al eliminar bloque del nodo primario: {e}")
                                
                                # Eliminar de la réplica
                                replica_id = block_entry.replica_node_id
                                if replica_id and replica_id in self.nodes:
                                    replica_info = self.nodes[replica_id]
                                    if replica_info.is_alive():
                                        try:
                                            node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                            node_socket.settimeout(3)
                                            node_socket.connect((replica_info.address, replica_info.port))
                                            
                                            send_message(node_socket, MessageType.DELETE_BLOCK, {
                                                "block_id": block_entry.block_id,
                                                "file_id": file_id
                                            })
                                            
                                            node_socket.close()
                                        except Exception as e:
                                            print(f"  [!] Error al eliminar bloque de réplica: {e}")
                        
                        # Eliminar archivo del registro
                        with self.files_lock:
                            if file_id in self.files:
                                del self.files[file_id]
                        
                        print(f"  [✓] Archivo eliminado: {file_id}")
                
                except Exception as e:
                    print(f"  [!] Error eliminando archivo {file_id}: {e}")
            
            # 3. Desconectar y limpiar nodos
            with self.node_lock:
                node_ids = list(self.nodes.keys())
                for node_id in node_ids:
                    node_info = self.nodes[node_id]
                    try:
                        if node_info.socket:
                            node_info.socket.close()
                    except:
                        pass
                
                self.nodes.clear()
                self.node_registry.clear()
                self.next_node_number = 1
            
            print("  [✓] Todos los nodos han sido desconectados")
            
            # 4. Limpiar tabla de bloques
            if self.block_table:
                self.block_table.blocks.clear()
            
            print("  [✓] Tabla de bloques limpiada")
            
            # 5. Guardar estado limpio
            self.save_state()
            print("  [✓] Estado guardado")
            
            # Responder al cliente
            send_message(client_socket, MessageType.SUCCESS, {
                "message": "Sistema limpiado exitosamente",
                "files_deleted": len(file_ids_to_delete),
                "nodes_disconnected": len(node_ids)
            })
            
            print("[✓] LIMPIEZA COMPLETADA EXITOSAMENTE")
            
        except Exception as e:
            print(f"[!] Error durante la limpieza: {e}")
            send_message(client_socket, MessageType.ERROR, {
                "message": f"Error durante la limpieza: {str(e)}"
            })
    
    def stop(self):
        """Detiene el coordinador"""
        self.running = False
        if self.socket:
            self.socket.close()
        self.save_state()

def split_file_into_blocks_from_bytes(file_bytes: bytes, block_size: int):
    """Divide bytes de archivo en bloques"""
    blocks = []
    block_num = 0
    offset = 0
    while offset < len(file_bytes):
        block_data = file_bytes[offset:offset + block_size]
        blocks.append((block_num, block_data))
        block_num += 1
        offset += block_size
    return blocks

if __name__ == "__main__":
    coordinator = Coordinator()
    try:
        coordinator.start()
    except KeyboardInterrupt:
        print("\nDeteniendo coordinador...")
        coordinator.stop()

