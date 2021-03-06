from __future__ import with_statement

# {{{ MultitouchSupport
import time
import ctypes
import threading
from ctypes.util import find_library

CFArrayRef = ctypes.c_void_p
CFMutableArrayRef = ctypes.c_void_p
CFIndex = ctypes.c_long

MultitouchSupport = ctypes.CDLL("/System/Library/PrivateFrameworks/MultitouchSupport.framework/MultitouchSupport")

CFArrayGetCount = MultitouchSupport.CFArrayGetCount
CFArrayGetCount.argtypes = [CFArrayRef]
CFArrayGetCount.restype = CFIndex

CFArrayGetValueAtIndex = MultitouchSupport.CFArrayGetValueAtIndex
CFArrayGetValueAtIndex.argtypes = [CFArrayRef, CFIndex]
CFArrayGetValueAtIndex.restype = ctypes.c_void_p

MTDeviceCreateList = MultitouchSupport.MTDeviceCreateList
MTDeviceCreateList.argtypes = []
MTDeviceCreateList.restype = CFMutableArrayRef

class MTPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float),
                ("y", ctypes.c_float)]

class MTVector(ctypes.Structure):
    _fields_ = [("position", MTPoint),
                ("velocity", MTPoint)]

class MTData(ctypes.Structure):
    _fields_ = [
        ("frame", ctypes.c_int),
        ("timestamp", ctypes.c_double),
        ("identifier", ctypes.c_int),
        ("state", ctypes.c_int),  # Current state (of unknown meaning).
        ("unknown1", ctypes.c_int),
        ("unknown2", ctypes.c_int),
        ("normalized", MTVector),  # Normalized position and vector of
        # the touch (0 to 1).
        ("size", ctypes.c_float),  # The area of the touch.
        ("unknown3", ctypes.c_int),
        # The following three define the ellipsoid of a finger.
        ("angle", ctypes.c_float),
        ("major_axis", ctypes.c_float),
        ("minor_axis", ctypes.c_float),
        ("unknown4", MTVector),
        ("unknown5_1", ctypes.c_int),
        ("unknown5_2", ctypes.c_int),
        ("unknown6", ctypes.c_float),
    ]

MTDataRef = ctypes.POINTER(MTData)

MTContactCallbackFunction = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, MTDataRef,
                                             ctypes.c_int, ctypes.c_double, ctypes.c_int)

MTDeviceRef = ctypes.c_void_p

MTRegisterContactFrameCallback = MultitouchSupport.MTRegisterContactFrameCallback
MTRegisterContactFrameCallback.argtypes = [MTDeviceRef, MTContactCallbackFunction]
MTRegisterContactFrameCallback.restype = None

MTDeviceStart = MultitouchSupport.MTDeviceStart
MTDeviceStart.argtypes = [MTDeviceRef, ctypes.c_int]
MTDeviceStart.restype = None

MTDeviceStop = MultitouchSupport.MTDeviceStop
MTDeviceStop.argtypes = [MTDeviceRef]
#MTDeviceStop.restype = None

def _cfarray_to_list(arr):
    rv = []
    n = CFArrayGetCount(arr)
    for i in xrange(n):
        rv.append(CFArrayGetValueAtIndex(arr, i))
        return rv

# }}}

from Queue import Queue

touches_lock = threading.Lock()
touches = []

def init_multitouch(cb):
    devices = _cfarray_to_list(MultitouchSupport.MTDeviceCreateList())
    for device in devices:
        MTRegisterContactFrameCallback(device, cb)
        MTDeviceStart(device, 0)
        return devices

def stop_multitouch(devices):
    for device in devices:
        MTDeviceStop(device)

@MTContactCallbackFunction
def touch_callback(device, data_ptr, n_fingers, timestamp, frame):
    fingers = []
    for i in xrange(n_fingers):
        fingers.append(data_ptr[i])
        touches[:] = [(frame, timestamp, fingers)]
        return 0

import pygame
from pygame import draw, display, mouse
from pygame.locals import *
from numpy import *

pygame.init()

#n_samples = 22050 * 4
#sa = zeros((n_samples, 2))
#sound = sndarray.make_sound(sa)
#sa = sndarray.samples(sound)
#sound.play(-1)

devs = init_multitouch(touch_callback)

flags = FULLSCREEN | HWSURFACE | DOUBLEBUF
mode = max(display.list_modes(0, flags))
display.set_mode(mode, flags)
#display.set_mode((640, 480))
screen = display.get_surface()
width, height = screen.get_size()
txtfont = pygame.font.SysFont(None, 40)

mouse.set_visible(False)

fingers = []

start = None
prevtime = None
df = 0
curpos = (0, 0)
curvel = (0, 0)

from xbmc_client import DummyClient

ws = DummyClient('ws://bh:9090/', protocols=['http-only', 'chat'])
ws.connect()
print 'Connected'

prevspeed = 0
volume = 0
ppsent = False
yvel = None

