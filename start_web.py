#!/usr/bin/env python3
"""
Script para iniciar el servidor web Django
"""
import os
import sys
import subprocess
import argparse
import json

# Cambiar al directorio webapp
webapp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webapp')
os.chdir(webapp_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Iniciar servidor web Django')
    parser.add_argument('--coordinator-host', type=str, 
                       help='Dirección IP del coordinador (ej: 192.168.1.100). Por defecto: localhost',
                       default='127.0.0.1')
    
    args = parser.parse_args()
    
    # Guardar la IP del coordinador en un archivo de configuración
    config_file = os.path.join(webapp_dir, 'coordinator_config.json')
    with open(config_file, 'w') as f:
        json.dump({'coordinator_host': args.coordinator_host}, f)
    
    print("=" * 60)
    print("SISTEMA DE ARCHIVOS DISTRIBUIDO - INTERFAZ WEB")
    print("=" * 60)
    print("Iniciando servidor web Django...")
    print(f"Coordinador configurado en: {args.coordinator_host}:8888")
    print("=" * 60)
    print("\nEl servidor estará disponible en:")
    print("  - Local: http://127.0.0.1:8000")
    print("  - Red: http://TU_IP:8000 (accesible desde otras PCs)")
    print("\nPresiona Ctrl+C para detener el servidor")
    print("=" * 60)

    # Ejecutar Django en todas las interfaces (0.0.0.0) para aceptar conexiones externas
    try:
        subprocess.run([sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'], check=True)
    except KeyboardInterrupt:
        print("\n\nServidor detenido.")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nAsegúrate de haber instalado Django:")
        print("  pip install Django")

