"""
Protocolo de comunicación entre coordinador, nodos y clientes
"""
import json
import struct
from enum import Enum

class MessageType(Enum):
    """Tipos de mensajes del protocolo"""
    # Mensajes del nodo al coordinador
    NODE_REGISTER = "NODE_REGISTER"
    NODE_HEARTBEAT = "NODE_HEARTBEAT"
    NODE_DISCONNECT = "NODE_DISCONNECT"
    BLOCK_STORED = "BLOCK_STORED"
    BLOCK_RETRIEVED = "BLOCK_RETRIEVED"
    BLOCK_DELETED = "BLOCK_DELETED"
    
    # Mensajes del coordinador al nodo
    REGISTER_RESPONSE = "REGISTER_RESPONSE"
    STORE_BLOCK = "STORE_BLOCK"
    RETRIEVE_BLOCK = "RETRIEVE_BLOCK"
    DELETE_BLOCK = "DELETE_BLOCK"
    UPDATE_BLOCK_TABLE = "UPDATE_BLOCK_TABLE"
    
    # Mensajes del cliente al coordinador
    UPLOAD_FILE = "UPLOAD_FILE"
    DOWNLOAD_FILE = "DOWNLOAD_FILE"
    DELETE_FILE = "DELETE_FILE"
    LIST_FILES = "LIST_FILES"
    GET_FILE_INFO = "GET_FILE_INFO"
    GET_BLOCK_TABLE = "GET_BLOCK_TABLE"
    GET_ACTIVE_NODES = "GET_ACTIVE_NODES"
    
    # Mensajes del coordinador al cliente
    UPLOAD_RESPONSE = "UPLOAD_RESPONSE"
    DOWNLOAD_RESPONSE = "DOWNLOAD_RESPONSE"
    DELETE_RESPONSE = "DELETE_RESPONSE"
    FILE_LIST = "FILE_LIST"
    FILE_INFO = "FILE_INFO"
    BLOCK_TABLE_DATA = "BLOCK_TABLE_DATA"
    ACTIVE_NODES_DATA = "ACTIVE_NODES_DATA"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"

def create_message(msg_type: MessageType, data: dict = None):
    """Crea un mensaje serializado"""
    message = {
        "type": msg_type.value,
        "data": data or {}
    }
    json_msg = json.dumps(message).encode('utf-8')
    # Prefijo con longitud del mensaje (4 bytes)
    length = struct.pack('!I', len(json_msg))
    return length + json_msg

def receive_message(socket):
    """Recibe un mensaje completo del socket"""
    # Leer longitud del mensaje (4 bytes)
    length_data = b''
    while len(length_data) < 4:
        chunk = socket.recv(4 - len(length_data))
        if not chunk:
            return None
        length_data += chunk
    
    length = struct.unpack('!I', length_data)[0]
    
    # Leer el mensaje completo
    message_data = b''
    while len(message_data) < length:
        chunk = socket.recv(length - len(message_data))
        if not chunk:
            return None
        message_data += chunk
    
    return json.loads(message_data.decode('utf-8'))

def send_message(socket, msg_type: MessageType, data: dict = None):
    """Envía un mensaje a través del socket"""
    message = create_message(msg_type, data)
    socket.sendall(message)

