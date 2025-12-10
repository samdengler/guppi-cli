# Release Process

This document describes the process for releasing a new version of guppi-cli.

## Prerequisites

- Clean working directory (`git status` shows no uncommitted changes)
- All tests passing
- On the `main` branch
- Push access to the repository

## Version Bumping

guppi-cli follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes, incompatible API changes
- **MINOR** (0.X.0): New features, backward-compatible
- **PATCH** (0.0.X): Bug fixes, backward-compatible

## Release Steps

### 1. Update Version

Update the version in both locations:
- `pyproject.toml` - `version = "X.Y.Z"`
- `src/guppi/__version__.py` - `__version__ = "X.Y.Z"`

If not specified, the agent should prompt for version bump type (major/minor/patch).

### 2. Commit Version Bump

```bash
git add pyproject.toml src/guppi/__version__.py
git commit -m "Bump version to X.Y.Z"
git push
```

### 3. Create Git Tag

```bash
git tag -a vX.Y.Z -m "Release version X.Y.Z"
git push origin vX.Y.Z
```

### 4. Create GitHub Release

Create a GitHub release with:
- **Tag**: `vX.Y.Z`
- **Title**: `guppi vX.Y.Z`
- **Body**: Auto-generated release notes from commits since last release, including:
  - New features
  - Bug fixes
  - Breaking changes (if any)
  - Upgrade instructions (if needed)

Use the GitHub CLI or API to create the release programmatically.

### 5. Verify Installation

Test the release:
```bash
# Upgrade existing installation
uv tool upgrade guppi

# Or fresh install
uv tool install guppi

# Verify version
guppi --version
```

## Example Release Notes Template

```markdown
## What's Changed

### Features
- Feature description (#PR)

### Bug Fixes
- Bug fix description (#PR)

### Other Changes
- Other changes (#PR)

**Full Changelog**: https://github.com/samdengler/guppi-cli/compare/vX.Y.Z...vA.B.C
```

## Rollback

If a release has issues:

1. Delete the GitHub release
2. Delete the git tag: `git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`
3. Revert the version bump commit
4. Fix the issue and re-release

## Automation

Future enhancement: Consider adding a release script or GitHub Action to automate these steps.
