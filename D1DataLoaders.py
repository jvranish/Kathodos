import struct
import string

def byteToBools(byte):
  return (bool(byte & 128), bool(byte & 64), bool(byte & 32), bool(byte & 16), bool(byte & 8), bool(byte & 4), bool(byte & 2), bool(byte & 1))

class UnpackableFile(file):
  def __init__(self, filename):
    file.__init__(self, filename, 'rb')
  
  def unpack(self, fmt):
    size = struct.calcsize(fmt)
    packedData = self.read(size)
    unpackedValues = struct.unpack(fmt, packedData)
    if len(unpackedValues) == 1:
      unpackedValues, = unpackedValues
    return unpackedValues
    
  def unpackIf(self, fmt, cond):
    return self.unpack(fmt) if cond else None
    
  def unpackN(self, n, f):
    return [f() for i in xrange(n)]

class D1LevelFile(UnpackableFile):
  def __init__(self, filename):
    UnpackableFile.__init__(self, filename)  
  
  def unpackFixed(self):
    fixedValue = self.unpack("i")
    return float(fixedValue)/2.0**16
    
  def unpackFixedShort(self):
    fixedValue = self.unpack("h")
    return float(fixedValue)/2.0**12

  def unpackVertex(self):
    x, y, z = self.unpackN(3, self.unpackFixed)
    return (-x, y, z)
    
  def unpackCube(self):
    bitmask = self.unpack("B")
    unused, energyCenter, front, back, bottom, right, top, left = byteToBools(bitmask)
    neighborFlags = [left, top, right, bottom, back, front]
    neighborIds = [self.unpackIf("H", x) for x in neighborFlags]
      
    cubeVertIds = self.unpackN(8, lambda : self.unpack("H"))
    
    if energyCenter:
      special = self.unpack("B")
      energyCenterNumber = self.unpack("b")
      energyCenterValue = self.unpack("h")
      eCenterData  = (special, energyCenterNumber, energyCenterValue)
    else:
      eCenterData = None
      
    staticLightValue = self.unpackFixedShort()
    wallBitmask = self.unpack("B")
    unused, unused, frontWall, backWall, bottomWall, rightWall, topWall, leftWall = byteToBools(wallBitmask)
    #leftWall, topWall, rightWall, bottomWall, backWall, frontWall, unused, unused = byteToBools(wallBitmask)
    wallFlags = [leftWall, topWall, rightWall, bottomWall, backWall, frontWall]
    wallIds = [self.unpackIf("B", x) for x in wallFlags]
    for i, x in enumerate(wallIds):
      if x == 0xFF:
        wallFlags[i] = False
    
    def unpackUVL():
      U = self.unpackFixedShort()
      V = self.unpackFixedShort()
      L = self.unpackFixedShort()
      return (U,V,L)
    
    def unpackTexture():
      primary = self.unpack("H")
      if primary & 0x8000:
        primary = primary & 0x7fff
        secondary = self.unpack("H")
      else:
        secondary = None
      UVLs = self.unpackN(4, unpackUVL)
      return (primary, secondary, UVLs)
    
    sides = []
    walls = []
    
    # left, top, right, bottom, back, front
    sideVertIndx = [[2, 3, 7, 6], [7, 3, 0, 4], [0, 1, 5, 4], [5, 1, 2, 6], [4, 5, 6, 7], [3, 2, 1, 0]]    
    for neighborFlag, wallFlag, sideVerts in zip(neighborFlags, wallFlags, sideVertIndx):
      if not neighborFlag or wallFlag:
        texureData = unpackTexture()
        if not neighborFlag:
          sides.append( (sideVerts, texureData) )  
        else:
          walls.append( (sideVerts, texureData) )

      
    return (cubeVertIds, sides, walls, staticLightValue, eCenterData)
    
  def unpackLevel(self):
    #TODO Perhaps put this in __init__ somehow, perhaps add some extra failure conditions?
    header = self.unpack("4siiii")
    signature, version, mineDataOffset, objectsOffset, fileSize = header
    print signature, version
    print mineDataOffset, objectsOffset
    print fileSize
    self.seek(mineDataOffset+1)
    #self.setOffset(mineDataOffset+1)

    vertexCount, cubeCount = self.unpack("hh")
    print vertexCount, cubeCount
    verts = self.unpackN(vertexCount, self.unpackVertex)
    #print verts
    cubes = self.unpackN(cubeCount, self.unpackCube)
    currentOffset = self.tell()
    print currentOffset == objectsOffset # check to see if we got everything just right
    
    #vert1, = self.unpack("L")
    #print float(vert1)/2.0**16-1
    return (header, verts, cubes)

  

  
