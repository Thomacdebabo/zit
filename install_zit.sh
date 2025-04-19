#!/bin/bash
export INSTALL_DIR="$HOME/.local/bin"
cd $INSTALL_DIR
wget https://github.com/Thomacdebabo/zit/releases/latest -o zit
chmod +x zit