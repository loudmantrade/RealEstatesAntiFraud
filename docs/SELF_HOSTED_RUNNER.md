# Self-Hosted GitHub Actions Runner Setup

Self-hosted runner deployed on mixfm2 server for unlimited free GitHub Actions minutes.

## Server Info

- **Host:** mixfm2 (h2.mixfm.com.ua)
- **OS:** Ubuntu 24.04 LTS (6.8.0-87-generic)
- **CPU:** 6 cores
- **RAM:** 9.7GB
- **Disk:** 86GB available
- **Docker:** 28.2.2

## Architecture

```
┌─────────────────────────────────┐
│  mixfm2 Server                  │
│                                 │
│  ┌───────────────────────────┐  │
│  │  Docker Containers        │  │
│  │                           │  │
│  │  ┌─────────────────────┐  │  │
│  │  │  GitHub Runner      │  │  │
│  │  │  (myoung34/image)   │  │  │
│  │  └─────────────────────┘  │  │
│  │                           │  │
│  │  ┌─────────────────────┐  │  │
│  │  │  PostgreSQL 15      │  │  │
│  │  │  alpine             │  │  │
│  │  └─────────────────────┘  │  │
│  │                           │  │
│  │  ┌─────────────────────┐  │  │
│  │  │  Redis 7            │  │  │
│  │  │  alpine             │  │  │
│  │  └─────────────────────┘  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

## Setup Instructions

### 1. Server Access

```bash
ssh mixfm2
```

### 2. Install Dependencies

```bash
# Docker already installed via apt install docker.io
# Install docker-compose
sudo apt-get update
sudo apt-get install -y docker-compose
```

### 3. Create Configuration

```bash
# Create runner directory
mkdir -p ~/github-runner
cd ~/github-runner

# Create docker-compose.yml (see below)
# Create .env with RUNNER_TOKEN (see below)
```

### 4. Get Runner Token

From local machine:

```bash
gh api -X POST repos/loudmantrade/RealEstatesAntiFraud/actions/runners/registration-token --jq '.token'
```

Create `~/github-runner/.env`:

```env
RUNNER_TOKEN=<token_from_above>
```

### 5. Start Services

```bash
cd ~/github-runner
docker-compose up -d

# Check status
docker-compose ps
docker logs github-runner
```

## Configuration Files

### docker-compose.yml

Located at: `~/github-runner/docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: runner-postgres
    environment:
      POSTGRES_DB: realestate_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d realestate_test"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: runner-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  github-runner:
    image: myoung34/github-runner:latest
    container_name: github-runner
    environment:
      REPO_URL: https://github.com/loudmantrade/RealEstatesAntiFraud
      RUNNER_NAME: self-hosted-mixfm2
      RUNNER_TOKEN: ${RUNNER_TOKEN}
      RUNNER_WORKDIR: /tmp/runner/work
      LABELS: self-hosted,linux,x64,docker
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - runner_data:/tmp/runner
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    network_mode: host

volumes:
  postgres_data:
  redis_data:
  runner_data:
```

## Runner Status

Check runner status in GitHub:

```bash
gh api repos/loudmantrade/RealEstatesAntiFraud/actions/runners --jq '.runners[] | {name: .name, status: .status, busy: .busy}'
```

Expected output:

```json
{
  "busy": false,
  "name": "self-hosted-mixfm2",
  "status": "online"
}
```

## Usage in Workflows

To use self-hosted runner, specify in workflow:

```yaml
jobs:
  test:
    runs-on: self-hosted  # Instead of ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      # ... rest of workflow
```

## Maintenance

### Auto-Restart Configuration

**All services are configured to restart automatically:**

- **Docker service**: Enabled in systemd (`systemctl is-enabled docker` → `enabled`)
- **All containers**: Set to `restart: unless-stopped` policy
- **On server reboot**: Docker starts automatically, then all containers start
- **On container crash**: Containers restart automatically

**Verification commands:**

```bash
# Check Docker auto-start
ssh mixfm2 "systemctl is-enabled docker"
# Expected: enabled

