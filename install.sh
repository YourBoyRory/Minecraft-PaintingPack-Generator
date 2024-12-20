#!/bin/bash

# install app
sudo mkdir /opt/MCPaintingStudio
sudo cp ./*.py /opt/MCPaintingStudio/
sudo cp -r ./assets /opt/MCPaintingStudio/
sudo cp -r ./styles /opt/MCPaintingStudio/
sudo cp -r ./src /opt/MCPaintingStudio/

# install venv and dependecies
sudo python -m venv /opt/MCPaintingStudio/venv
source /opt/MCPaintingStudio/venv/bin/activate
sudo /opt/MCPaintingStudio/venv/bin/pip install -r requirements.txt

# Install Theme
sudo cp -r ./styles /opt/MCPaintingStudio/venv/lib/*/site-packages/PyQt5/Qt5/plugins/

# Make Launchers
sudo tee /usr/local/bin/MCPaintingStudio > /dev/null <<EOF
#!/bin/bash
source /opt/MCPaintingStudio/venv/bin/activate
python /opt/MCPaintingStudio/PaintingStudio.py $@
EOF
sudo chmod +x /usr/local/bin/MCPaintingStudio
sudo tee /usr/share/applications/MCPaintingStudio.desktop > /dev/null <<EOF
[Desktop Entry]
Version=1.0
Name=MCPaintingStudio
Comment=Make paitings for minecraft out of any image
Exec=/usr/local/bin/MCPaintingStudio %f
Icon=/opt/MCPaintingStudio/assets/icon.png
Terminal=false
Type=Application
Categories=Multimedia;Video;Utility;AudioVideo;
EOF
