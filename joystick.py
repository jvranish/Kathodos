#-----------------------------------------------------
# Filename:     joystick.py
#
# Author:       Ron Klose
#
# Description:  JoystickHandler object uses pygame to
#               enumerates game devices connected to
#               the system and poll for events from
#               the joystick.  Any events caught will
#               send a custom event to the panda3D
#               event handler.
#-----------------------------------------------------
import pygame
from pygame.locals import *

class JoystickHandler:
  '''
  A handler for game devices.  Initializes pygame,
  enumerates the game devices, and adds pollInputDevice
  to the task manager.
  '''
  def __init__(self):
    # Initializes all imported pygame modules.
    # Calls pygame.joystick.init()
    pygame.init()

    self.joy = []

    # Enumerate all game devices recognized
    self.enumerateDevices()

    taskMgr.add(self.pollInputDevice, 'JoystickTask')
    
  def enumerateDevices(self):
    '''
    Creates and initializes a Joystick object for each game
    connected to the system.

    Inputs:
      None
    Outputs:
      None
    '''
    # Enumerate joysticks
    for device in range(pygame.joystick.get_count()):
      joystick = pygame.joystick.Joystick(device)
      joystick.init()
        
      self.joy.append(joystick)

  def getDevices(self):
    '''
    Returns a list of the enumerated devices

    Inputs:
      None
    Outputs:
      self.joy - List of Joystick objects
    '''
    return self.joy

  def getDeviceName(self, joystick_id):
    '''
    Returns the device name for a given
    joystick ID

    Inputs:
      joystick_id - The ID of the joystick to get
                    the name of
    Outputs:
      deviceName  - The name of the device based
                    on the given ID
    '''
    deviceName = self.joy[joystick_id].get_name()
    
    return deviceName

  def pollInputDevice(self, task):
    '''
    Polls for pygame joystick events and sends
    custom signals to panda3D for events to be handled.

    Inputs:
      task
    Outputs:
      task.cont
    '''
    for event in pygame.event.get():
      if event.type is JOYBUTTONDOWN:
        name = 'joystick%d-button%d' % (event.joy, event.button)
        messenger.send(name)
      elif event.type is JOYBUTTONUP:
        name = 'joystick%d-button%d-up' % (event.joy, event.button)
        messenger.send(name)
      elif event.type is JOYHATMOTION:
        name = 'joystick%d-hat%d' % (event.joy, event.hat)
        messenger.send(name, [event.value])
      elif event.type is JOYAXISMOTION:
        name = 'joystick%d-axis%d' % (event.joy, event.axis)
        messenger.send(name, [event.value])
      elif event.type is JOYBALLMOTION:
        name = 'joystick%d-ball%d' % (event.joy, event.hat)
        messenger.send(name, [event.rel])

      # Left in for debug purposes until a menu is implemented
      # to map the buttons to actions
      #print name

    return task.cont
