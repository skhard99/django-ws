#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting Blue/Green Deployment...${NC}"

# STEP 1: Decide next color
CURRENT_COLOR=$(grep 'server web_' nginx/default.conf | grep -v "#" | head -1 | cut -d'_' -f2 | cut -d':' -f1)
if [ "$CURRENT_COLOR" = "blue" ]; then
  NEXT_COLOR="green"
  NEXT_PORT="8002"
else
  NEXT_COLOR="blue"
  NEXT_PORT="8001"
fi

echo -e "${YELLOW}🔄 Current: $CURRENT_COLOR, Next: $NEXT_COLOR${NC}"

# STEP 2: Build & start next color
echo -e "${YELLOW}🏗️  Building and starting web_$NEXT_COLOR...${NC}"
docker-compose up -d --build web_$NEXT_COLOR

# STEP 3: Wait for health check
echo -e "${YELLOW}⏳ Waiting for health check...${NC}"
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  if curl -f "http://localhost:$NEXT_PORT/health/" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed for $NEXT_COLOR${NC}"
    break
  fi
  
  ATTEMPT=$((ATTEMPT + 1))
  echo -e "${YELLOW}⏳ Attempt $ATTEMPT/$MAX_ATTEMPTS - waiting for $NEXT_COLOR to be ready...${NC}"
  sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  echo -e "${RED}❌ Health check failed for $NEXT_COLOR after $MAX_ATTEMPTS attempts${NC}"
  exit 1
fi

# STEP 4: Additional smoke tests
echo -e "${YELLOW}🧪 Running smoke tests...${NC}"
if curl -f "http://localhost:$NEXT_PORT/metrics/" > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Metrics endpoint working${NC}"
else
  echo -e "${RED}❌ Metrics endpoint failed${NC}"
  exit 1
fi

# STEP 5: Flip traffic
echo -e "${YELLOW}🔁 Switching NGINX traffic to $NEXT_COLOR${NC}"
sed -i.bak "s/server web_$CURRENT_COLOR/server web_$NEXT_COLOR/" nginx/default.conf
docker-compose restart nginx

# Wait for nginx to restart
sleep 3

# STEP 6: Test the switch
echo -e "${YELLOW}🧪 Testing traffic switch...${NC}"
if curl -f "http://localhost/health/" > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Traffic successfully switched to $NEXT_COLOR${NC}"
else
  echo -e "${RED}❌ Traffic switch failed, rolling back...${NC}"
  # Rollback
  sed -i.bak "s/server web_$NEXT_COLOR/server web_$CURRENT_COLOR/" nginx/default.conf
  docker-compose restart nginx
  exit 1
fi

# STEP 7: Graceful shutdown of old color
echo -e "${YELLOW}🧹 Gracefully stopping old container: web_$CURRENT_COLOR${NC}"
docker-compose stop web_$CURRENT_COLOR

echo -e "${GREEN}🎉 Blue/Green promotion to $NEXT_COLOR completed successfully!${NC}"
echo -e "${GREEN}🌐 Application is now running on: http://localhost${NC}"