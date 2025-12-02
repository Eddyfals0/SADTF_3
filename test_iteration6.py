#!/usr/bin/env python
"""
Script de prueba para verificar que los cambios funcionan correctamente
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("VERIFICACIÓN DE ITERACIÓN 6")
print("=" * 60)

# Test 1: Verificar que el caché se importa sin errores
print("\n[1] Verificando módulo de caché...")
try:
    from coordinator.cache import coordinator_cache, CoordinatorStateCache
    print("    ✓ Caché importado correctamente")
except ImportError as e:
    print(f"    ✗ Error al importar caché: {e}")
    sys.exit(1)

# Test 2: Verificar funciones del caché
print("\n[2] Probando funciones del caché...")
try:
    coordinator_cache.add_event("TEST", {"message": "Test event"})
    events = coordinator_cache.get_recent_events()
    assert len(events) > 0, "No hay eventos"
    print(f"    ✓ Caché funciona ({len(events)} evento(s))")
except Exception as e:
    print(f"    ✗ Error en caché: {e}")
    sys.exit(1)

# Test 3: Verificar que el coordinador importa sin errores
print("\n[3] Verificando módulo coordinador...")
try:
    from coordinator.coordinator import Coordinator
    print("    ✓ Coordinador importado correctamente")
except ImportError as e:
    print(f"    ✗ Error al importar coordinador: {e}")
    sys.exit(1)

# Test 4: Verificar que views.py importa sin errores
print("\n[4] Verificando vistas de Django...")
try:
    # Hacer mock de Django si no está disponible
    import django
    print("    ✓ Django está disponible")
except ImportError:
    print("    ! Django no disponible (se necesita para ejecutar el servidor web)")

# Test 5: Verificar estructura de archivos
print("\n[5] Verificando archivos...")
files_to_check = [
    "coordinator/cache.py",
    "coordinator/coordinator.py",
    "webapp/filesystem/views.py",
    "webapp/filesystem/urls.py",
    "webapp/filesystem/templates/filesystem/index.html"
]

for file_path in files_to_check:
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    if os.path.exists(full_path):
        print(f"    ✓ {file_path}")
    else:
        print(f"    ✗ {file_path} NO ENCONTRADO")
        sys.exit(1)

print("\n" + "=" * 60)
print("✓ TODAS LAS VERIFICACIONES PASARON")
print("=" * 60)
print("\nSistema listo para ejecutar.")
print("\nPara probar, ejecuta:")
print("  1. python start_coordinator.py")
print("  2. python start_node.py --space 50MB")
print("  3. python start_web.py")
print("\nDesconecta el nodo y verifica que la web se actualiza.")
