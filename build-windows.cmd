
python -m venv ./venv-windows
source ./venv-windows/Scripts/activate.bat
pip install -r requirements.txt
pyinstaller --onefile --windowed --name "MCPaintingStudio" --add-data "assets:assets/" ./PaintingStudio.py
echo.
echo Build Done
echo.
dir ./dist/
