import direct.directbase.DirectStart
from panda3d.core import *
from pandac.PandaModules import *
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
from joystick import *
import sys
# import random, sys, os, math


def clampVector(v, maxLength):
  if v.length() > maxLength:
    v.normalize()
    return v * maxLength
  else:
    return v

class World(DirectObject):

    def handleLaserHitLevel(self, entry):
      laser = entry.getFromNodePath()
      laser.removeNode()
      self.laserHitWall.play()
      #print "hit level"
    def handleLaserHitShip(self, entry):
      laser = entry.getFromNodePath()
      laser.removeNode()
      self.laserHitPlayer.play()
      #print "hit ship"


    def __init__(self):
        self.keyMap = {"left":0, "right":0, "forward":0, "cam-left":0, "cam-right":0}
        self.axisData = Vec3(0.0,0.0,0.0)
        base.win.setClearColor(Vec4(0,0,0,1))

        base.disableMouse()
        base.enableParticles()
        angleInt = AngularEulerIntegrator() # add angular integrator to the physics manager (for rotational physics)
        base.physicsMgr.attachAngularIntegrator(angleInt)


        self.environ = loader.loadModel("levels/minerva")
        self.environ.reparentTo(render)
        #self.environ.setPos(0,0,0)
        #self.environ.setTag("MyTag", '0')
        #self.environ.setCollideMask(BitMask32.bit(1))
        #self.environ.setCollideMask(BitMask32.bit(0)) # BitMask32.bit(0)
        #print self.environ.getChild(0).getChild(0).getChildren()
        #self.environ.node().setFromCollideMask(GeomNode.getDefaultCollideMask())
        #self.environ.node().setFromCollideMask(GeomNode.getDefaultCollideMask()).setIntoCollideMask(0)
        

        self.cHandler = PhysicsCollisionHandler()

        self.cTrav = CollisionTraverser()
        self.cTrav.setRespectPrevTransform( True )
        #self.cTrav.showCollisions(render)
        
        
        self.pHandler = CollisionHandlerEvent()
        self.pHandler.addInPattern('%fn-into-%in')
        #self.cHandler.addCollider(
        #self.cHandler.addCollider(collideNode, actorNodePath)
        #self.cTrav.addCollider(self.environ, self.pHandler)
        self.accept('laser-bounds-into-player-player1-bounds', self.handleLaserHitShip)
        self.accept('laser-bounds-into-level', self.handleLaserHitLevel)
        
        self.laserSound = base.loader.loadSfx("media/sound/laser02.wav")
        self.laserHitWall = base.loader.loadSfx("media/sound/explode1.wav")
        self.laserHitPlayer = base.loader.loadSfx("media/sound/shit01.wav")
        
        
        class Player:
          def __init__(player, name, pos):
            nodePath = NodePath(PandaNode("playerShipNode"))
            nodePath.reparentTo(render)
            actorNode = ActorNode("playerShip-physics")
            actorNode.getPhysicsObject().setMass(2000.0) # two metric tons
            #actorNode.getPhysicsObject().setTerminalVelocity(150.0)
            
            base.physicsMgr.attachPhysicalNode(actorNode)
            
            actorNodePath = nodePath.attachNewNode(actorNode)
            actorNodePath.setPos(pos)
            
            modelNode = loader.loadModel("media/models/Fighter")
            modelNode.reparentTo(actorNodePath)
            modelNode.setScale(0.1)
            modelNode.setHpr(180.0, 0.0, 0.0)
            
            
            #thrusterForce = LinearVectorForce(0, 0, 0)
            #thrusterForce.setMassDependent(1)
            
            #rotThrusterForce = AngularVectorForce(0, 0, 0)

            #forceNode = ForceNode('player-thrusters') # Attach a thruster force
            #forceNode.addForce(thrusterForce)
            #forceNode.addForce(rotThrusterForce)
            
            
            #thrusterForceNodePath = modelNode.attachNewNode(forceNode)
            #forceNodePath = render.attachNewNode(forceNode)
            #actorNode.getPhysical(0).setViscosity(0.1)
            #actorNode.getPhysical(0).addAngularForce(rotThrusterForce)
            #actorNode.getPhysical(0).addLinearForce(thrusterForce)
            
            
            boundingSphere = CollisionNode('player-' + name + '-bounds')
            boundingSphere.addSolid(CollisionSphere(0, 0, 0, 2))
            collideNode = actorNodePath.attachNewNode(boundingSphere)
            #collideNode.show()
            
            self.cHandler.addCollider(collideNode, actorNodePath)
            self.cTrav.addCollider(collideNode, self.cHandler)
            
            player.nodePath = nodePath
            player.actorNode = actorNode
            player.actorNodePath = actorNodePath
            player.modelNode = modelNode
            player.collideNode = collideNode
            player.laserCool = 0.0
            #player.thrusterForce = thrusterForce
            #player.rotThrusterForce = rotThrusterForce
            #player.forceNodePath  = forceNodePath
            
          def createLaserProjectile(player):
            laser = PandaNode("laserProjectile")
            self.laserSound.play()
            velocity = Vec3(0.0, -120.0, 0.0) #-120
            nodePath = player.actorNodePath.attachNewNode(laser)

            actorNode = ActorNode("projectile-laser")
            actorNode.getPhysicsObject().setVelocity(velocity)
            #actorNode.setPos(0.0, -3.0, 0.0)
            
            base.physicsMgr.attachPhysicalNode(actorNode)
            
            actorNodePath = nodePath.attachNewNode(actorNode)
            actorNodePath.setPos(0.0, -3.0, 0.0)
            
            modelNode = NodePath(PandaNode("laserNode"))
            modelNode.reparentTo(actorNodePath)
            #modelNode.setPos(0.0, -2.0, 0.0)
              
            pointA = Point3(0.0, 0.0, 0.0)
            pointB = Point3(0.0, -1.0, 0.0)
            boundingObject = CollisionNode('laser-bounds')
            #boundingObject.addSolid(CollisionSegment(pointA, pointB))
            boundingObject.addSolid(CollisionSphere(0.0, 0.0, 0.0, 0.1))
            boundingObject.setIntoCollideMask(0)
            collideNode = actorNodePath.attachNewNode(boundingObject)
            collideNode.show()
            
            #self.cHandler.addCollider(collideNode, actorNodePath)
            #self.cTrav.addCollider(collideNode, self.cHandler)
            
            self.cTrav.addCollider(collideNode, self.pHandler)
            
            nodePath.wrtReparentTo(render)
          
        self.playerShip = Player("player1", Vec3(0,-40,0))
        
       
        
        base.camera.reparentTo( self.playerShip.actorNodePath)
        base.camera.setPos(Vec3(0,20,5))
        #
        base.camera.lookAt(self.playerShip.actorNodePath)

        # Create joystick handler
        self.joy = JoystickHandler()

        # Accept the control keys for movement and rotation
        #def addAxisControlKeys(namePos, nameNeg, stateName):
        #  def set
        #  setControlState(stateName, 0.0)
        #  self.accept(namePos, setControlState, [stateName, 1.0])
        #  self.accept(namePos + "-up", setControlState, [stateName, -1.0])
        def setControlState(name, value):
          self.__dict__[name] = value
        def setHatState(left, right, up, down, value):
          self.__dict__[left] = False
          self.__dict__[right] = False
          self.__dict__[up] = False
          self.__dict__[down] = False

          (x,y) = value

          if x == -1:
            self.__dict__[left] = True
          elif x == 1:
            self.__dict__[right] = True

          if y == -1:
            self.__dict__[down] = True
          elif y == 1:
            self.__dict__[up] = True

        def setAxisState(name, value):
          if name == 'x':
            self.axisData[0] = -value
          elif name == 'y':
            self.axisData[1] = -value
          elif name == 'z':
            self.axisData[2] = -value

        def addControlKey(keyName, stateName):
          setControlState(stateName, False)
          self.accept(keyName, setControlState, [stateName, True])
          self.accept(keyName + "-up", setControlState, [stateName, False])

        def addHatKey(keyName, left, right, up, down):
          self.accept(keyName, setHatState, [left, right, up, down])

        def addAxis(joyName):
          self.accept(joyName + '-axis0', setAxisState, ['x'])
          self.accept(joyName + '-axis1', setAxisState, ['y'])
          self.accept(joyName + '-axis3', setAxisState, ['z'])


        self.accept("escape", sys.exit)
        addControlKey("a", "moveLeft")
        addControlKey("d", "moveRight")
        addControlKey("w", "moveUp")
        addControlKey("s", "moveDown")

        # Hard coded joystick controls
        addControlKey("joystick0-button6", "moveBackward")
        addControlKey("joystick0-button7", "moveForward")
        addControlKey("joystick0-button5", "fireOn")
        addControlKey("joystick0-button2", "yawLeft")
        addControlKey("joystick0-button1", "yawRight")
        addControlKey("joystick0-button3", "pitchUp")
        addControlKey("joystick0-button0", "pitchDown")
        # Specify the actions to take for each direction of the hat
        addHatKey("joystick0-hat0", "moveLeft", "moveRight", "moveUp", "moveDown")
        addAxis("joystick0")

        addControlKey("4", "yawLeft")
        addControlKey("6", "yawRight")
        addControlKey("8", "pitchUp")
        addControlKey("5", "pitchDown")
        addControlKey("7", "rollLeft")
        addControlKey("9", "rollRight")
        
        addControlKey("+", "moveForward")
        addControlKey("enter", "moveBackward")
        
        addControlKey("space", "fireOn")

        taskMgr.add(self.move, "moveTask")
        print taskMgr

        # Create some lighting
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor(Vec4(.3, .3, .3, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(Vec3(-5, -5, -5))
        directionalLight.setColor(Vec4(1, 1, 1, 1))
        directionalLight.setSpecularColor(Vec4(1, 1, 1, 1))
        render.setLight(render.attachNewNode(ambientLight))
        render.setLight(render.attachNewNode(directionalLight))
        base.cTrav = self.cTrav
        self.clock = ClockObject()
        base.setFrameRateMeter(True)
        #self.count = 0

    # Accepts arrow keys to move either the player or the menu cursor,
    # Also deals with grid checking and collision detection
    def move(self, task):
      #md = base.win.getPointer(0) 
      #x = md.getX() 
      #y = md.getY() 
      #if base.win.movePointer(0, base.win.getXSize()/2, base.win.getYSize()/2): 
      #  pass
      if self.fireOn:# and self.bla:
        if task.time >= self.playerShip.laserCool:
          self.playerShip.createLaserProjectile()
          self.playerShip.laserCool = task.time + 0.4
  
      #print self.count
      #if not self.fireOn:
      #  self.bla = True
      
      #forward = self.playerShip.getPos() - base.camera.getPos(render)
      #forward.normalize()
      
      rotation = self.playerShip.actorNodePath.getHpr(render)
      translation = self.playerShip.actorNodePath.getPos(render)
      lcs = self.playerShip.actorNodePath.getMat()
      #print rotation
      #self.playerShip.forceNodePath.setHpr(rotation)
      #self.playerShip.forceNodePath.setPos(translation)
      

      forward = Vec3(0.0, -1.0, 0.0)
      left = Vec3(1.0, 0.0, 0.0)
      up = Vec3(0.0, 0.0, 1.0)
      moveAmount = Vec3(0.0, 0.0, 0.0)
      if self.moveForward:
        moveAmount += forward
      if self.moveBackward:
        moveAmount -= forward
      if self.moveLeft:
        moveAmount += left
      if self.moveRight:
        moveAmount -= left
      if self.moveUp:
        moveAmount += up
      if self.moveDown:
        moveAmount -= up

      currentVelocity = self.playerShip.actorNode.getPhysicsObject().getVelocity()
      #print currentVelocity
      moveAmount = Vec3(lcs.xformVec(moveAmount))
      desiredVelocity = moveAmount * 80.0
      deltaVel = desiredVelocity - currentVelocity
      
      maxAccel = 10.0
      #desiredCloseTime = 0.2 # *(1.0/desiredCloseTime)
      if deltaVel.length():
        thrust = clampVector(deltaVel * 0.1, maxAccel)
        #print thrust.length()
        #print "DeltaVel", deltaVel, currentVelocity, thrust
        #self.playerShip.actorNode.getPhysicsObject().addImpulse(Vec3(lcs.xformVec(thrust)))
        self.playerShip.actorNode.getPhysicsObject().addImpulse(thrust)
        #self.playerShip.thrusterForce.setVector(thrust*mass)
      
      heading = Vec3(1.0, 0.0, 0.0)
      pitch = Vec3(0.0, 1.0, 0.0)
      roll = Vec3(0.0, 0.0, 1.0)
      rotateAmount = Vec3(0.0, 0.0, 0.0)

      # Joystick data
      rotateAmount = self.axisData

      if self.yawLeft:
        rotateAmount += heading
      if self.yawRight:
        rotateAmount -= heading
      if self.pitchUp:
        rotateAmount += pitch
      if self.pitchDown:
        rotateAmount -= pitch
      if self.rollLeft:
        rotateAmount += roll
      if self.rollRight:
        rotateAmount -= roll
      
      h, p, r = rotateAmount * 1.5 * self.clock.getDt() * 100.0
      #desiredRotation = LRotationf()
      #desiredRotation.setHpr(rotateAmount * 0.9)
      #temp = LRotationf()
      #temp.setHpr(rotation)
      #desiredRotation = temp * desiredRotation
      
      #currentRotation = self.playerShip.actorNode.getPhysicsObject().getRotation()
      #deltaRotation = desiredRotation #- currentRotation
      self.playerShip.actorNode.getPhysicsObject().addLocalTorque(LRotationf(h, p, r)*0.1)
      #self.playerShip.rotThrusterForce.setHpr(h, p, r)

      #self.cTrav.traverse(render)
      self.clock.tick()

      return task.cont


w = World()
run()


