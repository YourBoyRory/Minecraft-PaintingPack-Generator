import os
from io import BytesIO
from PIL import Image 
from PaintingGenerator import PaintingGenerator
from ResourcePackBuilder import ResourcePackBuilder

if __name__ == "__main__":
    
    mcMeta = { 
        "pack": {
            "description": "NSFW Furry Paintings!",
            "pack_format": 42
        }
    }
    pack_builder = ResourcePackBuilder("NSFW_furry_paintings", "../pack.png" , mcMeta)
    directory = "../input_nsfw"
    
    for file in os.listdir(directory):
        
        filename = os.path.splitext(file)[0].lower().strip()
        filename_split = filename.split('-')
        paintingName=filename_split[0]
        frame=filename_split[-1]
        path = os.path.join(directory, file)
        
        #print(path)
        print(f"{paintingName} using frame {frame}")
        
        art = Image.open(path)
        painting_maker = PaintingGenerator()
        painting = painting_maker.makePaiting(4, frame, art)
        image_bytes = BytesIO()
        painting.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        pack_builder.addFile(f'assets/minecraft/textures/painting/{paintingName}.png', image_bytes.read())
    
    pack_builder.writePack()
