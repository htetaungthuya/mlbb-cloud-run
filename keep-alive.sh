#!/bin/bash
BOT_URL="https://mlbb-cloud-run.onrender.com"

while true; do
    echo "✅ Pinging Render instance..."
    curl -s $BOT_URL > /dev/null
    sleep 600  # 10 minutes interval → minimal CPU / battery impact
done
