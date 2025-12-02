"""
Utilidades comunes
"""
import os
import hashlib
import shutil
from pathlib import Path

def ensure_directory(path):
    """Asegura que un directorio existe"""
    Path(path).mkdir(parents=True, exist_ok=True)

def calculate_file_hash(file_path):
    """Calcula el hash MD5 de un archivo"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_size(file_path):
    """Obtiene el tamaño de un archivo"""
    return os.path.getsize(file_path)

def split_file_into_blocks(file_path, block_size):
    """Divide un archivo en bloques de tamaño especificado"""
    blocks = []
    with open(file_path, "rb") as f:
        block_num = 0
        while True:
            block_data = f.read(block_size)
            if not block_data:
                break
            blocks.append((block_num, block_data))
            block_num += 1
    return blocks

def combine_blocks_into_file(blocks, output_path):
    """Combina bloques en un archivo"""
    # Ordenar bloques por número
    blocks.sort(key=lambda x: x[0])
    
    with open(output_path, "wb") as f:
        for _, block_data in blocks:
            f.write(block_data)

def get_directory_size(directory):
    """Obtiene el tamaño total de un directorio"""
    total = 0
    try:
        for entry in os.scandir(directory):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_directory_size(entry.path)
    except PermissionError:
        pass
    return total

def format_size(size_bytes):
    """Formatea el tamaño en bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

