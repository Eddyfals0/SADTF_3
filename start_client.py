#!/usr/bin/env python3
"""
Script para iniciar el cliente GUI
"""
import sys
import os

# Añadir directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import tkinter as tk
except ImportError:
    print("Error: tkinter no está disponible.")
    print("Por favor instale tkinter:")
    print("  Ubuntu/Debian: sudo apt-get install python3-tk")
    print("  Windows: tkinter viene incluido con Python")
    print("  macOS: tkinter viene incluido con Python")
    sys.exit(1)

from client.gui import DistributedFileSystemGUI

if __name__ == "__main__":
    print("=" * 60)
    print("SISTEMA DE ARCHIVOS DISTRIBUIDO - CLIENTE GUI")
    print("=" * 60)
    print("Iniciando interfaz gráfica...")
    print("=" * 60)
    
    root = tk.Tk()
    app = DistributedFileSystemGUI(root)
    root.mainloop()

