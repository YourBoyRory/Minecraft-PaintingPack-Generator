from PIL import Image 


class PaintingGenerator:

    def makePaiting(self, scale, scale_method, background_color, painting, art):

        frame = Image.open("./assets/painting/" + painting + ".png").convert('RGBA')
        
        # The Maff :3
        pack_res = 16*scale
        width, height = frame.size
        height = int(height/16)
        width = int(width/16)
        painting_size = (pack_res*width, pack_res*height)
        blackout_size = ((pack_res*width)-(scale*2), (pack_res*height)-(scale*2))
        
        blackout = Image.new('RGB', (blackout_size), color = background_color)
        painting = frame.resize(painting_size, Image.NEAREST)
        painting.paste(blackout, (scale,scale))
        
        if scale_method == "Stretch":
            diff = (scale,scale)
            art_size = ((pack_res*width)-(scale*2), (pack_res*height)-(scale*2))
            art_resized = art.resize(art_size)
        elif scale_method == "Fit":
            art_width, art_height = art.size
            if art_height > art_width:
                new_height = (pack_res*height)-(scale*2)
                temp_width = (pack_res*width)-(scale*2)
                new_width = int((new_height / art_height) * art_width)
                diff = (scale + (temp_width-new_width)//2,scale)
            else:
                new_width = (pack_res*width)-(scale*2)
                temp_height = (pack_res*height)-(scale*2)
                new_height = int((new_width / art_width) * art_height)
                diff = (scale,scale + (temp_height-new_height)//2)
            art_size = (new_width, new_height)
            art_resized = art.resize(art_size)
        elif scale_method == "Crop":
            diff = (scale,scale)
            art_width, art_height = art.size
            if art_height > art_width:
                new_width = (pack_res*width)-(scale*2)
                new_height = int((new_width / art_width) * art_height)
                art_size = (new_width, new_height)
                art_fitted = art.resize(art_size)
                crop_height = (new_height - new_width)//2
                crop_box = (0, crop_height, art_width, new_height-crop_height)
            else:
                new_height = (pack_res*height)-(scale*2)
                new_width = int((new_height / art_height) * art_width)
                art_size = (new_width, new_height)
                art_fitted = art.resize(art_size)
                crop_width = (new_width - new_height)//2
                crop_box = (crop_width, 0, new_width-crop_width, new_height)
            art_resized = art_fitted.crop(crop_box)

        painting.paste(art_resized, diff, art_resized.convert('RGBA'))
        
        return painting
        

# Displaying the image
if __name__ == "__main__":
    art = Image.open("../pool.jpg")
    maker = PaintingGenerator()
    painting = maker.makePaiting(4, "Crop", "wither", art)
    painting.show()
