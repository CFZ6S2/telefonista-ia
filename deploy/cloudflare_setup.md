# Configuración de Cloudflare Tunnel (VPS Firewall Bypass)

Debido a que el firewall del proveedor del VPS bloquea el puerto 443 (HTTPS), Vapi.ai no podía conectarse al webhook (exige HTTPS estrictamente). Para solucionarlo, se implementó **Cloudflare Tunnel (cloudflared)**.

## Servicios en el VPS

Se configuraron dos servicios systemd en el VPS (`178.156.186.149`):

### 1. `cloudflared-telefonista.service`
Mantiene un túnel rápido (quick tunnel) activo apuntando al contenedor Docker interno.
- **Comando:** `/usr/bin/cloudflared tunnel --url http://localhost:8089 --no-autoupdate`

### 2. `vapi-tunnel-updater.service`
Como los quick tunnels cambian de URL (`*.trycloudflare.com`) en cada reinicio, este servicio ejecuta el script `update-vapi-tunnel.sh` en cada arranque.
- Lee la nueva URL del log de `cloudflared`.
- Hace un `PATCH` a la API de Vapi para actualizar el `serverUrl` del asistente automáticamente.

## Archivos
- `deploy/update-vapi-tunnel.sh`: El script que realiza la actualización vía API. Se encuentra en el VPS en `/usr/local/bin/update-vapi-tunnel.sh`.
