#!/usr/bin/env bash
#
# install.sh - one-click installer for x-use.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ihuzaifashoukat/x-use/main/install.sh | bash
#   ./install.sh [--dir PATH] [--dev] [--update] [-h|--help]
#
# What it does:
#   1. Preflight: git and Python >= 3.10 must be present.
#   2. Clone the repo (or reuse/update an existing clone, or install in
#      place when run from inside the repo).
#   3. Create a virtual environment (venv/) and install x-use into it.
#   4. Bootstrap local config: .env and config/accounts.json from the
#      shipped examples (never overwrites existing files).
#   5. Run `x-use doctor` so you immediately see what is left to set up.
#
# The script is idempotent: re-running it reuses the clone and the venv.
# It never uses sudo and never touches files outside the install directory.

set -euo pipefail

# XUSE_REPO_URL overrides the clone source (forks, mirrors, testing).
readonly REPO_URL="${XUSE_REPO_URL:-https://github.com/ihuzaifashoukat/x-use.git}"
readonly DEFAULT_DIR="x-use"
readonly MIN_PYTHON_MAJOR=3
readonly MIN_PYTHON_MINOR=10

INSTALL_DIR=""
DEV_INSTALL=0
UPDATE=0

# --- output helpers -----------------------------------------------------------

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
    C_RESET=$'\033[0m'; C_BOLD=$'\033[1m'
    C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'; C_RED=$'\033[31m'
else
    C_RESET=""; C_BOLD=""; C_GREEN=""; C_YELLOW=""; C_RED=""
fi

info() { printf '%s==>%s %s\n' "${C_GREEN}" "${C_RESET}" "$*"; }
warn() { printf '%swarn:%s %s\n' "${C_YELLOW}" "${C_RESET}" "$*" >&2; }
die()  { printf '%serror:%s %s\n' "${C_RED}" "${C_RESET}" "$*" >&2; exit 1; }

trap 'die "installation failed at line ${LINENO} - re-run with bash -x install.sh for a trace."' ERR

usage() {
    cat <<'EOF'
install.sh - one-click installer for x-use.

Usage:
  curl -fsSL https://raw.githubusercontent.com/ihuzaifashoukat/x-use/main/install.sh | bash
  ./install.sh [--dir PATH] [--dev] [--update] [-h|--help]

Options:
  --dir PATH   Install into PATH instead of ./x-use
  --dev        Install with dev extras (pytest) for contributors
  --update     git pull --ff-only an existing checkout before installing
  -h, --help   Show this help
EOF
    exit "${1:-0}"
}

# --- arguments ----------------------------------------------------------------

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir)
            [[ $# -ge 2 ]] || die "--dir requires a path argument."
            INSTALL_DIR="$2"; shift 2 ;;
        --dir=*)
            INSTALL_DIR="${1#*=}"; shift ;;
        --dev)
            DEV_INSTALL=1; shift ;;
        --update)
            UPDATE=1; shift ;;
        -h|--help)
            usage 0 ;;
        *)
            die "unknown option '$1' (try --help)." ;;
    esac
done

# --- preflight ------------------------------------------------------------------

command -v git >/dev/null 2>&1 || die "git is not installed (or not on PATH)."

PYTHON=""
for candidate in python3 python; do
    command -v "${candidate}" >/dev/null 2>&1 || continue
    if "${candidate}" -c "import sys; raise SystemExit(0 if sys.version_info >= (${MIN_PYTHON_MAJOR}, ${MIN_PYTHON_MINOR}) else 1)" 2>/dev/null; then
        PYTHON="${candidate}"
        break
    fi
done
[[ -n "${PYTHON}" ]] || die "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ not found. Install it from https://www.python.org/downloads/ and re-run."

PY_VERSION="$("${PYTHON}" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
info "git $(git --version | awk '{print $3}'), python ${PY_VERSION} - preflight OK."

# --- repo: clone / update / in-place ---------------------------------------------

if [[ -z "${INSTALL_DIR}" && -f "pyproject.toml" ]] && grep -q '^name = "x-use"' pyproject.toml 2>/dev/null; then
    # Running from inside the repo: install in place.
    INSTALL_DIR="$(pwd)"
fi
INSTALL_DIR="${INSTALL_DIR:-${DEFAULT_DIR}}"

if [[ -f "${INSTALL_DIR}/pyproject.toml" ]] && grep -q '^name = "x-use"' "${INSTALL_DIR}/pyproject.toml" 2>/dev/null; then
    if [[ "${UPDATE}" -eq 1 ]]; then
        info "Updating existing clone in ${INSTALL_DIR} ..."
        git -C "${INSTALL_DIR}" pull --ff-only || warn "git pull failed - keeping the existing checkout."
    else
        info "Existing x-use checkout found in ${INSTALL_DIR} - reusing it (pass --update to pull latest)."
    fi
