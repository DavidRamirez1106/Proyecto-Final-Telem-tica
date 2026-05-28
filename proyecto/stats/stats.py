"""
App de Estadísticas — Genera reporte con gráficas y lo envía por correo.
Uso: python stats.py          (genera y envía el reporte)
     python stats.py --web    (sirve un dashboard web en el puerto 8080)
"""

import os
import io
import smtplib
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

import psycopg2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Configuración ──────────────────────────────────────────────────────────────
DB_CFG = dict(
    host=os.getenv("DB_HOST", "db"),
    port=int(os.getenv("DB_PORT", 5432)),
    dbname=os.getenv("DB_NAME", "registro"),
    user=os.getenv("DB_USER", "appuser"),
    password=os.getenv("DB_PASSWORD", "apppass123"),
)
SMTP_HOST  = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT  = int(os.getenv("SMTP_PORT", 587))
SMTP_USER  = os.getenv("SMTP_USER", "")
SMTP_PASS  = os.getenv("SMTP_PASS", "")
DEST_EMAIL = os.getenv("DEST_EMAIL", "ialondonoo@eafit.edu.co")

COLORS = ["#1e5fa8", "#b45309", "#0f6e56", "#993356"]
CARRERAS = ["Medicina/Medicine", "Ingeniería/Engineering", "Abogacía/Law", "Licenciatura/Education"]


def get_data():
    """Obtiene datos de estadísticas desde la base de datos."""
    conn = psycopg2.connect(**DB_CFG)
    cur = conn.cursor()
    cur.execute("SELECT * FROM stats_por_comuna;")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()
    return rows, cols


