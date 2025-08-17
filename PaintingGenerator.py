from PIL import Image
import os
import sys

class PaintingGenerator:

    def makePaiting(self, scale, scale_method, offset, background_color, painting, showFrame, art):

        self.scale = scale
        self.background_color = background_color

        frame = self.callPainting(painting)

        # The Maff :3
        pack_res = 16*self.scale
        width, height = frame.size
        height = int(height/16)
        width = int(width/16)

        painting = frame.resize((pack_res*width, pack_res*height), Image.NEAREST)

        target_width = (pack_res*width)
        target_height = (pack_res*height)
        art_size = (target_width-(self.scale*2), target_height-(self.scale*2))

        if scale_method == "Stretch":
            art_scaled = self.stretch(art, target_width, target_height)
        elif scale_method == "Fit":
            art_scaled = self.fit(art, target_width, target_height)
        elif scale_method == "Crop":
            art_scaled = self.crop(art, target_width, target_height, offset)
        if showFrame:
            art_size = (target_width-(self.scale*2), target_height-(self.scale*2))
            diff = (self.scale,self.scale)
        else:
            art_size = (target_width, target_height)
            diff = (0,0)
        art_resized = art_scaled.resize(art_size, Image.NEAREST)
        painting.paste(art_resized, diff, art_resized.convert('RGBA'))

        return painting

    def callPainting(self, painting):
        return Image.open(self.resource_path(painting + ".png")).convert('RGBA')

    def stretch(self, art, target_width, target_height):
        art_size = (target_width, target_height)
        blackout = Image.new('RGB', (target_width, target_height), color = self.background_color)
        art_resized = art.resize(art_size)
        blackout.paste(art_resized, (0,0), art_resized.convert('RGBA'))
        return blackout

    def fit(self, art, target_width, target_height):
        art_width, art_height = art.size
        blackout = Image.new('RGB', (target_width, target_height), color = self.background_color)

        new_height = target_height
        new_width = int((art_width / art_height) * target_height)
        diff = ((target_width-new_width)//2, 0)
        if (new_height > target_height) or (new_width > target_width):
            print("Warning: Switching Methods")
            new_width = target_width
            new_height = int((art_height / art_width) * target_width)
            diff = (0,(target_height-new_height)//2)

        art_size = (new_width, new_height)
        art_resized = art.resize(art_size)
        blackout.paste(art_resized, diff, art_resized.convert('RGBA'))
        return blackout

    def crop(self, art, target_width, target_height, offset):
        art_width, art_height = art.size
        blackout = Image.new('RGB', (target_width, target_height), color = self.background_color)

        new_width = target_width
        new_height = int((art_height / art_width) * target_width)
        diff = (0,int((target_height-new_height)*offset))
        if (new_height < target_height) or (new_width < target_width):
            print("Warning: Switching Methods")
            new_height = target_height
            new_width = int((art_width / art_height) * target_height)
            diff = (int((target_width-new_width)*offset), 0)

        art_size = (new_width, new_height)
        art_resized = art.resize(art_size)
        blackout.paste(art_resized, diff, art_resized.convert('RGBA'))
        return blackout

    def resource_path(self, file):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'assets', 'painting', file)

# Displaying the image
if __name__ == "__main__":
    #art = Image.open("../input.png")
    art = Image.open("../pool.jpg")
    maker = PaintingGenerator()
    painting = maker.makePaiting(16, "Fit", "black", "finding", art)
    painting.show()
