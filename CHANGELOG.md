# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive .gitignore file
- README.md with full documentation
- LICENSE file (MIT)
- CONTRIBUTING.md guidelines
- .env.example template
- CHANGELOG.md

## [1.0.0] - 2025-01-06

### Added
- Web portal for device registration
- Telegram bot integration
- Admin dashboard with secure authentication
- REST API for device management
- Mobile-responsive design
- Password hashing and security features
- Device statistics and search functionality

### Security
- Password hashing using Werkzeug
- Secure session management
- Input validation and sanitization
- SQL injection protection
- CSRF protection

### API Endpoints
- `GET /api/devices` - Get all devices
- `GET /api/devices/<id>` - Get device by ID
- `GET /api/devices/check?name=<name>` - Check device existence
- `GET /api/devices/search?q=<query>` - Search devices
- `GET /api/devices/stats` - Get statistics

[Unreleased]: https://github.com/yourusername/tgfinal/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/tgfinal/releases/tag/v1.0.0

