#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo -e "${BLUE}🛑 Tearing down test environment...${NC}"
echo ""

# Stop and remove containers
echo -e "${YELLOW}📦 Stopping test containers...${NC}"
if docker-compose -f docker-compose.test.yml ps -q 2>/dev/null | grep -q .; then
    docker-compose -f docker-compose.test.yml down -v
    echo -e "${GREEN}✓${NC} Test containers stopped and removed"
else
    echo -e "${YELLOW}⚠${NC}  No test containers running"
fi

# Optional: Clean up volumes
if [ "$1" == "--clean-volumes" ]; then
    echo ""
    echo -e "${YELLOW}🗑️  Removing test data volumes...${NC}"
    docker volume rm $(docker volume ls -q | grep -E 'realestate.*test') 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Test volumes removed"
fi

# Optional: Clean up Python cache
if [ "$1" == "--clean-all" ] || [ "$2" == "--clean-all" ]; then
    echo ""
    echo -e "${YELLOW}🧹 Cleaning Python cache...${NC}"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    rm -rf htmlcov/ .coverage coverage.json 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Python cache cleaned"
fi

echo ""
echo -e "${GREEN}✨ Test environment torn down${NC}"
echo ""
echo -e "Usage options:"
echo -e "  ${BLUE}bash scripts/teardown_test_env.sh${NC}                 - Stop containers"
echo -e "  ${BLUE}bash scripts/teardown_test_env.sh --clean-volumes${NC} - Stop containers and remove volumes"
echo -e "  ${BLUE}bash scripts/teardown_test_env.sh --clean-all${NC}     - Stop containers and clean all caches"
echo ""
