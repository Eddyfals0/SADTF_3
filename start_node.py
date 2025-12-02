#!/usr/bin/env python3
"""
Script para iniciar un nodo
"""
import sys
import os
import argparse

# Añadir directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from node.node import Node
from config import MIN_SHARED_SPACE, MAX_SHARED_SPACE

def parse_size(size_str):
    """Parsea tamaño en formato '50MB' o '50' (asume MB)"""
    size_str = size_str.upper().strip()
    if size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    else:
        # Asumir MB
        return int(size_str) * 1024 * 1024

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Iniciar un nodo del sistema distribuido')
    parser.add_argument('--space', type=str, 
                       help=f'Espacio compartido (ej: 50MB, 70MB). Rango: {MIN_SHARED_SPACE//(1024*1024)}-{MAX_SHARED_SPACE//(1024*1024)} MB',
                       default=f"{MIN_SHARED_SPACE//(1024*1024)}MB",
                       required=True)
    parser.add_argument('--coordinator-host', type=str, 
                       help='Dirección IP del coordinador (ej: 192.168.1.100). Por defecto: localhost',
                       default=None)
    
    args = parser.parse_args()
    
    try:
        space_size = parse_size(args.space)
        
        if space_size < MIN_SHARED_SPACE or space_size > MAX_SHARED_SPACE:
            print(f"Error: El espacio debe estar entre {MIN_SHARED_SPACE//(1024*1024)} y {MAX_SHARED_SPACE//(1024*1024)} MB")
            sys.exit(1)
    except ValueError:
        print("Error: Tamaño de espacio inválido. Use formato como '50MB' o '70'")
        sys.exit(1)
    
    print("=" * 60)
    print("SISTEMA DE ARCHIVOS DISTRIBUIDO - NODO")
    print("=" * 60)
    print(f"ID del Nodo: Será asignado por el coordinador")
    print(f"Espacio Compartido: {space_size // (1024*1024)} MB")
    print(f"Coordinador: {args.coordinator_host or 'localhost (por defecto)'}")
    print("Presione Ctrl+C para detener")
    print("=" * 60)
    
    node = Node(None, space_size, args.coordinator_host)
    try:
        node.start()
    except KeyboardInterrupt:
        print("\n\nDeteniendo nodo...")
        node.stop()
        print("Nodo detenido.")

