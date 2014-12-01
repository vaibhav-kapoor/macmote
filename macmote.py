from __future__ import with_statement
# {{{ MultitouchSupport
import time
import sys
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
        ("state", ctypes.c_int), # Current state (of unknown meaning).
        ("unknown1", ctypes.c_int),
        ("unknown2", ctypes.c_int),
        ("normalized", MTVector), # Normalized position and vector of
        # the touch (0 to 1).
        ("size", ctypes.c_float), # The area of the touch.
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
curpos = (0, 0)
curvel = (0, 0)
df = 0
prevspeed = 0

prevtime = None
navtime = None
trialstart = None
trialtime = 0

volume = 0
from xbmc_client import DummyClient
ws = DummyClient('ws://bh:9090/', protocols=['http-only', 'chat'])
ws.connect()
print 'Connected'

def speed_coord(curpos):
    speed = 0
    if curpos[0] <= 280 and curpos[0] > 0:
	speed = -16
	draw.rect(screen, (65,105,225), (0, 0, 280, height), 0)
    elif curpos[0] > 280 and curpos[0] <= 400:
	speed = -8
	draw.rect(screen, (100,149,237), (280, 0, 120, height), 0)
    elif curpos[0] > 400 and curpos[0] <= 540:
	speed = -4
	draw.rect(screen, (30,144,255), (400, 0, 140, height), 0)
    elif curpos[0] > 540 and curpos[0] <= 700:
	speed = 1
	draw.rect(screen, (0,0,0), (540, 320, 160, 130), 1)
    elif curpos[0] > 700 and curpos[0] <= 840:
	speed = 4
	draw.rect(screen, (255,127,80), (700, 0, 160, height), 0)
    elif curpos[0] > 840 and curpos[0] <= 980:
	speed = 8
	draw.rect(screen, (255,99,71), (840, 0, 140, height), 0)
    elif curpos[0] > 980:
	speed = 16
	draw.rect(screen, (255,69,0), (980, 0, width-980, height), 0)

    return speed

def draw_lines():

    draw.line(screen, (0, 0, 0), (620, 360), (620, 410), 2)
    draw.line(screen, (0, 0, 0), (595, 385), (645, 385), 2)
    #draw.rect(screen, (0,0,0), (540, 320, 160, 130), 1)
    #draw.line(screen, (0, 0, 0), (595, 400), (645, 400), 1)
    #draw.line(screen, (0, 0, 0), (540, height/2+50), (540, height/2-80), 1)
    #draw.line(screen, (0, 0, 0), (699, height/2+50), (699, height/2-80), 1)
    #draw.line(screen, (0, 0, 0), (839, height/2+50), (839, height/2-80), 1)
    #draw.line(screen, (0, 0, 0), (400, height/2+50), (400, height/2-80), 1)
    #draw.line(screen, (0, 0, 0), (980, height/2+50), (980, height/2-80), 1)
    #draw.line(screen, (0, 0, 0), (280, height/2+50), (280, height/2-80), 1)
    #draw.line(screen, (0, 0, 0), (600, height/2-100), (640, height/2-100), 2)
    #draw.line(screen, (0, 0, 0), (600, height/2-200), (640, height/2-200), 2)
    #draw.line(screen, (0, 0, 0), (600, height/2-300), (640, height/2-300), 2)
    #draw.line(screen, (0, 0, 0), (600, height/2), (640, height/2), 2)
    #draw.line(screen, (0, 0, 0), (600, height/2+100), (640, height/2+100), 2)
    #draw.line(screen, (0, 0, 0), (600, height/2+200), (640, height/2+200), 2)
    #draw.line(screen, (0, 0, 0), (600, height/2+300), (640, height/2+300), 2)

def draw_rectangles():
    pass
    #draw.rect(screen, (0,0,0), (540, 320, 160, 130), 1)

    #FW/RW
    #draw.rect(screen, (255,127,80), (700, 0, 160, height), 0)
    #draw.rect(screen, (255,99,71), (840, 0, 140, height), 0)
    #draw.rect(screen, (255,69,0), (980, 0, width-980, height), 0)


    #draw.rect(screen, (30,144,255), (400, 0, 140, height), 0)
    #draw.rect(screen, (100,149,237), (280, 0, 120, height), 0)
    #draw.rect(screen, (65,105,225), (0, 0, 280, height), 0)

    # Volume rectangles
    #draw.rect(screen, (255,127,80), (400, 190, 440, 130), 0)
    #draw.rect(screen, (135,206,235), (400, 450, 440, 130), 0)

import ujson
from collections import defaultdict

