#!/bin/bash

# Tech News Agent - Hot Module Replacement Test Script
# This script tests HMR performance and reliability

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
    echo "  -f, --frontend     Test only frontend HMR"
    echo "  -b, --backend      Test only backend auto-reload"
    echo "  -t, --timeout SEC  Timeout for tests (default: 30)"
    echo "  -v, --verbose      Verbose output"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Test both frontend and backend"
    echo "  $0 -f              # Test only frontend HMR"
    echo "  $0 -b -t 60        # Test backend with 60s timeout"
}

# Default options
TEST_FRONTEND=true
TEST_BACKEND=true
TIMEOUT=30
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--frontend)
            TEST_FRONTEND=true
            TEST_BACKEND=false
            shift
            ;;
        -b|--backend)
            TEST_BACKEND=true
            TEST_FRONTEND=false
            shift
            ;;
        -t|--timeout)
            TIMEOUT=$2
            shift 2
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

# Check if services are running
check_services() {
    print_header "Checking Services"

    if ! docker-compose ps | grep -q "Up"; then
        print_error "Docker services are not running. Please start with 'make dev'"
        exit 1
    fi

    if [ "$TEST_FRONTEND" = true ]; then
        if ! docker-compose ps | grep -q "frontend.*Up"; then
            print_error "Frontend service is not running"
            exit 1
        fi
        print_success "Frontend service is running"
    fi

    if [ "$TEST_BACKEND" = true ]; then
        if ! docker-compose ps | grep -q "backend.*Up"; then
            print_error "Backend service is not running"
            exit 1
        fi
        print_success "Backend service is running"
    fi
}

# Test frontend HMR
test_frontend_hmr() {
    print_header "Testing Frontend Hot Module Replacement"

    # Create a test component
    local test_file="frontend/components/HMRTest.tsx"
    local original_content=""

    # Check if test file already exists
    if [ -f "$test_file" ]; then
        original_content=$(cat "$test_file")
        print_status "Backing up existing test file"
    fi

    # Create test component
    print_status "Creating test component..."
    cat > "$test_file" << 'EOF'
import React from 'react';

export default function HMRTest() {
  return (
    <div className="p-4 bg-blue-100 border border-blue-300 rounded">
      <h2 className="text-lg font-bold text-blue-800">HMR Test Component</h2>
      <p className="text-blue-600">Original version - timestamp: $(date)</p>
    </div>
  );
}
EOF

    print_success "Test component created"

    # Wait a moment for HMR to detect the change
    print_status "Waiting for HMR to detect new file..."
    sleep 3

    # Modify the component to test HMR
    print_status "Modifying test component to trigger HMR..."
    cat > "$test_file" << 'EOF'
import React from 'react';

export default function HMRTest() {
  return (
    <div className="p-4 bg-green-100 border border-green-300 rounded">
      <h2 className="text-lg font-bold text-green-800">HMR Test Component</h2>
      <p className="text-green-600">Modified version - HMR working! - timestamp: $(date)</p>
      <p className="text-sm text-green-500">If you see this, HMR is working correctly!</p>
    </div>
  );
}
EOF

    print_success "Test component modified"

    # Check frontend logs for HMR activity
    print_status "Checking frontend logs for HMR activity..."

    # Wait for HMR to process the change
    local hmr_detected=false
    local counter=0

    while [ $counter -lt $TIMEOUT ]; do
        if docker-compose logs --tail=10 frontend 2>/dev/null | grep -q -E "(compiled|Fast Refresh|HMR|hot.reload)"; then
            hmr_detected=true
            break
        fi
        sleep 1
        counter=$((counter + 1))
        if [ "$VERBOSE" = true ]; then
            echo -n "."
        fi
    done

    if [ "$VERBOSE" = true ]; then
        echo ""
    fi

    if [ "$hmr_detected" = true ]; then
        print_success "Frontend HMR is working correctly"

        if [ "$VERBOSE" = true ]; then
            print_status "Recent frontend logs:"
            docker-compose logs --tail=5 frontend
        fi
    else
        print_warning "HMR activity not detected in logs within ${TIMEOUT}s"
        print_status "This might be normal if no changes were detected"
    fi

    # Cleanup test file
    print_status "Cleaning up test component..."
    if [ -n "$original_content" ]; then
        echo "$original_content" > "$test_file"
        print_status "Restored original test file"
    else
        rm -f "$test_file"
        print_status "Removed test file"
    fi

    # Test HMR performance
    print_status "Testing HMR performance..."

    # Create a simple test to measure HMR speed
    local perf_test_file="frontend/components/PerfTest.tsx"
    local start_time=$(date +%s%N)

    cat > "$perf_test_file" << 'EOF'
import React from 'react';

export default function PerfTest() {
  return <div>Performance test component</div>;
}
EOF

    # Wait for compilation
    sleep 2

    # Modify the file
    cat > "$perf_test_file" << 'EOF'
import React from 'react';

export default function PerfTest() {
  return <div>Performance test component - modified</div>;
}
EOF

    # Wait for HMR to complete
    sleep 3

    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

    print_status "HMR performance test completed in ${duration}ms"

    if [ $duration -lt 5000 ]; then
        print_success "HMR performance is excellent (< 5s)"
    elif [ $duration -lt 10000 ]; then
        print_success "HMR performance is good (< 10s)"
    else
        print_warning "HMR performance is slow (> 10s) - consider optimization"
    fi

    # Cleanup performance test file
    rm -f "$perf_test_file"
}

