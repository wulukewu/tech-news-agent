#!/bin/bash

# Load environment variables from .env file
set -a
source ../.env
set +a

# Run the cleanup script
python3 scripts/cleanup_invalid_users.py
