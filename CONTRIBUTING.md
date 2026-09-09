# Contributing to MindMirror

Thank you for your interest in contributing to MindMirror! This guide will help you get started.

## Table of Contents

* [Code of Conduct](#code-of-conduct)
* [Getting Started](#getting-started)
* [Development Setup](#development-setup)
* [How to Contribute](#how-to-contribute)
* [Reporting Bugs](#reporting-bugs)
* [Suggesting Features](#suggesting-features)
* [Development Workflow](#development-workflow)
* [Code Style](#code-style)
* [Testing](#testing)
* [Pull Request Process](#pull-request-process)

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

MindMirror is an open-source, privacy-first AI companion for emotional reflection. Contributions of all kinds are welcome:

* Bug fixes
* New features
* Documentation improvements
* Tests
* Accessibility improvements
* UI/UX enhancements

## Development Setup

### Prerequisites

* Docker Desktop
* Git
* At least **8 GB RAM**
* At least **10 GB free disk space** (for AI model downloads)

### Clone and Start

```bash
git clone https://github.com/HASSANFARYAD/MindMirror.git
cd MindMirror
cp .env.example .env
docker-compose up --build
```

Once running:

* **Frontend:** http://localhost:3000
* **Backend API:** http://localhost:8000
* **API Docs:** http://localhost:8000/docs

### Environment Variables

Open `.env` and configure the values for your environment. See `.env.example` for all available options.

## How to Contribute

### First-Time Contributors

Look for issues labeled:

* `good first issue` — starter-friendly tasks
* `help wanted` — contributions needed
* `documentation` — doc improvements
* `enhancement` — new features or improvements

### Contribution Types

| Type | Examples |
|------|----------|
| Bug fixes | Fix broken functionality, error handling |
| Features | New CBT techniques, integrations, UI components |
| Documentation | README improvements, inline docs, guides |
| Tests | Unit tests, integration tests |
| Accessibility | ARIA labels, keyboard navigation, screen reader support |
| Internationalization | Translations, locale support |

## Reporting Bugs

Open an issue and include:

1. **What happened** — a clear description of the bug
2. **What you expected to happen** — the expected behavior
3. **Steps to reproduce** — numbered steps to trigger the bug
4. **Environment** — browser, OS, Docker version
5. **Logs or screenshots** — any relevant output

## Suggesting Features

Open a feature request and include:

1. **The problem** — what issue does this solve?
2. **Your vision** — how should the feature work?
3. **Why it matters** — who benefits and how?
4. **Implementation ideas** — any technical thoughts (optional)

## Development Workflow

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/MindMirror.git
cd MindMirror
```

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:

* `feature/description` — new features
* `fix/description` — bug fixes
* `docs/description` — documentation changes
* `test/description` — test additions or fixes

### 3. Make Changes

* Follow the code style guidelines below
* Keep changes focused — one feature or fix per pull request
* Write tests for new functionality
* Update documentation when needed

### 4. Test Your Changes

**Frontend:**

```bash
cd frontend
npm test
```

**Backend:**

```bash
cd backend
python3 -m pytest -v
```

### 5. Commit

Write clear, descriptive commit messages:

```
feat: add emotion trend chart to dashboard
fix: resolve journal entry save timeout
docs: update environment variable guide
test: add unit tests for CBT analysis service
```

### 6. Push and Open a Pull Request

```bash
git push origin feature/your-feature-name
```

## Code Style

### Frontend (TypeScript / React)

* Use TypeScript for all new components
* Follow existing component patterns in the codebase
* Use Tailwind CSS for styling
* Keep components small and focused

### Backend (Python / FastAPI)

* Follow PEP 8 style guidelines
* Use type hints for function signatures
* Keep route handlers thin — delegate logic to services
* Use Pydantic models for request/response validation

### General

* Write self-documenting code
* Keep functions focused on a single responsibility
* Handle errors gracefully
* Avoid adding unnecessary dependencies

## Testing

### Frontend

```bash
cd frontend
npm test
```

Uses Vitest and React Testing Library.

### Backend

```bash
cd backend
python3 -m pytest -v
```

Uses pytest.

### Test Guidelines

* Write tests for new features and bug fixes
* Test edge cases and error paths
* Keep tests readable and maintainable
* Aim for meaningful coverage, not 100% line coverage

## Pull Request Process

1. **Fill out the PR template** — describe what changed and why
2. **Link the issue** — reference any related issues (e.g., `Closes #42`)
3. **Ensure tests pass** — run the full test suite before submitting
4. **Request a review** — tag a maintainer if you need feedback
5. **Respond to feedback** — make requested changes promptly
6. **Keep it focused** — one feature or fix per PR

### PR Title Format

Follow the same convention as commit messages:

```
feat: add offline journal sync
fix: correct emotion analysis encoding
docs: clarify Docker setup steps
```

## Questions?

If you have questions about contributing, open a discussion or issue. We are happy to help.

Thank you for contributing to MindMirror!