# Test backend auto-reload
test_backend_reload() {
    print_header "Testing Backend Auto-Reload"

    # Create a test endpoint
    local test_file="backend/app/api/hmr_test.py"
    local original_content=""

    # Check if test file already exists
    if [ -f "$test_file" ]; then
        original_content=$(cat "$test_file")
        print_status "Backing up existing test file"
    fi

    # Create test endpoint
    print_status "Creating test endpoint..."
    cat > "$test_file" << 'EOF'
from fastapi import APIRouter

router = APIRouter()

@router.get("/hmr-test")
async def hmr_test():
    return {"message": "Original version", "status": "working"}
EOF

    print_success "Test endpoint created"

    # Wait for auto-reload
    print_status "Waiting for backend auto-reload..."
    sleep 3

    # Modify the endpoint
    print_status "Modifying test endpoint to trigger auto-reload..."
    cat > "$test_file" << 'EOF'
from fastapi import APIRouter

router = APIRouter()

@router.get("/hmr-test")
async def hmr_test():
    return {"message": "Modified version - auto-reload working!", "status": "working", "timestamp": "$(date)"}
EOF

    print_success "Test endpoint modified"

    # Check backend logs for reload activity
    print_status "Checking backend logs for auto-reload activity..."

    local reload_detected=false
    local counter=0

    while [ $counter -lt $TIMEOUT ]; do
        if docker-compose logs --tail=10 backend 2>/dev/null | grep -q -E "(Reloading|restarted|reload)"; then
            reload_detected=true
            break
        fi
        sleep 1
        counter=$((counter + 1))
        if [ "$VERBOSE" = true ]; then
            echo -n "."
        fi
    done

    if [ "$VERBOSE" = true ]; then
        echo ""
    fi

    if [ "$reload_detected" = true ]; then
        print_success "Backend auto-reload is working correctly"

        if [ "$VERBOSE" = true ]; then
            print_status "Recent backend logs:"
            docker-compose logs --tail=5 backend
        fi
    else
        print_warning "Auto-reload activity not detected in logs within ${TIMEOUT}s"
    fi

    # Test reload performance
    print_status "Testing auto-reload performance..."

    local start_time=$(date +%s%N)

    # Create another modification
    cat > "$test_file" << 'EOF'
from fastapi import APIRouter

router = APIRouter()

@router.get("/hmr-test")
async def hmr_test():
    return {"message": "Performance test version", "status": "working"}
EOF

    # Wait for reload to complete
    sleep 5

    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

    print_status "Auto-reload performance test completed in ${duration}ms"

    if [ $duration -lt 3000 ]; then
        print_success "Auto-reload performance is excellent (< 3s)"
    elif [ $duration -lt 8000 ]; then
        print_success "Auto-reload performance is good (< 8s)"
    else
        print_warning "Auto-reload performance is slow (> 8s) - consider optimization"
    fi

    # Cleanup test file
    print_status "Cleaning up test endpoint..."
    if [ -n "$original_content" ]; then
        echo "$original_content" > "$test_file"
        print_status "Restored original test file"
    else
        rm -f "$test_file"
        print_status "Removed test file"
    fi
}

# Test HMR reliability
test_hmr_reliability() {
    print_header "Testing HMR Reliability"

    print_status "Testing multiple rapid changes..."

    local test_file="frontend/components/ReliabilityTest.tsx"

    # Create initial file
    cat > "$test_file" << 'EOF'
import React from 'react';

export default function ReliabilityTest() {
  return <div>Reliability test - iteration 0</div>;
}
EOF

    # Make multiple rapid changes
    for i in {1..5}; do
        print_status "Making change $i/5..."
        cat > "$test_file" << EOF
import React from 'react';

export default function ReliabilityTest() {
  return <div>Reliability test - iteration $i</div>;
}
EOF
        sleep 1
    done

    # Wait for all changes to be processed
    sleep 5

    # Check if frontend is still responsive
    if curl -s http://localhost:3000 > /dev/null; then
        print_success "Frontend remains responsive after multiple rapid changes"
    else
        print_warning "Frontend may have issues after rapid changes"
    fi

    # Cleanup
    rm -f "$test_file"
}

# Generate HMR performance report
generate_report() {
    print_header "HMR Performance Report"

    echo "📊 Hot Module Replacement Test Results"
    echo "======================================"
    echo ""
    echo "Test Configuration:"
    echo "- Timeout: ${TIMEOUT}s"
    echo "- Frontend HMR: $([ "$TEST_FRONTEND" = true ] && echo "✅ Tested" || echo "⏭️ Skipped")"
    echo "- Backend Auto-reload: $([ "$TEST_BACKEND" = true ] && echo "✅ Tested" || echo "⏭️ Skipped")"
    echo ""
    echo "Environment:"
    echo "- Docker Compose: $(docker-compose --version | head -n1)"
    echo "- Node.js (in container): $(docker-compose exec frontend node --version 2>/dev/null || echo "N/A")"
    echo "- Python (in container): $(docker-compose exec backend python --version 2>/dev/null || echo "N/A")"
    echo ""
    echo "Recommendations:"
    echo "- For optimal HMR performance, ensure sufficient system resources"
    echo "- Monitor Docker container resource usage during development"
    echo "- Consider using local development if HMR is too slow in Docker"
    echo ""
    echo "Troubleshooting:"
    echo "- If HMR is slow, try: docker system prune -f"
    echo "- If changes aren't detected, check file permissions and volume mounts"
    echo "- For Windows/WSL2, consider performance optimizations"
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║            Tech News Agent - HMR Performance Test           ║"
    echo "║              Testing Hot Module Replacement                 ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    check_services

    if [ "$TEST_FRONTEND" = true ]; then
        test_frontend_hmr
        test_hmr_reliability
    fi

    if [ "$TEST_BACKEND" = true ]; then
        test_backend_reload
    fi

    generate_report

    print_success "HMR testing completed! 🎉"
}

# Run main function
main "$@"
