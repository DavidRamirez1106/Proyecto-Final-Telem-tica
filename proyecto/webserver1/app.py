"""
Web Server 1 — English version
Registration form: name, commune, date, career interest
"""

import os
from datetime import date
from flask import Flask, render_template_string, request, redirect, url_for, flash
import psycopg2

app = Flask(__name__)
app.secret_key = "secret_key_ws1"

DB_CFG = dict(
    host=os.getenv("DB_HOST", "db"),
    port=int(os.getenv("DB_PORT", 5432)),
    dbname=os.getenv("DB_NAME", "registro"),
    user=os.getenv("DB_USER", "appuser"),
    password=os.getenv("DB_PASSWORD", "apppass123"),
)

COMMUNES = [f"Commune {i}" for i in range(1, 11)]
CAREERS = ["Medicine", "Engineering", "Law", "Education"]

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>University Registration — EAFIT</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',sans-serif;background:#f0f4f8;min-height:100vh;display:flex;align-items:center;justify-content:center}
    .card{background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.10);padding:40px 48px;width:100%;max-width:520px}
    h1{font-size:1.6rem;color:#1a2e4a;margin-bottom:4px}
    .subtitle{color:#64748b;font-size:.9rem;margin-bottom:28px}
    .badge{display:inline-block;background:#e8f4fd;color:#1e5fa8;font-size:.75rem;font-weight:600;border-radius:20px;padding:3px 12px;margin-bottom:16px;letter-spacing:.5px}
    label{display:block;font-size:.82rem;font-weight:600;color:#334155;margin-bottom:5px;margin-top:16px}
    input,select{width:100%;padding:10px 14px;border:1.5px solid #cbd5e1;border-radius:8px;font-size:.95rem;color:#1e293b;transition:border .2s}
    input:focus,select:focus{outline:none;border-color:#3b82f6}
    .btn{width:100%;margin-top:28px;padding:13px;background:#1e5fa8;color:#fff;border:none;border-radius:10px;font-size:1rem;font-weight:600;cursor:pointer;transition:background .2s}
    .btn:hover{background:#1748a0}
    .msg{padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:.88rem}
    .success{background:#dcfce7;color:#166534}
    .error{background:#fee2e2;color:#991b1b}
    footer{margin-top:24px;text-align:center;color:#94a3b8;font-size:.78rem}
    .server-tag{position:fixed;top:12px;right:14px;background:#1e5fa8;color:#fff;padding:4px 12px;border-radius:20px;font-size:.75rem;font-weight:600}
  </style>
</head>
<body>
<div class="server-tag">WEB SERVER 1 — EN</div>
<div class="card">
  <span class="badge">🇬🇧 English</span>
  <h1>University Interest Registration</h1>
  <p class="subtitle">Fill in your information to register your academic interest.</p>

  {% for msg in messages %}
    <div class="msg {{ msg[0] }}">{{ msg[1] }}</div>
  {% endfor %}

  <form method="POST" action="/">
    <label for="nombre">Full name</label>
    <input id="nombre" name="nombre" type="text" placeholder="Your full name" required>

    <label for="comuna">City Commune (1–10)</label>
    <select id="comuna" name="comuna" required>
      <option value="">Select your commune…</option>
      {% for c in communes %}
        <option value="{{ c }}">{{ c }}</option>
      {% endfor %}
    </select>

    <label for="fecha">Registration date</label>
    <input id="fecha" name="fecha" type="date" value="{{ today }}" required>

    <label for="carrera">Career of interest</label>
    <select id="carrera" name="carrera" required>
      <option value="">Select a career…</option>
      {% for car in careers %}
        <option value="{{ car }}">{{ car }}</option>
      {% endfor %}
    </select>

    <button class="btn" type="submit">Register ›</button>
  </form>
  <footer>EAFIT University · Internet Architecture & Protocols</footer>
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
    messages = []
    if request.method == "POST":
        nombre  = request.form.get("nombre", "").strip()
        comuna  = request.form.get("comuna", "").strip()
        fecha   = request.form.get("fecha", "").strip()
        carrera = request.form.get("carrera", "").strip()

        if not all([nombre, comuna, fecha, carrera]):
            messages.append(("error", "Please fill in all fields."))
        else:
            try:
                with get_db() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO registros (nombre, comuna, fecha, carrera, servidor) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            (nombre, comuna, fecha, carrera, "WS1-EN")
                        )
                    conn.commit()
                messages.append(("success", f"✅ Registration successful! Welcome, {nombre}."))
            except Exception as e:
                messages.append(("error", f"Database error: {e}"))

    return render_template_string(
        HTML,
        communes=COMMUNES,
        careers=CAREERS,
        today=date.today().isoformat(),
        messages=messages,
    )

@app.route("/health")
def health():
    return {"status": "ok", "server": "WS1-EN"}, 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
