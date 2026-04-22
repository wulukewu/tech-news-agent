# Tech News Agent - Deployment Guide

This document provides comprehensive instructions for deploying the Tech News Agent application in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Development Deployment](#development-deployment)
4. [Production Deployment with Docker](#production-deployment-with-docker)
5. [Cloud Deployment Options](#cloud-deployment-options)
6. [Health Checks and Monitoring](#health-checks-and-monitoring)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Node.js**: Version 20 or higher (for local development)
- **Python**: Version 3.11 or higher (for backend development)

### Required Accounts

- **Discord Developer Account**: For OAuth2 authentication
- **PostgreSQL Database**: For production deployment

## Environment Configuration

### Backend Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/tech_news_agent

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_REDIRECT_URI=http://localhost:8000/api/auth/discord/callback

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Environment
ENVIRONMENT=development
```

### Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Feature Flags (optional)
NEXT_PUBLIC_ENABLE_PWA=false
NEXT_PUBLIC_ENABLE_ANALYTICS=false
```

### Production Environment Variables

For production, update the URLs and ensure secure values:

```bash
# Backend .env
DATABASE_URL=postgresql://user:password@db-host:5432/tech_news_agent
DISCORD_REDIRECT_URI=https://yourdomain.com/api/auth/discord/callback
JWT_SECRET_KEY=generate_a_strong_random_key_here
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com
ENVIRONMENT=production

# Frontend .env.local
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_URL=https://yourdomain.com
```

## Development Deployment

### Using Docker Compose (Recommended)

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/tech-news-agent.git
   cd tech-news-agent
   ```

2. **Configure environment variables**:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the services**:

   ```bash
   docker-compose up -d
   ```

4. **Verify the services are running**:

   ```bash
   docker-compose ps
   ```

5. **View logs**:

   ```bash
   # All services
   docker-compose logs -f

   # Specific service
   docker-compose logs -f frontend
   docker-compose logs -f backend
   ```

6. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

7. **Stop the services**:
   ```bash
   docker-compose down
   ```

### Local Development (Without Docker)

#### Backend Setup

1. **Create virtual environment**:

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations**:

   ```bash
   alembic upgrade head
   ```

4. **Start the backend server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. **Install dependencies**:

   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**:

   ```bash
   npm run dev
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000

## Production Deployment with Docker

### Building Production Images

1. **Build the backend image**:

   ```bash
   cd backend
   docker build -t tech-news-agent-backend:latest -f Dockerfile .
   ```

2. **Build the frontend image**:
   ```bash
   cd frontend
   docker build -t tech-news-agent-frontend:latest -f Dockerfile .
   ```

### Production Docker Compose

Create a `docker-compose.prod.yml` file:

```yaml
version: '3.8'

services:
  backend:
    image: tech-news-agent-backend:latest
    container_name: tech-news-agent-backend
    restart: always
    env_file: .env
    ports:
      - '8000:8000'
    environment:
      - ENVIRONMENT=production
    networks:
      - tech-news-network
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8000/api/health']
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    image: tech-news-agent-frontend:latest
    container_name: tech-news-agent-frontend
    restart: always
    ports:
      - '3000:3000'
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
      - NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL}
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - tech-news-network
    healthcheck:
      test:
        [
          'CMD',
          'wget',
          '--no-verbose',
          '--tries=1',
          '--spider',
          'http://localhost:3000/api/health',
        ]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  tech-news-network:
    driver: bridge
```

### Deploy to Production

1. **Set production environment variables**:

   ```bash
   export NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
   export NEXT_PUBLIC_APP_URL=https://yourdomain.com
   ```

2. **Start production services**:

   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Verify deployment**:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   docker-compose -f docker-compose.prod.yml logs -f
   ```

## Cloud Deployment Options

### Option 1: Vercel (Frontend) + Railway/Render (Backend)

#### Deploy Frontend to Vercel

1. **Install Vercel CLI**:

   ```bash
   npm install -g vercel
   ```

2. **Deploy**:

   ```bash
   cd frontend
   vercel
   ```

3. **Configure environment variables** in Vercel dashboard:
   - `NEXT_PUBLIC_API_BASE_URL`
   - `NEXT_PUBLIC_APP_URL`

4. **Set up custom domain** (optional) in Vercel dashboard

#### Deploy Backend to Railway

1. **Install Railway CLI**:

   ```bash
   npm install -g @railway/cli
   ```

2. **Login and initialize**:

   ```bash
   railway login
   railway init
   ```

3. **Deploy**:

   ```bash
   cd backend
   railway up
   ```

4. **Configure environment variables** in Railway dashboard

### Option 2: AWS ECS (Elastic Container Service)

1. **Push images to ECR**:

   ```bash
   # Authenticate Docker to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Tag and push backend
   docker tag tech-news-agent-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/tech-news-agent-backend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/tech-news-agent-backend:latest

   # Tag and push frontend
   docker tag tech-news-agent-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/tech-news-agent-frontend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/tech-news-agent-frontend:latest
   ```

2. **Create ECS task definitions** for backend and frontend

3. **Create ECS services** with load balancers

4. **Configure environment variables** in task definitions

### Option 3: DigitalOcean App Platform

1. **Connect your GitHub repository** to DigitalOcean

2. **Configure build settings**:
   - Backend: Dockerfile path: `backend/Dockerfile`
   - Frontend: Dockerfile path: `frontend/Dockerfile`

3. **Set environment variables** in App Platform dashboard

4. **Deploy** and monitor in the dashboard

## Health Checks and Monitoring

### Health Check Endpoints

#### Backend Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Frontend Health Check

```bash
curl http://localhost:3000/api/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Monitoring Commands

```bash
# Check container status
docker-compose ps

# View resource usage
docker stats

# Check logs
docker-compose logs -f --tail=100

# Check specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Execute commands in containers
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Performance Monitoring

1. **Backend Metrics**:
   - API response times
   - Database query performance
   - Memory usage
   - CPU usage

2. **Frontend Metrics**:
   - Lighthouse scores
   - Core Web Vitals (LCP, FID, CLS)
   - Bundle size
   - Page load times

## Troubleshooting

### Common Issues

#### 1. Frontend Cannot Connect to Backend

**Symptoms**: CORS errors, network errors in browser console

**Solutions**:

- Verify `NEXT_PUBLIC_API_BASE_URL` is set correctly
- Check backend CORS configuration in `.env`
- Ensure backend is running and accessible
- Check Docker network configuration

```bash
# Test backend connectivity
curl http://localhost:8000/api/health

# Check Docker network
docker network inspect tech-news-network
```

#### 2. Docker Build Fails

**Symptoms**: Build errors, dependency installation failures

**Solutions**:

- Clear Docker cache: `docker system prune -a`
- Rebuild without cache: `docker-compose build --no-cache`
- Check Dockerfile syntax
- Verify all required files are present

#### 3. Database Connection Errors

**Symptoms**: Backend fails to start, database connection errors

**Solutions**:

- Verify `DATABASE_URL` is correct
- Ensure database is running and accessible
- Check database credentials
- Run migrations: `alembic upgrade head`

#### 4. Environment Variables Not Loading

**Symptoms**: Application uses default values, features not working

**Solutions**:

- Verify `.env` file exists and is in the correct location
- Check file permissions: `chmod 600 .env`
- Restart containers: `docker-compose restart`
- Check environment variable names (no typos)

#### 5. Port Already in Use

**Symptoms**: Cannot start services, port binding errors

**Solutions**:

```bash
# Find process using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or use different ports in docker-compose.yml
ports:
  - '3001:3000'  # Map to different host port
```

### Debugging Tips

1. **Enable verbose logging**:

   ```bash
   # Backend
   export LOG_LEVEL=DEBUG

   # Frontend
   export NEXT_PUBLIC_DEBUG=true
   ```

2. **Access container shell**:

   ```bash
   docker-compose exec backend bash
   docker-compose exec frontend sh
   ```

3. **Check container logs**:

   ```bash
   docker-compose logs -f --tail=100 backend
   docker-compose logs -f --tail=100 frontend
   ```

4. **Inspect Docker networks**:

   ```bash
   docker network ls
   docker network inspect tech-news-network
   ```

5. **Test API endpoints**:

   ```bash
   # Health check
   curl http://localhost:8000/api/health

   # API documentation
   open http://localhost:8000/docs
   ```

## Security Considerations

### Production Checklist

- [ ] Change all default passwords and secrets
- [ ] Use strong JWT secret key (minimum 32 characters)
- [ ] Enable HTTPS/TLS for all connections
- [ ] Configure proper CORS origins (no wildcards)
- [ ] Set secure cookie flags (HttpOnly, Secure, SameSite)
- [ ] Implement rate limiting
- [ ] Enable security headers (CSP, HSTS, X-Frame-Options)
- [ ] Regular security updates for dependencies
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] Firewall rules configured
- [ ] Secrets stored in secure vault (not in code)

### Environment-Specific Settings

**Development**:

- Debug mode enabled
- Detailed error messages
- Hot reload enabled
- CORS allows localhost

**Production**:

- Debug mode disabled
- Generic error messages
- Optimized builds
- Strict CORS policy
- HTTPS only
- Security headers enabled

## Backup and Recovery

### Database Backup

```bash
# Backup database
docker-compose exec backend pg_dump -U postgres tech_news_agent > backup.sql

# Restore database
docker-compose exec -T backend psql -U postgres tech_news_agent < backup.sql
```

### Application Data Backup

```bash
# Backup volumes
docker run --rm -v tech-news-agent_data:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz /data

# Restore volumes
docker run --rm -v tech-news-agent_data:/data -v $(pwd):/backup alpine tar xzf /backup/data-backup.tar.gz -C /
```

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer**: Use Nginx or cloud load balancer
2. **Multiple Frontend Instances**: Scale Next.js containers
3. **Multiple Backend Instances**: Scale FastAPI containers
4. **Database**: Use managed database service (RDS, Cloud SQL)
5. **Session Storage**: Use Redis for shared sessions

### Vertical Scaling

Adjust resource limits in `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**:
   - Review application logs
   - Check error rates
   - Monitor resource usage

2. **Monthly**:
   - Update dependencies
   - Review security advisories
   - Database optimization
   - Backup verification

3. **Quarterly**:
   - Performance audit
   - Security audit
   - Capacity planning
   - Disaster recovery test

### Getting Help

- **Documentation**: Check this guide and README files
- **Logs**: Review application and container logs
- **Issues**: Check GitHub issues for known problems
- **Community**: Join our Discord server for support

## Additional Resources

- [Next.js Deployment Documentation](https://nextjs.org/docs/deployment)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
