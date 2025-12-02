"""
Nodo del sistema distribuido
"""
import socket
import threading
import time
import os
import base64
import uuid
from typing import Optional

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    COORDINATOR_HOST, COORDINATOR_PORT, SHARED_DIRECTORY,
    MIN_SHARED_SPACE, MAX_SHARED_SPACE, HEARTBEAT_INTERVAL, BLOCK_SIZE, USER_SHARED_DIRECTORY
)
from common.protocol import MessageType, receive_message, send_message
from node.storage import BlockStorage
from common.utils import ensure_directory

class Node:
    """Nodo del sistema distribuido"""
    
    def __init__(self, node_id: Optional[str] = None, shared_space_size: Optional[int] = None, coordinator_host: Optional[str] = None):
        # Si no se proporciona node_id, buscar en el directorio compartido del usuario
        if node_id is None:
            node_id = self._find_or_create_node_id()
        
        self.node_id = node_id
        
        # Validar tamaño del espacio compartido
        if shared_space_size:
            if shared_space_size < MIN_SHARED_SPACE or shared_space_size > MAX_SHARED_SPACE:
                raise ValueError(f"El espacio compartido debe estar entre {MIN_SHARED_SPACE//(1024*1024)} y {MAX_SHARED_SPACE//(1024*1024)} MB")
            self.shared_space_size = shared_space_size
        else:
            self.shared_space_size = MIN_SHARED_SPACE
        
        self.coordinator_host = coordinator_host or COORDINATOR_HOST
        
        # Usar directorio compartido del usuario
        self.shared_space_path = os.path.join(USER_SHARED_DIRECTORY, self.node_id, SHARED_DIRECTORY)
        ensure_directory(self.shared_space_path)
        
        # Almacenamiento de bloques
        self.storage = BlockStorage(self.node_id, self.shared_space_path, self.shared_space_size)
        
        # Conexión con coordinador
        self.coordinator_socket: Optional[socket.socket] = None
        self.running = False
        
        # Threads
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.listener_thread: Optional[threading.Thread] = None
        
        # Socket para recibir conexiones del coordinador
        self.listener_socket: Optional[socket.socket] = None
        self.listener_port = 0
    
    def _find_or_create_node_id(self) -> str:
        """
        Busca una carpeta de nodo existente en el directorio compartido del usuario.
        Si existe, retorna el ID. Si no, genera uno nuevo.
        """
        ensure_directory(USER_SHARED_DIRECTORY)
        
        # Buscar carpetas existentes
        try:
            if os.path.exists(USER_SHARED_DIRECTORY):
                subdirs = [d for d in os.listdir(USER_SHARED_DIRECTORY) 
                          if os.path.isdir(os.path.join(USER_SHARED_DIRECTORY, d))]
                
                # Si hay carpetas, usar la primera (asumiendo que es un nodo registrado)
                if subdirs:
                    found_id = subdirs[0]
                    print(f"[*] Nodo encontrado: {found_id}")
                    return found_id
        except Exception as e:
            print(f"[!] Error al buscar nodos existentes: {e}")
        
        # Si no hay nodos, generar uno nuevo
        new_node_id = f"node_{uuid.uuid4().hex[:8]}"
        print(f"[*] Nuevo nodo creado: {new_node_id}")
        return new_node_id
    
    def start(self):
        """Inicia el nodo"""
        # Conectar con coordinador
        try:
            self.coordinator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.coordinator_socket.connect((self.coordinator_host, COORDINATOR_PORT))
            
            # Iniciar socket listener para recibir comandos del coordinador
            self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener_socket.bind(('', 0))
            self.listener_port = self.listener_socket.getsockname()[1]
            self.listener_socket.listen(5)
            
            # Registrar nodo en coordinador
            self.register_with_coordinator()
            
            self.running = True
            
            # Iniciar thread de heartbeat
            self.heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
            self.heartbeat_thread.start()
            
            # Iniciar thread listener para comandos del coordinador
            self.listener_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
            self.listener_thread.start()
            
            print(f"Nodo {self.node_id} iniciado")
            print(f"Espacio compartido: {self.shared_space_size / (1024*1024):.2f} MB")
            print(f"Puerto listener: {self.listener_port}")
            
            # Mantener conexión activa
            self.handle_coordinator_messages()
            
        except Exception as e:
            print(f"Error iniciando nodo: {e}")
            self.stop()
    
    def register_with_coordinator(self):
        """Registra el nodo con el coordinador"""
        try:
            # Intentar obtener IP local conectándose a un servidor externo
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "127.0.0.1"
        
        # Enviar registro sin node_id (o con None) para que el coordinador lo asigne
        send_message(self.coordinator_socket, MessageType.NODE_REGISTER, {
            "node_id": self.node_id if self.node_id and self.node_id.startswith("nodo") else None,
            "address": local_ip,
            "port": self.listener_port,
            "shared_space_size": self.shared_space_size
        })
        
        # Esperar respuesta
        response = receive_message(self.coordinator_socket)
        if response and response.get("type") == MessageType.REGISTER_RESPONSE.value:
            data = response.get("data", {})
            if data.get("success"):
                # Actualizar el node_id con el asignado por el coordinador
                assigned_id = data.get("node_id")
                if assigned_id:
                    self.node_id = assigned_id
                    print(f"Nodo registrado exitosamente como: {self.node_id}")
                    print(f"Total de bloques en el sistema: {data.get('total_blocks', 0)}")
                else:
                    print(f"Nodo registrado exitosamente. Total de bloques: {data.get('total_blocks', 0)}")
            else:
                print("Error registrando nodo")
    
    def send_heartbeat(self):
        """Envía heartbeat periódico al coordinador"""
        while self.running:
            try:
                if self.coordinator_socket:
                    send_message(self.coordinator_socket, MessageType.NODE_HEARTBEAT, {
                        "node_id": self.node_id
                    })
            except:
                pass
            time.sleep(HEARTBEAT_INTERVAL)
    
    def listen_for_commands(self):
        """Escucha comandos del coordinador"""
        while self.running:
            try:
                if self.listener_socket:
                    client_socket, address = self.listener_socket.accept()
                    threading.Thread(target=self.handle_coordinator_command, 
                                   args=(client_socket,), daemon=True).start()
            except:
                pass
    
    def handle_coordinator_command(self, client_socket: socket.socket):
        """Maneja comandos del coordinador"""
        try:
            while self.running:
                message = receive_message(client_socket)
                if not message:
                    break
                
                msg_type = MessageType(message["type"])
                data = message.get("data", {})
                
                if msg_type == MessageType.STORE_BLOCK:
                    self.handle_store_block(client_socket, data)
                elif msg_type == MessageType.RETRIEVE_BLOCK:
                    self.handle_retrieve_block(client_socket, data)
                elif msg_type == MessageType.DELETE_BLOCK:
                    self.handle_delete_block(client_socket, data)
                elif msg_type == MessageType.UPDATE_BLOCK_TABLE:
                    # Actualizar tabla de bloques local si es necesario
                    pass
                
        except Exception as e:
            print(f"Error manejando comando del coordinador: {e}")
        finally:
            client_socket.close()
    
    def handle_store_block(self, client_socket: socket.socket, data: dict):
        """Almacena bloques recibidos del coordinador"""
        blocks = data.get("blocks", [])
        stored_count = 0
        
        for block_info in blocks:
            block_id = block_info.get("block_id")
            file_id = block_info.get("file_id")
            block_number = block_info.get("block_number")
            block_data_b64 = block_info.get("block_data")
            is_replica = block_info.get("is_replica", False)
            
            try:
                block_data = base64.b64decode(block_data_b64)
                if self.storage.store_block(block_id, file_id, block_number, block_data, is_replica):
                    stored_count += 1
                    # Notificar al coordinador
                    send_message(self.coordinator_socket, MessageType.BLOCK_STORED, {
                        "block_id": block_id,
                        "file_id": file_id,
                        "node_id": self.node_id
                    })
            except Exception as e:
                print(f"Error almacenando bloque {block_id}: {e}")
        
        # Responder al coordinador
        send_message(client_socket, MessageType.SUCCESS, {
            "message": f"Almacenados {stored_count} bloques"
        })
    
    def handle_retrieve_block(self, client_socket: socket.socket, data: dict):
        """Recupera un bloque solicitado"""
        block_id = data.get("block_id")
        file_id = data.get("file_id")
        block_number = data.get("block_number")
        
        # Intentar obtener el bloque (puede ser original o réplica)
        block_data = self.storage.retrieve_block(block_id)
        
        if block_data:
            send_message(client_socket, MessageType.BLOCK_RETRIEVED, {
                "block_id": block_id,
                "file_id": file_id,
                "block_number": block_number,
                "block_data": base64.b64encode(block_data).decode('utf-8')
            })
        else:
            send_message(client_socket, MessageType.ERROR, {
                "message": f"Bloque {block_id} no encontrado"
            })
    
    def handle_delete_block(self, client_socket: socket.socket, data: dict):
        """Elimina un bloque (puede ser original o réplica)"""
        block_id = data.get("block_id")
        file_id = data.get("file_id")
        
        # Eliminar tanto el original como la réplica si existen
        deleted = False
        
        # Intentar eliminar bloque original
        if self.storage.delete_block(block_id):
            deleted = True
        
        # Intentar eliminar réplica (si existe con sufijo _replica)
        # Buscar en los metadatos
        stored_blocks = self.storage.get_stored_blocks()
        for stored_id, info in stored_blocks.items():
            if stored_id == block_id or (block_id in stored_id and file_id == info.get("file_id")):
                if self.storage.delete_block(stored_id):
                    deleted = True
        
        if deleted:
            send_message(client_socket, MessageType.BLOCK_DELETED, {
                "block_id": block_id,
                "file_id": file_id,
                "node_id": self.node_id
            })
        else:
            send_message(client_socket, MessageType.ERROR, {
                "message": f"Error eliminando bloque {block_id}"
            })
    
    def handle_coordinator_messages(self):
        """Maneja mensajes del coordinador en la conexión principal"""
        try:
            while self.running:
                message = receive_message(self.coordinator_socket)
                if not message:
                    break
                # Los comandos principales se manejan en listen_for_commands
        except:
            pass
    
    def stop(self):
        """Detiene el nodo"""
        self.running = False
        
        # Notificar desconexión al coordinador
        if self.coordinator_socket:
            try:
                send_message(self.coordinator_socket, MessageType.NODE_DISCONNECT, {
                    "node_id": self.node_id
                })
                self.coordinator_socket.close()
            except:
                pass
        
        if self.listener_socket:
            try:
                self.listener_socket.close()
            except:
                pass
        
        print(f"Nodo {self.node_id} detenido")

if __name__ == "__main__":
    import sys
    
    node_id = sys.argv[1] if len(sys.argv) > 1 else None
    space_size = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    node = Node(node_id, space_size)
    try:
        node.start()
    except KeyboardInterrupt:
        print("\nDeteniendo nodo...")
        node.stop()

