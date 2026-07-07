# Contributing

## Development setup

1. Create and activate a virtual environment.
2. Install development dependencies:

```bash
pip install -e ".[dev,bdf,viz]"
```

## Common commands

```bash
ruff check .
black --check .
mypy src
pytest
```

## Pull request checklist

- Add or update tests for behavior changes.
- Keep public APIs backwards compatible unless explicitly planned.
- Update `CHANGELOG.md` for user-visible changes.
