#!/usr/bin/env python3
"""
Script para iniciar el coordinador
"""
import sys
import os

# Añadir directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from coordinator.coordinator import Coordinator
from config import COORDINATOR_PORT

if __name__ == "__main__":
    print("=" * 60)
    print("SISTEMA DE ARCHIVOS DISTRIBUIDO - COORDINADOR")
    print("=" * 60)
    print(f"Iniciando coordinador en puerto {COORDINATOR_PORT}...")
    print("Presione Ctrl+C para detener")
    print("=" * 60)
    
    coordinator = Coordinator()
    try:
        coordinator.start()
    except KeyboardInterrupt:
        print("\n\nDeteniendo coordinador...")
        coordinator.stop()
        print("Coordinador detenido.")

