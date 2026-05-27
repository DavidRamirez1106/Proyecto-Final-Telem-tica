"""
Web Server 2 — Versión en Español
Formulario de registro: nombre, comuna, fecha, carrera de interés
"""

import os
from datetime import date
from flask import Flask, render_template_string, request
import psycopg2

app = Flask(__name__)
app.secret_key = "clave_secreta_ws2"

DB_CFG = dict(
    host=os.getenv("DB_HOST", "db"),
    port=int(os.getenv("DB_PORT", 5432)),
    dbname=os.getenv("DB_NAME", "registro"),
    user=os.getenv("DB_USER", "appuser"),
    password=os.getenv("DB_PASSWORD", "apppass123"),
)

COMUNAS = [f"Comuna {i}" for i in range(1, 11)]
CARRERAS = ["Medicina", "Ingeniería", "Abogacía", "Licenciatura"]

HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Registro Universitario — EAFIT</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',sans-serif;background:#f5f0eb;min-height:100vh;display:flex;align-items:center;justify-content:center}
    .card{background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.10);padding:40px 48px;width:100%;max-width:520px}
    h1{font-size:1.6rem;color:#2d1a00;margin-bottom:4px}
    .subtitle{color:#78716c;font-size:.9rem;margin-bottom:28px}
    .badge{display:inline-block;background:#fef3c7;color:#92400e;font-size:.75rem;font-weight:600;border-radius:20px;padding:3px 12px;margin-bottom:16px;letter-spacing:.5px}
    label{display:block;font-size:.82rem;font-weight:600;color:#44403c;margin-bottom:5px;margin-top:16px}
    input,select{width:100%;padding:10px 14px;border:1.5px solid #d6d3d1;border-radius:8px;font-size:.95rem;color:#1c1917;transition:border .2s}
    input:focus,select:focus{outline:none;border-color:#d97706}
    .btn{width:100%;margin-top:28px;padding:13px;background:#b45309;color:#fff;border:none;border-radius:10px;font-size:1rem;font-weight:600;cursor:pointer;transition:background .2s}
    .btn:hover{background:#92400e}
    .msg{padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:.88rem}
    .exito{background:#dcfce7;color:#166534}
    .error{background:#fee2e2;color:#991b1b}
    footer{margin-top:24px;text-align:center;color:#a8a29e;font-size:.78rem}
    .server-tag{position:fixed;top:12px;right:14px;background:#b45309;color:#fff;padding:4px 12px;border-radius:20px;font-size:.75rem;font-weight:600}
  </style>
</head>
<body>
<div class="server-tag">WEB SERVER 2 — ES</div>
<div class="card">
  <span class="badge">🇨🇴 Español</span>
  <h1>Registro de Interés Universitario</h1>
  <p class="subtitle">Completa tus datos para registrar tu interés en estudiar una carrera de pregrado.</p>

  {% for msg in mensajes %}
    <div class="msg {{ msg[0] }}">{{ msg[1] }}</div>
  {% endfor %}

  <form method="POST" action="/">
    <label for="nombre">Nombre completo</label>
    <input id="nombre" name="nombre" type="text" placeholder="Tu nombre completo" required>

    <label for="comuna">Comuna de la ciudad (1–10)</label>
    <select id="comuna" name="comuna" required>
      <option value="">Selecciona tu comuna…</option>
      {% for c in comunas %}
        <option value="{{ c }}">{{ c }}</option>
      {% endfor %}
    </select>

    <label for="fecha">Fecha de ingreso</label>
    <input id="fecha" name="fecha" type="date" value="{{ hoy }}" required>

    <label for="carrera">Carrera de interés</label>
    <select id="carrera" name="carrera" required>
      <option value="">Selecciona una carrera…</option>
      {% for car in carreras %}
        <option value="{{ car }}">{{ car }}</option>
      {% endfor %}
    </select>

    <button class="btn" type="submit">Registrarme ›</button>
  </form>
  <footer>Universidad EAFIT · Internet: Arquitectura y Protocolos</footer>
</div>
</body>
</html>
"""

def get_db():
    return psycopg2.connect(**DB_CFG)

def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS registros (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    comuna TEXT NOT NULL,
                    fecha DATE NOT NULL,
                    carrera TEXT NOT NULL,
                    servidor TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()

@app.route("/", methods=["GET", "POST"])
def index():
    mensajes = []
    if request.method == "POST":
        nombre  = request.form.get("nombre", "").strip()
        comuna  = request.form.get("comuna", "").strip()
        fecha   = request.form.get("fecha", "").strip()
        carrera = request.form.get("carrera", "").strip()

        if not all([nombre, comuna, fecha, carrera]):
            mensajes.append(("error", "Por favor completa todos los campos."))
        else:
            try:
                with get_db() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO registros (nombre, comuna, fecha, carrera, servidor) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            (nombre, comuna, fecha, carrera, "WS2-ES")
                        )
                    conn.commit()
                mensajes.append(("exito", f"✅ ¡Registro exitoso! Bienvenido/a, {nombre}."))
            except Exception as e:
                mensajes.append(("error", f"Error en la base de datos: {e}"))

    return render_template_string(
        HTML,
        comunas=COMUNAS,
        carreras=CARRERAS,
        hoy=date.today().isoformat(),
        mensajes=mensajes,
    )

@app.route("/health")
def health():
    return {"status": "ok", "servidor": "WS2-ES"}, 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
