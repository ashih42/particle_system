#!/bin/sh

echo 'Installing dependencies...'
HOMEBREW_NO_AUTO_UPDATE=1 brew install -v glfw

echo 'Installing Python packages...'
pip3 install -r setup/requirements.txt
