#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Maximum wait time in seconds
MAX_WAIT=60
INTERVAL=2

wait_for_service() {
    local service_name=$1
    local check_command=$2
    local elapsed=0
    
    echo -n "  Waiting for $service_name..."
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        if eval "$check_command" &> /dev/null; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        sleep $INTERVAL
        elapsed=$((elapsed + INTERVAL))
        echo -n "."
    done
    
    echo -e " ${RED}✗${NC}"
    echo -e "${RED}❌ $service_name failed to start within ${MAX_WAIT}s${NC}"
    return 1
}

# Wait for PostgreSQL
wait_for_service "PostgreSQL" "docker exec realestate-test-db pg_isready -U test_user -d realestate_test"

# Wait for Redis
wait_for_service "Redis" "docker exec real-estate-redis-test redis-cli ping"

echo -e "${GREEN}✓${NC} All services are ready"
