#!/bin/bash

# Tech News Agent - Development Setup Script
# This script sets up the development environment for the Tech News Agent project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    local missing_deps=()

    # Check Docker
    if ! command_exists docker; then
        missing_deps+=("docker")
    else
        print_success "Docker is installed ($(docker --version | cut -d' ' -f3 | cut -d',' -f1))"
    fi

    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        missing_deps+=("docker-compose")
    else
        if command_exists docker-compose; then
            print_success "Docker Compose is installed ($(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1))"
        else
            print_success "Docker Compose is installed ($(docker compose version --short))"
        fi
    fi

    # Check Node.js (optional for local development)
    if command_exists node; then
        print_success "Node.js is installed ($(node --version))"
    else
        print_warning "Node.js not found (optional for local development)"
    fi

    # Check Python (optional for local development)
    if command_exists python3; then
        print_success "Python 3 is installed ($(python3 --version))"
    elif command_exists python; then
        print_success "Python is installed ($(python --version))"
    else
        print_warning "Python not found (optional for local development)"
    fi

    # Check Make
    if command_exists make; then
        print_success "Make is installed"
    else
        print_warning "Make not found (optional but recommended)"
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo "Please install the missing dependencies and run this script again."
        echo ""
        echo "Installation guides:"
        echo "- Docker: https://docs.docker.com/get-docker/"
        echo "- Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

# Setup environment variables
setup_environment() {
    print_header "Setting Up Environment Variables"

    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            print_status "Copying .env.example to .env"
            cp .env.example .env
            print_success "Created .env file from template"
            print_warning "Please edit .env file with your actual configuration values"
            echo ""
            echo "Required variables to configure:"
            echo "- SUPABASE_URL and SUPABASE_KEY"
            echo "- GROQ_API_KEY"
            echo "- JWT_SECRET_KEY (generate with: openssl rand -hex 32)"
            echo "- Discord OAuth credentials (optional)"
            echo "- Discord bot token (optional)"
            echo ""
        else
            print_error ".env.example not found. Please create .env file manually."
            exit 1
        fi
    else
        print_success ".env file already exists"
    fi
}

# Install pre-commit hooks
setup_pre_commit() {
    print_header "Setting Up Pre-commit Hooks"

    if [ -f scripts/setup-pre-commit.sh ]; then
        print_status "Running pre-commit setup script"
        bash scripts/setup-pre-commit.sh
        print_success "Pre-commit hooks configured"
    else
        print_warning "Pre-commit setup script not found, skipping"
    fi
}

# Build Docker images
build_images() {
    print_header "Building Docker Images"

    print_status "Building development Docker images..."
    if docker-compose build; then
        print_success "Docker images built successfully"
    else
        print_error "Failed to build Docker images"
        exit 1
    fi
}

# Install local dependencies (optional)
install_local_deps() {
    print_header "Installing Local Dependencies (Optional)"

    # Frontend dependencies
    if [ -d frontend ] && command_exists npm; then
        print_status "Installing frontend dependencies..."
        cd frontend
        if npm install; then
            print_success "Frontend dependencies installed"
        else
            print_warning "Failed to install frontend dependencies"
        fi
        cd ..
    fi

    # Backend dependencies
    if [ -d backend ] && (command_exists python3 || command_exists python); then
        print_status "Installing backend dependencies..."
        cd backend

        # Try to create virtual environment
        if command_exists python3; then
            python3 -m venv venv 2>/dev/null || true
        elif command_exists python; then
            python -m venv venv 2>/dev/null || true
        fi

        # Install requirements
        if [ -f requirements.txt ]; then
            if [ -f venv/bin/activate ]; then
                source venv/bin/activate
                pip install -r requirements.txt
                print_success "Backend dependencies installed in virtual environment"
            else
                pip install -r requirements.txt
                print_success "Backend dependencies installed globally"
            fi
        fi
        cd ..
    fi
}

# Verify setup
verify_setup() {
    print_header "Verifying Setup"

    # Check if Docker images exist
    if docker images | grep -q "tech-news-agent"; then
        print_success "Docker images are available"
    else
        print_warning "Docker images not found, you may need to run 'make build-dev'"
    fi

    # Check if .env has required variables
    if [ -f .env ]; then
        local missing_vars=()

        # Check for critical variables
        if ! grep -q "^SUPABASE_URL=" .env || grep -q "^SUPABASE_URL=$" .env; then
            missing_vars+=("SUPABASE_URL")
        fi

        if ! grep -q "^SUPABASE_KEY=" .env || grep -q "^SUPABASE_KEY=$" .env; then
            missing_vars+=("SUPABASE_KEY")
        fi

        if ! grep -q "^GROQ_API_KEY=" .env || grep -q "^GROQ_API_KEY=$" .env; then
            missing_vars+=("GROQ_API_KEY")
        fi

        if ! grep -q "^JWT_SECRET_KEY=" .env || grep -q "^JWT_SECRET_KEY=$" .env; then
            missing_vars+=("JWT_SECRET_KEY")
        fi

        if [ ${#missing_vars[@]} -ne 0 ]; then
            print_warning "Missing or empty environment variables: ${missing_vars[*]}"
            print_warning "Please configure these variables in .env file"
        else
            print_success "Required environment variables are configured"
        fi
    fi
}

# Print next steps
print_next_steps() {
    print_header "Setup Complete!"

    echo "🎉 Development environment setup is complete!"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Configure environment variables in .env file"
    echo "   - Add your Supabase URL and service role key"
    echo "   - Add your Groq API key"
    echo "   - Generate JWT secret: openssl rand -hex 32"
    echo ""
    echo "2. Initialize database (if not done already):"
    echo "   - Run backend/scripts/init_supabase.sql in Supabase SQL Editor"
    echo ""
    echo "3. Start development environment:"
    echo "   make dev              # Start all services"
    echo "   make logs-dev         # View logs"
    echo ""
    echo "4. Access the application:"
    echo "   - Web: http://localhost:3000"
    echo "   - API: http://localhost:8000"
    echo "   - API Docs: http://localhost:8000/docs"
    echo ""
    echo "5. Useful development commands:"
    echo "   make lint             # Run code quality checks"
    echo "   make format           # Format code"
    echo "   make test             # Run tests"
    echo "   make clean            # Clean up containers and images"
    echo ""
    echo "📚 For more information, see:"
    echo "   - README.md"
    echo "   - docs/QUICKSTART.md"
    echo "   - docs/DEVELOPER_GUIDE.md"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                Tech News Agent - Dev Setup                  ║"
    echo "║              Setting up development environment              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    check_prerequisites
    setup_environment
    setup_pre_commit
    build_images
    install_local_deps
    verify_setup
    print_next_steps
}

# Run main function
main "$@"
