"""
Módulo de almacenamiento de bloques en nodos
"""
import os
import json
from typing import Optional, Dict
from pathlib import Path

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SHARED_DIRECTORY, BLOCK_SIZE
from common.utils import ensure_directory, get_directory_size

class BlockStorage:
    """Gestión de almacenamiento de bloques en un nodo"""
    
    def __init__(self, node_id: str, shared_space_path: str, max_size: int):
        self.node_id = node_id
        self.shared_space_path = shared_space_path
        self.max_size = max_size
        self.blocks: Dict[str, Dict] = {}  # block_id -> info
        
        ensure_directory(shared_space_path)
        
        # Cargar metadatos de bloques almacenados
        self.load_metadata()
    
    def load_metadata(self):
        """Carga metadatos de bloques almacenados"""
        metadata_file = os.path.join(self.shared_space_path, ".metadata.json")
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    self.blocks = json.load(f)
            except:
                self.blocks = {}
    
    def save_metadata(self):
        """Guarda metadatos de bloques"""
        metadata_file = os.path.join(self.shared_space_path, ".metadata.json")
        try:
            with open(metadata_file, 'w') as f:
                json.dump(self.blocks, f, indent=2)
        except Exception as e:
            print(f"Error guardando metadatos: {e}")
    
    def get_available_space(self) -> int:
        """Obtiene espacio disponible"""
        used = get_directory_size(self.shared_space_path)
        return max(0, self.max_size - used)
    
    def can_store_block(self, block_size: int) -> bool:
        """Verifica si se puede almacenar un bloque"""
        return self.get_available_space() >= block_size
    
    def store_block(self, block_id: int, file_id: str, block_number: int, 
                   block_data: bytes, is_replica: bool = False) -> bool:
        """Almacena un bloque"""
        if not self.can_store_block(len(block_data)):
            return False
        
        block_filename = f"block_{block_id}_{file_id}_{block_number}.dat"
        block_path = os.path.join(self.shared_space_path, block_filename)
        
        try:
            with open(block_path, 'wb') as f:
                f.write(block_data)
            
            # Guardar metadatos
            self.blocks[str(block_id)] = {
                "block_id": block_id,
                "file_id": file_id,
                "block_number": block_number,
                "filename": block_filename,
                "size": len(block_data),
                "is_replica": is_replica
            }
            
            self.save_metadata()
            return True
        except Exception as e:
            print(f"Error almacenando bloque {block_id}: {e}")
            return False
    
    def retrieve_block(self, block_id: int) -> Optional[bytes]:
        """Recupera un bloque"""
        block_info = self.blocks.get(str(block_id))
        if not block_info:
            return None
        
        block_path = os.path.join(self.shared_space_path, block_info["filename"])
        if not os.path.exists(block_path):
            return None
        
        try:
            with open(block_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Error recuperando bloque {block_id}: {e}")
            return None
    
    def delete_block(self, block_id: int) -> bool:
        """Elimina un bloque"""
        block_info = self.blocks.get(str(block_id))
        if not block_info:
            return False
        
        block_path = os.path.join(self.shared_space_path, block_info["filename"])
        
        try:
            if os.path.exists(block_path):
                os.remove(block_path)
            del self.blocks[str(block_id)]
            self.save_metadata()
            return True
        except Exception as e:
            print(f"Error eliminando bloque {block_id}: {e}")
            return False
    
    def delete_file_blocks(self, file_id: str) -> int:
        """Elimina todos los bloques de un archivo"""
        deleted = 0
        blocks_to_delete = [bid for bid, info in self.blocks.items() 
                           if info.get("file_id") == file_id]
        
        for block_id in blocks_to_delete:
            if self.delete_block(int(block_id)):
                deleted += 1
        
        return deleted
    
    def get_stored_blocks(self) -> Dict:
        """Obtiene información de todos los bloques almacenados"""
        return self.blocks.copy()

