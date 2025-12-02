"""
Programa para limpiar todos los datos del sistema
- Elimina todos los nodos en memoria
- Elimina datos del coordinador (registros, tablas de bloques, archivos)
- Elimina carpetas de nodos
- Restaura el sistema a estado inicial
"""
import os
import json
import shutil
import sys
from pathlib import Path

def get_user_shared_directory():
    """Obtiene la ruta del directorio compartido del usuario actual"""
    username = os.getenv('USERNAME')
    shared_dir = f"C:\\Users\\{username}\\espacioCompartido"
    return shared_dir

def cleanup_coordinator_data():
    """Limpia todos los datos del coordinador"""
    print("[*] Limpiando datos del coordinador...")
    
    coordinator_data_dir = "coordinator_data"
    if os.path.exists(coordinator_data_dir):
        try:
            shutil.rmtree(coordinator_data_dir)
            print(f"    ✓ Eliminado directorio: {coordinator_data_dir}")
        except Exception as e:
            print(f"    ✗ Error al eliminar {coordinator_data_dir}: {e}")
    
    # Limpiar también el directorio de base de datos de Django
    webapp_db = "webapp/db.sqlite3"
    if os.path.exists(webapp_db):
        try:
            os.remove(webapp_db)
            print(f"    ✓ Eliminada base de datos web: {webapp_db}")
        except Exception as e:
            print(f"    ✗ Error al eliminar {webapp_db}: {e}")

def cleanup_local_nodes():
    """Limpia todos los nodos locales en el proyecto"""
    print("[*] Limpiando nodos locales...")
    
    current_dir = os.getcwd()
    
    # Patrones de carpetas de nodos
    node_patterns = ['node_', 'node1']
    
    for item in os.listdir(current_dir):
        item_path = os.path.join(current_dir, item)
        
        # Verificar si es un nodo
        is_node = any(item.startswith(pattern) for pattern in node_patterns)
        
        if is_node and os.path.isdir(item_path):
            try:
                shutil.rmtree(item_path)
                print(f"    ✓ Eliminado nodo local: {item}")
            except Exception as e:
                print(f"    ✗ Error al eliminar nodo {item}: {e}")

def cleanup_user_shared_space():
    """Limpia el directorio compartido del usuario"""
    print("[*] Limpiando directorio compartido del usuario...")
    
    shared_dir = get_user_shared_directory()
    
    if os.path.exists(shared_dir):
        try:
            # Eliminar todo dentro del directorio
            for item in os.listdir(shared_dir):
                item_path = os.path.join(shared_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"    ✓ Eliminada carpeta de nodo: {item}")
                else:
                    os.remove(item_path)
                    print(f"    ✓ Eliminado archivo: {item}")
        except Exception as e:
            print(f"    ✗ Error al limpiar directorio compartido: {e}")
    else:
        print(f"    ℹ Directorio no existe: {shared_dir}")

def cleanup_pycache():
    """Limpia cachés de Python"""
    print("[*] Limpiando cachés de Python...")
    
    for root, dirs, files in os.walk(os.getcwd()):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"    ✓ Eliminado: {pycache_path}")
            except Exception as e:
                print(f"    ✗ Error al eliminar {pycache_path}: {e}")

def confirm_cleanup():
    """Solicita confirmación antes de ejecutar limpieza"""
    print("\n" + "="*70)
    print("⚠️  ADVERTENCIA: Se eliminarán todos los datos del sistema")
    print("="*70)
    print("\nEsto incluye:")
    print("  • Todos los nodos en memoria")
    print("  • Todos los registros del coordinador")
    print("  • Tabla de bloques")
    print("  • Archivos almacenados")
    print("  • Carpetas de nodos en: {}".format(get_user_shared_directory()))
    print("\n¿Está seguro de que desea continuar? (sí/no): ", end="")
    
    response = input().strip().lower()
    return response in ['sí', 'si', 'yes', 's', 'y']

def main():
    """Función principal"""
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║                    LIMPIEZA DEL SISTEMA DISTRIBUIDO              ║")
    print("╚════════════════════════════════════════════════════════════════════╝\n")
    
    if not confirm_cleanup():
        print("\n[✓] Limpieza cancelada")
        return
    
    print("\n[*] Iniciando limpieza...\n")
    
    try:
        cleanup_coordinator_data()
        cleanup_local_nodes()
        cleanup_user_shared_space()
        cleanup_pycache()
        
        print("\n" + "="*70)
        print("✓ LIMPIEZA COMPLETADA EXITOSAMENTE")
        print("="*70)
        print("\nEl sistema está listo para comenzar de cero.")
        print("  • Directorio compartido: {}".format(get_user_shared_directory()))
        
    except Exception as e:
        print(f"\n✗ Error durante la limpieza: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