else
    if [[ -e "${INSTALL_DIR}" ]]; then
        die "'${INSTALL_DIR}' exists but is not an x-use checkout. Pick another --dir or remove it."
    fi
    info "Cloning ${REPO_URL} -> ${INSTALL_DIR} ..."
    git clone --depth 1 "${REPO_URL}" "${INSTALL_DIR}"
    [[ -f "${INSTALL_DIR}/pyproject.toml" ]] && grep -q '^name = "x-use"' "${INSTALL_DIR}/pyproject.toml" 2>/dev/null \
        || die "the clone does not look like x-use v2 (missing pyproject.toml). The default branch may predate the v2 merge - clone the right branch or set XUSE_REPO_URL."
fi

# --- virtual environment -----------------------------------------------------------

VENV_DIR="${INSTALL_DIR}/venv"
if [[ -d "${VENV_DIR}" ]]; then
    info "Virtual environment already exists at ${VENV_DIR} - reusing it."
else
    info "Creating virtual environment at ${VENV_DIR} ..."
    "${PYTHON}" -m venv "${VENV_DIR}"
fi

# venv layout differs by platform: bin/ on Linux/macOS, Scripts/ on Windows (Git Bash).
if [[ -x "${VENV_DIR}/bin/python" ]]; then
    VENV_PY="${VENV_DIR}/bin/python"
elif [[ -x "${VENV_DIR}/Scripts/python.exe" ]]; then
    VENV_PY="${VENV_DIR}/Scripts/python.exe"
else
    die "venv created at ${VENV_DIR} but no python executable found inside it."
fi
BIN_DIR="$(dirname "${VENV_PY}")"

# --- install ------------------------------------------------------------------------

info "Installing x-use (this can take a minute) ..."
"${VENV_PY}" -m pip install --quiet --upgrade pip
if [[ "${DEV_INSTALL}" -eq 1 ]]; then
    (cd "${INSTALL_DIR}" && "${VENV_PY}" -m pip install --quiet -e '.[dev]')
else
    (cd "${INSTALL_DIR}" && "${VENV_PY}" -m pip install --quiet -e .)
fi

XUSE_BIN="${BIN_DIR}/x-use"
[[ -x "${XUSE_BIN}" ]] || XUSE_BIN="${BIN_DIR}/x-use.exe"
[[ -x "${XUSE_BIN}" ]] || die "install finished but the x-use command was not found in ${BIN_DIR}."
"${XUSE_BIN}" --help >/dev/null 2>&1 || die "x-use was installed but fails to run (${XUSE_BIN} --help)."
info "Installed x-use -> ${XUSE_BIN}"

# --- config bootstrap (never overwrites) ----------------------------------------------

if [[ -f "${INSTALL_DIR}/.env.example" && ! -f "${INSTALL_DIR}/.env" ]]; then
    cp "${INSTALL_DIR}/.env.example" "${INSTALL_DIR}/.env"
    info "Created .env from .env.example - add your LLM API key(s) there."
fi
if [[ -f "${INSTALL_DIR}/config/accounts.example.json" && ! -f "${INSTALL_DIR}/config/accounts.json" ]]; then
    cp "${INSTALL_DIR}/config/accounts.example.json" "${INSTALL_DIR}/config/accounts.json"
    info "Created config/accounts.json from the example (ships inactive - configure it via x-use init)."
fi

# --- doctor ----------------------------------------------------------------------------

info "Running preflight checks (x-use doctor) ..."
DOCTOR_FAILED=0
(cd "${INSTALL_DIR}" && "${XUSE_BIN}" doctor) || DOCTOR_FAILED=1

# --- done -------------------------------------------------------------------------------

# Claude Desktop on Windows needs a C:\... path; cygpath converts when available.
MCP_BIN="$(cygpath -w "${XUSE_BIN}" 2>/dev/null || printf '%s' "${XUSE_BIN}")"

printf '\n%sx-use is installed.%s\n' "${C_BOLD}" "${C_RESET}"
if [[ "${DOCTOR_FAILED}" -eq 1 ]]; then
    warn "doctor reported issues above - fix the FAIL rows, then you are set."
fi
cat <<EOF

Next steps:
  1. cd ${INSTALL_DIR}
  2. ${BIN_DIR}/x-use init      # interactive wizard: account, cookies, LLM keys
  3. ${BIN_DIR}/x-use doctor    # re-check until every row is PASS/SKIP
  4. ${BIN_DIR}/x-use run       # or connect an MCP client (below)

MCP client config (e.g. claude_desktop_config.json):
  {
    "mcpServers": {
      "x-use": {
        "command": "${MCP_BIN}",
        "args": ["mcp"]
      }
    }
  }

Docs: README.md, BEST_PRACTICES.md, docs/CONFIG_REFERENCE.md
EOF
