# Tech News Agent Documentation

Complete documentation for the Tech News Agent project.

## 📚 Quick Navigation

### Getting Started

- [Quick Start Guide](./QUICKSTART.md) - Get up and running in minutes
- [Environment Setup](./setup/ENV_SETUP_GUIDE.md) - Complete environment variable reference
- [Environment File Structure](./ENV_FILE_STRUCTURE.md) - 📁 Why we use a single .env file
- [Docker Guide](./docker/DOCKER_GUIDE.md) - Docker deployment instructions

### User Guides

- [User Guide](./USER_GUIDE.md) - Using the web interface and Discord bot
- [Manual Scheduler Trigger](./MANUAL_SCHEDULER_TRIGGER.md) - On-demand article fetching
- [Manual Trigger Examples](./MANUAL_TRIGGER_EXAMPLES.md) - Practical examples

### Developer Resources

- [Developer Guide](./DEVELOPER_GUIDE.md) - Architecture and API reference
- [Project Overview](./PROJECT_OVERVIEW.md) - Comprehensive system documentation
- [Architecture](./ARCHITECTURE.md) - System architecture details
- [API Contracts](./API_CONTRACTS.md) - API specifications
- [Code Quality](./CODE_QUALITY.md) - Code standards and best practices

### Development Workflows

- [Development Workflows](./DEVELOPMENT_WORKFLOWS.md) - Common development tasks
- [Pre-commit Hooks](./PRE_COMMIT_HOOKS.md) - Git hooks setup
- [Pre-commit Quick Reference](./PRE_COMMIT_QUICK_REFERENCE.md) - Quick reference
- [Quick Start Code Quality](./QUICK_START_CODE_QUALITY.md) - Code quality tools

### Testing

- [Testing Guide](./testing/supabase-migration-testing.md) - Testing strategies and tools
- [Testing Documentation](./TESTING.md) - Comprehensive testing guide

### Deployment

- [Deployment Guide](./deployment/DEPLOYMENT.md) - Production deployment steps
- [Deployment Checklist](./deployment/deployment-checklist.md) - Complete Netlify + Render deployment guide
- [Render Deployment Guide](./deployment/render-deployment.md) - 🚀 Complete Render deployment with memory optimization
- [OAuth Redirect Fix](./deployment/oauth-redirect-fix.md) - 🔧 Fix Discord OAuth redirect to localhost issue
- [Render Environment Setup](./deployment/render-env-setup.md) - Quick environment variable setup for Render
- [Netlify Deployment Complete](./deployment/netlify-deployment-complete.md) - ✅ Current deployment status & next steps
- [Netlify Frontend Guide](./deployment/netlify-frontend.md) - Next.js deployment to Netlify (免費版)
- [Netlify Deployment Troubleshooting](./deployment/netlify-deployment.md) - Fix 404 errors and common issues
- [Netlify Fixes Summary](./deployment/netlify-fixes-summary.md) - Summary of all fixes applied
- [Render Backend Guide](./deployment/render-backend.md) - FastAPI deployment to Render (免費版)
- [Vercel Frontend Guide](./deployment/vercel-frontend.md) - Alternative: Next.js on Vercel
- [Public Bot Setup](./PUBLIC_BOT_SETUP.md) - Making your bot public
- [Public Bot Migration](./PUBLIC_BOT_MIGRATION_SUMMARY.md) - Migration guide
- [Public Bot Quickstart](./PUBLIC_BOT_QUICKSTART.md) - Quick setup

### Migration & Refactoring

- [Migration Guide](./MIGRATION_GUIDE.md) - Database and code migrations
- [Refactoring Migration Guide](./REFACTORING_MIGRATION_GUIDE.md) - Refactoring strategies
- [Rollback Procedures](./ROLLBACK_PROCEDURES.md) - How to rollback changes

### Backend Documentation

- [Reading List API Implementation](./backend/READING_LIST_API_IMPLEMENTATION.md) - Reading list feature details

### Project Management

- [Task Summaries](./tasks/) - Completed task documentation
- [TypeScript Errors Fix Plan](./tasks/typescript-errors-fix-plan.md) - Systematic plan to fix all type errors
- [CI Documentation](./ci/) - Continuous integration setup
- [File Organization](./FILE_ORGANIZATION.md) - Project structure guide
- [Restructure Summary](./RESTRUCTURE_SUMMARY.md) - Recent restructuring changes

### Troubleshooting

