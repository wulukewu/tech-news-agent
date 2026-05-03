# Tech News Agent — Documentation

Complete documentation for the Tech News Agent project. Use the sections below to navigate.

---

## 🚀 Getting Started

| | |
|---|---|
| [Quick Start](guides/quick-start.md) | Get up and running in minutes |
| [Environment Setup](setup/env-setup-guide.md) | Configure `.env` and credentials |
| [OAuth Setup](setup/oauth-setup-guide.md) | Discord OAuth configuration |
| [Docker Guide](docker/docker-guide.md) | Run with Docker Compose |
| [User Guide](guides/user-guide.md) | End-user feature walkthrough |

---

## 🏗️ Architecture & Design

| | |
|---|---|
| [Architecture Overview](architecture/architecture-overview.md) | System design, components, data flow |
| [Project Overview](architecture/project-overview.md) | High-level project summary |
| [Notification Lock Mechanism](architecture/notification-lock-mechanism.md) | Distributed locking for notifications |
| [API Contracts](api/api-contracts.md) | Full REST API specification |
| [Smart Conversation Endpoints](api/smart-conversation-endpoints.md) | Conversation & QA API details |

---

## ⚙️ Backend

| | |
|---|---|
| [Backend Overview](backend/README.md) | Index of all backend docs |
| [Bot / Discord Cogs](backend/bot/README.md) | Discord bot architecture and cog reference |
| [Core Layer](backend/core/README.md) | Config, errors, logger, validators |
| [Services](backend/services/README.md) | Service layer, scheduler, rate limiting |
| [QA Agent](backend/qa-agent/README.md) | Conversational AI subsystem |
| [Repositories](backend/repositories/README.md) | Data access layer |
| [Notifications](backend/notifications/README.md) | Notification system internals |
| [Migrations](backend/migrations/README.md) | Database migration guides |
| [Implementation Details](backend/implementation/README.md) | Specific feature implementations |
| [Tests](backend/tests/README.md) | Test structure and coverage |
| [Troubleshooting](backend/troubleshooting/README.md) | Backend-specific issues |

---

## 🎨 Frontend

| | |
|---|---|
| [Frontend Overview](frontend/README.md) | Index of all frontend docs |
| [i18n Guide](frontend/i18n-guide.md) | Internationalization (EN/ZH) |
| [Design Tokens](frontend/design-tokens.md) | Color, typography, spacing system |
| [ESLint i18n Rules](frontend/eslint-i18n-rules.md) | Linting rules for translations |
| [Components](frontend/components/README.md) | UI component documentation |
| [Contexts](frontend/contexts/README.md) | React context providers |
| [Lib / API Client](frontend/lib/README.md) | API client, hooks, utilities |
| [Tests](frontend/tests/README.md) | Frontend test structure |

---

## 🚢 Deployment

| | |
|---|---|
| [Deployment Guide](deployment/deployment-guide.md) | Full deployment walkthrough |
| [Deployment Checklist](deployment/deployment-checklist.md) | Pre-deploy checklist |
| [Rollback Procedures](deployment/rollback-procedures.md) | How to roll back a release |
| [Netlify Frontend](deployment/netlify-frontend.md) | Deploy frontend to Netlify |
| [Render Backend](deployment/render-deployment.md) | Deploy backend to Render |
| [Public Bot Setup](deployment/public-bot-setup.md) | Discord bot for public servers |
| [All Deployment Docs](deployment/README.md) | Full deployment index |

---

## 💻 Development

| | |
|---|---|
| [Developer Guide](development/developer-guide.md) | Setup, workflow, conventions |
| [Development Workflows](development/development-workflows.md) | Day-to-day dev process |
| [Code Quality](development/code-quality.md) | Linting, formatting, standards |
| [Pre-commit Hooks](development/pre-commit-hooks.md) | Automated checks on commit |
| [Refactoring Guide](development/refactoring-migration-guide.md) | Large-scale refactoring patterns |
| [All Development Docs](development/README.md) | Full development index |

---

## 🧪 Testing

| | |
|---|---|
| [Testing Guide](testing/testing-guide.md) | Test strategy and how to run tests |
| [Test Fixtures](testing/test-fixtures.md) | Shared fixtures and factories |
| [Test Data Isolation](testing/test-data-isolation.md) | Keeping tests independent |
| [All Testing Docs](testing/README.md) | Full testing index |

---

## 🔧 Setup & Configuration

| | |
|---|---|
| [Environment Variables](setup/env-setup-guide.md) | All env vars explained |
| [Quick Env Setup](setup/quick-env-setup.md) | Minimal setup for local dev |
| [All Setup Docs](setup/README.md) | Full setup index |

---

## 🗄️ Database Migrations

| | |
|---|---|
| [Migration Guide](migrations/migration-guide.md) | How to run and write migrations |
| [Migration 009 Guide](migrations/migration-009-guide.md) | Specific migration reference |
| [Scripts Reference](scripts/README.md) | Migration and utility scripts |

---

## ✨ Features & Improvements

| | |
|---|---|
| [Features](features/README.md) | Feature design documents |
| [Improvements](improvements/README.md) | Roadmaps and improvement proposals |
| [UX Improvements](ux-improvements/README.md) | UI/UX change records |
| [Implementation Notes](implementation/README.md) | Feature implementation summaries |

---

## 🚨 Fixes & Troubleshooting

| | |
|---|---|
| [Troubleshooting Guide](troubleshooting/troubleshooting-guide.md) | Common issues and solutions |
| [Known Fixes](fixes/README.md) | Documented bug fixes |

---

## 📦 Archive

Historical development records (task completions, CI status snapshots, fix summaries).

→ [Browse Archive](archive/README.md)

---

## 📁 Directory Structure

```
docs/
├── api/                  API contracts and endpoint specs
├── architecture/         System architecture and design decisions
├── backend/              Backend documentation (bot, core, services, qa-agent, ...)
├── ci/                   CI/CD configuration and guides
├── deployment/           Deployment guides (Netlify, Render, Docker, ...)
├── development/          Developer guides, workflows, code quality
├── docker/               Docker-specific documentation
├── features/             Feature design documents
├── fixes/                Key bug fix documentation
├── frontend/             Frontend documentation (i18n, components, lib, ...)
├── guides/               User-facing guides and quick starts
├── implementation/       Feature implementation summaries
├── improvements/         Improvement proposals and roadmaps
├── migrations/           Database migration guides
├── scripts/              Script usage documentation
├── setup/                Environment and configuration setup
├── testing/              Test strategy and guides
├── troubleshooting/      Troubleshooting guides
├── ui-improvements/      UI change records
├── ux-improvements/      UX change records
└── archive/              Historical task/CI/fix records
```
