#!/bin/bash

clear

curl -X POST "$DISCORD_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  --data-binary @./push_notifs_payload.json
