#!/bin/bash

python -m venv ./venv-linux
source ./venv-linux/bin/activate
pip install -r requirements.txt
#
pyinstaller --onefile --name "MCPaintingStudio" --add-data "assets:assets/" --add-data "styles:PyQt5/Qt5/plugins/styles" ./PaintingStudio.py

echo " "
echo "Packaging Complete"
echo " "

ls -lh ./dist/
