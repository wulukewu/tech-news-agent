# Developer Guide

Welcome to the Tech News Agent development guide.

## Project Structure

- `backend/`: FastAPI application, Discord bot, services, and tests.
- `frontend/`: Next.js application, UI components, and lib modules.
- `docs/`: Project documentation.
- `scripts/`: Development, CI, and migration scripts.

## Setup for Development

1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m app.main
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Testing

- **Backend**: `pytest -v`
- **Frontend**: `npm test`

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and add tests.
3. Run checks: `./scripts/ci-fix.sh && ./scripts/ci-local-test.sh`
4. Submit a Pull Request.
