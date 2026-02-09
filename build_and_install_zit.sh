#!/bin/bash
export INSTALL_DIR="$HOME/.local/bin"

uv run pyinstaller --onefile --name zit-python run_zit.py
chmod +x dist/zit-python
sudo rm -f $INSTALL_DIR/zit-python
sudo cp dist/zit-python $INSTALL_DIR/zit-python
sudo cp zit-bash/zit $INSTALL_DIR/zit
sudo cp zit-bash/ted-to-zit $INSTALL_DIR/ted-to-zit