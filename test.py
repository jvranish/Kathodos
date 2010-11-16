import direct.directbase.DirectStart
from panda3d.core import *
from pandac.PandaModules import *
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
from joystick import *
import sys
# import random, sys, os, math


class PlayerIntent:
  def __init__(self, playerNum, fireOn = False, thrusters = Vec3(0.0, 0.0, 0.0), rotThrusters = Vec3(0.0, 0.0, 0.0)):
    self.playerNum = playerNum
    self.fireOn = fireOn
    self.thrusters = Vec3(thrusters)
    self.rotThrusters = Vec3(rotThrusters)
    
  def __add__(self, other):
    return PlayerIntent( self.playerNum
                       , self.fireOn or other.fireOn
                       , Vec3(tuple([max((-1.0, min((1.0, x)))) for x in self.thrusters + other.thrusters]))
                       , Vec3(tuple([max((-1.0, min((1.0, x)))) for x in self.rotThrusters + other.rotThrusters]))
                       )
  
  #these functions are helper functions 
  # for event handling
  def setFireOn(self, a): self.fireOn = a
  
  def setForwardThruster(self, x):  self.thrusters[1] = -x
  def setLeftThruster(self, x):     self.thrusters[0] = x
  def setUpThruster(self, x):       self.thrusters[2] = x      
  
  def setHeadingThruster(self, x): self.rotThrusters[0] = x  #aka Yaw
  def setPitchThruster(self, x):   self.rotThrusters[1] = x
  def setRollThruster(self, x):    self.rotThrusters[2] = x
  
  # call processIntent on player object
  def process(self, world):
    world.players[self.playerNum].processIntent(self, world)
  

def clampVector(v, maxLength):
  if v.length() > maxLength:
    v.normalize()
    return v * maxLength
  else:
    return v
    
def neg(x):
  return -x
    
def compose(f, g):
  def fg(x):
    return f(g(x))
  return fg

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
      
    def time2frames(self, t):
      return int(round(t/self.clock.getDt()))
      
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

        self.cHandler = PhysicsCollisionHandler()

        self.cTrav = CollisionTraverser()
        self.cTrav.setRespectPrevTransform( True )
        #self.cTrav.showCollisions(render)
        
        self.pHandler = CollisionHandlerEvent()
        self.pHandler.addInPattern('%fn-into-%in')
        self.accept('laser-bounds-into-player-player1-bounds', self.handleLaserHitShip)
        self.accept('laser-bounds-into-level', self.handleLaserHitLevel)
        
        self.laserSound = base.loader.loadSfx("media/sound/laser02.wav")
        self.laserHitWall = base.loader.loadSfx("media/sound/explode1.wav")
        self.laserHitPlayer = base.loader.loadSfx("media/sound/shit01.wav")
        
        #TODO this is lame, but just getting ready for the new architecture
        self.joystickIntent = PlayerIntent(0)
        self.keyboardIntent = PlayerIntent(0)
        
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
          
          #TODO add a filter for multiple intent packets for a single player
          def processIntent(player, intent, world):
            if intent.fireOn:
              if world.clock.getFrameCount() >= player.laserCool:
                player.createLaserProjectile()
                player.laserCool = world.clock.getFrameCount() + world.time2frames(0.4)

            lcs = player.actorNodePath.getMat()

            currentVelocity = player.actorNode.getPhysicsObject().getVelocity()
            desiredVelocity = Vec3(lcs.xformVec(intent.thrusters)) * 80.0
            deltaVel = desiredVelocity - currentVelocity
            #TODO, there are a lot of arbitrary number here,
            #  we should group them mostly in one place and label their units
            maxAccel = 10.0
            
            thrust = clampVector(deltaVel * 0.1, maxAccel)
            player.actorNode.getPhysicsObject().addImpulse(thrust)
                        
            h, p, r = intent.rotThrusters * 1.5 * world.clock.getDt() * 100.0 # TODO fix this world.dt
            player.actorNode.getPhysicsObject().addLocalTorque(LRotationf(h, p, r)*0.1)
          
        self.playerShip = Player("player1", Vec3(0,-40,0))
        self.players = [self.playerShip]
       
        
        base.camera.reparentTo( self.playerShip.actorNodePath)
        base.camera.setPos(Vec3(0,20,5))
        #
        base.camera.lookAt(self.playerShip.actorNodePath)

        # Create joystick handler
        self.joy = JoystickHandler()

        def addControlKey(keyName, f):
          self.accept(keyName, f, [True])
          self.accept(keyName + "-up", f, [False])
          
        def addKeyAxis(keyA, keyB, f):
          def magic(a, b, x = [0.0, 0.0]):
            if a != None: x[0] = a
            if b != None: x[1] = b
            f(sum(x))
          self.accept(keyA, magic, [1.0, None])
          self.accept(keyA + "-up", magic, [0.0, None])
          self.accept(keyB, magic, [None, -1.0])
          self.accept(keyB + "-up", magic, [None, 0.0])

        def addHatAxis(hatName, setLeftRight, setUpDown, f = lambda x: x, g = lambda x: x):
          def h((leftRight, upDown)):
            setLeftRight(f(leftRight))
            setUpDown(g(upDown))
          self.accept(hatName, h)

        def addAxis(joyAxisName, f, g = lambda x: x):
          self.accept(joyAxisName, compose(f, g))

          
        self.accept("escape", sys.exit)
        
        addKeyAxis("a", "d", self.keyboardIntent.setLeftThruster)
        addKeyAxis("w", "s", self.keyboardIntent.setUpThruster)
        addKeyAxis("t", "enter", self.keyboardIntent.setForwardThruster)
    
        addKeyAxis("4", "6", self.keyboardIntent.setHeadingThruster)
        addKeyAxis("8", "5", self.keyboardIntent.setPitchThruster)
        addKeyAxis("7", "9", self.keyboardIntent.setRollThruster)
        addControlKey("space", self.keyboardIntent.setFireOn)

        # Hard coded joystick controls (Ron's config)
        #addKeyAxis("joystick0-button7", "joystick0-button6", self.keyboardIntent.setForwardThruster)
        #addKeyAxis("joystick0-button2", "joystick0-button1", self.keyboardIntent.setHeadingThruster)
        #addKeyAxis("joystick0-button3", "joystick0-button0", self.keyboardIntent.setPitchThruster)
        
        addAxis("joystick0-axis0", self.joystickIntent.setHeadingThruster, neg)
        addAxis("joystick0-axis1", self.joystickIntent.setPitchThruster, neg)
        addAxis("joystick0-axis2", self.joystickIntent.setForwardThruster, neg)
        addHatAxis("joystick0-hat0", self.joystickIntent.setLeftThruster, self.joystickIntent.setUpThruster, neg)
        addControlKey("joystick0-button0", self.joystickIntent.setFireOn)
        

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
        self.clock.setMode(self.clock.MNonRealTime)
        self.clock.setFrameRate(60.0)
        base.setFrameRateMeter(True)
        #self.count = 0

    # Accepts arrow keys to move either the player or the menu cursor,
    # Also deals with grid checking and collision detection
    def move(self, task):
      self.processFrame([self.keyboardIntent + self.joystickIntent])
      #self.cTrav.traverse(render)

      return task.cont
      
    def processFrame(self, frameEvents):
      for event in frameEvents:
        event.process(self)
      self.clock.tick()
  
w = World()
run()


