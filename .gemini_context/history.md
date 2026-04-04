# Project History - Aura (Marty Financial Planner)

## 2026-04-04
- Automated Google Chrome installation in the devcontainer.
- Created `.devcontainer/setup.sh` to handle browser extraction (`google-chrome-stable`) and Python dependency installation.
- Removed `chromium` from the `Dockerfile` to avoid redundancy.
- Modified `devcontainer.json` to use `postCreateCommand` for running the setup script.
