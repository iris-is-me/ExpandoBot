#!/bin/bash

if [ ! -f "./assets/push_notification_payload.json" ]; then
    echo "Error: file does not exist" >&2
    exit 1
fi

curl -X POST "$DISCORD_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  --data @./assets/push_notification_payload.json
