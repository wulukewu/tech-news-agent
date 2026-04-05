#!/bin/bash

# Test script for manual scheduler trigger API endpoints
# Usage: ./scripts/test_manual_trigger.sh [API_BASE_URL] [JWT_TOKEN]

API_BASE_URL=${1:-"http://localhost:8000"}
JWT_TOKEN=${2:-""}

echo "Testing Manual Scheduler Trigger API"
echo "====================================="
echo ""

if [ -z "$JWT_TOKEN" ]; then
    echo "⚠️  Warning: No JWT token provided. Requests will fail with 401."
    echo "Usage: $0 [API_BASE_URL] [JWT_TOKEN]"
    echo ""
fi

# Test 1: Trigger scheduler
echo "Test 1: POST /api/scheduler/trigger"
echo "------------------------------------"
if [ -z "$JWT_TOKEN" ]; then
    curl -X POST "${API_BASE_URL}/api/scheduler/trigger" \
        -H "Content-Type: application/json" \
        -w "\nHTTP Status: %{http_code}\n" \
        -s
else
    curl -X POST "${API_BASE_URL}/api/scheduler/trigger" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${JWT_TOKEN}" \
        -w "\nHTTP Status: %{http_code}\n" \
        -s
fi
echo ""
echo ""

# Test 2: Get scheduler status
echo "Test 2: GET /api/scheduler/status"
echo "----------------------------------"
if [ -z "$JWT_TOKEN" ]; then
    curl -X GET "${API_BASE_URL}/api/scheduler/status" \
        -H "Content-Type: application/json" \
        -w "\nHTTP Status: %{http_code}\n" \
        -s
else
    curl -X GET "${API_BASE_URL}/api/scheduler/status" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${JWT_TOKEN}" \
        -w "\nHTTP Status: %{http_code}\n" \
        -s
fi
echo ""
echo ""

# Test 3: Health check (public endpoint)
echo "Test 3: GET /health/scheduler"
echo "------------------------------"
curl -X GET "${API_BASE_URL}/health/scheduler" \
    -H "Content-Type: application/json" \
    -w "\nHTTP Status: %{http_code}\n" \
    -s
echo ""
echo ""

echo "====================================="
echo "Tests completed!"
echo ""
echo "Expected results:"
echo "- Test 1 & 2: 401 without token, 202/200 with valid token"
echo "- Test 3: 200 or 503 (public endpoint)"
