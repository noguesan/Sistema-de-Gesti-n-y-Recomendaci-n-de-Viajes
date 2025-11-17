# Este archivo contiene funciones generales o compartidas por todo el sistema.

import json
import os
import csv
from bson import ObjectId
from config_paths import DATA_DIR

from funciones_redis import r
from funciones_mongo import insertar_documento

# === Lectura de archivos ===

def cargar_json(nombre_archivo):
    """
    Lee un archivo JSON desde la carpeta /data y devuelve su contenido.
    Ejemplo: cargar_json("usuarios.json")
    """
    ruta = os.path.join(DATA_DIR, nombre_archivo)
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)

def cargar_csv(nombre_archivo):
    """
    Carga un archivo CSV desde la carpeta /data y devuelve una lista de diccionarios.
    Cada fila del CSV se convierte en un diccionario con los nombres de las columnas como claves.
    """
    ruta = os.path.join(DATA_DIR, nombre_archivo)
    with open(ruta, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)
    
# === funciones que usan mas de una base de datos ===
def confirmar_reserva_temporal(reserva_id):
    """
    Pasa una reserva desde Redis a MongoDB.
    - Si se inserta correctamente en MongoDB → elimina la temporal.
    - Si falla (ej: reserva_id duplicado) → NO borra nada.
    """
    key = f"temp_reserva:{reserva_id}"
    data = r.get(key)

    if not data:
        print("⚠️ No existe la reserva temporal en Redis.")
        return False

    reserva = json.loads(data)

    try:
        insertar_documento("reservas", reserva)
        # Si se insertó bien, se borra de Redis
        r.delete(key)
        print("✅ Reserva confirmada y movida a MongoDB.")
        return True

    except Exception as e:
        print("⚠️ Error al confirmar reserva:", e)
        return False

