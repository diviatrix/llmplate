# Deployment Guide

This guide covers deploying the LLM Template Backend to production.

## Prerequisites

- Docker and Docker Compose installed
- Domain name with SSL certificate
- Server with at least 4GB RAM
- MongoDB backup strategy
- API keys for LLM providers

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/llm-template-backend.git
cd llm-template-backend
```

### 2. Configure Environment

```bash
cp .env.example .env.prod
# Edit .env.prod with production values
```

Required environment variables:
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `MONGODB_URL` - Production MongoDB connection string
- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `GOOGLE_CLIENT_ID/SECRET` - OAuth credentials
- `GITHUB_CLIENT_ID/SECRET` - OAuth credentials

### 3. Deploy with Docker Compose

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Production Configuration

### SSL/TLS Setup

1. Generate SSL certificates:
```bash
# Using Let's Encrypt
certbot certonly --standalone -d yourdomain.com
```

2. Update nginx configuration:
```bash
# Copy certificates to docker/ssl/
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/ssl/key.pem
```

### Database Setup

1. Initialize MongoDB with authentication:
```javascript
// docker/mongo-init.js
db.createUser({
  user: "llm_user",
  pwd: "secure_password",
  roles: [
    {
      role: "readWrite",
      db: "llm_template_db"
    }
  ]
});
```

2. Enable MongoDB replica set for transactions:
```bash
docker exec -it llm_template_mongodb mongosh
rs.initiate()
```

### Performance Optimization

1. **Nginx Caching**:
```nginx
# Add to nginx.conf
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g;
```

2. **MongoDB Indexes**:
```javascript
// Run in MongoDB shell
db.users.createIndex({ email: 1 }, { unique: true });
db.templates.createIndex({ created_by: 1, created_at: -1 });
db.generations.createIndex({ user_id: 1, created_at: -1 });
```

3. **Redis Configuration**:
```bash
# Add to redis.conf
maxmemory 1gb
maxmemory-policy allkeys-lru
```

## Monitoring

### Health Checks

- API Health: `https://yourdomain.com/health`
- Celery Flower: `https://yourdomain.com:5555`
- Prometheus: `https://yourdomain.com:9090`
- Grafana: `https://yourdomain.com:3000`

### Log Aggregation

1. Install Elasticsearch and Kibana:
```yaml
# Add to docker-compose.prod.yml
elasticsearch:
  image: elasticsearch:8.11.0
  environment:
    - discovery.type=single-node
    - ES_JAVA_OPTS=-Xms512m -Xmx512m

kibana:
  image: kibana:8.11.0
  ports:
    - "5601:5601"
```

2. Configure Filebeat for log shipping:
```yaml
filebeat.inputs:
- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'
```

### Alerts

Configure alerts in Grafana:
- High error rate (> 5%)
- Slow response time (> 1s)
- High memory usage (> 80%)
- Failed Celery tasks

## Backup and Recovery

### Automated Backups

1. Create backup script:
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
docker exec llm_template_mongodb mongodump --out $BACKUP_DIR
tar -czf "$BACKUP_DIR.tar.gz" $BACKUP_DIR
rm -rf $BACKUP_DIR

# Upload to S3
aws s3 cp "$BACKUP_DIR.tar.gz" s3://your-backup-bucket/
```

2. Schedule with cron:
```bash
0 2 * * * /opt/llm-template-backend/scripts/backup.sh
```

### Disaster Recovery

1. **Database Restore**:
```bash
# Download backup
aws s3 cp s3://your-backup-bucket/backup.tar.gz .

# Extract and restore
tar -xzf backup.tar.gz
docker exec -i llm_template_mongodb mongorestore backup/
```

2. **Application Rollback**:
```bash
# Tag releases
docker tag llm-template-backend:latest llm-template-backend:v1.0.0

# Rollback if needed
docker-compose -f docker-compose.prod.yml down
docker tag llm-template-backend:v1.0.0 llm-template-backend:latest
docker-compose -f docker-compose.prod.yml up -d
```

## Scaling

### Horizontal Scaling

1. **Application Instances**:
```yaml
# docker-compose.prod.yml
app:
  deploy:
    replicas: 4
```

2. **Load Balancer Configuration**:
```nginx
upstream app_backend {
    least_conn;
    server app_1:8000 max_fails=3 fail_timeout=30s;
    server app_2:8000 max_fails=3 fail_timeout=30s;
    server app_3:8000 max_fails=3 fail_timeout=30s;
    server app_4:8000 max_fails=3 fail_timeout=30s;
}
```

3. **Celery Workers**:
```bash
# Scale workers based on queue length
celery -A app.celery_app worker --autoscale=10,3
```

### Database Scaling

1. **MongoDB Sharding**:
```javascript
sh.enableSharding("llm_template_db")
sh.shardCollection("llm_template_db.generations", { user_id: 1 })
```

2. **Read Replicas**:
```python
# app/database.py
read_preference = ReadPreference.SECONDARY_PREFERRED
```

## Security Hardening

### Network Security

1. **Firewall Rules**:
```bash
# Allow only necessary ports
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

2. **Docker Network Isolation**:
```yaml
networks:
  frontend:
    internal: false
  backend:
    internal: true
```

### Application Security

1. **Rate Limiting**:
```python
# app/middleware.py
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

2. **Security Headers**:
```python
# app/main.py
from secure import SecureHeaders
secure_headers = SecureHeaders()
app.add_middleware(SecureHeaders.framework.fastapi())
```

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**:
```bash
# Check MongoDB logs
docker logs llm_template_mongodb

# Test connection
docker exec -it app python -c "from app.database import check_database_health; import asyncio; print(asyncio.run(check_database_health()))"
```

2. **Celery Tasks Not Processing**:
```bash
# Check Celery logs
docker logs llm_template_celery

# Inspect queues
docker exec -it llm_template_celery celery -A app.celery_app inspect active
```

3. **High Memory Usage**:
```bash
# Check container stats
docker stats

# Limit memory
docker update --memory="1g" llm_template_app
```

### Debug Mode

Enable debug logging:
```python
# .env.prod
DEBUG=true
LOG_LEVEL=DEBUG
```

View detailed logs:
```bash
docker-compose -f docker-compose.prod.yml logs -f app | grep ERROR
```

## Maintenance

### Regular Tasks

- **Weekly**: Review logs for errors
- **Monthly**: Update dependencies
- **Quarterly**: Security audit
- **Yearly**: Major version upgrades

### Update Procedure

1. **Test in Staging**:
```bash
git checkout -b staging
# Make changes
docker-compose -f docker-compose.staging.yml up -d
# Run tests
make test
```

2. **Deploy to Production**:
```bash
git checkout main
git merge staging
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

3. **Rollback if Needed**:
```bash
git revert HEAD
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

## Cost Optimization

### Resource Usage

- Use spot instances for Celery workers
- Enable MongoDB compression
- Implement caching for expensive operations
- Use CDN for static assets

### Monitoring Costs

Track API usage:
```python
# app/middleware.py
@app.middleware("http")
async def track_api_usage(request: Request, call_next):
    # Log to monitoring service
    await log_api_call(request.url.path, request.client.host)
    return await call_next(request)
```

## Support

For production support:
- Check logs: `docker-compose logs -f`
- Monitor health: `curl https://yourdomain.com/health`
- Review metrics in Grafana
- Check Sentry for errors

For emergencies:
1. Scale down to single instance
2. Disable background tasks
3. Enable maintenance mode
4. Contact support team