# Security Scripts for Product Service

This directory contains scripts to set up comprehensive security scanning and pre-commit hooks for the Product Service.

## 🔐 Pre-commit Security Hooks

### Quick Start

**Linux/macOS:**

```bash
chmod +x scripts/install-precommit.sh
./scripts/install-precommit.sh
```

**Windows:**

```cmd
scripts\install-precommit.bat
```

### Uninstallation

If you need to remove the pre-commit hooks and security tools:

**Linux/macOS:**

```bash
chmod +x scripts/uninstall-precommit.sh
./scripts/uninstall-precommit.sh
```

**Windows:**

```cmd
scripts\uninstall-precommit.bat
```

The uninstall script will:

- ✅ Remove all pre-commit Git hooks
- ✅ Delete configuration files (.pre-commit-config.yaml, .secrets.baseline)
- ✅ Clean up cache directories
- ✅ Optionally uninstall Python security packages
- ✅ Optionally remove binary tools (trufflehog, hadolint)
- ✅ Clean up .gitignore entries
- ✅ Verify complete removal

### What Gets Installed

The installation script sets up the following security tools:

#### Secret Detection

- **detect-secrets**: Baseline secret scanning with allowlist management
- **TruffleHog**: Advanced secret scanning with verification
- **Custom patterns**: Additional regex patterns for sensitive data

#### Python Security

- **Bandit**: Python security linter (SAST)
- **Safety**: Dependency vulnerability scanning
- **pip-audit**: Additional dependency security scanning

#### Code Quality & Security

- **Black**: Code formatter
- **isort**: Import sorting
- **flake8**: Linting with security plugins
- **mypy**: Type checking

#### Infrastructure Security

- **hadolint**: Dockerfile security linting
- **yamllint**: YAML file validation

#### File Security

- **Large file detection**: Prevents accidentally committing large files
- **Private key detection**: Catches accidentally committed private keys
- **Environment file check**: Prevents committing .env files

### Security Hooks Behavior

#### On `git commit`:

- ✅ Secret scanning (detect-secrets, TruffleHog)
- ✅ Python security analysis (Bandit)
- ✅ Dependency vulnerability check (Safety)
- ✅ Code formatting (Black, isort)
- ✅ Linting (flake8)
- ✅ File security checks
- ✅ Custom secret pattern matching

#### On `git push`:

- ✅ TODO/FIXME comment check (warns about unresolved items)

### Manual Usage

```bash
# Run all hooks on all files
python -m pre_commit run --all-files
# OR (if pre-commit is in PATH)
pre-commit run --all-files

# Run specific hook
python -m pre_commit run bandit --all-files
python -m pre_commit run detect-secrets --all-files
python -m pre_commit run trufflehog --all-files

# Update hook versions
python -m pre_commit autoupdate

# Skip hooks (NOT recommended)
git commit --no-verify

# Uninstall hooks and cleanup
bash scripts/uninstall-precommit.sh
```

### Secret Management

#### Initial Setup

1. The script creates `.secrets.baseline` containing known/approved secrets
2. Review this file and remove any actual secrets
3. Commit the baseline to track approved patterns

#### Managing Secrets

```bash
# Update baseline after reviewing new secrets
detect-secrets scan --baseline .secrets.baseline --update

# Audit secrets interactively
detect-secrets audit .secrets.baseline
```

### Troubleshooting

#### Hook Failures

- **Bandit failures**: Review security warnings and fix or suppress with `# nosec`
- **Safety failures**: Update vulnerable dependencies
- **Secret detection**: Review flagged secrets and update baseline if legitimate

#### Uninstall Issues

- **Hooks still running**: Run `git config --local --unset core.hooksPath` to reset Git hooks path
- **Python packages remain**: Manually run `pip uninstall <package-name>` for specific packages
- **Permission denied**: Run with elevated privileges or check file permissions
- **Binary tools remain**: Manually check and remove from `/usr/local/bin/` or `~/.local/bin/`

#### Performance Issues

- Hooks run incrementally by default (only on changed files)
- Use `--all-files` only when necessary
- Consider excluding large directories in `.pre-commit-config.yaml`

#### Windows-Specific Issues

- Ensure Python and pip are in PATH
- TruffleHog requires manual installation on Windows
- Use Git Bash for better compatibility

### Local Development Workflow

The pre-commit hooks run automatically when you make commits, providing immediate security feedback during development:

#### � What Happens During Commit

1. **Before your commit is created**, pre-commit automatically runs all security tools
2. **If issues are found**, the commit is blocked and you'll see detailed output
3. **Fix the issues** and try committing again
4. **Clean commits** proceed normally

#### ⚡ Benefits of Local Security

- **Fast feedback**: Catch issues immediately, not after pushing
- **Privacy**: Secrets are caught before they ever leave your machine
- **Developer efficiency**: Fix issues in your current context
- **Team consistency**: Everyone runs the same security checks

### Security Best Practices

1. **Never bypass hooks**: Resist the temptation to use `--no-verify`
2. **Regular updates**: Run `pre-commit autoupdate` monthly
3. **Baseline maintenance**: Regularly audit and update `.secrets.baseline`
4. **Team training**: Ensure all developers understand the security tools
5. **Local testing**: Run `pre-commit run --all-files` periodically for full codebase checks

### Custom Patterns

The configuration includes custom regex patterns for detecting:

- Database connection strings
- API keys and tokens
- Passwords and secrets in various formats
- Private keys and certificates

To modify patterns, edit the `custom-secret-patterns` hook in `.pre-commit-config.yaml`.

### Dependencies

Main security dependencies (installed via `requirements-dev.txt`):

- `pre-commit>=3.6.0`
- `bandit>=1.7.5`
- `safety>=2.3.5`
- `detect-secrets>=1.4.0`
- `semgrep>=1.45.0`

### Support

For issues with:

- **Pre-commit framework**: https://pre-commit.com/
- **detect-secrets**: https://github.com/Yelp/detect-secrets
- **Bandit**: https://bandit.readthedocs.io/
- **TruffleHog**: https://github.com/trufflesecurity/trufflehog

---

## � Available Scripts Summary

This directory contains the following scripts for managing pre-commit security hooks:

### Installation Scripts

- `install-precommit.sh` - Linux/macOS installation script
- `install-precommit.bat` - Windows installation script

### Uninstallation Scripts

- `uninstall-precommit.sh` - Linux/macOS uninstallation script
- `uninstall-precommit.bat` - Windows uninstallation script

### Quick Reference

```bash
# Install (Linux/macOS)
./scripts/install-precommit.sh

# Install (Windows)
scripts\install-precommit.bat

# Uninstall (Linux/macOS)
./scripts/uninstall-precommit.sh

# Uninstall (Windows)
scripts\uninstall-precommit.bat
```

---

## �🛡️ Additional Security Tools

### Branch Protection (GitHub)

Enable in repository settings:

- Require PR reviews
- Require status checks (pre-commit, CI)
- Require up-to-date branches
- Include administrators

### Push Protection (GitHub)

Enable in repository security settings:

- Secret scanning alerts
- Push protection for secrets
- Dependency vulnerability alerts

### Recommended GitHub Actions

- CodeQL analysis
- Dependency review
- Security scanning workflows
