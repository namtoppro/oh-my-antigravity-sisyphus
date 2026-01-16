# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **CLI Doctor**: `sisyphus-mcp doctor` command for diagnosing MCP server connection issues.
- **Stability**: Added forced unbuffered mode (`-u`) and warning suppression (`-W ignore`) to Python execution args in MCP config to prevent IDE connection failures.
- **Encoding**: Enforced `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` in MCP config environment variables.

### Fixed
- **Windows Support**: add binary mode handling for stdin/stdout in `server.py` to fix `Error: calling "initialize": EOF`.
- **Package Data**: Included `templates/*.md` in `pyproject.toml` regarding `GEMINI.md` missing issue during pip installation.
- **Path Resolution**: Improved `get_template_path()` in `cli/main.py` to correctly locate `GEMINI.md` in pip-installed environments.

## [1.0.0] - 2026-01-15
- Initial release of Oh-My-Antigravity-Sisyphus MCP Server.
