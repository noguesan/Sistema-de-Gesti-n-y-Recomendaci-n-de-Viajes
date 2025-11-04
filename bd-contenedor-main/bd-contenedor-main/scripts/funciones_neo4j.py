from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# === Cargar variables de entorno desde /docker/.env ===
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "docker", ".env"))

# === Datos de conexión ===
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j123")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")

# === Conexión con Neo4j ===
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
except Exception as e:
    driver = None
    print("❌ Error al conectar con Neo4j:", e)


# ======================================================
# FUNCIONES PRINCIPALES
# ======================================================

def crear_constraint_unico(label, propiedad):
    """
    Crea un constraint de unicidad en la propiedad indicada (si no existe).
    Evita duplicados al hacer MERGE.
    """
    query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{propiedad} IS UNIQUE"
    with driver.session() as session:
        session.run(query)
    print(f"🧩 Constraint de unicidad asegurado: ({label}.{propiedad})")


def crear_nodo(tx, label, propiedades):
    """
    Crea un nodo (MERGE) usando solo su propiedad ID.
    """
    if not propiedades:
        return
    clave_id = list(propiedades.keys())[0]
    query = f"MERGE (n:{label} {{{clave_id}: ${clave_id}}})"
    tx.run(query, **propiedades)


def insertar_varios_nodos(label, lista_nodos):
    """
    Inserta múltiples nodos (usando MERGE) y asegura constraints únicos.
    """
    if not lista_nodos:
        print(f"[ADVERTENCIA] No hay nodos para insertar en '{label}'.")
        return

    propiedad_id = list(lista_nodos[0].keys())[0]
    crear_constraint_unico(label, propiedad_id)

    with driver.session() as session:
        for nodo in lista_nodos:
            session.execute_write(crear_nodo, label, nodo)
    print(f"✅ Se insertaron {len(lista_nodos)} nodos en '{label}' (solo IDs).")


def crear_relacion(tx, label_origen, prop_origen, valor_origen,
                   label_destino, prop_destino, valor_destino,
                   tipo_relacion):
    """
    Crea una relación dirigida entre dos nodos (si ambos existen).
    """
    query = (
        f"MATCH (a:{label_origen} {{{prop_origen}: $valor_origen}}), "
        f"(b:{label_destino} {{{prop_destino}: $valor_destino}}) "
        f"MERGE (a)-[r:{tipo_relacion}]->(b)"
    )
    tx.run(query, valor_origen=valor_origen, valor_destino=valor_destino)


def insertar_varias_relaciones(lista_relaciones):
    """
    Inserta múltiples relaciones entre nodos.
    """
    if not lista_relaciones:
        print("[ADVERTENCIA] Lista vacía: no se insertaron relaciones.")
        return

    with driver.session() as session:
        for rel in lista_relaciones:
            session.execute_write(
                crear_relacion,
                rel["label_origen"], rel["prop_origen"], rel["valor_origen"],
                rel["label_destino"], rel["prop_destino"], rel["valor_destino"],
                rel["tipo"]
            )
    print(f"✅ Se insertaron {len(lista_relaciones)} relaciones.")


# ======================================================
# FUNCIONES DE LIMPIEZA Y GESTIÓN
# ======================================================

def limpiar_base():
    """
    Elimina todos los nodos y relaciones del grafo.
    ⚠️ Usar solo en desarrollo o para reiniciar la base.
    """
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("🧹 Base de datos Neo4j limpiada con éxito.")


def borrar_todo_de_tipo(label):
    """
    Elimina todos los nodos y relaciones de un tipo específico.
    Ejemplo: borrar_todo_de_tipo('Usuario')
    """
    with driver.session() as session:
        session.run(f"MATCH (n:{label}) DETACH DELETE n")
    print(f"🗑️ Todos los nodos del tipo '{label}' fueron eliminados.")


def cerrar_conexion():
    """
    Cierra la conexión con Neo4j de forma segura.
    Usar al finalizar el programa o notebook para liberar recursos.
    """
    if driver:
        driver.close()
        print("🔒 Conexión con Neo4j cerrada correctamente.")


def mostrar_relaciones():
    """
    Muestra todas las relaciones sociales y de visitas.
    """
    if not driver:
        print("❌ No hay conexión activa con Neo4j.")
        return

    def ejecutar_y_mostrar(query, descripcion):
        with driver.session() as session:
            resultados = session.run(query)
            print(f"\n🔹 {descripcion}:")
            encontrados = False
            for r in resultados:
                print(f"  {r['origen']} -[{r['relacion']}]-> {r['destino']}")
                encontrados = True
            if not encontrados:
                print("  (sin resultados)")

    query_sociales = """
    MATCH (u1:Usuario)-[r]->(u2:Usuario)
    RETURN u1.usuario_id AS origen, type(r) AS relacion, u2.usuario_id AS destino
    ORDER BY origen, destino
    """
    ejecutar_y_mostrar(query_sociales, "Relaciones sociales (Usuario ↔ Usuario)")

    query_visitas = """
    MATCH (u:Usuario)-[r:VISITO]->(d:Destino)
    RETURN u.usuario_id AS origen, type(r) AS relacion, d.destino_id AS destino
    ORDER BY origen, destino
    """
    ejecutar_y_mostrar(query_visitas, "Relaciones de visitas (Usuario → Destino)")
