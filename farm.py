from PIL.ImageOps import grayscale
import pyautogui as gui
import pydirectinput as di
import sys
import time
import mss
import mss.tools
from PIL import Image
import numpy as np
import gc
import random
from itertools import cycle
import math

windowTitle = "New World"
generalConfidence = .7

# todo - move everything in state and import/export state as json
state = {
  "moving": False,
  "maxDistanceToGatherable": 500
}

animationSleepTime = .1 + (.1 * random.random())
afkMoveDirection = ["a", "d"]
afkMovesCount = 15
startMoveDirection = "d"

moveDirections = {
  "forward": "w",
  "backward": "s",
  "left": "a",
  "right": "d",
}

resourceList = [
  "boulder",
  "flint",
  "bush",
  "youngTree",
  "deadTree",
  "matureTree",
  "hemp",
  "lostPresent",
  "iron",
  "corn",
  "cranberries",
  "nuts",
  "wolf",
  "water",
  "bulrush",
  "briar",
  "herbs",
  "turkey",
]

commonGatherDelay = 2
gatherDelay = {
  "boulder": 1,
  "flint": .2,
  "bush": .5,
  "lostPresent": 1.2,
  "youngTree": commonGatherDelay,
  "deadTree": commonGatherDelay,
  "matureTree": commonGatherDelay,
  "hemp": commonGatherDelay,
  "iron": commonGatherDelay,
  "corn": commonGatherDelay,
  "cranberries": commonGatherDelay,
  "nuts": commonGatherDelay,
  "wolf": commonGatherDelay,
  "turkey": commonGatherDelay,
  "bulrush": commonGatherDelay,
  "briar": commonGatherDelay,
  "herbs": 1,
  "water": 2.5,
}

def debug(screen, area):
  areaSS = screen.grab(area)
  mss.tools.to_png(areaSS.rgb, areaSS.size, output="area-{top}x{left}_{width}x{height}.png".format(**area))
  return areaSS


def detectKilledAndRespawn():
  if gui.locateOnScreen("imgs/respawnPoints.png", grayscale=True, confidence=generalConfidence) is not None:
    print("You Died! Rip")
    respawnPoint = gui.locateOnScreen("imgs/nearestSettlement.png", grayscale=True, confidence=generalConfidence)
    respawnButton = gui.locateOnScreen("imgs/respawnButton.png", grayscale=True, confidence=generalConfidence)
    print(f"Respawn Point {respawnPoint}")
    [respawnPointX, respawnPointY] = gui.center(respawnPoint)
    di.click(respawnPointX, respawnPointY)
    time.sleep(1)
    print(f"RespawnButton {respawnButton}")
    [respawnButtonX, respawnButtonY] = gui.center(respawnButton)
    di.click(respawnButtonX, respawnButtonY)


def detectAfkAndRejoin():
  if gui.locateOnScreen("imgs/afkKick.png", grayscale=True, confidence=generalConfidence) is not None:
    afkKickOkButton = gui.locateOnScreen("imgs/afkKickOk.png", grayscale=True, confidence=generalConfidence)
    print(f"AfkKickOkButton {afkKickOkButton}")
    [afkOkX, afkOkY] = gui.center(afkKickOkButton)
    di.click(afkOkX, afkOkY)
    time.sleep(15)
    joinServer()

def joinServer():
  if (mainMenuContinueButton := gui.locateOnScreen("imgs/mainMenuContinue.png", grayscale=True, confidence=generalConfidence)) is not None:
    print(f"Main menu > Continue button {mainMenuContinueButton}")
    [continueBtnX, continueBtnY] = gui.center(mainMenuContinueButton)
    di.click(continueBtnX, continueBtnY)
    time.sleep(1.5)
    if (mainMenuPlayButton := gui.locateOnScreen("imgs/mainMenuPlay.png", grayscale=True, confidence=generalConfidence)) is not None:
      print(f"Main menu > Play button {mainMenuPlayButton}")
      [playBtnX, playBtnY] = gui.center(mainMenuPlayButton)
      di.click(playBtnX, playBtnY)
      time.sleep(20)


def detectResource(gameArea, confidence): 
  for resource in resourceList:
    if gui.locate(f"imgs/{resource}.png", gameArea, grayscale=True, confidence=confidence) is not None:
      return resource

def getMoves(count, start="d"):
  dCount = count*2
  startDirectionIndex = afkMoveDirection.index(start)
  mirrorDirectionIndex = 1 - startDirectionIndex
  list = [afkMoveDirection[startDirectionIndex] if x < count else afkMoveDirection[mirrorDirectionIndex] for x in range(dCount)]
  return list

def stepBack(moving):
  if moving:
    with gui.hold(moveDirections["backward"]):
      time.sleep(.8)

def isItemOnTheLeft(screenCenter, itemCenter):
  [sX, sY] = screenCenter
  [iX, iY] = itemCenter
  #screen coords inverted?
  return sX > iX

def isItemBack(screenCenter, itemCenter):
  [sX, sY] = screenCenter
  [iX, iY] = itemCenter
  return sY < iY

