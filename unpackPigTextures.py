
import struct

import D1DataLoaders

from pandac.PandaModules import *
from panda3d.core import *


def readPalette():
  palette = []
  with open('origData/palette.bmp', 'rb') as f:
    f.read(14) # BMP header
    f.read(40) # DIB header
    for i in xrange(256):
      color = f.read(4) # read palette colors
      b, g, r, unused = struct.unpack('BBBB', color)
      palette.append((r, g, b))
  return palette
    
    
def unpackPigTextures():
  palette = readPalette()
  textures, sounds = D1DataLoaders.loadD1Pig("origData/descent.pig")
  for textureName, data in textures:
    name, frame, abm, xsize, ysize, (transparent, noLighting, rle, pagedOut, rleBig, averageColor) = textureName
    newImage = PNMImage(xsize, ysize)
    print name, frame
    if abm:
      print name, frame, transparent, noLighting
    if transparent:
      newImage.addAlpha()
    for x in xrange(xsize):
      for y in xrange(ysize):
        value = data[y*xsize + x]
        r, g, b = palette[value]
        if transparent:
          a = 0 if value >= 254 else 255
          newImage.setAlphaVal(x, y, a)
        newImage.setXelVal(x, y, r, g, b)
    if frame > 0:
      newImage.write(Filename("media/textures/" + name + "-" + str(frame) + ".png"))
    else: 
      newImage.write(Filename("media/textures/" + name + ".png"))
unpackPigTextures()