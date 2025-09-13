#!/bin/bash
read -p "Enter ticket text: " ticket

if [ -z "$ticket" ]; then
  echo "No input given. Please enter a support ticket description."
  exit 1
fi

curl -s -X POST "http://127.0.0.1:8000/resolve-ticket" \
  -H "Content-Type: application/json" \
  -d "{\"ticket_text\": \"$ticket\"}" | jq .
