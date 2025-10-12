# Deployment Guide

This guide covers deploying Ragora in various environments, from development to production.

## 🎯 Deployment Options

### 1. Development Deployment

For local development and testing.

#### Using DevContainer (Recommended)

```bash
# Clone repository
git clone https://github.com/vahidlari/aiapps.git
cd aiapps

# Open in VS Code DevContainer
code .
# Click "Reopen in Container"

# Download and start database server
wget https://github.com/vahidlari/aiapps/releases/latest/download/ragora-database-server.tar.gz
tar -xzf ragora-database-server.tar.gz
cd ragora-database-server
./database-manager.sh start

# Install Ragora in dev mode
cd ../ragora
pip install -e ".[dev]"
```

See devcontainer documentation in the root folder of the development repository.

#### Local Installation

```bash
# Install Ragora
pip install ragora

# Download and start database server
wget https://github.com/vahidlari/aiapps/releases/latest/download/ragora-database-server.tar.gz
tar -xzf ragora-database-server.tar.gz
cd ragora-database-server
./database-manager.sh start
```

### 2. Production Deployment

For production environments with proper security and scalability.

#### Using Ragora Database Server (Quick Setup)

For smaller production deployments or getting started quickly:

```bash
# Download database server
wget https://github.com/vahidlari/aiapps/releases/latest/download/ragora-database-server.tar.gz
tar -xzf ragora-database-server.tar.gz
cd ragora-database-server

# Configure for production (edit config.yaml)
cp examples/config-production.yaml config.yaml
nano config.yaml  # Enable authentication, adjust settings

# Start with production config
./database-manager.sh start

# Install Ragora
pip install ragora

# Deploy your application
# ... your application setup ...
```

**Advantages:**
- Quick setup with pre-configured Weaviate
- Zero dependencies (only Docker)
- Includes configuration examples for production
- Suitable for single-server deployments

**Note:** For large-scale production with multiple servers, clustering, or cloud-native deployment, see the custom Docker Compose section below.

#### Custom Docker Compose Deployment

For larger production environments with custom requirements, create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  weaviate:
    image: semitechnologies/weaviate:1.22.4
    restart: always
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_APIKEY_ENABLED: 'true'
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: '${WEAVIATE_API_KEY}'
      AUTHENTICATION_APIKEY_USERS: 'admin'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-transformers'
      ENABLE_MODULES: 'text2vec-transformers'
      TRANSFORMERS_INFERENCE_API: 'http://t2v-transformers:8080'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
    networks:
      - ragora_network

  t2v-transformers:
    image: semitechnologies/transformers-inference:sentence-transformers-multi-qa-MiniLM-L6-cos-v1
    restart: always
    environment:
      ENABLE_CUDA: '0'
    networks:
      - ragora_network

  ragora-api:
    build: .
    restart: always
    ports:
      - "8000:8000"
    environment:
      WEAVIATE_URL: 'http://weaviate:8080'
      WEAVIATE_API_KEY: '${WEAVIATE_API_KEY}'
    depends_on:
      - weaviate
    networks:
      - ragora_network

volumes:
  weaviate_data:

networks:
  ragora_network:
    driver: bridge
```

Deploy:

```bash
# Set environment variables
export WEAVIATE_API_KEY="your-secure-api-key"

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Cloud Deployment

#### AWS Deployment

**Using ECS (Elastic Container Service):**

```bash
# Build and push image
docker build -t ragora-app .
docker tag ragora-app:latest ${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/ragora:latest
docker push ${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/ragora:latest

# Deploy to ECS (using AWS CLI or Console)
aws ecs create-service \
  --cluster ragora-cluster \
  --service-name ragora-service \
  --task-definition ragora-task \
  --desired-count 2
```

**Weaviate on AWS:**
- Use Weaviate Cloud Services (WCS)
- Or deploy on EC2 with proper security groups
- Consider using RDS for metadata storage

#### Google Cloud Platform

**Using Cloud Run:**

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/${PROJECT_ID}/ragora
gcloud run deploy ragora \
  --image gcr.io/${PROJECT_ID}/ragora \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Weaviate on GCP:**
- Use Weaviate Cloud Services
- Or deploy on GKE (Google Kubernetes Engine)
- Consider using Cloud SQL for metadata

#### Azure Deployment

**Using Azure Container Instances:**

```bash
# Create resource group
az group create --name ragora-rg --location eastus

# Deploy container
az container create \
  --resource-group ragora-rg \
  --name ragora-app \
  --image youracr.azurecr.io/ragora:latest \
  --dns-name-label ragora-app \
  --ports 8000
```

## 🔒 Security Configuration

### Authentication

Enable API key authentication for Weaviate:

```python
from ragora.core import DatabaseManager

db_manager = DatabaseManager(
    url="http://weaviate:8080",
    api_key="your-secure-api-key"
)
```

Environment variables:

```bash
export WEAVIATE_URL="http://weaviate:8080"
export WEAVIATE_API_KEY="your-secure-api-key"
export EMBEDDING_MODEL="all-mpnet-base-v2"
```

