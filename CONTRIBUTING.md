# Contributing to WhatNow

Thank you for your interest in contributing to WhatNow!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/whatnow.git
cd whatnow
```

2. Install in development mode:
```bash
pip install -e ".[dev]"
```

3. Install system dependencies (see README.md for your platform)

## Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Keep functions focused and well-documented
- Write docstrings for all public functions and classes

## Testing

Currently, manual testing is required. Run the application:
```bash
python -m whatnow
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test your changes thoroughly
5. Commit with clear messages: `git commit -m "Add feature X"`
6. Push to your fork: `git push origin feature/my-feature`
7. Create a pull request

## Areas for Contribution

- Adding tests (unit tests, integration tests)
- Improving UI/UX
- Adding more sync integrations (Todoist, Notion, etc.)
- Documentation improvements
- Bug fixes
- Performance optimizations

## Questions?

Feel free to open an issue for discussion before working on major changes.
