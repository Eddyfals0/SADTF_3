"""
Tabla de bloques del sistema distribuido con IDs tipo paginación
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
    """Entrada en la tabla de bloques con estructura tipo lista ligada"""
    block_id: str  # Formato: "nodo{numero}bloque{numero}" ej: "nodo1001"
    status: BlockStatus
    file_id: str
    block_number: int  # Número de bloque dentro del archivo
    primary_node_id: str  # Nodo donde está el bloque original
    replica_node_id: Optional[str] = None  # Nodo donde está la réplica
    next_block_id: Optional[str] = None  # Para estructura tipo lista ligada
    
    def to_dict(self):
        """Convierte la entrada a diccionario"""
        return {
            "block_id": self.block_id,
            "status": self.status.value,
            "file_id": self.file_id,
            "block_number": self.block_number,
            "primary_node_id": self.primary_node_id,
            "replica_node_id": self.replica_node_id,
            "next_block_id": self.next_block_id
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea una entrada desde un diccionario"""
        return cls(
            block_id=data["block_id"],
            status=BlockStatus(data["status"]),
            file_id=data["file_id"],
            block_number=data["block_number"],
            primary_node_id=data.get("primary_node_id", data.get("node_id", "")),
            replica_node_id=data.get("replica_node_id"),
            next_block_id=data.get("next_block_id")
        )

