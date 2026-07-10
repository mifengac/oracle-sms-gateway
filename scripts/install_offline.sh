#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if compgen -G "instantclient_11_2/ubuntu22-debs/libaio1_*.deb" >/dev/null; then
  sudo apt install -y ./instantclient_11_2/ubuntu22-debs/libaio1_*.deb
fi

python3 -m venv .venv
. .venv/bin/activate
pip install --no-index --find-links instantclient_11_2/python-wheels -r requirements.txt

ln -sf libclntsh.so.11.1 instantclient_11_2/libclntsh.so
ln -sf libocci.so.11.1 instantclient_11_2/libocci.so

echo "Offline install complete."
