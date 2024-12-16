
python -m venv ./venv-windows
source ./venv-windows/Scripts/activate.bat
pip install -r requirements.txt
pyinstaller --name "MCPaintingStudio" --add-data "assets:assets/" --add-data "styles:styles/" ./PaintingStudio.py
echo.
echo Build Done
echo.
dir ./dist/
