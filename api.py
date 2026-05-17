"""
============================================================
API FLASK - Mini Data Warehouse
Endpoints completos para el dashboard
============================================================
"""
from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import os

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    "host"    : "aws-1-us-west-1.pooler.supabase.com",
    "port"    : 6543,
    "dbname"  : "postgres",
    "user"    : "postgres.qiljbefohyrkfnrrwdcr",
    "password": "Pintura12_#$",
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

# Posiciones exactas (30 columnas, 29 comas)
COL_TARDIA    = 11   # entrega_tardia
COL_ESTADO    = 15   # customer_state
COL_PRICE     = 20   # price
COL_FREIGHT   = 21   # freight_value
COL_PRECIO    = 22   # precio_total
COL_CATEGORIA = 23   # product_category_name

FILTRO = "LENGTH(contenido) - LENGTH(REPLACE(contenido, ',', '')) = 29"


# ── GET /api/resumen ─────────────────────────────────────────
@app.route("/api/resumen", methods=["GET"])
def resumen():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM datos_recibidos WHERE origen='TCP'")
    total_tcp = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM datos_recibidos WHERE origen='UDP'")
    total_udp = cur.fetchone()[0]
    cur.execute(f"""
        SELECT COUNT(*) FROM datos_recibidos
        WHERE origen='TCP' AND {FILTRO}
          AND SPLIT_PART(contenido,',',%s)='True'
    """, (COL_TARDIA,))
    total_tardias = cur.fetchone()[0]
    cur.execute(f"""
        SELECT COUNT(DISTINCT SPLIT_PART(contenido,',',%s))
        FROM datos_recibidos WHERE origen='TCP' AND {FILTRO}
    """, (COL_CATEGORIA,))
    total_categorias = cur.fetchone()[0]
    cur.execute(f"""
        SELECT
            ROUND(AVG(CAST(SPLIT_PART(contenido,',',%s) AS NUMERIC)),2),
            ROUND(SUM(CAST(SPLIT_PART(contenido,',',%s) AS NUMERIC)),2)
        FROM datos_recibidos WHERE origen='TCP' AND {FILTRO}
          AND SPLIT_PART(contenido,',',%s) ~ '^[0-9]+(\.[0-9]+)?$'
    """, (COL_FREIGHT, COL_PRECIO, COL_FREIGHT))
    row = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({
        "total_tcp"       : total_tcp,
        "total_udp"       : total_udp,
        "total_tardias"   : total_tardias,
        "total_categorias": total_categorias,
        "avg_flete"       : float(row[0]) if row[0] else 0,
        "total_ventas"    : float(row[1]) if row[1] else 0,
    })


# ── GET /api/retrasos-por-categoria ─────────────────────────
@app.route("/api/retrasos-por-categoria", methods=["GET"])
def retrasos_por_categoria():
    conn = get_conn(); cur = conn.cursor()
    cur.execute(f"""
        SELECT
            SPLIT_PART(contenido,',',%s) AS categoria,
            COUNT(*) AS total_ordenes,
            SUM(CASE WHEN SPLIT_PART(contenido,',',%s)='True' THEN 1 ELSE 0 END) AS tardias,
            ROUND(100.0 * SUM(CASE WHEN SPLIT_PART(contenido,',',%s)='True' THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*),0),1) AS pct_tardia
        FROM datos_recibidos
        WHERE origen='TCP' AND {FILTRO}
          AND SPLIT_PART(contenido,',',%s) != ''
        GROUP BY categoria
        ORDER BY tardias DESC, pct_tardia DESC
        LIMIT 15
    """, (COL_CATEGORIA, COL_TARDIA, COL_TARDIA, COL_CATEGORIA))
    filas = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([{
        "categoria"    : f[0] or "sin_categoria",
        "total_ordenes": f[1],
        "tardias"      : f[2],
        "pct_tardia"   : float(f[3]) if f[3] else 0.0
    } for f in filas])


