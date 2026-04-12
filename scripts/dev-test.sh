#!/bin/bash

# Tech News Agent - Development Testing Script
# This script runs tests for both frontend and backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -f, --frontend     Run only frontend tests"
    echo "  -b, --backend      Run only backend tests"
    echo "  -u, --unit         Run only unit tests"
    echo "  -i, --integration  Run only integration tests"
    echo "  -p, --property     Run only property-based tests"
    echo "  -e, --e2e          Run only end-to-end tests"
    echo "  -c, --coverage     Run tests with coverage report"
    echo "  -w, --watch        Run tests in watch mode (frontend only)"
    echo "  -v, --verbose      Run tests with verbose output"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Run all tests"
    echo "  $0 -f -c           # Run frontend tests with coverage"
    echo "  $0 -b -u           # Run backend unit tests only"
    echo "  $0 -p -v           # Run property tests with verbose output"
}

# Default options
RUN_FRONTEND=true
RUN_BACKEND=true
RUN_UNIT=true
RUN_INTEGRATION=true
RUN_PROPERTY=true
RUN_E2E=true
WITH_COVERAGE=false
WATCH_MODE=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--frontend)
            RUN_FRONTEND=true
            RUN_BACKEND=false
            shift
            ;;
        -b|--backend)
            RUN_BACKEND=true
            RUN_FRONTEND=false
            shift
            ;;
        -u|--unit)
            RUN_UNIT=true
            RUN_INTEGRATION=false
            RUN_PROPERTY=false
            RUN_E2E=false
            shift
            ;;
        -i|--integration)
            RUN_INTEGRATION=true
            RUN_UNIT=false
            RUN_PROPERTY=false
            RUN_E2E=false
            shift
            ;;
        -p|--property)
            RUN_PROPERTY=true
            RUN_UNIT=false
            RUN_INTEGRATION=false
            RUN_E2E=false
            shift
            ;;
        -e|--e2e)
            RUN_E2E=true
            RUN_UNIT=false
            RUN_INTEGRATION=false
            RUN_PROPERTY=false
            shift
            ;;
        -c|--coverage)
            WITH_COVERAGE=true
            shift
            ;;
        -w|--watch)
            WATCH_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Run backend tests
run_backend_tests() {
    print_header "Running Backend Tests"

    if [ ! -d "backend" ]; then
        print_error "Backend directory not found"
        return 1
    fi

    cd backend

    # Check if we're in Docker or local environment
    if docker-compose ps | grep -q "backend.*Up"; then
        print_status "Running tests in Docker container"

        # Build test command
        local test_cmd="pytest"

        if [ "$VERBOSE" = true ]; then
            test_cmd="$test_cmd -v"
        fi

        if [ "$WITH_COVERAGE" = true ]; then
            test_cmd="$test_cmd --cov=app --cov-report=html --cov-report=term"
        fi

        # Add specific test filters
        if [ "$RUN_UNIT" = true ] && [ "$RUN_INTEGRATION" = false ] && [ "$RUN_PROPERTY" = false ]; then
            test_cmd="$test_cmd tests/unit/"
        elif [ "$RUN_INTEGRATION" = true ] && [ "$RUN_UNIT" = false ] && [ "$RUN_PROPERTY" = false ]; then
            test_cmd="$test_cmd tests/integration/"
        elif [ "$RUN_PROPERTY" = true ] && [ "$RUN_UNIT" = false ] && [ "$RUN_INTEGRATION" = false ]; then
            test_cmd="$test_cmd tests/test_database_properties.py"
        fi

        # Run tests in Docker
        docker-compose exec backend $test_cmd

    else
        print_status "Running tests locally"

        # Check if virtual environment exists
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
            print_status "Activated virtual environment"
        fi

        # Build test command
        local test_cmd="pytest"

        if [ "$VERBOSE" = true ]; then
            test_cmd="$test_cmd -v"
        fi

        if [ "$WITH_COVERAGE" = true ]; then
            test_cmd="$test_cmd --cov=app --cov-report=html --cov-report=term"
        fi

        # Add specific test filters
        if [ "$RUN_UNIT" = true ] && [ "$RUN_INTEGRATION" = false ] && [ "$RUN_PROPERTY" = false ]; then
            test_cmd="$test_cmd tests/unit/"
        elif [ "$RUN_INTEGRATION" = true ] && [ "$RUN_UNIT" = false ] && [ "$RUN_PROPERTY" = false ]; then
            test_cmd="$test_cmd tests/integration/"
        elif [ "$RUN_PROPERTY" = true ] && [ "$RUN_UNIT" = false ] && [ "$RUN_INTEGRATION" = false ]; then
            test_cmd="$test_cmd tests/test_database_properties.py"
        fi

        # Run tests
        $test_cmd
    fi

    local exit_code=$?
    cd ..

    if [ $exit_code -eq 0 ]; then
        print_success "Backend tests passed"
    else
        print_error "Backend tests failed"
        return $exit_code
    fi
}