def save_trial(filename, group, user, inputdevice, trial_time):
    try:
	with open(filename, 'r') as infile:
	    jsonp = ujson.load(infile)
    except (ValueError, IOError):
	    jsonp = {}

    jsonp[group] = jsonp.get(group, {user:{"input": {inputdevice: {"times":[]}}}})
    jsonp[group][user] = jsonp[group].get(user, { "input": { inputdevice: {"times":[]}}})
    jsonp[group][user]['input'][inputdevice] = jsonp[group][user]['input'].get(inputdevice, {
	"times": [] })

    jsonp[group][user]['input'][inputdevice]['times'].append(trial_time)

    with open(filename, 'w') as outfile:
	ujson.dump(jsonp, outfile)

    return

while True:
    if touches:
        frame, timestamp, fingers = touches.pop()

    #print frame, timestamp
    screen.fill((0xef, 0xef, 0xef))

    draw_lines()
    draw_rectangles()

    event = pygame.event.poll()

    if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE) or ws.appstatus == 'ended':

	trialtime = time.time() - trialstart
	print sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
	save_trial(sys.argv[1], sys.argv[2], sys.argv[3] , sys.argv[4], trialtime)
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
        #print "finger", i, "at", (x, y)
        #xofs = int(finger.minor_axis / 2)
        #yofs = int(finger.major_axis / 2)

        if prev:
            draw.line(screen, (0xd0, 0xd0, 0xd0), p, prev[0], 3)
            draw.circle(screen, 0, prev[0], prev[1], 0)
        prev = p, r

        draw.circle(screen, 0, p, r, 0)
        #draw.ellipse(screen, 0, (x - xofs, y - yofs, xofs * 2, yofs * 2))

        #sa[int(pos.x * n_samples)] = int(-32768 + pos.y * 65536)

        vx = vel.x
        vy = -vel.y
        posvx = x + vx / 10 * width
        posvy = y + vy / 10 * height
        draw.line(screen, 0, p, (posvx, posvy))

    # EXIT! One finger still, four motioning quickly downward.
    if len(fingers) == 1:
	if not start: start = time.time()
	if not trialstart: trialstart = time.time()
	for i, finger in enumerate(fingers):
	    vel = finger.normalized.velocity
	    pos = finger.normalized.position
	    x = int(pos.x * width)
	    y = int((1 - pos.y) * height)
	    p = (x, y)
	    r = int(finger.size * 10)

	    if i == 0:
		curvel = (vel.x, vel.y)
		curpos = (x, y)

    elif len(fingers) == 5:
        n_still = 0
        n_down = 0
        for i, finger in enumerate(fingers):
            vel = finger.normalized.velocity
            #print i, "%.2f, %.2f" % (vel.x, vel.y)
            t = 0.1
            if -t <= vel.x < t and -t <= vel.y < t:
                n_still += 1
            elif -2 <= vel.x < 2 and vel.y < -4:
                n_down += 1
        if n_still == 1 and n_down == 4:
            break
    else:
	if start: df = time.time() - start
	start = None
	curpos = (0, 0)


    if df > 0 and df <= 0.1875:
	if ws.appstatus == 'player':
	    ws.play_pause()
	elif ws.appstatus == 'navigation':
	    ws.input_select()
	df = 0

    else:
	if ws.appstatus == 'player':
	    speed = speed_coord(curpos)
	    if abs(curvel[0]) > 0.15:
		if prevspeed != speed:
		    ws.set_speed(speed)
		    prevspeed = speed
	    else:
		#label = txtfont.render(str(volume), 1, (0, 0, 0))
		#screen.blit(label, (100,100))
		if curpos[1] < 320 and curpos[1] > 0:
		    if not prevtime: prevtime = time.time()
		    draw.rect(screen, (255,127,80), (400, 190, 440, 130), 0)
		    curtime = time.time() - prevtime
		    if curtime > 0.1:
			if volume <=100: volume += 2
			ws.set_volume(volume)
			prevtime = time.time()
		elif curpos[1] > 450:
		    draw.rect(screen, (135,206,235), (400, 450, 440, 130), 0)
		    if not prevtime: prevtime = time.time()
		    curtime = time.time() - prevtime
		    if curtime > 0.1:
			if volume >=0: volume -= 2
			ws.set_volume(volume)
			prevtime = time.time()
	else:
	    if not navtime: navtime = time.time()
	    catime = time.time() - navtime
	    if curpos[0] > 740 and curpos[1] >= 220 and curpos[1] < 520:
		if not navtime: navtime = time.time()
		catime = time.time() - navtime
		if catime > 0.375:
		    ws.input_right()
		    navtime = time.time()
	    elif curpos[0] < 520 and curpos[1] >= 220 and curpos[1] < 520:
		if catime > 0.375:
		    ws.input_left()
		    navtime = time.time()
	    elif curpos[1] < 220 and curpos[1] > 0:
		if catime > 0.375:
		    ws.input_up()
		    navtime = time.time()
	    elif curpos[1] > 520:
		if catime > 0.375:
		    ws.input_down()
		    navtime = time.time()

	label = txtfont.render(str(curpos), 1, (0, 0, 0))
	screen.blit(label, (100,100))

    display.flip()

stop_multitouch(devs)



