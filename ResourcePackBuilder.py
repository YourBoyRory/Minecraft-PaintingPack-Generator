import zipfile
import json
from io import BytesIO
from PIL import Image

# Create a simple image with Pillow

class ResourcePackBuilder:
    
    packData = {}
    
    def __init__(self, packName, packIcon, mcMeta):
        self.packName = f'{packName}.zip'
        if mcMeta != None:
            packMeta = json.dumps(mcMeta, indent=4)
            self.addFile("pack.mcmeta", str(packMeta))
        if packIcon != None:
            with open(packIcon, 'rb') as f:
                self.addFile("pack.png", f.read())
        

    def addFile(self, filePath, file):
        self.packData[filePath] = file
        
    def writePack(self):
        with zipfile.ZipFile(self.packName, 'w') as zipf:
            for filePath, file in self.packData.items():
                zipf.writestr(filePath, file)


if __name__ == "__main__":
    
    image = Image.new('RGB', (100, 100), color = 'blue')
    image_name = 'image.png'
    
    image_bytes = BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    
    mcMeta = {
        "pack": {
            "description": "Test",
            "pack_format": 0
        }
    }
    
    
    maker = ResourcePackBuilder("furry_paintings", "../pack.png" , mcMeta)
    maker.addFile(f'/assets/minecraft/textures/painting/{image_name}', image_bytes.read())
    maker.writePack()