class BlockTable:
    """Tabla de bloques del sistema con IDs tipo paginación"""
    
    def __init__(self, node_blocks: Dict[str, int]):
        """
        Inicializa la tabla de bloques
        node_blocks: Dict[node_id, num_blocks] - número de bloques por nodo
        """
        self.node_blocks = node_blocks.copy()
        self.blocks: Dict[str, BlockEntry] = {}  # block_id -> BlockEntry
        self.file_blocks: Dict[str, List[str]] = {}  # file_id -> lista de block_ids
        self.node_block_ranges: Dict[str, Tuple[int, int]] = {}  # node_id -> (inicio, fin)
        
        # Crear todos los bloques con IDs tipo paginación
        block_counter = 0
        for node_id, num_blocks in sorted(node_blocks.items()):
            node_num = int(node_id.replace("nodo", ""))
            start_block = block_counter
            end_block = block_counter + num_blocks
            
            self.node_block_ranges[node_id] = (start_block, end_block)
            
            # Crear bloques para este nodo: nodo1001, nodo1002, etc.
            for i in range(num_blocks):
                block_num = i + 1
                block_id = f"nodo{node_num}{block_num:03d}"  # nodo1001, nodo1002, etc.
                
                self.blocks[block_id] = BlockEntry(
                    block_id=block_id,
                    status=BlockStatus.FREE,
                    file_id="",
                    block_number=-1,
                    primary_node_id=node_id,
                    replica_node_id=None,
                    next_block_id=None
                )
            
            block_counter += num_blocks
        
        self.total_blocks = block_counter
    
    def get_blocks_for_node(self, node_id: str) -> List[str]:
        """Obtiene todos los block_ids de un nodo"""
        node_num = int(node_id.replace("nodo", ""))
        if node_id not in self.node_block_ranges:
            return []
        
        num_blocks = self.node_blocks[node_id]
        return [f"nodo{node_num}{i+1:03d}" for i in range(num_blocks)]
    
    def allocate_blocks(self, file_id: str, num_blocks: int, available_nodes: List[str]) -> List[Tuple[str, str, str]]:
        """
        Asigna bloques libres para un archivo
        Retorna lista de (block_id, primary_node_id, replica_node_id)
        Usa estructura tipo lista ligada para enlazar bloques del mismo archivo
        """
        if len(available_nodes) < 2:
            raise ValueError("Se necesitan al menos 2 nodos para replicación")
        
        # Obtener bloques libres de todos los nodos disponibles
        free_blocks = []
        for node_id in available_nodes:
            node_blocks = self.get_blocks_for_node(node_id)
            for block_id in node_blocks:
                if block_id in self.blocks and self.blocks[block_id].status == BlockStatus.FREE:
                    free_blocks.append((block_id, node_id))
        
        if len(free_blocks) < num_blocks:
            raise ValueError(f"No hay suficientes bloques libres. Necesarios: {num_blocks}, Disponibles: {len(free_blocks)}")
        
        allocated = []
        
        for i in range(num_blocks):
            # Seleccionar bloque libre
            block_id, primary_node_id = free_blocks[i]
            
            # Seleccionar nodo diferente para réplica (rotación circular)
            replica_node_id = None
            node_idx = available_nodes.index(primary_node_id) if primary_node_id in available_nodes else 0
            
            # Buscar nodo para réplica (rotar por los nodos disponibles)
            for offset in range(1, len(available_nodes)):
                candidate_idx = (node_idx + offset) % len(available_nodes)
                candidate_node = available_nodes[candidate_idx]
                
                if candidate_node != primary_node_id:
                    # Verificar que el nodo candidato tenga bloques libres
                    candidate_blocks = self.get_blocks_for_node(candidate_node)
                    for candidate_block_id in candidate_blocks:
                        if (candidate_block_id in self.blocks and 
                            self.blocks[candidate_block_id].status == BlockStatus.FREE):
                            replica_node_id = candidate_node
                            break
                    if replica_node_id:
                        break
            
            if not replica_node_id:
                # Si no hay nodo disponible para réplica, usar el siguiente en la lista
                replica_node_id = available_nodes[(node_idx + 1) % len(available_nodes)]
            
            # Crear entrada del bloque con lista ligada
            next_block_id = None
            if i < num_blocks - 1:
                # El siguiente bloque será el siguiente en la lista
                if i + 1 < len(free_blocks):
                    next_block_id = free_blocks[i + 1][0]
            
            # Actualizar entrada del bloque
            self.blocks[block_id] = BlockEntry(
                block_id=block_id,
                status=BlockStatus.REPLICATED,
                file_id=file_id,
                block_number=i,
                primary_node_id=primary_node_id,
                replica_node_id=replica_node_id,
                next_block_id=next_block_id
            )
            
            allocated.append((block_id, primary_node_id, replica_node_id))
        
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
                entry = self.blocks[block_id]
                # Mantener la información del nodo primario
                primary_node_id = entry.primary_node_id
                
                self.blocks[block_id] = BlockEntry(
                    block_id=block_id,
                    status=BlockStatus.FREE,
                    file_id="",
                    block_number=-1,
                    primary_node_id=primary_node_id,
                    replica_node_id=None,
                    next_block_id=None
                )
        
        del self.file_blocks[file_id]
    
    def get_file_blocks(self, file_id: str) -> List[BlockEntry]:
        """Obtiene todas las entradas de bloques de un archivo (siguiendo la lista ligada)"""
        if file_id not in self.file_blocks:
            return []
        
        blocks_list = []
        # Obtener el primer bloque
        first_block_id = self.file_blocks[file_id][0] if self.file_blocks[file_id] else None
        
        if first_block_id and first_block_id in self.blocks:
            current_block_id = first_block_id
            visited = set()
            
            # Seguir la lista ligada
            while current_block_id and current_block_id not in visited:
                visited.add(current_block_id)
                if current_block_id in self.blocks:
                    entry = self.blocks[current_block_id]
                    if entry.file_id == file_id:
                        blocks_list.append(entry)
                    current_block_id = entry.next_block_id
                else:
                    break
        
        return blocks_list
    
    def get_block_info(self, block_id: str) -> Optional[BlockEntry]:
        """Obtiene información de un bloque específico"""
        return self.blocks.get(block_id)
    
    def get_all_blocks(self) -> List[BlockEntry]:
        """Obtiene todas las entradas de la tabla"""
        return list(self.blocks.values())
    
    def get_free_blocks_count(self) -> int:
        """Cuenta bloques libres"""
        return sum(1 for entry in self.blocks.values() 
                   if entry.status == BlockStatus.FREE)
    
    def update_node_blocks(self, node_blocks: Dict[str, int]):
        """Actualiza la tabla cuando se agregan o quitan nodos"""
        # Guardar bloques usados
        used_blocks = {}
        for block_id, entry in self.blocks.items():
            if entry.status != BlockStatus.FREE:
                used_blocks[block_id] = entry
        
        # Recrear tabla con nuevos nodos
        self.__init__(node_blocks)
        
        # Restaurar bloques usados
        for block_id, entry in used_blocks.items():
            if block_id in self.blocks:
                self.blocks[block_id] = entry
    
    def to_dict(self):
        """Convierte la tabla completa a diccionario"""
        return {
            "total_blocks": self.total_blocks,
            "free_blocks": self.get_free_blocks_count(),
            "used_blocks": self.total_blocks - self.get_free_blocks_count(),
            "blocks": [entry.to_dict() for entry in self.blocks.values()],
            "file_blocks": self.file_blocks,
            "node_block_ranges": {k: {"start": v[0], "end": v[1]} 
                                 for k, v in self.node_block_ranges.items()}
        }
    
    def update_block_node(self, block_id: str, new_node_id: str, is_replica: bool = False):
        """Actualiza el nodo de un bloque (útil cuando un nodo falla)"""
        if block_id in self.blocks:
            entry = self.blocks[block_id]
            if is_replica:
                entry.replica_node_id = new_node_id
            else:
                entry.primary_node_id = new_node_id
