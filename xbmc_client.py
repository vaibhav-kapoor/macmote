#! /usr/bin/env python

import threading
from ws4py.client.threadedclient import WebSocketClient

import pygame
import ujson as json

class DummyClient(WebSocketClient):

    def __init__(self, url, protocols=None):
        """docstring for __init__"""
        WebSocketClient.__init__(self, url, protocols)

        self.appstatus = 'navigation'
        self._th = threading.Thread(target=self.run,
                                    name='DummyClient')
        self._th.daemon = True

    def opened(self):
        def data_provider():
            for i in range(1, 200, 25):
                yield "#" * i

        self.send(data_provider())

        for i in range(0, 200, 25):
            self.send("*" * i)

    def closed(self, code, reason=None):
        print "Closed down", code, reason

    def received_message(self, m):
	try:

	    print m

	    if len(m.data) > 0:
		payload = json.loads(m.data)
		method = payload['method']
		if method == 'Player.OnStop':
		    self.appstatus = 'navigation'
		elif method == 'Player.OnPlay':
		    self.appstatus = 'player'

	    if len(m) == 175:
		self.close(reason='Bye bye')
	except:
	    return

    def play_pause(self):
        command = {"jsonrpc": "2.0", "method": "Player.PlayPause",
                   "params": {"playerid": 1}}
        self.send(json.dumps(command))

    def set_speed(self, speed):
        command = {"jsonrpc": "2.0", "method": "Player.SetSpeed",
                   "params": {"playerid": 1, "speed": speed}}
        self.send(json.dumps(command))

    def set_volume(self, volume):
        command = {"jsonrpc": "2.0", "method": "Application.SetVolume",
                   "params": {"volume": volume}}
        self.send(json.dumps(command))

    def input_right(self):
        command = {"jsonrpc": "2.0", "method": "Input.Right",
                   "params": {}}
        self.send(json.dumps(command))

    def input_left(self):
        command = {"jsonrpc": "2.0", "method": "Input.Left",
                   "params": {}}
        self.send(json.dumps(command))

    def input_up(self):
        command = {"jsonrpc": "2.0", "method": "Input.Up",
                   "params": {}}
        self.send(json.dumps(command))

    def input_down(self):
        command = {"jsonrpc": "2.0", "method": "Input.Down",
                   "params": {}}
        self.send(json.dumps(command))

    def input_select(self):
        command = {"jsonrpc": "2.0", "method": "Input.Select",
                   "params": {}}
        self.send(json.dumps(command))

if __name__ == '__main__':
    try:
        pygame.init()
        screen = pygame.display.set_mode((640, 480))
        clock = pygame.time.Clock()
        ws = DummyClient('ws://bh:9090/', protocols=['http-only', 'chat'])
        ws.connect()
        print 'Started Websocket client'
        command = {"jsonrpc": "2.0", "method": "Input.Left"}

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    ws.close()
                    break
                else: pass

                if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                    print 'command pressed'
                    ws.play_pause()
                else: pass

            screen.fill((0,0,0))
            pygame.display.flip()
            clock.tick(60)

    except KeyboardInterrupt:
        ws.close()

