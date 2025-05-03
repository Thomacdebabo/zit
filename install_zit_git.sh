#!/bin/bash
export INSTALL_DIR="$HOME/.local/bin"
cd $INSTALL_DIR
RELEASE_INFO=$(curl -s https://api.github.com/repos/Thomacdebabo/zit/releases/latest)
VERSION=$(echo "$RELEASE_INFO" | grep -o '"tag_name": "v[0-9.]*"' | cut -d'"' -f4)
echo "Installing zit-git version $VERSION"
curl --silent --show-error -L https://github.com/Thomacdebabo/zit/releases/download/$VERSION/zit-git -o zit-git
chmod +x zit-git