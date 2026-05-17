# Importa la librería psycopg2 para conectarse y trabajar con PostgreSQL
import psycopg2 # type: ignore
# Importa datetime para registrar la fecha y hora actual
from datetime import datetime


# Diccionario con la configuración necesaria para conectarse a Supabase/PostgreSQL
DB_CONFIG = {
    "host": "aws-1-us-west-1.pooler.supabase.com",  # Dirección del servidor
    "port": 6543,                                   # Puerto de conexión
    "dbname": "postgres",                           # Nombre de la base de datos
    "user": "postgres.qiljbefohyrkfnrrwdcr",        # Usuario de acceso
    "password": "Pintura12_#$"                      # Contraseña del usuario
}


def obtener_conexion():
    """
    Intenta establecer una conexión con la base de datos.
    
    Retorna:
        - conexion: objeto de conexión si todo sale bien
        - None: si ocurre algún error
    """
    try:
        # Se crea la conexión usando los datos del diccionario DB_CONFIG
        conexion = psycopg2.connect(**DB_CONFIG)
        return conexion

    except Exception as e:
        # Si ocurre un error, se muestra en pantalla
        print("Error de conexión:", e)
        return None


def crear_tabla():
    """
    Crea la tabla 'datos_recibidos' si todavía no existe.
    Esta tabla almacenará:
        - id: identificador único
        - origen: quién envió el dato
        - contenido: mensaje o información recibida
        - fecha: fecha y hora de registro
    """

    # Se obtiene una conexión a la base de datos
    conexion = obtener_conexion()

    # Si no se pudo conectar, termina la función
    if conexion is None:
        return

    # Se crea un cursor para ejecutar instrucciones SQL
    cursor = conexion.cursor()

    # Consulta SQL para crear la tabla
    sql = """
    CREATE TABLE IF NOT EXISTS datos_recibidos (
        id SERIAL PRIMARY KEY,
        origen VARCHAR(10),
        contenido TEXT,
        fecha TIMESTAMP
    );
    """

    # Ejecuta la consulta SQL
    cursor.execute(sql)

    # Guarda los cambios realizados en la base de datos
    conexion.commit()

    # Cierra cursor y conexión para liberar recursos
    cursor.close()
    conexion.close()

    print("Tabla lista")


def insertar_registro(origen, contenido):
    """
    Inserta un nuevo registro en la tabla datos_recibidos.

    Parámetros:
        origen (str): identificador del origen del mensaje
        contenido (str): mensaje o dato a guardar
    """

    # Se obtiene conexión a la base de datos
    conexion = obtener_conexion()

    # Si no hay conexión, termina
    if conexion is None:
        return

    # Cursor para ejecutar SQL
    cursor = conexion.cursor()

    # Consulta SQL parametrizada para insertar datos
    # %s evita inyecciones SQL al pasar valores de forma segura
    sql = """
    INSERT INTO datos_recibidos (origen, contenido, fecha)
    VALUES (%s, %s, %s);
    """

    # Ejecuta inserción usando:
    # origen recibido
    # contenido recibido
    # fecha y hora actual del sistema
    cursor.execute(sql, (origen, contenido, datetime.now()))

    # Guarda cambios
    conexion.commit()

    # Cierra recursos
    cursor.close()
    conexion.close()

    print("Registro guardado")


# Punto de entrada principal del programa
if __name__ == "__main__":
    
    # Primero crea la tabla si no existe
    crear_tabla()

    # Después inserta un registro de prueba
    insertar_registro("TEST", "Prueba desde Python")