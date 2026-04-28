# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Tianyan, please report it responsibly.

### How to Report

1. **DO NOT** open a public GitHub issue for security vulnerabilities
2. Email security concerns to: **security@tianyan.dev**
3. Include as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Release**: Within 30 days (depending on severity)

### Security Measures

Tianyan implements the following security measures:

- **API Key Authentication**: All API endpoints require valid API keys
- **Rate Limiting**: Daily usage limits per API key
- **Input Validation**: All inputs validated via Pydantic models
- **Compliance Checker**: Automated detection of sensitive content
- **Data Privacy**: 100% synthetic data, no real personal information
- **CORS Policy**: Configurable allowed origins
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy

### Responsible Disclosure

We appreciate responsible disclosure and will acknowledge security researchers who help improve Tianyan's security.

## Contact

- Security Email: security@tianyan.dev
- GitHub Issues: https://github.com/MoKangMedical/tianyan/issues
