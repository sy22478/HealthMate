# Contributing to HealthChat RAG

Thank you for your interest in contributing! Please follow these guidelines to help us maintain a high-quality, consistent codebase.

## Getting Started
- Fork the repository and clone your fork.
- Create a new branch for each feature or bugfix (see Feature Branch Workflow in README).

## Running Tests
- Install dependencies: `pip install -r requirements.txt`
- Run all tests: `pytest healthchat-rag/tests/`
- Run with coverage: `pytest --cov=healthchat-rag/app --cov-report=term-missing healthchat-rag/tests/`
- All new code must include appropriate unit and/or integration tests.

## Coding Standards
- Use clear, descriptive variable and function names.
- Write docstrings for all public functions and classes.
- Follow PEP8 style guidelines (use `black` or `flake8` for formatting/linting).
- Keep functions and modules focused and concise.

## Pull Request (PR) Process
- Ensure your branch is up to date with `main` before opening a PR.
- Include a clear description of your changes and reference any related issues.
- Make sure all tests pass and coverage is maintained or improved.
- Request a review from a project maintainer.
- Address any review comments promptly.
- After merging, delete your feature branch.

## Additional Tips
- Use draft PRs for work in progress.
- Ask questions or propose ideas in issues or discussions.
- Be respectful and collaborative—review others’ code constructively.

Thank you for helping make HealthChat RAG better! 