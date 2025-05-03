#!/bin/bash
export INSTALL_DIR="$HOME/.local/bin"
cd $INSTALL_DIR
RELEASE_INFO=$(curl -s https://api.github.com/repos/Thomacdebabo/zit/releases/latest)
VERSION=$(echo "$RELEASE_INFO" | grep -o '"tag_name": "v[0-9.]*"' | cut -d'"' -f4)
echo "Installing zit version $VERSION"
curl --silent --show-error -L https://github.com/Thomacdebabo/zit/releases/download/$VERSION/zit -o zit
curl --silent --show-error -L https://github.com/Thomacdebabo/zit/releases/download/$VERSION/zit-fm -o zit-fm
curl --silent --show-error -L https://github.com/Thomacdebabo/zit/releases/download/$VERSION/zit-sys -o zit-sys
curl --silent --show-error -L https://github.com/Thomacdebabo/zit/releases/download/$VERSION/zit-git -o zit-git
chmod +x zit
chmod +x zit-fm
chmod +x zit-sys
chmod +x zit-git