def fig_barras_apiladas(rows):
    """Gráfica de barras apiladas: registros por comuna y carrera."""
    comunas = [r[0] for r in rows]
    med = [r[2] for r in rows]
    ing = [r[3] for r in rows]
    abo = [r[4] for r in rows]
    lic = [r[5] for r in rows]

    x = np.arange(len(comunas))
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    bars = [
        ax.bar(x, med, color=COLORS[0], label="Medicina"),
        ax.bar(x, ing, bottom=med, color=COLORS[1], label="Ingeniería"),
        ax.bar(x, abo, bottom=[m+i for m,i in zip(med,ing)], color=COLORS[2], label="Abogacía"),
        ax.bar(x, lic, bottom=[m+i+a for m,i,a in zip(med,ing,abo)], color=COLORS[3], label="Licenciatura"),
    ]
    ax.set_xticks(x)
    ax.set_xticklabels(comunas, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Cantidad de registros")
    ax.set_title("Registros por Comuna y Carrera", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="upper right", fontsize=8)
    ax.spines[["top","right"]].set_visible(False)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf.read()


def fig_pie_carreras(rows):
    """Gráfica circular: distribución total por carrera."""
    totales = [sum(r[2] for r in rows), sum(r[3] for r in rows),
               sum(r[4] for r in rows), sum(r[5] for r in rows)]
    labels = ["Medicina", "Ingeniería", "Abogacía", "Licenciatura"]

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("#f8fafc")
    wedges, texts, autotexts = ax.pie(
        totales, labels=labels, colors=COLORS,
        autopct="%1.1f%%", startangle=140,
        pctdistance=0.82, wedgeprops=dict(edgecolor="white", linewidth=1.5)
    )
    for t in autotexts:
        t.set_fontsize(9)
    ax.set_title("Distribución por Carrera (Total)", fontsize=12, fontweight="bold")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf.read()


def fig_linea_tiempo():
    """Gráfica de línea: registros por día."""
    conn = psycopg2.connect(**DB_CFG)
    cur = conn.cursor()
    cur.execute("""
        SELECT fecha::text, COUNT(*) AS total
        FROM registros
        GROUP BY fecha
        ORDER BY fecha;
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    fechas = [r[0] for r in rows]
    totales = [r[1] for r in rows]

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    ax.plot(fechas, totales, color=COLORS[0], linewidth=2, marker="o", markersize=5)
    ax.fill_between(range(len(fechas)), totales, alpha=0.15, color=COLORS[0])
    ax.set_xticks(range(len(fechas)))
    ax.set_xticklabels(fechas, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Registros")
    ax.set_title("Evolución de Registros por Día", fontsize=12, fontweight="bold")
    ax.spines[["top","right"]].set_visible(False)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf.read()


def build_html_table(rows):
    total_general = sum(r[1] for r in rows)
    filas = ""
    for r in rows:
        filas += f"""<tr>
          <td>{r[0]}</td><td>{r[1]}</td>
          <td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td>
        </tr>"""
    return f"""
    <table border="0" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;font-family:sans-serif;font-size:13px">
      <thead>
        <tr style="background:#1e5fa8;color:#fff">
          <th>Comuna</th><th>Total</th>
          <th>Medicina</th><th>Ingeniería</th><th>Abogacía</th><th>Licenciatura</th>
        </tr>
      </thead>
      <tbody>{filas}</tbody>
      <tfoot>
        <tr style="background:#f1f5f9;font-weight:bold">
          <td>TOTAL</td><td>{total_general}</td>
          <td>{sum(r[2] for r in rows)}</td><td>{sum(r[3] for r in rows)}</td>
          <td>{sum(r[4] for r in rows)}</td><td>{sum(r[5] for r in rows)}</td>
        </tr>
      </tfoot>
    </table>"""


def enviar_correo(rows, img_barras, img_pie, img_linea):
    """Construye el correo HTML con imágenes embebidas y lo envía por SMTP."""
    tabla = build_html_table(rows)
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""
    <html><body style="font-family:sans-serif;color:#1e293b;max-width:700px;margin:auto">
      <h2 style="color:#1e5fa8">📊 Reporte de Estadísticas — {ahora}</h2>
      <p>A continuación se presentan las estadísticas acumuladas del sistema de registro universitario.</p>
      <h3>Resumen por Comuna y Carrera</h3>
      {tabla}
      <h3>Gráfica 1: Distribución por Comuna</h3>
      <img src="cid:img_barras" style="max-width:100%;border-radius:8px">
      <h3>Gráfica 2: Distribución por Carrera</h3>
      <img src="cid:img_pie" style="max-width:100%;border-radius:8px">
      {"<h3>Gráfica 3: Evolución Temporal</h3><img src='cid:img_linea' style='max-width:100%;border-radius:8px'>" if img_linea else ""}
      <hr style="margin-top:32px">
      <p style="font-size:11px;color:#94a3b8">Generado automáticamente por el sistema de estadísticas — EAFIT Internet Arquitectura y Protocolos</p>
    </body></html>"""

    msg = MIMEMultipart("related")
    msg["Subject"] = f"Estadísticas Registro Universitario — {ahora}"
    msg["From"]    = SMTP_USER
    msg["To"]      = DEST_EMAIL

    alt = MIMEMultipart("alternative")
    msg.attach(alt)
    alt.attach(MIMEText(html, "html"))

    for cid, data in [("img_barras", img_barras), ("img_pie", img_pie)]:
        img = MIMEImage(data, "png")
        img.add_header("Content-ID", f"<{cid}>")
        img.add_header("Content-Disposition", "inline")
        msg.attach(img)

    if img_linea:
        img = MIMEImage(img_linea, "png")
        img.add_header("Content-ID", "<img_linea>")
        img.add_header("Content-Disposition", "inline")
        msg.attach(img)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, DEST_EMAIL, msg.as_bytes())

    print(f"✅ Correo enviado a {DEST_EMAIL}")


def web_dashboard(rows, img_barras, img_pie, img_linea):
    """Sirve un dashboard web simple en el puerto 8080."""
    import base64
    from http.server import BaseHTTPRequestHandler, HTTPServer

    b64_bar  = base64.b64encode(img_barras).decode() if img_barras else ""
    b64_pie  = base64.b64encode(img_pie).decode() if img_pie else ""
    b64_lin  = base64.b64encode(img_linea).decode() if img_linea else ""
    tabla    = build_html_table(rows)
    ahora    = datetime.now().strftime("%Y-%m-%d %H:%M")

    html_page = f"""<!doctype html><html><head><meta charset="utf-8">
    <title>Estadísticas</title>
    <style>body{{font-family:sans-serif;max-width:860px;margin:40px auto;color:#1e293b}}
    h1{{color:#1e5fa8}}img{{max-width:100%;border-radius:8px;margin:16px 0}}
    table{{border-collapse:collapse;width:100%}}th{{background:#1e5fa8;color:#fff;padding:8px}}
    td{{padding:8px;border-bottom:1px solid #e2e8f0}}
    .btn{{background:#1e5fa8;color:#fff;border:none;padding:10px 24px;border-radius:8px;cursor:pointer;font-size:1rem}}
    .btn:hover{{background:#1748a0}}</style></head><body>
    <h1>📊 Estadísticas — {ahora}</h1>
    <form method="POST" action="/send"><button class="btn">📧 Enviar reporte por correo</button></form>
    <h2>Por Comuna y Carrera</h2>{tabla}
    <h2>Distribución por Comuna</h2><img src="data:image/png;base64,{b64_bar}">
    <h2>Distribución por Carrera</h2><img src="data:image/png;base64,{b64_pie}">
    {"<h2>Evolución Temporal</h2><img src='data:image/png;base64," + b64_lin + "'>" if b64_lin else ""}
    </body></html>"""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode())

        def do_POST(self):
            try:
                enviar_correo(rows, img_barras, img_pie, img_linea)
                resp = b"<h2>Correo enviado exitosamente.</h2><a href='/'>Volver</a>"
            except Exception as e:
                resp = f"<h2>Error: {e}</h2><a href='/'>Volver</a>".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(resp)

        def log_message(self, *args):
            pass  # silenciar logs por defecto

    print("🌐 Dashboard disponible en http://localhost:8080")
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()


# ── Punto de entrada ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--web", action="store_true", help="Servir dashboard web")
    args = parser.parse_args()

    print("📥 Obteniendo datos de la base de datos…")
    rows, _ = get_data()

    if not rows:
        print("⚠️  No hay datos en la base de datos todavía.")
    else:
        print(f"   {sum(r[1] for r in rows)} registros totales en {len(rows)} comunas.")

    print("📊 Generando gráficas…")
    img_barras = fig_barras_apiladas(rows) if rows else None
    img_pie    = fig_pie_carreras(rows) if rows else None
    img_linea  = fig_linea_tiempo()

    if args.web:
        web_dashboard(rows, img_barras or b"", img_pie or b"", img_linea)
    else:
        if not rows:
            print("⚠️  No hay datos. No se envía correo.")
        else:
            print("📧 Enviando correo…")
            enviar_correo(rows, img_barras, img_pie, img_linea)