while True:
    if touches:
        frame, timestamp, fingers = touches.pop()

    #print frame, timestamp
    screen.fill((0xef, 0xef, 0xef))
    draw.line(screen, (0, 0, 0), (620, 0), (620, height), 4)
    draw.line(screen, (0, 0, 0), (540, height/2+20), (540, height/2-20), 4)
    draw.line(screen, (0, 0, 0), (700, height/2+20), (700, height/2-20), 4)
    draw.line(screen, (0, 0, 0), (840, height/2+20), (840, height/2-20), 4)
    draw.line(screen, (0, 0, 0), (400, height/2+20), (400, height/2-20), 4)
    draw.line(screen, (0, 0, 0), (980, height/2+20), (980, height/2-20), 4)
    draw.line(screen, (0, 0, 0), (280, height/2+20), (280, height/2-20), 4)
    draw.line(screen, (0, 0, 0), (600, height/2-100), (640, height/2-100), 4)
    draw.line(screen, (0, 0, 0), (600, height/2-200), (640, height/2-200), 4)
    draw.line(screen, (0, 0, 0), (600, height/2-300), (640, height/2-300), 4)
    draw.line(screen, (0, 0, 0), (600, height/2), (640, height/2), 4)
    draw.line(screen, (0, 0, 0), (600, height/2+100), (640, height/2+100), 4)
    draw.line(screen, (0, 0, 0), (600, height/2+200), (640, height/2+200), 4)
    draw.line(screen, (0, 0, 0), (600, height/2+300), (640, height/2+300), 4)


    event = pygame.event.poll()

    if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        ws.close()
        print 'Exiting'
        break

    prev = None
    for i, finger in enumerate(fingers):
        pos = finger.normalized.position
        vel = finger.normalized.velocity

        x = int(pos.x * width)
        y = int((1 - pos.y) * height)
        p = (x, y)
        r = int(finger.size * 10)

	if i == 0:
	    curpos = p
	    curvel = (vel.x, vel.y)

	if prev:
            draw.line(screen, (0xd0, 0xd0, 0xd0), p, prev[0], 3)
            draw.circle(screen, 0, prev[0], prev[1], 0)
    if prev:
        draw.line(screen, (0xd0, 0xd0, 0xd0), p, prev[0], 3)
        draw.circle(screen, 0, prev[0], prev[1], 0)
        prev = p, r

        draw.circle(screen, 0, p, r, 0)

        vx = vel.x
        vy = -vel.y
        posvx = x + vx / 10 * width
        posvy = y + vy / 10 * height
        draw.line(screen, 0, p, (posvx, posvy))



    # EXIT! One finger still, four motioning quickly downward.
    end = time.time()
    if start: df = end - start

    if len(fingers) == 1:
	if not start: start = time.time()

    elif len(fingers) == 5:
	n_still = 0
        n_down = 0
        for i, finger in enumerate(fingers):
            vel = finger.normalized.velocity
            t = 0.1
            if -t <= vel.x < t and -t <= vel.y < t:
                n_still += 1
            elif -2 <= vel.x < 2 and vel.y < -4:
                n_down += 1
        if n_still == 1 and n_down == 4:
            break
    else:
	start = None
	ppsent = False
	df = 0

    if df > 0 and df <= 0.1875:
	if not ppsent:
	    ws.play_pause()
	    ppsent = True
    elif df > 0.1875:

	if curvel[0] > 0.15 or curvel[0] < -0.15:
	    if curpos[0] <= 280:
		if prevspeed != -16:
		    ws.set_speed(-16)
		    prevspeed = -16
	    elif curpos[0] > 280 and curpos[0] <= 400:
		if prevspeed != -8:
		    ws.set_speed(-8)
		    prevspeed = -8
	    elif curpos[0] > 400 and curpos[0] <= 540:
		if prevspeed != -4:
		    ws.set_speed(-4)
		    prevspeed = -4
	    elif curpos[0] > 540 and curpos[0] <= 700:
		if prevspeed != 1:
		    ws.set_speed(1)
		    prevspeed = 1
	    elif curpos[0] > 700 and curpos[0] <= 840:
		if prevspeed != 4:
		    ws.set_speed(4)
		    prevspeed = 4
	    elif curpos[0] > 840 and curpos[0] <= 980:
		if prevspeed != 8:
		    ws.set_speed(8)
		    prevspeed = 8
	    elif curpos[0] > 980:
		if prevspeed != 16:
		    ws.set_speed(16)
		    prevspeed = 16

	if curpos[1] > 20:
	    if not prevtime: prevtime = time.time()
	    curtime = time.time() - prevtime
	    if curtime > 0.1:
		if volume <=100: volume += 1
		ws.set_volume(volume)
		prevtime = time.time()
        if not start: start = time.time()
        elif len(fingers) == 5:
            n_still = 0
            n_down = 0
            for i, finger in enumerate(fingers):
                vel = finger.normalized.velocity
                t = 0.1
                if -t <= vel.x < t and -t <= vel.y < t:
                    n_still += 1
                elif -2 <= vel.x < 2 and vel.y < -4:
                    n_down += 1
                    if n_still == 1 and n_down == 4:
                        break
                    else:
                        end = time.time()
                        if start: df = end - start
                        start = None

    if df >= 0.1875:
        ws.play_pause()

        label = txtfont.render(str(df), 1, (0, 0, 0))
        screen.blit(label, (100,100))
    else:
        pass


    display.flip()

stop_multitouch(devs)
