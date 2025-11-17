import redis
import os
import json
from dotenv import load_dotenv

# === Cargar variables de entorno desde /docker/.env ===
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "docker", ".env"))

# Crear conexión a Redis usando contraseña
r = redis.Redis(
    host='redis',              # usar el nombre del servicio de Docker Compose
    port=6379,
    password=os.getenv("REDIS_PASSWORD","redis123"),
    decode_responses=True
)

# --- Limpieza general (solo desarrollo) ---
def flush_all():
    """Elimina todas las claves de Redis."""
    r.flushall()

# --- Usuarios conectados ---
def add_connected_user(usuario_id):
    """Agrega un usuario a la lista de conectados."""
    r.sadd("usuarios_conectados", usuario_id)

def remove_connected_user(usuario_id):
    """Quita un usuario de la lista de conectados."""
    r.srem("usuarios_conectados", usuario_id)

def get_connected_users():
    """Retorna la lista de usuarios conectados."""
    return list(r.smembers("usuarios_conectados"))

# --- Búsquedas recientes por usuario ---
def push_recent_search(usuario_id, search_term, max_items=5):
    """Agrega una búsqueda reciente a la lista del usuario (tipo lista)."""
    key = f"recent_search:{usuario_id}"
    r.lpush(key, search_term)
    r.ltrim(key, 0, max_items-1)

def get_recent_searches(usuario_id):
    """Devuelve las búsquedas recientes del usuario."""
    key = f"recent_search:{usuario_id}"
    return r.lrange(key, 0, -1)

# --- Reservas temporales ---
def create_temp_reservation(reserva_id, reserva_data):
    """Crea una reserva temporal en Redis."""
    key = f"temp_reserva:{reserva_id}"
    r.set(key, json.dumps(reserva_data))

def get_temp_reservation(reserva_id):
    """Obtiene una reserva temporal."""
    key = f"temp_reserva:{reserva_id}"
    data = r.get(key)
    return json.loads(data) if data else None

def delete_temp_reservation(reserva_id):
    """Elimina una reserva temporal."""
    key = f"temp_reserva:{reserva_id}"
    r.delete(key)

def get_all_temp_reservations():
    """Devuelve todas las reservas temporales almacenadas en Redis."""
    keys = r.keys("temp_reserva:*")
    reservas = []

    for key in keys:
        data = r.get(key)
        if data:
            reservas.append(json.loads(data))

    return reservas

# --- Cache de resultados de consultas (TTL opcional) ---
def cache_query_result(key, data, ttl_seconds=None):
    """Guarda resultados en cache con TTL opcional."""
    r.set(key, json.dumps(data))
    if ttl_seconds:
        r.expire(key, ttl_seconds)

def get_cached_query(key):
    """Obtiene resultados cacheados."""
    data = r.get(key)
    return json.loads(data) if data else None