def distance(screenCenter, itemCenter):
  [sX, sY] = screenCenter
  [iX, iY] = itemCenter
  return math.sqrt((math.pow((sX - iX),2) + math.pow((sY - iY), 2)))

def getMoveDelay(distanceInPixels):
  y = distanceInPixels
  k = 0.52 
  x = (y / k)
  print(f"y = {y}, k={k} x={x}")
  return x / 1000

def move(direction, distance):
  delay = getMoveDelay(distance)
  print(f"{direction} =>  {delay}")
  with gui.hold(direction):
    time.sleep(0.8)

  #gui.keyDown(direction, _pause=False)
  #time.sleep(1)
  #gui.keyUp(direction)

def randomMove(delay=0):
  if random.randint(1, 10) == 2:
    time.sleep(delay)
    afkKey = afkMoveDirection[random.randint(0, 1)]
    print(f"Random Move {afkKey}")
    gui.keyDown(afkKey)
    time.sleep(.2)
    gui.keyUp(afkKey)

def detectGatherableMoveCloserOrRandom(gameArea, screenCenter):
  if (gatherableIcon := gui.locate("imgs/gatherableClose.png", gameArea, grayscale=True, confidence=generalConfidence)) is not None:
    print(f"Gatherable icon : {gatherableIcon}")
    [gatherX, gatherY] = gui.center(gatherableIcon)
    print(f"GatherableIconCenter: {gatherX}x{gatherY}")
    [screenCenterX, screenCenterY] = screenCenter
    print(f"ScreenCenter: {screenCenterX}x{screenCenterY}") 

    dist = round(distance(screenCenter, [gatherX, gatherY]))
    print(f"Distance between center & gatherableIcon's center = {dist}")
    if dist > state["maxDistanceToGatherable"]:
      print(f"Distance {dist} is over maxDistanceAllowed {state['maxDistanceToGatherable']}")
      #randomMove()
      return
    #if isItemBack(screenCenter, [gatherX, gatherY]):
    #  print("Moving Back")
    #  # just reset if autowalking
    #  if state["moving"]:
    #    gui.keyUp(moveDirections["forward"])
    #    state["moving"] = False
    #  move(moveDirections["backward"], distance=dist)
    #else:
    #  print("Moving Front")
    #  if state["moving"] is not True:
    #    state["moving"] = True
    #  move(moveDirections["forward"], distance=dist)

    isLeftSide = isItemOnTheLeft(screenCenter, [gatherX, gatherY])
    print(f"GatherableIcon => isLeftSide? {isLeftSide}")
    if isLeftSide:
      print("Moving left")
      move(moveDirections["left"], distance=dist)
    else:
      print("Moving right")
      move(moveDirections["right"], distance=dist)
  else:
    print("No gatherable icon detected")
    #randomMove()

def main():
  gameWindow = gui.getWindowsWithTitle(windowTitle)
  if len(gameWindow) == 0:
    print(f"Please start {windowTitle}")
    sys.exit(-1)
  print(gameWindow) 
  for window in gameWindow:
    if window.title == windowTitle:
      game = window
      break
  
  game.activate()
  centerX = game.left + (game.width/2)
  centerY = game.top + (game.height/2)

  print(f"center of the window {centerX}x{centerY}")
  screen = mss.mss()

  gatherArea = {
    "mon": 1,
    "top": game.top,
    "left": game.left,
    "width": game.width,
    "height": game.height,
  }
  # move(moveDirections["forward"])
  # sys.exit(0)
  #gatherArea = {
  #  "mon": 1,
  #  "top": round(0.15 * game.height),
  #  "left": game.left + round(0.15 * game.width),
  #  "width": round(0.75 * game.width),
  #  "height": round(0.75 * game.height)
  #}
  #gatherWaterArea = {
  #  "mon": 1,
  #  "top": round(0.25 * game.height),
  #  "left": game.left + round(0.2 * game.width),
  #  "width": round(0.5 * game.width),
  #  "height": round(0.6 * game.height)
  #}
  print(gatherArea)
  debug(screen, gatherArea)

  afkMoves = getMoves(afkMovesCount, startMoveDirection)
  infAfkMoves = cycle(afkMoves)

  #while (key := next(infAfkMoves, None)) is not None:
  while True: 
    #joinServer()
    #detectAfkAndRejoin()
    #detectKilledAndRespawn()

    gameArea = Image.fromarray(np.array(screen.grab(gatherArea)))
    if (resource := detectResource(gameArea, generalConfidence)) is not None:
      stepBack(state["moving"])
      if state["moving"]:
        gui.keyUp(moveDirections["forward"])
        state["moving"] = False
      print(f"Detected {resource}")
      gui.press("e")
      gc.collect()
      time.sleep(gatherDelay[resource])
    randomMove(.7)
    #else:
    #  gameArea = Image.fromarray(np.array(screen.grab(gatherArea)))
    #  print("nothing to gather, move on...")
    #  if not state["moving"]: 
    #    gui.keyDown(moveDirections["forward"])
    #    state["moving"] = True
    #  detectGatherableMoveCloserOrRandom(gameArea, [centerX, centerY])
    #  gameArea = Image.fromarray(np.array(screen.grab(gatherArea)))


if __name__ == '__main__':
  main()