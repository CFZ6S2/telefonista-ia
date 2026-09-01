#!/bin/bash
# ============================================================
# Telefonista IA - HTTPS Setup con Nginx + Let's Encrypt
# Ejecutar en el VPS como root:
#   bash /opt/telefonista-ia/setup-https.sh telefonista-api.duckdns.org email@ejemplo.com
# ============================================================

set -euo pipefail

DOMAIN="${1:?Uso: $0 <dominio> <email>}"
EMAIL="${2:?Uso: $0 <dominio> <email>}"
BACKEND_PORT=8089

echo "==> Configurando HTTPS para ${DOMAIN}"

# 1. Instalar Nginx y Certbot
echo "==> Instalando Nginx y Certbot..."
apt-get update -qq
apt-get install -y -qq nginx certbot python3-certbot-nginx

# 2. Crear configuracion Nginx inicial (solo HTTP para validacion Certbot)
echo "==> Creando configuracion Nginx..."
cat > /etc/nginx/sites-available/telefonista <<'NGINX_CONF'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;

    location / {
        proxy_pass http://127.0.0.1:BACKEND_PORT_PLACEHOLDER;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
NGINX_CONF

sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" /etc/nginx/sites-available/telefonista
sed -i "s/BACKEND_PORT_PLACEHOLDER/${BACKEND_PORT}/g" /etc/nginx/sites-available/telefonista

# 3. Activar el sitio y desactivar el default
ln -sf /etc/nginx/sites-available/telefonista /etc/nginx/sites-enabled/telefonista
rm -f /etc/nginx/sites-enabled/default

# 4. Verificar y reiniciar Nginx
echo "==> Verificando configuracion Nginx..."
nginx -t
systemctl restart nginx

# 5. Abrir puertos 80 y 443 en UFW
echo "==> Abriendo puertos 80 y 443 en UFW..."
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force reload

# 6. Obtener certificado SSL con Certbot (modifica Nginx automaticamente)
echo "==> Obteniendo certificado SSL de Let's Encrypt..."
certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos -m "${EMAIL}" --redirect

# 7. Agregar headers de seguridad al bloque SSL generado por Certbot
echo "==> Agregando headers de seguridad..."
sed -i '/listen 443 ssl/a\
    add_header X-Content-Type-Options nosniff always;\
    add_header X-Frame-Options DENY always;\
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;' /etc/nginx/sites-available/telefonista

nginx -t && systemctl reload nginx

# 8. Verificar renovacion automatica
echo "==> Verificando renovacion automatica..."
certbot renew --dry-run

echo ""
echo "============================================"
echo "  HTTPS CONFIGURADO CON EXITO"
echo "  https://${DOMAIN}"
echo "============================================"
echo ""
echo "El certificado se renueva automaticamente."
echo "Recuerda actualizar VPS_PUBLIC_URL en .env:"
echo "  VPS_PUBLIC_URL=https://${DOMAIN}"
