#!/bin/bash
# Espera a que cloudflared tenga URL y actualiza Vapi automaticamente
VAPI_KEY="2ec800c0-99ce-41f3-8ec8-f71fdb961dad"
ASSISTANT_ID="dbc5639d-4e3e-4e90-a29f-56651ade28a7"

echo "$(date): Starting Vapi tunnel URL updater..." >> /var/log/vapi-tunnel-update.log

for i in $(seq 1 30); do
  CF_URL=$(journalctl -u cloudflared-telefonista --no-pager -n 200 2>/dev/null | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1)
  if [ -n "$CF_URL" ]; then
    SERVER_URL="${CF_URL}/api/v1/voice/webhook/agency_elite"
    RESP=$(curl -s -X PATCH "https://api.vapi.ai/assistant/${ASSISTANT_ID}" \
      -H "Authorization: Bearer ${VAPI_KEY}" \
      -H "Content-Type: application/json" \
      -d "{\"serverUrl\": \"${SERVER_URL}\"}")
    echo "$(date): Updated Vapi serverUrl to $SERVER_URL" >> /var/log/vapi-tunnel-update.log
    echo "$(date): Vapi response: $RESP" >> /var/log/vapi-tunnel-update.log
    echo "OK: $SERVER_URL"
    exit 0
  fi
  echo "$(date): Attempt $i - waiting for tunnel URL..." >> /var/log/vapi-tunnel-update.log
  sleep 2
done

echo "$(date): ERROR - No tunnel URL found after 60s" >> /var/log/vapi-tunnel-update.log
exit 1