# ── GET /api/ventas-por-estado ───────────────────────────────
@app.route("/api/ventas-por-estado", methods=["GET"])
def ventas_por_estado():
    conn = get_conn(); cur = conn.cursor()
    cur.execute(f"""
        SELECT
            SPLIT_PART(contenido,',',%s) AS estado,
            COUNT(*) AS total_ordenes,
            ROUND(SUM(CAST(SPLIT_PART(contenido,',',%s) AS NUMERIC)),2) AS total_ventas,
            ROUND(AVG(CAST(SPLIT_PART(contenido,',',%s) AS NUMERIC)),2) AS ticket_promedio
        FROM datos_recibidos
        WHERE origen='TCP' AND {FILTRO}
          AND SPLIT_PART(contenido,',',%s) != ''
          AND SPLIT_PART(contenido,',',%s) ~ '^[0-9]+(\.[0-9]+)?$'
        GROUP BY estado
        ORDER BY total_ventas DESC
        LIMIT 20
    """, (COL_ESTADO, COL_PRECIO, COL_PRECIO, COL_ESTADO, COL_PRECIO))
    filas = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([{
        "estado"         : f[0],
        "total_ordenes"  : f[1],
        "total_ventas"   : float(f[2]) if f[2] else 0,
        "ticket_promedio": float(f[3]) if f[3] else 0,
    } for f in filas])


# ── GET /api/costo-envio ─────────────────────────────────────
@app.route("/api/costo-envio", methods=["GET"])
def costo_envio():
    conn = get_conn(); cur = conn.cursor()
    cur.execute(f"""
        SELECT
            SPLIT_PART(contenido,',',%s) AS categoria,
            ROUND(AVG(CAST(SPLIT_PART(contenido,',',%s) AS NUMERIC)),2) AS avg_flete,
            ROUND(AVG(CAST(SPLIT_PART(contenido,',',%s) AS NUMERIC)),2) AS avg_precio,
            ROUND(100.0 * AVG(CAST(SPLIT_PART(contenido,',',%s) AS NUMERIC))
                / NULLIF(AVG(CAST(SPLIT_PART(contenido,',',%s) AS NUMERIC)),0),1) AS pct_flete
        FROM datos_recibidos
        WHERE origen='TCP' AND {FILTRO}
          AND SPLIT_PART(contenido,',',%s) != ''
          AND SPLIT_PART(contenido,',',%s) ~ '^[0-9]+(\.[0-9]+)?$'
          AND SPLIT_PART(contenido,',',%s) ~ '^[0-9]+(\.[0-9]+)?$'
        GROUP BY categoria
        ORDER BY avg_flete DESC
        LIMIT 15
    """, (COL_CATEGORIA, COL_FREIGHT, COL_PRICE,
          COL_FREIGHT, COL_PRICE,
          COL_CATEGORIA, COL_FREIGHT, COL_PRICE))
    filas = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([{
        "categoria" : f[0] or "sin_categoria",
        "avg_flete" : float(f[1]) if f[1] else 0,
        "avg_precio": float(f[2]) if f[2] else 0,
        "pct_flete" : float(f[3]) if f[3] else 0,
    } for f in filas])


# ── GET /api/ventas-por-mes ──────────────────────────────────
@app.route("/api/ventas-por-mes", methods=["GET"])
def ventas_por_mes():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        SELECT TO_CHAR(fecha,'YYYY-MM') AS mes,
               COUNT(*) AS total,
               COUNT(CASE WHEN origen='TCP' THEN 1 END) AS tcp,
               COUNT(CASE WHEN origen='UDP' THEN 1 END) AS udp
        FROM datos_recibidos
        GROUP BY mes ORDER BY mes ASC
    """)
    filas = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([{"mes":f[0],"total":f[1],"tcp":f[2],"udp":f[3]} for f in filas])


# ── GET /api/datos ───────────────────────────────────────────
@app.route("/api/datos", methods=["GET"])
def obtener_datos():
    conn = get_conn(); cur = conn.cursor()
    cur.execute(f"""
        SELECT id, origen,
            SPLIT_PART(contenido,',',%s),
            SPLIT_PART(contenido,',',%s),
            SPLIT_PART(contenido,',',%s),
            SPLIT_PART(contenido,',',%s),
            fecha
        FROM datos_recibidos
        WHERE origen='TCP' AND {FILTRO}
        ORDER BY fecha DESC LIMIT 200
    """, (COL_CATEGORIA, COL_TARDIA, COL_ESTADO, COL_PRECIO))
    filas = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({"total": len(filas), "datos": [{
        "id": f[0], "origen": f[1],
        "categoria": f[2] or "sin_categoria",
        "entrega_tardia": f[3], "estado": f[4],
        "precio_total": f[5], "fecha": str(f[6])
    } for f in filas]})


if __name__ == "__main__":
    print("="*55)
    print("  /api/resumen")
    print("  /api/retrasos-por-categoria")
    print("  /api/ventas-por-estado")
    print("  /api/costo-envio")
    print("  /api/ventas-por-mes")
    print("  /api/datos")
    print("="*55)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
