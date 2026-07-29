#!/bin/bash

curl -X POST "$DISCORD_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  --data @./push_notifs_payload.json