### Network Security

**Firewall Rules:**
- Allow inbound traffic only on necessary ports (8000 for API, 8080 for Weaviate)
- Use VPC/private networks for internal communication
- Enable HTTPS for external access

**Example AWS Security Group:**
```bash
# Allow API access
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0

# Allow Weaviate (internal only)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 8080 \
  --source-group sg-yyyyy
```

### Data Encryption

**At Rest:**
```yaml
# docker-compose.yml
services:
  weaviate:
    volumes:
      - type: volume
        source: weaviate_data
        target: /var/lib/weaviate
        volume:
          encrypted: true
```

**In Transit:**
- Use TLS/SSL for all connections
- Configure reverse proxy (nginx, traefik) with SSL certificates
- Use Let's Encrypt for free SSL certificates

## ⚡ Performance Optimization

### Scaling Strategies

#### Vertical Scaling

Increase resources for single instance:

```yaml
services:
  ragora-api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 16G
        reservations:
          cpus: '2.0'
          memory: 8G
```

#### Horizontal Scaling

Multiple instances with load balancer:

```yaml
services:
  ragora-api:
    deploy:
      replicas: 3
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Weaviate Optimization

**Resource Allocation:**
```yaml
services:
  weaviate:
    environment:
      LIMIT_RESOURCES: 'true'
      DISK_USE_WARNING_PERCENTAGE: 80
      DISK_USE_READONLY_PERCENTAGE: 90
    deploy:
      resources:
        limits:
          memory: 8G
```

**Sharding Configuration:**
```python
# For large datasets
schema = {
    "class": "Documents",
    "shardingConfig": {
        "desiredCount": 3,
        "actualCount": 3
    }
}
```

### Caching

Implement caching for frequent queries:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_query(query: str, top_k: int):
    return kbm.query(query, search_type="hybrid", top_k=top_k)
```

## 📊 Monitoring

### Application Monitoring

**Using Prometheus:**

```python
from prometheus_client import Counter, Histogram

query_counter = Counter('ragora_queries_total', 'Total queries')
query_duration = Histogram('ragora_query_duration_seconds', 'Query duration')

@query_duration.time()
def query_with_metrics(query: str):
    query_counter.inc()
    return kbm.query(query)
```

**Using Application Insights (Azure):**

```python
from applicationinsights import TelemetryClient

tc = TelemetryClient('your-instrumentation-key')

def query_with_telemetry(query: str):
    tc.track_event('Query', {'query': query})
    result = kbm.query(query)
    tc.flush()
    return result
```

### Database Monitoring

Monitor Weaviate health:

```python
import requests

def check_weaviate_health():
    response = requests.get('http://weaviate:8080/v1/.well-known/ready')
    return response.status_code == 200
```

### Logging

Configure structured logging:

```python
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('ragora')

def log_query(query: str, results: int, duration: float):
    logger.info(json.dumps({
        'event': 'query',
        'query': query,
        'results': results,
        'duration': duration
    }))
```

## 🔄 Backup and Recovery

### Data Backup

**Weaviate Backup:**

```bash
# Backup Weaviate data
docker exec weaviate tar czf /tmp/backup.tar.gz /var/lib/weaviate
docker cp weaviate:/tmp/backup.tar.gz ./backups/

# Schedule with cron
0 2 * * * /path/to/backup-script.sh
```

**Automated Backups:**

```yaml
services:
  backup:
    image: alpine
    volumes:
      - weaviate_data:/data:ro
      - ./backups:/backups
    command: |
      sh -c "tar czf /backups/backup-$(date +%Y%m%d).tar.gz /data"
```

### Disaster Recovery

**Recovery Steps:**

```bash
# Stop Weaviate
docker-compose stop weaviate

# Restore data
docker run --rm -v weaviate_data:/data -v ./backups:/backups alpine \
  tar xzf /backups/backup-20240101.tar.gz -C /data

# Start Weaviate
docker-compose start weaviate
```

## 🧪 Testing Deployment

### Health Checks

```python
def health_check():
    """Comprehensive health check."""
    checks = {
        'weaviate': check_weaviate_health(),
        'embedding_model': check_embedding_model(),
        'api': check_api_endpoints()
    }
    return all(checks.values()), checks
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/query

# Using Locust
pip install locust
locust -f locustfile.py --host=http://localhost:8000
```

## 🔗 Related Documentation

- [Getting Started](getting_started.md) - Initial setup
- [Architecture](architecture.md) - System architecture
- [Contributing](contributing.md) - Development guidelines
- [Database Server](../../../tools/database_server/README.md) - Database setup

## 📝 Production Checklist

- [ ] Enable authentication on Weaviate
- [ ] Configure SSL/TLS certificates
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups
- [ ] Implement rate limiting
- [ ] Set up logging aggregation
- [ ] Configure auto-scaling policies
- [ ] Document disaster recovery procedures
- [ ] Set up health checks
- [ ] Configure security groups/firewall rules
- [ ] Review and harden security settings
- [ ] Test backup and recovery procedures

