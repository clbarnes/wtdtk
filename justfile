_default:
    just --list

# Check for code quality issues.
lint:
    uv run ruff check
    uv run ruff format --check
    uv run mypy src tests
    uv run pydoclint src

# Fix lint and format issues where possible.
fix:
    uv run ruff check --fix
    uv run ruff format

# Run unit tests.
test:
    uv run pytest --verbose

# Generated documentation, by default in ./doc/html
doc docdir='doc/html':
    rm -rf {{docdir}}
    uv run --group doc pdoc \
        --output-directory {{docdir}} \
        --no-include-undocumented \
        --docformat numpy \
        --search \
        wtdtk

doc-view:
    just doc
    uv run python -m webbrowser "file://{{ justfile_directory() }}/doc/html/index.html"
