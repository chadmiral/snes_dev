import argparse
from fnmatch import fnmatchcase
import os

parser = argparse.ArgumentParser(description='SNES sprite conversion tool')
parser.add_argument('input', metavar='input_image', type=str, nargs='+', help='input image file')
parser.add_argument('--sizeX', help='output horizontal size')
parser.add_argument('--sizeY', help='output vertical size')
args = parser.parse_args()

from PIL import Image

def endianSwap(myByte):
    return ((myByte << 4) & 0xf0) | ((myByte >> 4) & 0x0f)

def getTileCount(img_PIL):
    return (img_PIL.width / 4, img_PIL.height / 4)

#return a 4x4 pixel tile sub-image
def getTile(img_PIL, tileSize, x, y):
    return img_PIL.crop((x * tileSize, y * tileSize, x * tileSize + tileSize, y * tileSize + tileSize))

def writeTilesPNG(img_PIL, tileSize):
    print("writing tiles pngs...")
    for j in range(int(img_PIL.height / tileSize)):
        for i in range(int(img_PIL.width / tileSize)):
            tile = getTile(img_PIL, tileSize, i, j)
            tile.save("tile%d%d.png"%(i, j))

def getTileBitplanes(tile_PIL, numBitPlanes):
    bytes = bytearray()
    myByte = 0
    bitCounter = 7
    
    for bpHigh in range(numBitPlanes >> 1):
        for y in range(tile_PIL.height):
            for bpLow in range(2):
                bp = bpHigh * 2 + bpLow
                print("bitplane: %d"%(bp))
                for x in range(tile_PIL.width):
                    
                    p = tile_PIL.getpixel((x, y))
                    print("(%d, %d): index: %x, bitmask: %x, bit: %d"%(x, y, p, 1 << bp, (p & (1 << bp)) != 0))
                    if (p & (1 << bp)) != 0:
                        myByte |= (1 << bitCounter)
                    bitCounter -= 1
                    if (bitCounter < 0):
                        #bytes.append(endianSwap(myByte))
                        bytes.append(myByte)
                        print("Byte: %02x, %02x"%(myByte, endianSwap(myByte)))

                        #new byte, reset our accumulator
                        bitCounter = 7
                        myByte = 0
    
    print(bytes)
    return bytes

def writeTilesBitplanes(img_PIL, tileSize, numBitPlanes):
    print("writing tile bitplanes")

    fp = open('mySprite.vra', 'wb')

    for j in range(int(img_PIL.height / tileSize)):
        for i in range(int(img_PIL.width / tileSize)):
            tile = getTile(img_PIL, tileSize, i, j)
            print("tile %d,%d"%(i, j))
            bytes = getTileBitplanes(tile, numBitPlanes)
            for b in bytes:
                fp.write(b.to_bytes(1, 'little'))
            #fp.write(bytes)
    
    fp.close()

#write the palette file
def writePalette(palette, numColors):
    print('Writing palette...')
    palette_bytes = palette.tobytes()

    '''
    # dump PIL's text palette
    fp = open('palette.txt', 'w')
    palette.save(fp)
    fp.close()
    '''

    #print("Color Palette:")
    print('              RGB               rgb888         bgr555    ')
    print('-----------------------------------------------------')

    # convert from rgb888 to bgr555 (snes palette format)
    fp = open('mySprite.pal', 'wb')
    for i in range(numColors):#range(0, len(palette_bytes), 3):
        r = palette_bytes[i * 3]
        g = palette_bytes[i * 3 + 1]
        b = palette_bytes[i * 3 + 2]

        # remove 3 most significant bits of each color channel & repack
        bgr555 = ((r & 0xf8) >> 3) | ((g & 0xf8) << 2) | ((b & 0xf8) << 7)

        print("%2d:\t(%3d, %3d, %3d)\t\t#%02x%02x%02x\t\t#%04x"%(i, palette_bytes[i], palette_bytes[i + 1], palette_bytes[i + 2], palette_bytes[i], palette_bytes[i + 1], palette_bytes[i + 2], bgr555))

        # but also, snes is little endian, so we need to store the least significant byte first
        fp.write(bgr555.to_bytes(2, 'little'))
        #fp.write(bgr555.to_bytes(2, 'big'))
        
    fp.close()


def main():
    numColors = 16

    for img_path in args.input:
        print("scrunching " + img_path + "...")
        orig_image = Image.open(img_path)

        img_PIL = None
        if orig_image.mode != 'P':
            print("Converting input image to 8-bit palettized...")

            # for some reason, if I do the conversion in memory, rather than save it out, my palette gets screwed up
            orig_image.convert(mode='P', palette=Image.ADAPTIVE, colors=numColors).save("tmp.png")
            img_PIL = Image.open("tmp.png")
            os.remove("tmp.png")

        else:
            img_PIL = orig_image
            
        (w, h) = (img_PIL.width, img_PIL.height)
        if args.sizeX:
            w = int(args.sizeX)
        if args.sizeY:
            h = int(args.sizeY)
        if args.sizeX or args.sizeY:
            img_PIL = img_PIL.resize((w, h), resample=Image.NEAREST)

        print("output dimensions: %dx%d"%(img_PIL.width,img_PIL.height))

        writeTilesPNG(img_PIL, 8)
        writeTilesBitplanes(img_PIL, 8, 4)

        # Write the palette
        if img_PIL.mode == 'P':
            pixels = img_PIL.load()
            palette = img_PIL.palette
            writePalette(palette, numColors)

            #print(getTileCount(img_PIL))

main()