- [Troubleshooting Guide](./TROUBLESHOOTING.md) - Common issues and solutions
- [Rate Limit Guide](./RATE_LIMIT_GUIDE.md) - Handling API rate limits
- [Frontend Errors Fix Guide](./frontend-errors-fix-guide.md) - Comprehensive frontend error solutions
- [Frontend Quick Fix](./frontend-quick-fix.md) - Quick fixes for common frontend issues
- [Service Worker Dev Guide](./service-worker-dev-guide.md) - Service worker development and debugging

### Validation & Verification

- [Final Validation Cutover](./FINAL_VALIDATION_CUTOVER.md) - Production readiness checklist
- [Final Verification Checklist](./FINAL_VERIFICATION_CHECKLIST.md) - Pre-launch verification

## 📂 Documentation Structure

```
docs/
├── README.md                          # This file
├── setup/                             # Setup guides
│   └── ENV_SETUP_GUIDE.md
├── docker/                            # Docker documentation
│   └── DOCKER_GUIDE.md
├── deployment/                        # Deployment guides
│   ├── DEPLOYMENT.md
│   └── DEPLOYMENT_CHECKLIST.md
├── testing/                           # Testing documentation
│   └── supabase-migration-testing.md
├── development/                       # Development notes
├── backend/                           # Backend-specific docs
│   └── READING_LIST_API_IMPLEMENTATION.md
├── tasks/                             # Task completion summaries
│   ├── TASK_11.3_COMPLETION_REPORT.md
│   ├── TASK_14.4_COVERAGE_SUMMARY.md
│   ├── TASK_15.1_COMPLETION_SUMMARY.md
│   ├── TASK_15.3_CI_QUALITY_ENHANCEMENT_SUMMARY.md
│   ├── TASK_16_COMPLETION_SUMMARY.md
│   └── TASK_18_COMPLETION_SUMMARY.md
└── ci/                                # CI/CD documentation
    ├── CI_FIXES_SUMMARY.md
    └── FINAL_CI_STATUS.md
```

## 🔍 Finding What You Need

### I want to...

**Get started quickly**
→ [Quick Start Guide](./QUICKSTART.md)

**Set up environment variables**
→ [Environment Setup](./setup/ENV_SETUP_GUIDE.md)

**Deploy with Docker**
→ [Docker Guide](./docker/DOCKER_GUIDE.md)

**Use the Discord bot**
→ [User Guide](./USER_GUIDE.md)

**Understand the architecture**
→ [Architecture](./ARCHITECTURE.md) or [Project Overview](./PROJECT_OVERVIEW.md)

**Write tests**
→ [Testing Guide](./testing/supabase-migration-testing.md)

**Deploy to production (免費版)**
→ [Netlify + Render 完整指南](./deployment/deployment-checklist.md)

**Fix Render memory issues**
→ [Render Deployment Guide](./deployment/render-deployment.md)

**Fix OAuth redirect to localhost**
→ [OAuth Redirect Fix](./deployment/oauth-redirect-fix.md)

**Set up Render environment variables**
→ [Render Environment Setup](./deployment/render-env-setup.md)

**Deploy Next.js to Netlify**
→ [Netlify Frontend Guide](./deployment/netlify-frontend.md)

**Fix Netlify 404 errors**
→ [Netlify Troubleshooting](./deployment/netlify-deployment.md)

**Deploy FastAPI to Render**
→ [Render Backend Guide](./deployment/render-backend.md)

**Troubleshoot issues**
→ [Troubleshooting Guide](./TROUBLESHOOTING.md) or [Frontend Errors Fix](./frontend-errors-fix-guide.md)

**Contribute code**
→ [Developer Guide](./DEVELOPER_GUIDE.md) and [Code Quality](./CODE_QUALITY.md)

## 📝 Documentation Standards

All documentation follows these principles:

1. **Clear and Concise**: Get to the point quickly
2. **Examples Included**: Show, don't just tell
3. **Up-to-date**: Regularly reviewed and updated
4. **Searchable**: Use clear headings and keywords
5. **Accessible**: Written for various skill levels

## 🤝 Contributing to Documentation

Found an error or want to improve the docs?

1. Edit the relevant markdown file
2. Follow the existing format and style
3. Test any code examples
4. Submit a pull request

## 📞 Need Help?

- 🐛 [Report Issues](https://github.com/yourusername/tech-news-agent/issues)
- 💬 [Ask Questions](https://github.com/yourusername/tech-news-agent/discussions)
- 📧 Contact the maintainers

---

**Last Updated**: April 2026
