# copra Documentation

This directory contains the source files for the copra documentation.

## Building the Documentation

To build the documentation locally, you'll need to install the development dependencies:

```bash
pip install -e .[dev]
```

Then, build the documentation with:

```bash
cd docs
make html
```

The built documentation will be available in `_build/html/index.html`.

## Documentation Structure

- `source/conf.py`: Sphinx configuration
- `source/index.rst`: Main documentation page
- `source/quickstart.rst`: Quick start guide

## Writing Documentation

- Use reStructuredText (.rst) for all documentation files
- Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstrings
- Use Sphinx's autodoc to automatically generate API documentation from docstrings
