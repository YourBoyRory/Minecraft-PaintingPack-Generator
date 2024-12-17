
python -m venv ./venv-windows
source ./venv-windows/Scripts/activate.bat
pip install -r requirements.txt
pyinstaller --name "MCPaintingStudio" --windowed --contents-directory MCPaintingStudio  --icon=assets/icon.ico --add-data "src:src/" --add-data "assets:assets/" --add-data "styles:styles/" ./PaintingStudio.py
echo.
echo Build Done
echo.
dir ./dist/
