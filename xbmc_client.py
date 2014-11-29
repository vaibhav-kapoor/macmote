#! /usr/bin/env python

from ws4py.client.threadedclient import WebSocketClient

import pygame
import json

class DummyClient(WebSocketClient):
    def opened(self):
        def data_provider():
            for i in range(1, 200, 25):
                yield "#" * i

        self.send(data_provider())

        for i in range(0, 200, 25):
            print i
            self.send("*" * i)

    def closed(self, code, reason=None):
        print "Closed down", code, reason

    def received_message(self, m):
        print m
        if len(m) == 175:
            self.close(reason='Bye bye')

    def play_pause(self):
	command = {"jsonrpc": "2.0", "method": "Player.PlayPause",
		    "params": { "playerid": 1 }, "id": 1}
	ws.send(json.dumps(command))

    def set_speed(self, speed):
	command = {"jsonrpc": "2.0", "method": "Player.SetSpeed",
		"params": { "playerid": 1, "speed": speed }, "id": 1}
	ws.send(json.dumps(command))

    def set_volume(self, volume):
	command = {"jsonrpc": "2.0", "method": "Player.SetVolume",
		    "params": { "playerid": 1, "volume": volume }, "id": 1}
	ws.send(json.dumps(command))

    def input_right(self):
	command = {"jsonrpc": "2.0", "method": "Input.Right",
		    "params": {}, "id": 1}
	ws.send(json.dumps(command))

    def input_left(self):
	command = {"jsonrpc": "2.0", "method": "Input.Left",
		    "params": {}, "id": 1}
	ws.send(json.dumps(command))

    def input_select(self):
	command = {"jsonrpc": "2.0", "method": "Input.Left",
		    "params": {}, "id": 1}
	ws.send(json.dumps(command))


if __name__ == '__main__':
    try:
	pygame.init()
	screen = pygame.display.set_mode((640, 480))
	clock = pygame.time.Clock()

        ws = DummyClient('ws://bh:9090/', protocols=['http-only', 'chat'])
        ws.connect()
        #ws.run_forever()
	print 'Started Websocket client'
	command = {"jsonrpc": "2.0", "method": "Input.Left", "id": 1}

	while True:
	    for event in pygame.event.get():
		if event.type == pygame.QUIT:
		    ws.close()
		    break

		if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
		    print 'command pressed'
		    ws.set_speed(-4)

	    screen.fill((0,0,0))
	    pygame.display.flip()
	    clock.tick(60)

    except KeyboardInterrupt:
        ws.close()
