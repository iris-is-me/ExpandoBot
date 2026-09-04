#!/bin/bash

COMMIT_MESSAGE=$(git log -1 --pretty=%B)
PAYLOAD=$(jq -n \
  --arg repo "$GITHUB_REPOSITORY" \
  --arg branch "$GITHUB_REF_NAME" \
  --arg actor "$GITHUB_ACTOR" \
  --arg sha "$GITHUB_SHA" \
  --arg message "$COMMIT_MESSAGE" \
  --arg timestamp "$(date +%s)" \
  '{
    embeds: [{
      title: "GitHub push",
      type: "rich",
      description: "A new commit has been pushed to the repository",
      color: 5814783,
      thumbnail: {
        url: ("https://github.com/" + $actor + ".png")
      },
      fields: [
        {
          name: "📦 Repository",
          value: ("[`" + $repo + "`](https://github.com/" + $repo + ")"),
          inline: true
        },
        {
          name: "🌿 Branch",
          value: ("[`" + $branch + "`](https://github.com/iris-is-me/ExpandoBot/tree/" + $branch + ")"),
          inline: true
        },
        {
          name: "👤 Author",
          value: ("[`" + $actor + "`](https://github.com/" + $actor + ")"),
          inline: true
        },
        {
          name: "🔗 Commit",
          value: ("[`" + ($sha[:7]) + "`](https://github.com/" + $repo + "/commit/" + $sha + ")"),
          inline: false
        },
        {
          name: "📝 Commit Message",
          value: $message,
          inline: false
        },
        {
          name: "📅 Timestamp",
          value: ("<t:" + $timestamp + ":F>"),
          inline: false
        }
      ],
      footer: {
        text: "GitHub Actions • Push Notification"
      }
    }]
  }')

curl \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "$DISCORD_WEBHOOK_URL"