# Run frontend tests
run_frontend_tests() {
    print_header "Running Frontend Tests"

    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found"
        return 1
    fi

    cd frontend

    # Check if we're in Docker or local environment
    if docker-compose ps | grep -q "frontend.*Up"; then
        print_status "Running tests in Docker container"

        # Build test command
        local test_cmd="npm run"

        if [ "$RUN_UNIT" = true ] && [ "$RUN_INTEGRATION" = false ] && [ "$RUN_E2E" = false ]; then
            test_cmd="$test_cmd test:unit"
        elif [ "$RUN_INTEGRATION" = true ] && [ "$RUN_UNIT" = false ] && [ "$RUN_E2E" = false ]; then
            test_cmd="$test_cmd test:integration"
        elif [ "$RUN_PROPERTY" = true ] && [ "$RUN_UNIT" = false ] && [ "$RUN_INTEGRATION" = false ]; then
            test_cmd="$test_cmd test:property"
        elif [ "$RUN_E2E" = true ] && [ "$RUN_UNIT" = false ] && [ "$RUN_INTEGRATION" = false ]; then
            test_cmd="$test_cmd test:e2e"
        elif [ "$WITH_COVERAGE" = true ]; then
            test_cmd="$test_cmd test:coverage"
        elif [ "$WATCH_MODE" = true ]; then
            test_cmd="$test_cmd test:watch"
        else
            test_cmd="$test_cmd test"
        fi

        # Run tests in Docker
        docker-compose exec frontend $test_cmd

    else
        print_status "Running tests locally"

        # Check if node_modules exists
        if [ ! -d "node_modules" ]; then
            print_status "Installing dependencies..."
            npm install
        fi

        # Build test command
        local test_cmd="npm run"

        if [ "$RUN_UNIT" = true ] && [ "$RUN_INTEGRATION" = false ] && [ "$RUN_E2E" = false ]; then
            test_cmd="$test_cmd test:unit"
        elif [ "$RUN_INTEGRATION" = true ] && [ "$RUN_UNIT" = false ] && [ "$RUN_E2E" = false ]; then
            test_cmd="$test_cmd test:integration"
        elif [ "$RUN_PROPERTY" = true ] && [ "$RUN_UNIT" = false ] && [ "$RUN_INTEGRATION" = false ]; then
            test_cmd="$test_cmd test:property"
        elif [ "$RUN_E2E" = true ] && [ "$RUN_UNIT" = false ] && [ "$RUN_INTEGRATION" = false ]; then
            test_cmd="$test_cmd test:e2e"
        elif [ "$WITH_COVERAGE" = true ]; then
            test_cmd="$test_cmd test:coverage"
        elif [ "$WATCH_MODE" = true ]; then
            test_cmd="$test_cmd test:watch"
        else
            test_cmd="$test_cmd test"
        fi

        # Run tests
        $test_cmd
    fi

    local exit_code=$?
    cd ..

    if [ $exit_code -eq 0 ]; then
        print_success "Frontend tests passed"
    else
        print_error "Frontend tests failed"
        return $exit_code
    fi
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                Tech News Agent - Test Runner                ║"
    echo "║                  Running development tests                  ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    local overall_exit_code=0

    # Run backend tests
    if [ "$RUN_BACKEND" = true ]; then
        if ! run_backend_tests; then
            overall_exit_code=1
        fi
    fi

    # Run frontend tests
    if [ "$RUN_FRONTEND" = true ]; then
        if ! run_frontend_tests; then
            overall_exit_code=1
        fi
    fi

    # Print summary
    print_header "Test Summary"

    if [ $overall_exit_code -eq 0 ]; then
        print_success "All tests passed! 🎉"
    else
        print_error "Some tests failed. Please check the output above."
    fi

    exit $overall_exit_code
}

# Run main function
main "$@"
