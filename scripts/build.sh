#!/usr/bin/env bash
# Builds a standalone aho-view binary with PyInstaller.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

icon="src/aho_view/resources/ahoviewico.ico"

# PyInstaller's --add-data separator differs by host OS: ';' on Windows, ':' elsewhere.
data_sep=":"
case "$(uname -s)" in
    MINGW* | MSYS* | CYGWIN*) data_sep=";" ;;
esac

uv run --group build pyinstaller \
    --noconfirm \
    --clean \
    --windowed \
    --onefile \
    --name aho-view \
    --icon "$icon" \
    --add-data "${icon}${data_sep}aho_view/resources" \
    src/aho_view/__main__.py

echo "Built binary: $repo_root/dist/aho-view"
