#!/bin/bash

PAYLOAD=$(cat <<EOF

{
  "embeds": [
    {
      "title": "GitHub push",
      "type": "rich",
      "description": "A new commit has been pushed to the repository",
      "color": 5814783,
      "thumbnail": {
        "url": "https://github.com/${GITHUB_ACTOR}.png"
        },
      "fields": [
        {
          "name": "📦 Repository",
          "value": "[${GITHUB_REPOSITORY}](https://github.com/${GITHUB_REPOSITORY})",
          "inline": true
        },
        {
          "name": "🌿 Branch",
          "value": "[${GITHUB_REF_NAME}](https://github.com/iris-is-me/ExpandoBot/tree/${GITHUB_REF_NAME})",
          "inline": true
        },
        {
          "name": "👤 Author",
          "value": "[${GITHUB_ACTOR}]( https://github.com/${GITHUB_ACTOR})",
          "inline": true
        },
        {
          "name": "🔗 Commit",
          "value": "[${GITHUB_SHA:0:7}](${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/commit/${GITHUB_SHA})",
          "inline": false
        },
        {
          "name": "📝 Commit Message",
          "value": "$(git log -1 --pretty=%B | sed ':a;N;$!ba;s/\n/ /g')",
          "inline": false
        },
        {
          "name": "📅 Timestamp",
          "value": "<t:$(date +%s):F>",
          "inline": false
        }
      ],
      "footer": {
        "text": "GitHub Actions • Push Notification"
      }
    }
  ]
}
EOF
)

curl \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "$DISCORD_WEBHOOK_URL"