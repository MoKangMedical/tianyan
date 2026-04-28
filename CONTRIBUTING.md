# Contributing to Tianyan

Thank you for your interest in contributing to Tianyan! This document provides guidelines and information for contributors.

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment info (OS, Python version, etc.)

### Suggesting Features

1. Check existing feature requests
2. Use the feature request template
3. Explain:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative solutions considered

### Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `python -m pytest tests/ -v`
5. Commit with clear messages: `git commit -m "feat: add your feature"`
6. Push to your fork: `git push origin feature/your-feature`
7. Create a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/MoKangMedical/tianyan.git
cd tianyan

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Start development server
python demo_server.py
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints for all function signatures
- Write docstrings for all public functions
- Keep functions small and focused
- Write tests for new features

## Commit Messages

Use conventional commits:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Request review from maintainers
5. Address review comments

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Questions?

- Open a GitHub Issue for bugs/features
- Join our discussions for questions
- Email: contribute@tianyan.dev

Thank you for contributing! 🎉
