# Contributing

Thank you for your interest in contributing to Luthier's ToolBox!

---

## Getting Started

### 1. Fork the Repository

Click the "Fork" button on [GitHub](https://github.com/HanzoRazer/luthiers-toolbox).

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/luthiers-toolbox.git
cd luthiers-toolbox
```

### 3. Set Up Development Environment

```bash
# Backend
cd services/api
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend
cd ../../packages/client
npm install
```

### 4. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

---

## Development Workflow

### Running Tests

```bash
# Backend tests
cd services/api
pytest

# Frontend tests
cd packages/client
npm test
```

### Code Style

**Python:**

- Follow PEP 8
- Use type hints
- Run `ruff` for linting

**TypeScript/Vue:**

- Use TypeScript strictly
- Follow Vue 3 Composition API patterns
- Run `npm run lint`

### Commit Messages

Follow conventional commits:

```
feat: add string tension calculator
fix: resolve DXF import crash on empty layers
docs: update installation guide
test: add unit tests for fret calculator
refactor: simplify toolpath generation
```

---

## Pull Request Process

### 1. Update Documentation

If your change affects user-facing features, update relevant docs.

### 2. Add Tests

- New features need tests
- Bug fixes should include regression tests
- Aim for good coverage

### 3. Run All Tests

```bash
# Backend
cd services/api
pytest

# Frontend
cd packages/client
npm test
npm run type-check
npm run build
```

### 4. Create Pull Request

- Fill out the PR template
- Link related issues
- Request review

### 5. Address Feedback

Respond to review comments and make requested changes.

---

## Code of Conduct

### Be Respectful

- Treat all contributors with respect
- Welcome newcomers
- Accept constructive criticism

### Be Collaborative

- Work together on solutions
- Share knowledge
- Help others learn

### Be Professional

- Focus on the work
- Keep discussions technical
- Assume good intent

---

## Areas for Contribution

### Good First Issues

Look for issues labeled `good first issue`:

- Documentation improvements
- Test coverage
- UI polish
- Bug fixes

### Feature Development

Check the roadmap and discuss with maintainers before starting large features.

### Documentation

- Fix typos
- Improve clarity
- Add examples
- Translate

### Testing

- Add unit tests
- Improve test coverage
- Add integration tests
- Test edge cases

---

## Architecture Overview

### Backend (FastAPI)

```
services/api/
├── app/
│   ├── main.py          # Application entry
│   ├── routers/         # API routes
│   ├── cam/             # CAM operations
│   ├── rmos/            # Safety system
│   ├── calculators/     # Math tools
│   └── schemas/         # Pydantic models
└── tests/               # Test suite
```

### Frontend (Vue 3)

```
packages/client/
├── src/
│   ├── views/           # Page components
│   ├── components/      # Reusable components
│   ├── stores/          # Pinia stores
│   ├── composables/     # Composition functions
│   └── sdk/             # API client
└── tests/               # Test suite
```

---

## Design Principles

### Safety First

- Manufacturing operations must be validated
- RMOS rules protect users from dangerous operations
- Never bypass safety checks without explicit override

### User Experience

- Simple operations should be simple
- Complex operations should be possible
- Provide clear feedback

### Performance

- Keep the UI responsive
- Optimize toolpath generation
- Cache expensive calculations

### Maintainability

- Write clear, documented code
- Prefer composition over inheritance
- Keep functions focused

---

## Communication

### GitHub Issues

- Report bugs
- Request features
- Ask questions

### GitHub Discussions

- General questions
- Ideas and proposals
- Show and tell

### Pull Requests

- Code review
- Technical discussion
- Implementation feedback

---

## Recognition

Contributors are recognized in:

- GitHub contributors list
- Release notes (for significant contributions)
- Documentation acknowledgments

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

If you have questions about contributing:

1. Check existing issues/discussions
2. Open a new discussion
3. Ask in a related issue

Thank you for helping make Luthier's ToolBox better!
