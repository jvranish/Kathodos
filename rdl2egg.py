
#from panda3d.core import *
from pandac.PandaModules import *
from panda3d.egg import *
import D1DataLoaders



def printTextureMaps(names):
  shorterList = {}
  for i, (name, frame, abm, xsize, ysize, (transparent, noLighting, rle, pagedOut, rleBig, averageColor), offset) in enumerate(names):
    print i, name, frame
    if name in shorterList:
      shorterList[name] += [i]
    else:
      shorterList[name] = [i]
  print len(shorterList.keys())
  print shorterList.keys()

def rdl2egg(rdlFilename, eggFilename):
  d1Level = D1DataLoaders.loadD1Level(rdlFilename)
  textureNames, sounds = D1DataLoaders.loadD1Pig("origData/descent.pig", False)
  printTextureMaps(textureNames)
  #filteredNames = []
  #k = 0
  #for i, (name, frame, abm, xsize, ysize, (transparent, noLighting, rle, pagedOut, rleBig, averageColor), offset) in enumerate(textureNames):
  #  if not abm and frame ==0:
  #    filteredNames.append((name, frame, abm, xsize, ysize, (transparent, noLighting, rle, pagedOut, rleBig, averageColor), offset))
  #    print k, name
  #    k +=1
  #textureNames = filteredNames
  #print len(textureNames)
    #print i, name, frame
  (header, verts, cubes) = d1Level
  currentTextures = {}
  def loadTexture(index):
    #print index
    
    if index >= len(textureNames):
      print "bad index", index
      index = index & 0x7FF
    #if index > 444:
    #  index -= 24
    #else:
    #  index += 153
    #print index
    oldIndex = index
    #if index == 577:
    #  index += 971
    if index >= 255:
      index += 715
    else:
      index += 718
    
    # 
    # 577 => 1548, 971  => 553, -24
    # 39 => 757, 718    => 192, 153
     
    (name, frame, abm, xsize, ysize, (transparent, noLighting, rle, pagedOut, rleBig, averageColor), offset) = textureNames[index]
    currentTextures[index]=(oldIndex, name, frame)
    if frame == 0:
      filename = "media/textures/" + name + ".png"
      #print filename
    else:
      filename = "media/textures/" + name + "-" + str(frame) + ".png"
    texture = EggTexture(name, Filename(filename))
    #texture.setWrapMode(Texture.WMRepeat)
    #texture.setWrapU(Texture.WMRepeat)
    #texture.setWrapV(Texture.WMRepeat)
    return texture
      
  
  data = EggData()
  group = EggGroup("level")
  group.setCsType(EggGroup.CSTPolyset)
  group.setCollideFlags(EggGroup.CFDescend | EggGroup.CFKeep)
  data.addChild(group)
  vp = EggVertexPool(rdlFilename)
  group.addChild(vp)
    
  for cubeVertIds, sides, walls, staticLightValue, eCenterData in cubes:
    for sideVerts, texureData in sides + walls:
      primary, secondary, UVLs = texureData
      poly = EggPolygon()
      group.addChild(poly)
      for vert, (U, V, L) in reversed(zip(sideVerts, UVLs)):
        v = EggVertex()
        x, y, z = verts[cubeVertIds[vert]]
        v.setPos(Point3D(x, y, z))
        v.setUv(Point2D(2.0*U, 2.0*V))
        vId = vp.addVertex(v)
        poly.addVertex(vId)
      primaryTex = loadTexture(primary)
      poly.addTexture(primaryTex)
      if secondary != None:
        secondaryTex = loadTexture(secondary)
        secondaryTex.multitextureOver(primaryTex)
        secondaryTex.setEnvType(EggTexture.ETDecal)
        primaryTex.setCombineMode(EggTexture.CCAlpha, EggTexture.CMReplace)
        #primaryTex.setCombineMode(EggTexture.CCAlpha, EggTexture.CMReplace)
        #secondaryTex.setCombineMode(EggTexture.CCRgb, EggTexture.CMReplace)
        
        #primaryTex.multitextureOver(secondaryTex)
        poly.addTexture(secondaryTex)
      
  print len(currentTextures.values())
  for a, b, c in currentTextures.values():
    print a, b, c
  
  
  data.writeEgg(Filename(eggFilename))
rdl2egg("origData/minerva.rdl", "levels/minerva.egg")
