# Contributing to EmbedGuard

Thank you for your interest in contributing to EmbedGuard! This document provides guidelines and information for contributors.

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributions from everyone.

## How to Contribute

### Reporting Issues

- Search existing issues before creating a new one
- Use the issue templates when available
- Include reproduction steps for bugs
- For security vulnerabilities, please email directly (do not create public issues)

### Pull Requests

1. **Fork the repository** and create your branch from `main`

2. **Set up development environment**:
   ```bash
   git clone https://github.com/your-username/embedguard.git
   cd embedguard
   python -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Make your changes** following our coding standards

4. **Add tests** for new functionality

5. **Run the test suite**:
   ```bash
   pytest tests/
   ```

6. **Run the release static-safety gate**:
   ```bash
   ruff check .
   ```

7. **Update documentation** if needed

8. **Submit a pull request** with a clear description

## Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Write docstrings for public APIs (Google style)
- Maximum line length: 88 characters (Black default)

### Documentation

- Update docstrings when changing function behavior
- Add examples for new features
- Keep README.md in sync with changes

### Testing

- Write unit tests for new functionality
- Keep or improve coverage for the code you change
- Use descriptive test names
- Include both positive and negative test cases

## Types of Contributions

### Bug Fixes

- Include a regression test
- Reference the issue number in commit message

### New Features

- Discuss major features in an issue first
- Add documentation and examples
- Include comprehensive tests

### Performance Improvements

- Include benchmarks showing improvement
- Ensure no regression in accuracy

### Additional Attack Vectors

- Include detection patterns
- Add test cases demonstrating detection
- Document false positive considerations

### Documentation

- Fix typos and clarify existing docs
- Add usage examples
- Improve API documentation

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/` - Documentation
- `perf/description` - Performance improvements

### Commit Messages

Use conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_prompt_detector.py

# With coverage
pytest --cov=embedguard tests/

# Verbose output
pytest -v tests/
```

### Code Quality

```bash
# Parse/runtime-fatal static checks configured in pyproject.toml
ruff check .
```

## Architecture Overview

For contributors new to the codebase:

```
embedguard/
├── core.py                 # Main EmbedGuard class - entry point
├── config.py               # Configuration management
├── types.py                # Type definitions
├── prompt_detector/        # Layer 1: Prompt injection detection
├── embedding_attestation/  # Layer 2: HMAC provenance simulator
├── retrieval_analyzer/     # Layer 3: Distribution analysis
├── output_verifier/        # Layer 4: Consistency verification
└── correlation_engine/     # Signal fusion and decision making
```

### Key Classes

- `EmbedGuard`: Main framework class in `core.py`
- `EmbedGuardConfig`: Configuration in `config.py`
- `PromptInjectionDetector`: Layer 1 in `prompt_detector/`
- `ThreatCorrelationEngine`: Signal fusion in `correlation_engine/`

## Getting Help

- Check existing documentation
- Search closed issues
- Open a discussion for questions
- Create an issue for bugs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
