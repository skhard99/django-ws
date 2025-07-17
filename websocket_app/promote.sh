#!/bin/bash

set -e

# STEP 1: Decide next color
CURRENT_COLOR=$(grep 'server web_' nginx/default.conf | grep -v "#" | cut -d'_' -f2 | cut -d':' -f1)
if [ "$CURRENT_COLOR" = "blue" ]; then
  NEXT_COLOR="green"
else
  NEXT_COLOR="blue"
fi

echo "🛠 Promoting $NEXT_COLOR..."

# STEP 2: Build & start next color (in detached mode)
docker-compose up -d --build web_$NEXT_COLOR

# STEP 3: Smoke test next color
echo "🚨 Smoke testing http://localhost:8002 (if green) or 8001 (if blue)"
PORT="8001"
if [ "$NEXT_COLOR" = "green" ]; then
  PORT="8002"
fi

curl -f "http://localhost:$PORT/metrics" > /dev/null
echo "✅ Smoke test passed."

# STEP 4: Flip traffic
echo "🔁 Switching NGINX traffic to $NEXT_COLOR"
sed -i.bak "s/server web_$CURRENT_COLOR/server web_$NEXT_COLOR/" nginx/default.conf
docker-compose restart nginx

# STEP 5: Retire old color
echo "🧹 Stopping old container: web_$CURRENT_COLOR"
docker-compose stop web_$CURRENT_COLOR

echo "🎉 Blue/Green promotion to $NEXT_COLOR complete."
