#!/bin/bash

# Tech News Agent - Deployment Verification Script
# This script verifies that the Docker Compose deployment is working correctly

set -e

echo "🚀 Tech News Agent - Deployment Verification"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success message
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error message
error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print warning message
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if Docker is installed
echo "1. Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    success "Docker is installed: $DOCKER_VERSION"
else
    error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
echo ""
echo "2. Checking Docker Compose installation..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    success "Docker Compose is installed: $COMPOSE_VERSION"
else
    error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
echo ""
echo "3. Checking environment configuration..."
if [ -f ".env" ]; then
    success ".env file exists"
else
    warning ".env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        success "Created .env from .env.example"
        warning "Please edit .env with your configuration before proceeding"
    else
        error ".env.example not found. Cannot create .env file."
        exit 1
    fi
fi

# Check if frontend .env.local exists
if [ -f "frontend/.env.local" ]; then
    success "frontend/.env.local file exists"
else
    warning "frontend/.env.local not found"
    if [ -f "frontend/.env.example" ]; then
        cp frontend/.env.example frontend/.env.local
        success "Created frontend/.env.local from .env.example"
    fi
fi

# Check if containers are running
echo ""
echo "4. Checking Docker containers..."
if docker-compose ps | grep -q "Up"; then
    success "Docker containers are running"
    docker-compose ps
else
    warning "Docker containers are not running"
    echo "   Starting containers..."
    docker-compose up -d
    echo "   Waiting for containers to start..."
    sleep 10
fi

# Check backend health
echo ""
echo "5. Checking backend health..."
BACKEND_URL="http://localhost:8000"
if curl -f -s "${BACKEND_URL}/api/health" > /dev/null 2>&1; then
    success "Backend is healthy and responding"
    BACKEND_RESPONSE=$(curl -s "${BACKEND_URL}/api/health")
    echo "   Response: $BACKEND_RESPONSE"
else
    error "Backend is not responding at ${BACKEND_URL}/api/health"
    echo "   Checking backend logs..."
    docker-compose logs --tail=20 backend
fi

# Check frontend health
echo ""
echo "6. Checking frontend health..."
FRONTEND_URL="http://localhost:3000"
if curl -f -s "${FRONTEND_URL}" > /dev/null 2>&1; then
    success "Frontend is healthy and responding"
else
    warning "Frontend is not responding at ${FRONTEND_URL}"
    echo "   This might be normal if Next.js is still building..."
    echo "   Checking frontend logs..."
    docker-compose logs --tail=20 frontend
fi

# Check Docker network
echo ""
echo "7. Checking Docker network..."
if docker network inspect tech-news-network > /dev/null 2>&1; then
    success "Docker network 'tech-news-network' exists"
else
    error "Docker network 'tech-news-network' does not exist"
fi

# Check container connectivity
echo ""
echo "8. Checking container connectivity..."
if docker-compose exec -T backend ping -c 1 frontend > /dev/null 2>&1; then
    success "Backend can reach frontend"
else
    warning "Backend cannot reach frontend (this might be normal)"
fi

# Display resource usage
echo ""
echo "9. Container resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose ps -q)

# Summary
echo ""
echo "=============================================="
echo "📊 Verification Summary"
echo "=============================================="
echo ""
echo "Backend URL:  ${BACKEND_URL}"
echo "Frontend URL: ${FRONTEND_URL}"
echo "API Docs:     ${BACKEND_URL}/docs"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
echo "To restart services:"
echo "  docker-compose restart"
echo ""

# Final check
if curl -f -s "${BACKEND_URL}/api/health" > /dev/null 2>&1 && curl -f -s "${FRONTEND_URL}" > /dev/null 2>&1; then
    success "All checks passed! 🎉"
    echo ""
    echo "You can now access the application at:"
    echo "  Frontend: ${FRONTEND_URL}"
    echo "  Backend:  ${BACKEND_URL}"
    echo "  API Docs: ${BACKEND_URL}/docs"
else
    warning "Some checks failed. Please review the output above."
    echo ""
    echo "Common issues:"
    echo "  - Containers still starting (wait a few minutes)"
    echo "  - Environment variables not configured"
    echo "  - Ports already in use"
    echo "  - Database connection issues"
    echo ""
    echo "Check logs with: docker-compose logs -f"
fi
