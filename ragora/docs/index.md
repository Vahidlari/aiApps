# Ragora Documentation

Ragora is a Retrieval-Augmented Generation toolkit for building document-centric
knowledge bases. This site combines authored guides with API reference pages
generated from the project docstrings so the published docs align with the
latest release.

## 🚀 Start Here

- [Getting Started](getting_started.md) – Install Ragora, create a knowledge
  base, and run your first queries.
- [DevContainer Setup](devcontainer.md) – Spin up the ready-to-use development
  container.
- [Development Workflow](development.md) – Branching model, tooling, and coding
  conventions.

## 📚 Learn More

- [Release Process](release.md) – Milestone-driven release automation and the
  documentation publishing workflow.
- [Deployment](deployment.md) – Production deployment patterns and
  infrastructure guidance.
- [Testing](testing.md) – Testing strategy, coverage goals, and helper tooling.
- [Design Decisions](design_decisions.md) – Architectural rationale behind core
  components.

## 🧰 Reference

- [API Reference](api-reference.md) – Auto-generated module documentation built
  from Ragora docstrings via mkdocstrings.
- [Contributing Guide](contributing.md) – Steps for proposing changes and
  collaborating on reviews.

## 🔄 Release & Documentation Flow

1. Conventional commits land on `main`.
2. Closing a milestone (or a manual dispatch) creates a release.
3. The `Generate Documentation` GitHub Action rebuilds this site and pushes the
   static output to `docs/` on `main`.
4. GitHub Pages publishes the updated docs at
   [https://vahidlari.github.io/aiApps](https://vahidlari.github.io/aiApps).

Need something else? File an issue on
[GitHub](https://github.com/vahidlari/aiApps/issues) or start a discussion with
the team!

