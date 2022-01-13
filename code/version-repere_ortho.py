# libraries circuitpython, moins de modules car capteurs en mode tout ou rien (officiel)
import board
import pwmio
from digitalio import DigitalInOut
from time import sleep

# liste pour faciliter l'accès aux capteurs de réflectance (broche 8 à 1 sur Polulu)
s = [DigitalInOut(board.GP12), DigitalInOut(board.GP13), DigitalInOut(board.GP14), DigitalInOut(board.GP15), DigitalInOut(board.GP16), DigitalInOut(board.GP17), DigitalInOut(board.GP18), DigitalInOut(board.GP19)]

# liste des sorties pour piloter les moteurs (câblage inversé)
m = [pwmio.PWMOut(board.GP11), pwmio.PWMOut(board.GP21), pwmio.PWMOut(board.GP10), pwmio.PWMOut(board.GP20)]

# 4 déphasages possibles (modulo)
ph = {"ALIG" : 0, "TRIG" : 90, "OPPO" : 180, "ANTI" : 270}

# dictionnaire avec les 4 mouvements possibles (absolu)
mv = {'F' : 1, 'L' : 2, 'R' : 3, 'B' : 4}

# initialisation phase et repère (choix arbitraire et absolu)
phase = X = Y = 0

# initialisation position de départ et coefficient des incréments (choix arbitraire et relatif)
x0, y0, dx, dy = 8, 3, 0, 1

# calcul déphasage entre les 2 systèmes (robot, labyrinthe)
def quadrant(phase):
    global x0, y0, dx, dy, X, Y, ph

    # table de vérité (relatif)
    if(phase == ph["ALIG"]):
        x0 += X
        y0 += Y
        dx = 0
        dy = 1
    elif(phase == ph["TRIG"]):
        x0 += Y
        y0 += X
        dx = -1
        dy = 0
    elif(phase == ph["OPPO"]):
        x0 -= X
        y0 -= Y
        dx = -1
        dy = 0
    elif(phase == ph["ANTI"]):
        x0 -= Y
        y0 -= X
        dx = 1
        dy = 0

    return phase

# profils de vitesse par défaut (constant)
CRUISE = 32768
BRAKES = 0

# liste 2D stockant l'itinéraire du robot
path = [["00" for col in range(0, 8)] for row in range(0, 8)]

def switchINTERS():
    turnLeft = not(s[0].value and s[1].value and s[2].value)
    middLeft, middRigh = not(s[3].value), not(s[4].value)
    turnRigh = not(s[5].value and s[6].value and s[7].value)

    global phase, X, Y

    # tour à gauche prioritaire sur la droite (choix arbitraire)
    if(turnLeft):
        print("debug : Turning left...")

        if(phase == ph["ANTI"]):
            phase = ph["ALIG"]
        else :
            phase += ph["TRIG"]
        side = mv['L']
    elif(turnRigh):
        print("debug : Turning right...")

        if(phase > ph["ALIG"]):
            phase -= ph["TRIG"]
        else :
            phase = ph["ANTI"]
        side = mv['R']

    # maintien en ligne droite nerveux (choix volontaire)
    elif(middLeft):
        if(middRigh):
            print("debug : Going forward...")

            X, Y = -1, 0
            side = mv['F']
        else:
            side = mv['L']
    elif(middRigh):
        side = mv['R']

    # marche arrière, utile lors d'une rotation mais saccadé et bloquant en impasse
    else:
        X, Y = 1, 0
        side = mv['B']

    # recalcul de la phase et mise à jour du trajet avant réitération
    phase = quadrant(phase)
    path[x0][y0] = "b1"
    path[x0+dx][y0+dy] = "b2"

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

# exécution du code limité pour ne pas surcharger la liste, interruption possible au clavier (code de test)
for i in range(10):
    try:
        switchMOTOR(switchINTERS())
        sleep(1)

    except KeyboardInterrupt:
        pass

# impression de l'itinéraire en terminal
for v in range(0, 8):
    print(path[v])
