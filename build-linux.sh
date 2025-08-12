#!/bin/bash

python -m venv ./venv-linux
source ./venv-linux/bin/activate
./venv-linux/bin/pip install -r requirements.txt


./venv-linux/bin/python3 -m PyInstaller --name "MCPaintingStudio" --icon=assets/icon.ico --add-data "src:src/" --add-data "assets:assets/" --add-data "styles:PyQt5/Qt5/plugins/styles" ./PaintingStudio.py

echo " "
echo "Packaging Complete"
echo " "

ls -lh ./dist/
