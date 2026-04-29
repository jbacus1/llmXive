# Developer Guide

Guide for developers contributing to the Climate-Smart Agricultural Practices project.

## Project Structure

```
.
├── src/                    # Source code
│   ├── cli/                # Command-line interface
│   ├── config/             # Configuration management
│   ├── data/               # Data collectors and processors
│   ├── models/             # ML/statistical models
│   └── services/           # Business logic services
├── tests/                  # Test suite
│   ├── contract/           # Schema contract tests
│   ├── integration/        # Integration tests
│   └── unit/               # Unit tests
├── data/                   # Data storage
├── docs/                   # Documentation
└── contracts/              # Schema contracts
```

## Development Workflow

1. **Setup Development Environment**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

2. **Run Tests**
```bash
pytest tests/ -v
```

3. **Code Quality**
```bash
black src/ tests/
flake8 src/ tests/
isort src/ tests/
```

## Testing Strategy

### Contract Tests
Verify schema compliance for all data outputs.

### Integration Tests
Test API interactions and end-to-end workflows.

### Unit Tests
Test individual components in isolation.

## Adding New Features

1. Create task in tasks.md
2. Write failing tests first (TDD approach)
3. Implement feature
4. Verify all tests pass
5. Update documentation

## User Story Implementation Order

1. Complete Phase 2 (Foundational) first - BLOCKS all stories
2. Implement user stories in priority order (P1 → P2 → P3 → P4)
3. Each story must be independently testable

## Principles

- **Principle I**: No unauthorized modifications to tasks.md
- **Principle II**: All claims verified against primary sources
- **Principle IV**: All data sources must be free/open
- **Principle V**: All API calls must have fail-fast validation

## Contributing

1. Fork the repository
2. Create feature branch
3. Implement with tests
4. Submit pull request
