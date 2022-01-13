# circuitpython libraries (official)
import board
import pwmio
import busio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from digitalio import DigitalInOut, Direction
from time import sleep

# bus_spi and chip select
bus_spi = busio.SPI(clock=board.GP2, MISO=board.GP4, MOSI=board.GP3)
broche_cs = DigitalInOut(board.GP5)

mcp = MCP.MCP3008(bus_spi, broche_cs)
L1, L2, L3, L4 = AnalogIn(mcp, MCP.P0), AnalogIn(mcp, MCP.P1), AnalogIn(mcp, MCP.P2), AnalogIn(mcp, MCP.P3)
R1, R2, R3, R4 = AnalogIn(mcp, MCP.P4), AnalogIn(mcp, MCP.P5), AnalogIn(mcp, MCP.P6), AnalogIn(mcp, MCP.P7)

mcpEN = DigitalInOut(board.GP28)
mcpEN.direction = Direction.OUTPUT
mcpEN.value = True

# light sensors array (pin 8 to 1 on Polulu)
s = [L1, L2, L3, L4, R1, R2, R3, R4]

# motors output array (inversed)
m = [pwmio.PWMOut(board.GP11), pwmio.PWMOut(board.GP21), pwmio.PWMOut(board.GP10), pwmio.PWMOut(board.GP20)]

# ph = {"ALIG" : 0, "TRIG" : 90, "OPPO" : 180, "ANTI" : 270}

# default speed settings (constant)
CRUISE, BRAKES = 32768, 0

state = 0

gauche, droite = 0, 0

def lineTracking(midL, midR):

    global state

    if(midL > 1 and midR > 1):
        switchMOTOR("FORWARD")

    elif(midL > 1):
        switchMOTOR("LEFT")

    elif(midR > 1):
        switchMOTOR("RIGHT")

    else:
        switchMOTOR("STOP")

def intersection():

    a, b, c = s[0].voltage, s[1].voltage, s[2].voltage

    d, e, f = s[5].voltage, s[6].voltage, s[7].voltage

    return (a > 1 and b > 1 and c > 1), (d > 1 and e > 1 and f > 1)

def switchMOTOR(side):

    if(side == "RIGHT"):
        m[0].duty_cycle = m[3].duty_cycle = CRUISE
        m[1].duty_cycle = m[2].duty_cycle = BRAKES

    elif(side == "FORWARD"):
        m[0].duty_cycle = m[1].duty_cycle = CRUISE
        m[2].duty_cycle = m[3].duty_cycle = BRAKES

    elif(side == "LEFT"):
        m[1].duty_cycle = m[2].duty_cycle = CRUISE
        m[0].duty_cycle = m[3].duty_cycle = BRAKES

    elif(side == "BACKWARD"):
        m[2].duty_cycle = m[3].duty_cycle = CRUISE
        m[0].duty_cycle = m[1].duty_cycle = BRAKES

    elif(side == "STOP"):
        m[0].duty_cycle = m[1].duty_cycle = m[2].duty_cycle = m[3].duty_cycle = BRAKES

while(True):
    if(state == 0):
        lineTracking(s[3].voltage, s[4].voltage)
        gauche, droite = intersection()

        sum = gauche + droite
        if(sum):
            bis = sum
            while(bis == sum):
                gauche0, droite0 = intersection()
                bis = gauche0 + droite0
                switchMOTOR("STOP")

                if(s[3].voltage > 1 and s[4].voltage > 1):
                    switchMOTOR("STOP")
                    state = 1

        elif(droite):
            switchMOTOR("STOP")
            state = 2

    elif(state == 1):
        switchMOTOR("LEFT")

        do = True
        while(do):
            do = not(s[3].voltage > 1 and s[4].voltage > 1)

        switchMOTOR("STOP")
        state = 0

    elif(state == 2):

        switchMOTOR("RIGHT")

        do = True
        while(do):
            do = not(s[3].voltage > 1 and s[4].voltage > 1)

        switchMOTOR("STOP")
        state = 0

    elif(state == 3):
        switchMOTOR("LEFT")
        sleep(2.5)
        switchMOTOR("BACKWARD")
        sleep(1.5)
        switchMOTOR("LEFT")
        do = True
        while(do):
            do = not(s[3].voltage > 1 and s[4].voltage > 1)

        switchMOTOR("STOP")
        state = 0
