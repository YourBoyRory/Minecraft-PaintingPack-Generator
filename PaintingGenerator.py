from PIL import Image 


class PaintingGenerator:

    def makePaiting(self, scale, painting, art):

        frame = Image.open("./assets/painting/" + painting + ".png").convert('RGBA')

        # The Maff :3
        pack_res = 16*scale
        width, height = frame.size
        height = int(height/16)
        width = int(width/16)
        diff = int(scale)
        painting_size = (pack_res*width, pack_res*height)
        art_size = ((pack_res*width)-(diff*2), (pack_res*height)-(diff*2))

        painting = frame.resize(painting_size, Image.NEAREST)
        blackout = Image.new('RGB', (art_size), color = 'black')
        art_resized = art.resize(art_size)
          

        painting.paste(blackout, (diff,diff))
        painting.paste(art_resized, (diff,diff), art_resized.convert('RGBA'))
        
        return painting

# Displaying the image
if __name__ == "__main__":
    art = Image.open("../input.jpg")
    maker = PaintingGenerator()
    painting = maker.makePaiting(16, "wither.png", art)
    painting.show()