class D1PigFile(UnpackableFile):
  def __init__(self, filename):
    UnpackableFile.__init__(self, filename)
  
  def unpackD1PigTextureName(self):
    name = self.unpack("8s")
    frame = self.unpack("B")
    abm = bool(frame & 0x20) # pick out 6th bit
    frame = frame & 0x1F # mask all but lower 5 bits
    name = name[:len(name) - len(name.lstrip(string.printable))]
    
    xsize = self.unpack("B")
    ysize = self.unpack("B")
    flag = self.unpack("B")
    
    transparent = bool(flag & 1)
    superTransparent = bool(flag & 2)
    noLighting = bool(flag & 4)
    rle = bool(flag & 8)
    pagedOut = bool(flag & 16)
    rleBig = bool(flag & 32)
    
    averageColor = self.unpack("B")
    offset = self.unpack("I")
    return (name, frame, abm, xsize, ysize, (transparent, noLighting, rle, pagedOut, rleBig, averageColor), offset)
  
  def unpackD1PigSoundName(self):
    name = self.unpack("8s")
    length = self.unpack("i")
    data_length = self.unpack("i") # which should be the same thing actually...
    offset = self.unpack("i")
    return (name, length, data_length, offset)
    
  def unpackD1Pig(self, loadTextureData):
    offset = self.unpack("I")
    self.seek(offset)
    numTextures, numSounds = self.unpack("ii")
    print numTextures, numSounds
    #names = self.unpackN(100, unpackDescent1PigTexture)
    textureNames = self.unpackN(numTextures, self.unpackD1PigTextureName)
    soundNames = self.unpackN(numSounds, self.unpackD1PigSoundName)
    OffsetOfEndOfDirectory = self.tell()
    def rleDecode(total_size):
      decodedData = [] 
      startOffset = self.tell()
      
      
      #byte = self.unpack("B")
      while self.tell() - startOffset < total_size:
        byte = self.unpack("B")
        if byte == 0xE0:
          pass
        elif byte & 0xE0 == 0xE0:
          runLength = byte & 0x1F
          runByte = self.unpack("B")
          decodedData.extend([runByte] * runLength)
        else:
          decodedData.append(byte)
        
      return decodedData
        
    if loadTextureData:
      textures = []
      for texture in textureNames:
        (name, frame, abm, xsize, ysize, (transparent, noLighting, rle, pagedOut, rleBig, averageColor), offset) = texture
        self.seek(offset + OffsetOfEndOfDirectory)
        #total_size = self.unpack("l")
        #print total_size
        if rle:
          total_size = self.unpack("I")
          line_sizes = self.unpackN(ysize, lambda : self.unpack("B"))
          data = rleDecode(total_size - 5 - ysize)
        elif rleBig:
          total_size = self.unpack("I")
          line_sizes = self.unpackN(ysize, lambda : self.unpack("H"))
          data = rleDecode(total_size - 6 - ysize)
        else:
          data = self.unpackN(xsize*ysize, lambda : self.unpack("B"))
        if len(data) != xsize*ysize:
          print name,  len(data), xsize*ysize, xsize, ysize, rle or rleBig
        #else:
          #print "\t", name,  len(data), xsize*ysize
          #raise Exception("failed RLE decode", len(data), xsize*ysize)
        textures.append(((name, frame, abm, xsize, ysize, (transparent, noLighting, rle, pagedOut, rleBig, averageColor)), data))
    else:
      textures = textureNames
    return(textures, soundNames)
    #mreturn(names)
    
def loadD1Level(filename):
  with D1LevelFile(filename) as f:
    #print f.read(4)
    return f.unpackLevel()
    #print dir(f)
  
#LoadD1Level("minerva.rdl")

def loadD1Pig(filename, loadTextureData = True):
  with D1PigFile(filename) as f:
    return f.unpackD1Pig(loadTextureData)
  
