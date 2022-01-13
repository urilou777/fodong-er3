# libraries circuitpython (officiel)
import board
import pwmio
import busio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from digitalio import DigitalInOut, Direction

# configuration de la communication SPI et du slave select
bus_spi = busio.SPI(clock=board.GP2, MISO=board.GP4, MOSI=board.GP3)
broche_cs = DigitalInOut(board.GP5)

# création de l'objet convertissant les 8 entrées analogiques
mcp = MCP.MCP3008(bus_spi, broche_cs)
L1, L2, L3, L4 = AnalogIn(mcp, MCP.P0), AnalogIn(mcp, MCP.P1), AnalogIn(mcp, MCP.P2), AnalogIn(mcp, MCP.P3)
R1, R2, R3, R4 = AnalogIn(mcp, MCP.P4), AnalogIn(mcp, MCP.P5), AnalogIn(mcp, MCP.P6), AnalogIn(mcp, MCP.P7)

# ensemble des LED de réflectance ON par défaut (mode économe non implémenté)
mcpEN = DigitalInOut(board.GP28)
mcpEN.direction = Direction.OUTPUT
mcpEN.value = True

# liste pour faciliter l'accès aux capteurs de réflectance (broche 8 à 1 sur Polulu)
s = [L1, L2, L3, L4, R1, R2, R3, R4]

# liste des sorties pour piloter les moteurs (câblage inversé)
m = [pwmio.PWMOut(board.GP11), pwmio.PWMOut(board.GP21), pwmio.PWMOut(board.GP10), pwmio.PWMOut(board.GP20)]

# dictionnaire avec les 4 mouvements possibles (absolu)
mv = {'F' : 1, 'L' : 2, 'R' : 3, 'B' : 4}

# profils de vitesse par défaut (constant)
CRUISE = 32768
BRAKES = 0

# seuil de tension minimum pour considérer une ligne (0-5V)
THRESHOLD = 1

# détection des intersections et "asservissement" en ligne droite
def switchINTERS():
    # redondance des 2/3 capteurs imposé pour confirmer une détection
    turnLeft = (s[0].voltage > THRESHOLD and s[1].voltage > THRESHOLD and s[2].voltage > THRESHOLD)
    middLeft, middRigh = s[3].voltage > THRESHOLD, s[4].voltage > THRESHOLD
    turnRigh = (s[5].voltage > THRESHOLD and s[6].voltage > THRESHOLD and s[7].voltage > THRESHOLD)

    # tour à gauche prioritaire sur la droite (choix arbitraire)
    if(turnLeft):
        side = mv['L']
    elif(turnRigh):
        side = mv['R']

    # maintien en ligne droite nerveux (choix volontaire)
    elif(middLeft):
        if(middRigh):
            side = mv['F']
        else:
            side = mv['L']
    elif(middRigh):
        side = mv['R']

    # marche arrière, utile lors d'une rotation mais saccadé et bloquant en impasse
    else:
        side = mv['B']

    return side

# pilotage des 2 moteurs pour une direction voulue avec table de vérité
def switchMOTOR(side):
    # rotation inversée des 2 côtés pour aller plus vite
    if(side == mv['R']):
        m[0].duty_cycle = m[3].duty_cycle = CRUISE
        m[1].duty_cycle = m[2].duty_cycle = BRAKES

    # rotation conjointe des 2 côtés pour aller plus vite
    elif(side == mv['F']):
        m[0].duty_cycle = m[1].duty_cycle = CRUISE
        m[2].duty_cycle = m[3].duty_cycle = BRAKES

    # rotation inversée des 2 côtés pour aller plus vite
    elif(side == mv['L']):
        m[1].duty_cycle = m[2].duty_cycle = CRUISE
        m[0].duty_cycle = m[3].duty_cycle = BRAKES

    # rotation conjointe des 2 côtés pour aller plus vite
    elif(side == mv['B']):
        m[2].duty_cycle = m[3].duty_cycle = CRUISE
        m[0].duty_cycle = m[1].duty_cycle = BRAKES

    # arrêt de toutes les rotations
    else :
        m[0].duty_cycle = m[1].duty_cycle = m[2].duty_cycle = m[3].duty_cycle = BRAKES

# exécution en permanence du code, interruption possible au clavier
while True :
    try:
        switchMOTOR(switchINTERS())

    except KeyboardInterrupt:
        pass
