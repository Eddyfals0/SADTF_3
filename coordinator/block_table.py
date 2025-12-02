"""
Tabla de bloques del sistema distribuido
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class BlockStatus(Enum):
    """Estado de un bloque"""
    FREE = "FREE"
    USED = "USED"
    REPLICATED = "REPLICATED"

@dataclass
class BlockEntry:
    """Entrada en la tabla de bloques"""
    block_id: int
    status: BlockStatus
    file_id: str
    block_number: int
    node_id: str
    replica_node_id: Optional[str] = None
    
    def to_dict(self):
        """Convierte la entrada a diccionario"""
        return {
            "block_id": self.block_id,
            "status": self.status.value,
            "file_id": self.file_id,
            "block_number": self.block_number,
            "node_id": self.node_id,
            "replica_node_id": self.replica_node_id
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea una entrada desde un diccionario"""
        return cls(
            block_id=data["block_id"],
            status=BlockStatus(data["status"]),
            file_id=data["file_id"],
            block_number=data["block_number"],
            node_id=data["node_id"],
            replica_node_id=data.get("replica_node_id")
        )

class BlockTable:
    """Tabla de bloques del sistema"""
    
    def __init__(self, total_blocks: int):
        self.total_blocks = total_blocks
        self.blocks: Dict[int, BlockEntry] = {}
        self.file_blocks: Dict[str, List[int]] = {}  # file_id -> lista de block_ids
        
        # Inicializar todos los bloques como libres
        for i in range(total_blocks):
            self.blocks[i] = BlockEntry(
                block_id=i,
                status=BlockStatus.FREE,
                file_id="",
                block_number=-1,
                node_id=""
            )
    
    def allocate_blocks(self, file_id: str, num_blocks: int, available_nodes: List[str]) -> List[Tuple[int, str, str]]:
        """
        Asigna bloques libres para un archivo
        Retorna lista de (block_id, node_id, replica_node_id)
        """
        if len(available_nodes) < 2:
            raise ValueError("Se necesitan al menos 2 nodos para replicación")
        
        allocated = []
        free_blocks = [bid for bid, entry in self.blocks.items() 
                      if entry.status == BlockStatus.FREE]
        
        if len(free_blocks) < num_blocks:
            raise ValueError(f"No hay suficientes bloques libres. Necesarios: {num_blocks}, Disponibles: {len(free_blocks)}")
        
        for i in range(num_blocks):
            block_id = free_blocks[i]
            # Seleccionar nodos diferentes para original y réplica
            node_idx = i % len(available_nodes)
            replica_idx = (i + 1) % len(available_nodes)
            node_id = available_nodes[node_idx]
            replica_node_id = available_nodes[replica_idx]
            
            # Actualizar entrada del bloque
            self.blocks[block_id] = BlockEntry(
                block_id=block_id,
                status=BlockStatus.REPLICATED,
                file_id=file_id,
                block_number=i,
                node_id=node_id,
                replica_node_id=replica_node_id
            )
            
            allocated.append((block_id, node_id, replica_node_id))
        
        # Registrar bloques del archivo
        if file_id not in self.file_blocks:
            self.file_blocks[file_id] = []
        self.file_blocks[file_id].extend([bid for bid, _, _ in allocated])
        
        return allocated
    
    def free_blocks(self, file_id: str):
        """Libera todos los bloques de un archivo"""
        if file_id not in self.file_blocks:
            return
        
        for block_id in self.file_blocks[file_id]:
            if block_id in self.blocks:
                self.blocks[block_id] = BlockEntry(
                    block_id=block_id,
                    status=BlockStatus.FREE,
                    file_id="",
                    block_number=-1,
                    node_id=""
                )
        
        del self.file_blocks[file_id]
    
    def get_file_blocks(self, file_id: str) -> List[BlockEntry]:
        """Obtiene todas las entradas de bloques de un archivo"""
        if file_id not in self.file_blocks:
            return []
        
        return [self.blocks[bid] for bid in self.file_blocks[file_id] 
                if bid in self.blocks]
    
    def get_block_info(self, block_id: int) -> Optional[BlockEntry]:
        """Obtiene información de un bloque específico"""
        return self.blocks.get(block_id)
    
    def get_all_blocks(self) -> List[BlockEntry]:
        """Obtiene todas las entradas de la tabla"""
        return list(self.blocks.values())
    
    def get_free_blocks_count(self) -> int:
        """Cuenta bloques libres"""
        return sum(1 for entry in self.blocks.values() 
                   if entry.status == BlockStatus.FREE)
    
    def to_dict(self):
        """Convierte la tabla completa a diccionario"""
        return {
            "total_blocks": self.total_blocks,
            "free_blocks": self.get_free_blocks_count(),
            "used_blocks": self.total_blocks - self.get_free_blocks_count(),
            "blocks": [entry.to_dict() for entry in self.blocks.values()],
            "file_blocks": self.file_blocks
        }
    
    def update_block_node(self, block_id: int, new_node_id: str, is_replica: bool = False):
        """Actualiza el nodo de un bloque (útil cuando un nodo falla)"""
        if block_id in self.blocks:
            entry = self.blocks[block_id]
            if is_replica:
                entry.replica_node_id = new_node_id
            else:
                entry.node_id = new_node_id

