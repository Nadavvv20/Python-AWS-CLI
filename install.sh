#!/usr/bin/env bash
# install.sh - Install awsctl with post-install banner
# Usage: bash install.sh

set -e

# Activate venv if it exists
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "Installing awsctl..."
pip install -e . --quiet

echo ""
python post_install.py
