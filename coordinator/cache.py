"""
Caché global de estado del coordinador para que Django pueda acceder
"""
import threading
import time

class CoordinatorStateCache:
    """Mantiene caché del estado del coordinador"""
    
    def __init__(self):
        self.recent_events = []
        self.events_lock = threading.Lock()
    
    def add_event(self, event_type: str, event_data: dict):
        """Agrega un evento reciente"""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": event_data
        }
        with self.events_lock:
            self.recent_events.append(event)
            # Mantener solo los últimos 50 eventos
            if len(self.recent_events) > 50:
                self.recent_events = self.recent_events[-50:]
    
    def get_recent_events(self) -> list:
        """Obtiene los eventos recientes"""
        with self.events_lock:
            return list(self.recent_events)
    
    def get_events_since(self, timestamp: float) -> list:
        """Obtiene eventos desde un cierto timestamp"""
        with self.events_lock:
            return [e for e in self.recent_events if e["timestamp"] > timestamp]
    
    def clear_events(self):
        """Limpia los eventos"""
        with self.events_lock:
            self.recent_events = []

# Instancia global
coordinator_cache = CoordinatorStateCache()
