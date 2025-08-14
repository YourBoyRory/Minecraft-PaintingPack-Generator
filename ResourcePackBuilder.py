import zipfile
import json
from io import BytesIO
from PIL import Image

# Create a simple image with Pillow

class ResourcePackBuilder:

    def __init__(self, mcMeta):
        self.packData = {}
        if mcMeta != None:
            packMeta = json.dumps(mcMeta, indent=4)
            self.addFile("pack.mcmeta", str(packMeta))

    def updateMeta(self, mcMeta):
        packMeta = json.dumps(mcMeta, indent=4)
        self.delFile("pack.mcmeta")
        self.addFile("pack.mcmeta", str(packMeta))

    def addFile(self, filePath, file):
        self.packData[filePath] = file

    def delFile(self, filePath):
        del self.packData[filePath]

    def writePack(self, packPath):
        with zipfile.ZipFile(packPath, 'w') as zipf:
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
    maker.writePack("./furry_paintings.zip")
