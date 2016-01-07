GROUPBASE = 0x45
PACKETEND = 0x55

UDP_PORT = 8899
UDP_IP = "192.168.11.255"

BASE = 0x41
ALLOFF = BASE
ALLON = BASE + 1
SPEEDSLOWER = BASE + 2
SPEEDFASTER = BASE + 3
WHITE = 0x45
WHITE2 = 0xC5
WHITEALL = 0x42
WHITEALL2 = 0xC2
ALL = 5
import socket
import time
import types

COLORDICT = {
         'violet'        : 0x00,
         'royal_blue'    : 0x10,
         'baby_blue'     : 0x20,
         'aqua'          : 0x30,
         'mint'          : 0x40,
         'seafoam_green' : 0x50,
         'green'         : 0x60,
         'lime_green'    : 0x70,
         'yellow'        : 0x80,
         'yellow_orange' : 0x90,
         'orange'        : 0xA0,
         'red'           : 0xB0,
         'pink'          : 0xC0,
         'fusia'         : 0xD0,
         'lilac'         : 0xE0,
         'lavendar'      : 0xF0
}


#
#  wait for 50ms before consecutive commands
#
class WirelessLights(object):

    def __init__(self, group=1, ):
        self.group = group
        self.packet = []
        self.all = group == ALL
        if self.all:
            self.on = self.onAll
            self.off = self.offAll
            self.white = self.whiteAll
        else:
            self.on = self.ON
            self.off = self.OFF
            self.white = self.WHITE

    def ON(self):
        self.packet.append(GROUPBASE + ((self.group - 1)*2) )
        self.packet.append(0x00)
        self.send()

    def OFF(self):
        self.packet.append(GROUPBASE + ((self.group - 1)*2) + 1)
        self.send()

    def onAll(self):
        self.packet.append(ALLON)
        self.packet.append(0x00)
        self.send()

    def send(self, use2ndByte=False):
        if not use2ndByte:
            self.packet.append(0x00);
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.packet.append(PACKETEND)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(self.packetToString(), (UDP_IP, UDP_PORT))
        sock.sendto(self.packetToString(), (UDP_IP, UDP_PORT))
        sock.sendto(self.packetToString(), (UDP_IP, UDP_PORT))
        sock.sendto(self.packetToString(), (UDP_IP, UDP_PORT))
        sock.sendto(self.packetToString(), (UDP_IP, UDP_PORT))
        sock.sendto(self.packetToString(), (UDP_IP, UDP_PORT))
        sock.close()
        self.packet = []

    def offAll(self):
        self.packet.append(ALLOFF)
        self.send()

    def packetToString(self):
        packetStr = ''
        for x in self.packet:
            packetStr += chr(x)

        return packetStr

    def WHITE(self):
        self.packet.append(WHITE + ((self.group - 1)*2))
        self.send()
        #packet is set []
        self.packet.append(WHITE2 + ((self.group - 1)*2))
        time.sleep(.1)
        self.send()

    def whiteAll(self):
        self.packet.append(WHITEALL)
        self.send()
        #packet is cleared by send
        self.packet.append(WHITEALL2)
        self.send()

    def setColor(self, color):
        self.packet.append(0x40)
        self.packet.append(COLORDICT[color.lower()])
        self.send(use2ndByte=True)

    def setColorInt(self, integer):
        self.packet.append(0x40)
        self.packet.append(integer)
        self.send(use2ndByte=True)

    def setBrightness(self, percent):
        self.packet.append(0x4E)
        self.packet.append( (percent * 0x1B)/100 )
        self.send(use2ndByte=True)

    def getColors(self):
        return list(COLORDICT.keys())


    def setColorHSL(self, hsl):
        # takes list or int of hue
        hue = 0
        if isinstance(hsl, list):
            hue = hsl[0]
        else:
            hue = hsl

        color = int(((-(hue - 240) % 360) / 360.0 * 255.0))
        self.setColorInt(color)
