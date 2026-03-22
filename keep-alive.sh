#!/bin/bash
BOT_URL="https://mlbb-cloud-run.onrender.com"
while true; do
  curl -s $BOT_URL > /dev/null
  sleep 600
done
