#!/bin/bash
read -p "Enter ticket text: " ticket
curl -s -X POST "http://127.0.0.1:8000/resolve-ticket" \
  -H "Content-Type: application/json" \
  -d "{\"ticket_text\": \"$ticket\"}" | jq

