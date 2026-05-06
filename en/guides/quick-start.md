# Quick Start Guide

This guide will help you get the Tech News Agent project up and running quickly.

## 🚀 Getting Started

There are two primary ways to run the project: using `Makefile` (recommended) or directly with `Docker Compose`.

### Method 1: Using Makefile (Recommended)

The `Makefile` provides convenient commands to manage your development and production environments.

#### Development Environment

```bash
# Start the development environment with hot reloading
make dev

# View logs for the development environment
make logs-dev

# Stop the development environment
make down-dev
```

#### Production Environment

```bash
# Start the production environment
make prod

# View logs for the production environment
make logs-prod

# Stop the production environment
make down-prod
```

### Method 2: Using Docker Compose Directly

You can also manage the services directly with `docker-compose` commands.

#### Development Environment

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

#### Production Environment

```bash
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml down
```

---

## 📝 First-Time Setup

Before running the application, you need to set up your environment variables.

1.  **Copy the example environment file:**

    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file** with your credentials and necessary settings. You can use a text editor like `nano`:

    ```bash
    nano .env
    ```

    For detailed explanations of all environment variables, refer to the [Environment Setup Guide](../setup/env-setup-guide.md).

3.  **Start the Development Environment:**

    ```bash
    make dev
    # or
    docker-compose up -d
    ```

4.  **Access the Application:**
    *   **Frontend**: `http://localhost:3000`
    *   **Backend API**: `http://localhost:8000`
    *   **API Documentation**: `http://localhost:8000/docs`

---

## 🔄 Development Workflow

### Frontend Development

*   Make changes in the `frontend/` directory.
*   Your browser will automatically hot-reload upon saving.
*   No need to restart containers.

### Backend Development

*   Make changes in the `backend/app/` directory.
*   FastAPI will automatically hot-reload upon saving.
*   No need to restart containers.

### Installing New Packages

#### Frontend (Node.js)

```bash
# Enter the frontend container
docker exec -it tech-news-agent-frontend-dev sh

# Install a new package
npm install <package-name>

# Exit the container
exit

# Rebuild (if necessary)
make build-dev
```

#### Backend (Python)

```bash
# Enter the backend container
docker exec -it tech-news-agent-backend-dev bash

# Install a new package
pip install <package-name>

# Update requirements.txt
pip freeze > requirements.txt

# Exit the container
exit

# Rebuild
make build-dev
```

---

## 🐛 Common Issues

### Q: Hot reload is not working?

A: Try rebuilding the containers:

```bash
make up-dev
# or
docker-compose up -d --build
```

### Q: Port already in use?

A: Modify the port mapping in `docker-compose.yml`. For example, to use port 3001 for the frontend:

```yaml
ports:
  - '3001:3000' # Change to 3001
```

### Q: Containers failing to start?

A: Check the logs to identify the problem:

```bash
make logs-dev
# or
docker-compose logs
```

### Q: How to clean up all containers and images?

A: Use the clean command:

```bash
make clean
```

---

## 📊 Viewing All Makefile Commands

You can see all available `Makefile` commands with their descriptions by running:

```bash
make help
```

---

## 🎯 Deploying to Production

1.  Ensure your environment variables are correctly set, especially security-related ones.
2.  Start the services using the production configuration:

    ```bash
    make prod
    # or
    docker-compose -f docker-compose.prod.yml up -d --build
    ```

3.  Check the service status:

    ```bash
    make logs-prod
    ```

4.  Access the application via your domain or IP address.

---

## 📚 More Information

For more detailed instructions, refer to the [Docker Guide](../docker/docker-guide.md).
