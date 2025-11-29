#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

check_service() {
    local service_name=$1
    local check_command=$2
    
    echo -n "  Checking $service_name..."
    
    if eval "$check_command" &> /dev/null; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

check_python_package() {
    local package=$1
    echo -n "  Checking $package..."
    
    if python -c "import $package" 2>/dev/null; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

echo "Verifying test environment..."
echo ""

# Check Docker containers
echo "Docker Containers:"
check_service "PostgreSQL container" "docker ps | grep realestate-test-db"
check_service "Redis container" "docker ps | grep real-estate-redis-test"

echo ""

# Check service connectivity
echo "Service Connectivity:"
check_service "PostgreSQL connection" "docker exec realestate-test-db pg_isready -U test_user -d realestate_test"
check_service "Redis connection" "docker exec real-estate-redis-test redis-cli ping"

echo ""

# Check Python packages
echo "Python Environment:"
check_python_package "pytest"
check_python_package "sqlalchemy"
check_python_package "redis"
check_python_package "fastapi"
check_python_package "alembic"

echo ""

# Check database tables
echo "Database Schema:"
echo -n "  Checking tables..."
TABLE_COUNT=$(docker exec realestate-test-db psql -U test_user -d realestate_test -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | xargs)

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo -e " ${GREEN}✓${NC} ($TABLE_COUNT tables)"
else
    echo -e " ${YELLOW}⚠${NC} (No tables found, migrations may not have run)"
fi

echo ""

# Summary
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS check(s) failed${NC}"
    exit 1
fi
