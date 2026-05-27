#!/bin/bash
# Genera un certificado SSL auto-firmado para PRUEBAS LOCALES.
# En producción, reemplazar con Let's Encrypt (certbot).

mkdir -p certs

openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout certs/privkey.pem \
  -out certs/fullchain.pem \
  -subj "/C=CO/ST=Antioquia/L=Medellin/O=EAFIT/OU=Internet/CN=tudominio.com"

echo ""
echo "✅  Certificado auto-firmado generado en ./certs/"
echo "    Para producción, usa: certbot certonly --standalone -d tudominio.com"
