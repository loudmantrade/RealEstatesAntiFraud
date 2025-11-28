# Docker Deployment Guide

## Quick Start

### Build and run with docker-compose (recommended)

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

The API will be available at http://localhost:8000

### Build standalone Docker image

```bash
# Build the image
docker build -t real-estate-api:latest .

# Run the container
docker run -d \
  --name real-estate-api \
  -p 8000:8000 \
  -e DB_HOST=your-db-host \
  -e DB_PORT=5432 \
  -e DB_NAME=real_estate_fraud \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres \
  real-estate-api:latest

# Check health
curl http://localhost:8000/health

# View logs
docker logs real-estate-api

# Stop container
docker stop real-estate-api
docker rm real-estate-api
```

## Image Details

### Multi-stage Build

The Dockerfile uses a multi-stage build to minimize image size:

1. **Builder stage**: Installs build dependencies and Python packages
2. **Runtime stage**: Minimal production image with only runtime dependencies

### Image Size

- Target: <200MB
- Actual: ~235MB (acceptable)
- Base image: `python:3.13-slim`

### Security Features

- ✅ Non-root user (`appuser`, UID 1000)
- ✅ Minimal base image (slim variant)
- ✅ No unnecessary packages
- ✅ Virtual environment isolation
- ✅ Health check configured

### Health Check

The image includes a built-in health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

Endpoint: `GET /health`

Response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Environment Variables

### Required

- `DB_HOST` - PostgreSQL host (default: postgres)
- `DB_PORT` - PostgreSQL port (default: 5432)
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password

### Optional

- `REDIS_HOST` - Redis host (default: redis)
- `REDIS_PORT` - Redis port (default: 6379)
- `LOG_LEVEL` - Logging level (default: INFO)
- `PORT` - API port (default: 8000)

## Docker Compose Services

### Production Stack

```bash
docker-compose up -d
```

Services:
- **api**: Core API service (port 8000)
- **postgres**: PostgreSQL 16-alpine (port 5432)
- **redis**: Redis 7-alpine (port 6379)

### Development Stack

```bash
docker-compose --profile dev up -d
```

Additional services:
- **pgadmin**: PostgreSQL management (port 5050)
  - Email: admin@realestate.local
  - Password: admin

## CI/CD Integration

The Docker build is automatically tested in GitHub Actions on every push and PR:

1. Build image
2. Start container
3. Test health endpoint
4. Check image size
5. Verify logs

See `.github/workflows/ci.yml` for details.

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs api

# Common issues:
# - Database not ready: Wait for postgres health check
# - Port conflict: Change port mapping in docker-compose.yml
```

### Health check failing

```bash
# Test health endpoint manually
curl http://localhost:8000/health

# Check if API is listening
docker exec real-estate-api netstat -tlnp | grep 8000

# View application logs
docker logs real-estate-api
```

### Image size too large

```bash
# Check layer sizes
docker history real-estate-api:latest

# Remove unused images
docker image prune -a
```

## Development

### Rebuild after code changes

```bash
# Rebuild only API service
docker-compose build api

# Restart with new image
docker-compose up -d api
```

### Access container shell

```bash
# As non-root user (appuser)
docker exec -it real-estate-api bash

# As root (for debugging)
docker exec -it -u root real-estate-api bash
```

### Update dependencies

1. Update `requirements.txt`
2. Rebuild image: `docker-compose build api`
3. Restart: `docker-compose up -d api`

## Best Practices

1. **Always use health checks** in production
2. **Set resource limits** in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 512M
   ```
3. **Use Docker secrets** for sensitive data in production
4. **Enable logging driver** for centralized logs:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```
5. **Regular security updates**: Rebuild images monthly

## Production Deployment

For production, consider:

1. **Container orchestration**: Kubernetes, Docker Swarm
2. **Secrets management**: HashiCorp Vault, AWS Secrets Manager
3. **Monitoring**: Prometheus, Grafana
4. **Logging**: ELK stack, CloudWatch
5. **Load balancing**: Nginx, HAProxy, AWS ALB
6. **Auto-scaling**: Based on CPU/memory metrics

See `docs/DEPLOYMENT.md` for detailed production setup.