# Check container restart policies
ssh mixfm2 "docker inspect github-runner runner-postgres runner-redis --format '{{.Name}}: {{.HostConfig.RestartPolicy.Name}}'"
# Expected output:
# /github-runner: RestartPolicy=unless-stopped
# /runner-postgres: RestartPolicy=unless-stopped
# /runner-redis: RestartPolicy=unless-stopped
```

**Test restart after reboot:**

```bash
# Stop all containers (simulates crash)
ssh mixfm2 "cd ~/github-runner && docker-compose stop"

# Start them back (simulates reboot)
ssh mixfm2 "cd ~/github-runner && docker-compose start"

# Verify all services are up
ssh mixfm2 "cd ~/github-runner && docker-compose ps"
```

### View Logs

```bash
ssh mixfm2
cd ~/github-runner

# All containers
docker-compose logs -f

# Specific container
docker logs -f github-runner
docker logs -f runner-postgres
docker logs -f runner-redis
```

### Restart Services

```bash
ssh mixfm2
cd ~/github-runner

# Restart all
docker-compose restart

# Restart specific service
docker-compose restart github-runner
```

### Stop Services

```bash
ssh mixfm2
cd ~/github-runner

docker-compose stop
```

### Update Images

```bash
ssh mixfm2
cd ~/github-runner

# Pull latest images
docker-compose pull

# Recreate containers
docker-compose up -d
```

### Renew Runner Token

Runner tokens expire after 1 hour. To regenerate:

```bash
# From local machine
gh api -X POST repos/loudmantrade/RealEstatesAntiFraud/actions/runners/registration-token --jq '.token'

# Update .env on server
ssh mixfm2
cd ~/github-runner
echo "RUNNER_TOKEN=<new_token>" > .env

# Restart runner
docker-compose restart github-runner
```

## Monitoring

### Check Resource Usage

```bash
ssh mixfm2

# CPU and memory
docker stats

# Disk usage
df -h
docker system df

# Container status
docker ps -a
```

### Clean Up

```bash
ssh mixfm2

# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes (careful!)
docker volume prune -f
```

## Benefits

✅ **Cost Savings**
- Unlimited free GitHub Actions minutes
- No $0.008/minute charges
- Estimated savings: $50-200/month

✅ **Performance**
- No queue time (dedicated runner)
- Faster CI execution
- Persistent dependency cache

✅ **Control**
- Fixed hardware specs (6 cores, 9.7GB RAM)
- Persistent PostgreSQL and Redis
- Full control over environment

## Troubleshooting

### Runner Offline

```bash
# Check container status
ssh mixfm2
docker ps | grep github-runner

# Check logs
docker logs github-runner --tail 100

# Restart if needed
cd ~/github-runner
docker-compose restart github-runner
```

### Database Connection Failed

```bash
# Check PostgreSQL health
docker ps | grep postgres

# Test connection
docker exec runner-postgres psql -U test_user -d realestate_test -c "SELECT 1;"

# Restart if needed
docker-compose restart runner-postgres
```

### Redis Connection Failed

```bash
# Check Redis health
docker ps | grep redis

# Test connection
docker exec runner-redis redis-cli ping

# Restart if needed
docker-compose restart runner-redis
```

### Disk Space Issues

```bash
# Check disk usage
ssh mixfm2
df -h
docker system df

# Clean up
docker system prune -a -f --volumes
```

## Security

- ✅ Runner isolated in Docker containers
- ✅ PostgreSQL/Redis not exposed externally (localhost only)
- ✅ Runner uses registration token (auto-rotates)
- ✅ Server accessible only via SSH
- ✅ Docker socket mounted (required for Docker-in-Docker)

## Future Migration

This setup is Phase 1 (Docker-based). Phase 2 will migrate to Kubernetes:
- Issue #170: Kubernetes migration with auto-scaling
- Actions Runner Controller for automatic scaling
- High availability with multiple replicas

## Related

- Issue #169: Self-hosted runner setup
- Issue #170: Kubernetes migration (Phase 2)
- Issue #111: CI/CD optimization project
