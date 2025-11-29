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

echo -e "${BLUE}🚀 Setting up test environment...${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker found"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ docker-compose is not installed. Please install docker-compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} docker-compose found"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.11+ first.${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

echo ""

# Start services
echo -e "${YELLOW}📦 Starting test containers...${NC}"
docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true
docker-compose -f docker-compose.test.yml up -d

echo ""

# Wait for services
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
bash "$SCRIPT_DIR/wait_for_services.sh"

echo ""

# Set up Python environment (if not exists)
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate and install dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip -q

# Install dependencies
pip install -r requirements.txt -q
pip install -r requirements-dev.txt -q
echo -e "${GREEN}✓${NC} Python dependencies installed"

echo ""

# Run migrations
echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
if [ -f "alembic.ini" ]; then
    alembic upgrade head
    echo -e "${GREEN}✓${NC} Database migrations applied"
else
    echo -e "${YELLOW}⚠${NC}  No alembic.ini found, skipping migrations"
fi

echo ""

# Verify setup
echo -e "${YELLOW}✅ Verifying setup...${NC}"
bash "$SCRIPT_DIR/verify_test_env.sh"

echo ""
echo -e "${GREEN}✨ Test environment is ready!${NC}"
echo ""
echo -e "To use the test environment:"
echo -e "  ${BLUE}source .venv/bin/activate${NC}"
echo -e "  ${BLUE}pytest tests/${NC}"
echo ""
echo -e "To stop the test environment:"
echo -e "  ${BLUE}bash scripts/teardown_test_env.sh${NC}"
echo ""
