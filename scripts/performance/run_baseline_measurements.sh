#!/bin/bash
# Master script to run all performance baseline measurements.
# This script measures API response times, frontend bundle size, and component render performance.

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1

    print_status "Waiting for service at $url to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "Service is ready!"
            return 0
        fi

        print_status "Attempt $attempt/$max_attempts - Service not ready yet, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "Service at $url did not become ready within $((max_attempts * 2)) seconds"
    return 1
}

# Main script
main() {
    print_status "Starting performance baseline measurements..."

    # Create output directory
    mkdir -p scripts/performance/baselines

    # Check prerequisites
    print_status "Checking prerequisites..."

    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi

    if ! command_exists node; then
        print_error "Node.js is required but not installed"
        exit 1
    fi

    if ! command_exists npm; then
        print_error "npm is required but not installed"
        exit 1
    fi

    # Check if backend is running
    backend_running=false
    if port_in_use 8000; then
        print_status "Backend appears to be running on port 8000"
        if wait_for_service "http://localhost:8000/health"; then
            backend_running=true
        fi
    fi

    # Start backend if not running
    backend_pid=""
    if [ "$backend_running" = false ]; then
        print_status "Starting backend for API performance measurement..."

        # Check if we're in the right directory
        if [ ! -d "backend" ]; then
            print_error "Backend directory not found. Please run this script from the project root."
            exit 1
        fi

        # Start backend in background
        cd backend
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        fi

        # Install dependencies if needed
        if [ ! -f ".deps_installed" ]; then
            print_status "Installing backend dependencies..."
            pip install -r requirements.txt
            touch .deps_installed
        fi

        # Start the backend
        python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        backend_pid=$!
        cd ..

        # Wait for backend to be ready
        if ! wait_for_service "http://localhost:8000/health"; then
            print_error "Failed to start backend"
            if [ -n "$backend_pid" ]; then
                kill $backend_pid 2>/dev/null || true
            fi
            exit 1
        fi
    fi

    # Cleanup function
    cleanup() {
        if [ -n "$backend_pid" ]; then
            print_status "Stopping backend (PID: $backend_pid)..."
            kill $backend_pid 2>/dev/null || true
            wait $backend_pid 2>/dev/null || true
        fi
    }

    # Set trap for cleanup
    trap cleanup EXIT

    # 1. Measure API Performance
    print_status "=== Task 17.1.1: Measuring API Response Times ==="

    if ! python3 scripts/performance/measure_api_performance.py; then
        print_error "API performance measurement failed"
        exit 1
    fi

    print_success "API performance measurement completed"

    # 2. Measure Bundle Size
    print_status "=== Task 17.1.2: Measuring Frontend Bundle Size ==="

    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found"
        exit 1
    fi

    # Install frontend dependencies if needed
    cd frontend
    if [ ! -d "node_modules" ] || [ ! -f ".deps_installed" ]; then
        print_status "Installing frontend dependencies..."
        npm install
        touch .deps_installed
    fi
    cd ..

    if ! node scripts/performance/measure_bundle_size.js; then
        print_error "Bundle size measurement failed"
        exit 1
    fi

    print_success "Bundle size measurement completed"

    # 3. Measure Component Render Performance
    print_status "=== Task 17.1.3: Measuring Component Render Performance ==="

    cd frontend
    if ! npm run test -- __tests__/performance/component_render_performance.test.tsx --verbose; then
        print_error "Component render performance measurement failed"
        cd ..
        exit 1
    fi
    cd ..

    print_success "Component render performance measurement completed"

    # Generate summary report
    print_status "=== Generating Performance Baseline Summary ==="

    python3 -c "
import json
import os
from pathlib import Path
from datetime import datetime

baseline_dir = Path('scripts/performance/baselines')
if not baseline_dir.exists():
    print('No baseline files found')
    exit(1)

# Find latest baseline files
api_files = sorted(baseline_dir.glob('api_baseline_*.json'))
bundle_files = sorted(baseline_dir.glob('bundle_baseline_*.json'))
component_files = sorted(baseline_dir.glob('component_baseline_*.json'))

summary = {
    'timestamp': datetime.now().isoformat(),
    'measurements_completed': []
}

if api_files:
    with open(api_files[-1]) as f:
        api_data = json.load(f)
    summary['api_performance'] = {
        'file': str(api_files[-1]),
        'overall_mean_response_time': api_data['summary']['overall_mean_response_time'],
        'average_success_rate': api_data['summary']['average_success_rate'],
        'endpoints_measured': api_data['summary']['total_endpoints_measured']
    }
    summary['measurements_completed'].append('API Performance')

if bundle_files:
    with open(bundle_files[-1]) as f:
        bundle_data = json.load(f)
    summary['bundle_size'] = {
        'file': str(bundle_files[-1]),
        'total_size_mb': bundle_data['summary']['totalBundleSizeMB'],
        'js_chunks_count': bundle_data['summary']['jsChunksCount'],
        'js_chunks_size_mb': bundle_data['summary']['jsChunksSizeMB']
    }
    summary['measurements_completed'].append('Bundle Size')

if component_files:
    with open(component_files[-1]) as f:
        component_data = json.load(f)
    summary['component_performance'] = {
        'file': str(component_files[-1]),
        'average_render_time': component_data['summary']['averageRenderTime'],
        'components_tested': component_data['summary']['totalComponentsTested'],
        'slowest_component': component_data['summary']['slowestComponent']
    }
    summary['measurements_completed'].append('Component Performance')

# Save summary
summary_file = baseline_dir / f'baseline_summary_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.json'
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f'Performance baseline summary saved to: {summary_file}')
print()
print('=== PERFORMANCE BASELINE SUMMARY ===')
print(f'Timestamp: {summary[\"timestamp\"]}')
print(f'Measurements completed: {len(summary[\"measurements_completed\"])}')

for measurement in summary['measurements_completed']:
    print(f'✓ {measurement}')

if 'api_performance' in summary:
    api = summary['api_performance']
    print(f'\\nAPI Performance:')
    print(f'  Mean response time: {api[\"overall_mean_response_time\"]:.2f}ms')
    print(f'  Success rate: {api[\"average_success_rate\"]:.1f}%')
    print(f'  Endpoints tested: {api[\"endpoints_measured\"]}')

if 'bundle_size' in summary:
    bundle = summary['bundle_size']
    print(f'\\nBundle Size:')
    print(f'  Total size: {bundle[\"total_size_mb\"]} MB')
    print(f'  JS chunks: {bundle[\"js_chunks_count\"]} files ({bundle[\"js_chunks_size_mb\"]} MB)')

if 'component_performance' in summary:
    comp = summary['component_performance']
    print(f'\\nComponent Performance:')
    print(f'  Average render time: {comp[\"average_render_time\"]:.2f}ms')
    print(f'  Components tested: {comp[\"components_tested\"]}')
    print(f'  Slowest component: {comp[\"slowest_component\"]}')

print(f'\\nAll baseline files saved in: scripts/performance/baselines/')
"

    print_success "Performance baseline measurements completed successfully!"
    print_status "Baseline files are available in: scripts/performance/baselines/"
}

# Run main function
main "$@"
