# ZeroTrust

![License](https://img.shields.io/badge/license-MIT-green.svg) ![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)

A minimal Python service for Issue-related tooling. This repository uses `app.py` as the application entrypoint.

## Table of Contents
- [Overview](#overview)
- [Requirements](#requirements)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Running](#running)
- [API Usage](#api-usage)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview
Lightweight Python Issue Tracker for managing and tracking issues efficiently.

## Requirements
- Python 3.8+
- pip
- git

## Quickstart

Clone and install dependencies:
```bash
git clone https://github.com/mannansainicyber/ZeroTrust.git
cd ZeroTrust
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration
Create a `.env` file in the project root with the following variables:
```env
FLASK_ENV=development
DATABASE_URL=sqlite:///issues.db
SECRET_KEY=your-secret-key-here
```

## Running

Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## API Usage

### Create an Issue
```bash
curl -X POST http://localhost:5000/api/issues \
  -H "Content-Type: application/json" \
  -d '{"title": "Bug fix", "description": "Fix login issue", "status": "open"}'
```

### Get Issues
```bash
curl http://localhost:5000/api/issues
```

### Update Issue
```bash
curl -X PUT http://localhost:5000/api/issues/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "closed"}'
```

## Testing
Run tests with:
```bash
pytest tests/
```

## Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Write tests for new functionality
4. Commit changes: `git commit -am 'Add new feature'`
5. Push to the branch: `git push origin feat/your-feature`
6. Open a Pull Request

Please ensure:
- Code follows PEP 8 style guidelines
- All tests pass before submitting PR
- Include descriptive commit messages

## Contact
Project maintainer — Mannan Saini  
Repo: https://github.com/mannansainicyber/ZeroTrust
