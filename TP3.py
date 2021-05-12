from gpiozero import LightSensor, PWMLED,  MCP3008
from signal import pause
from time import sleep
import matplotlib.pyplot as plt
import numpy as np
sensor = MCP3008(channel=0)
#sensor = LightSensor(pin=18,queue_len=5)
led = PWMLED(16)

# Vector for storing the objective value, photoresistance mesured, and value sent to the diode
# Used for the graph
objec = []
photo = []
diode = []

# Definition de l'objectif initials
SP = 0.5

# Definition des facteurs de P, I et D
Kp = 0.005
Ki = 0.0005
Kd = 0.0001


sum = 0
error = 0
olderror = 0
out = 0
n = 0

try:
    while True:

        n = n + 1

		# Change the objective value at a given iteration
        if n == 2000:
            SP = 0.2

        olderror = error
        sum2 = 0

		# Pour chaque point temporel, effectue un nombre de mesures, puis fait la moyenne


		# Temps correspondant à une valeur du vecteur 'photo'
        sleep_time = 0.4
		# Nombre de mesures la composant
        it = 5
        for i in range(it):
            sum2 = sum2 + sensor.value
            sleep(sleep_time/it)
        PV = sum2/it

        #PV = sensor.value
        error = SP - PV
        sum = sum + error

        # Calcule P, I et D
        P = error
        I = sum
        D = (error - olderror) / 0.05


        # Calcule, borne et met a jour la valeur de sortie
        out = out + (Kp * P) + (Ki * I) + (Kd * D)

        if out < 0:
            out = 0
        if out > 1:
            out = 1

        led.value = out

        # Affiche les valeurs pour debug
        #print("PV: " + str(PV) + " - error: " + str(error) + " - k*P: " + str(Kp * P) + " - out: " + str(out))

		# Ajoute les valeurs au vecteur
        objec = np.append(objec,SP)
        photo = np.append(photo,PV)
        diode = np.append(diode,out)


except KeyboardInterrupt:

	# Fait une moyenne glissante sur les 3 vecteurs
	# /!\ Grosse réplication de code, ne pas montrer à un ingénieur logiciel
    moy_size = 10
    photo_moy = []
    for i in range(len(photo)+1-moy_size):
        moy = 0
        for j in range(moy_size):
            moy = moy + photo[i+j]
        moy = moy/moy_size
        photo_moy = np.append(photo_moy,moy)

    diode_moy = []
    for i in range(len(diode)+1-moy_size):
        moy = 0
        for j in range(moy_size):
            moy = moy + diode[i+j]
        moy = moy/moy_size
        diode_moy = np.append(diode_moy,moy)

    objec_moy = []
    for i in range(len(objec)+1-moy_size):
        moy = 0
        for j in range(moy_size):
            moy = moy + objec[i+j]
        moy = moy/moy_size
        objec_moy = np.append(objec_moy,moy)

	# Trace le graphe
    x=range(0,len(photo_moy))
	# Pour l'objectif et la valeur mesurée
	plt.plot(x, objec_moy, x,photo_moy)
	# Pour l'objectif et la valeur envoyée à la diode
	plt.plot(x, objec_moy, x,diode_moy)
    plt.ylabel('Luminosité mesurée et valeur objectif en fonction du temps')
    plt.savefig('fig.png')

	# Sauvegarde le vecteur des valeur mesurées, pour traitement
    np.save('test.npz',photo)

print("End")
pause()
