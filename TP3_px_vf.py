#*****************************************************************************
#importation des librairies et connections au rasberry pi
#*****************************************************************************
from gpiozero import LightSensor, PWMLED
from signal import pause
from time import sleep
import matplotlib.pyplot as plt
import numpy as np
from scipy import interpolate
import json
sensor = LightSensor(pin=18, queue_len=5)
led = PWMLED(16)
#*****************************************************************************
#*****************************************************************************




#*****************************************************************************
#paramètres utilisateurs
#*****************************************************************************

time = 60 # durée d'enregistrement en secondes
sleep_time = 1 # pas de temps d'enregistrement en seconde

#*************Paramètre pour analyse par défaut************************

Ref = 0.60 # valeur cible pour la luminosité de la LED
#note: ici Ku et Tu ont été déterminé après une première analyse avec
#k_p non nul et ki=kd=0
Ku =0.1
Tu =5

#paramètre fixe pour l'analyse
Kp = 0.6*Ku #valeur par défaut =0
Ki = round(1.2*Ku/Tu, 8) #valeur par défaut =0
Kd = round(3*Ku*Tu/40, 8) #valeur par défaut =0
#*****************************************************************************



#****************Paramètre pour analyser Kp, Ki, Kd, Ref**********************

# Definition des facteurs de P, I et D à itérer
Kp_list = [0.05, 0.1, 0.5]
Ki_list = [round(1.2*Ku/Tu*value, 8) for value in [0.8, 1, 1.2] ]
Kd_list = [round(3*Ku*Tu/40*value, 8 )for value in [0.8, 1,1.2] ]
Ref_list = [0.50, 0.60, 0.70] #valeur cible à itérer


#*************variable bool pour l'activation de chaque analyse.**************

#*******(UN SEUL True)************
evaluate_kp = False #varialbe pour analyser kp
evaluate_ki = False #varialbe pour analyser ki
evaluate_kd = False #varialbe pour analyser kd
evaluate_ref = False #varialbe pour analyser différentes valeurs cibles
evaluate = True # variable pour analyse uniquement avec les params par défaut

#note: Seul cet paramètre sera modifié, les autres paramètres resteront fixes
#*****************************************************************************
#*****************************************************************************




#*****************************************************************************
#*****************************************************************************
# le reste du code peut être exécuté avec "python3 TP3_px_vf.py"
#*****************************************************************************
#*****************************************************************************




#*****************************************************************************
#Fonctions
#*****************************************************************************

#*************#definition de la fonction pour effecteur le PID*****************
def PID_LED(led, sensor, Kp,Ki,Kd, Ref, time, sleep_time, window=9):
    """
    Paramètres
        led : objet PWMLED() de gpiozero
            object permettant de fixer l'intensité de la LED
        sensor : objet LightSensor() de gpiozero
            object permettant de lire l'intensité de la LED
        Kp : float
            terme proportionnel du controleur
        Ki : float
            terme intégral du controleur
        Kd : float terme différentiel
            terme différentiel du controleur
        Ref: float
            valeur cible pour le controleur
        time: float
            temps d'enregistrement
        slee_time : float
            pas de temps pour la lecture de la LED
        window : int
            fenêtre pour moyenner la valeur de la photodiode
    """

    #valeur de la luminosité de la led pour l'itération du param K
    LED_vect = []
    #initialisation de l'erreur avant et de la sortie de la fonction
    error0 = 0
    out = 0
    #itération sur le nombre de pas de temps
    for i in range(int(time/sleep_time)):
        #mesure de la valeur de la photodiode
        #definition d'une fenêtre de moyennage temporelle (minimise le bruit)
        #window = window
        photo = 0
        for j in range(window):
            photo += sensor.value
            sleep(sleep_time/window)
        photo = photo/window #valeur moyenne
        print(photo) #affiche la valeur
        LED_vect.append(photo)

        #calcul de l'erreur
        error = Ref - photo

        #définition du PID
        P = Kp * error
        I = Ki * (error0 + error)*sleep_time
        D = Kd * (error - error0)/sleep_time

        #incrémentation le PID à la valeur de sortie
        out += P+I+D

        #retourne la valeur à imposer pour la LED
        out = max(min(1,out), 0) #limite la sortie entre 0 et 1

        #mise à jour des valeurs
        led.value = out
        error0 = error
    return LED_vect
#*****************************************************************************


#*********Fonction moyenne glissante  pour lisser les données****************
def sliding_avg(led_data, moy_size=3):
    led_moy = []
    for i in range(len(led_data)+1-moy_size):
        moy = 0
        for j in range(moy_size):
            moy = moy + led_data[i+j]
        moy = moy/moy_size
        led_moy.append(moy)

    return led_moy
#*****************************************************************************





#*****************************************************************************
#Main : exécution du PID
#*****************************************************************************

#********************Code pour le controle PID********************************

#liste pour contenir les données pour chaque valeur de paramètre
LEDs_vect = []

#détermine le paramètre à analyser
if not evaluate_ref and not evaluate: # détermine si on analyse Kp,Ki,Kd
    if evaluate_kp:
        K_list = Kp_list
    elif evaluate_ki:
        K_list = Ki_list
    elif evaluate_kd:
        K_list = Kd_list

    for K in K_list:
        if evaluate_kp:
            Kp=K
            print('Kp = '+str(Kp))
        elif evaluate_ki:
            Ki=K
            print('Ki = '+str(Ki))
        elif evaluate_kd:
            Kd=K
            print('Kd = '+str(Kd))

        LED_it = PID_LED(led, sensor, Kp,Ki,Kd, Ref, time, sleep_time, window=9)
        LEDs_vect.append(LED_it)
        led.value = 0
        sleep(3)

elif evaluate_ref: # détermine si on analyse différents ref
    for Ref in Ref_list:
        print('Cible = '+str(Ref))
        #les paramètres par défaut sont pris à l'exception de Ref
        LED_it = PID_LED(led, sensor, Kp,Ki,Kd, Ref, time, sleep_time, window=9)
        LEDs_vect.append(LED_it)
        led.value = 0
        sleep(3)

elif evaluate: #analyse unique
    LED_it = PID_LED(led, sensor, Kp,Ki,Kd, Ref, time, sleep_time, window=9)
    LEDs_vect.append(LED_it)
    led.value = 0
    sleep(3)
#*****************************************************************************


#************************Lissage des résultats*******************************
LEDs_clean = []
for led_data in LEDs_vect:
    led_moy = sliding_avg(led_data)
    LEDs_clean.append(led_moy)
time_clean = np.linspace(0, time, len(LEDs_clean[0]))
#*****************************************************************************
#*****************************************************************************



#*****************************************************************************
# Analyse des paramètres
#*****************************************************************************

#*****************Création d'un dictonnaire pour les param********************

#enregistrement des param par défaut
param = {'Ref':Ref}
param['time'] = time
param['sleep_time'] = sleep_time
param['Ku'] = Ku
param['Tu'] = Tu
param['Kp'] = Kp
param['Ki'] = Ki
param['Kd'] = Kd


#*******enregistrement des données brutes (raw) et traitées (clean)***********
time_raw = np.linspace(0, time, int(time/sleep_time))

if evaluate_kp:
    np.savez('PID_Kp_raw_data',LEDs_vect, time_raw)
    np.savez('PID_Kp_clean_data',LEDs_clean, time_clean)
    param['Kp_list'] = Kp_list
    with open("PID_Kp_param.json", 'w') as file:
            json.dump(param, file)

elif evaluate_ki:
    np.savez('PID_Ki_raw_data',LEDs_vect, time_raw)
    np.savez('PID_Ki_clean_data',LEDs_clean, time_clean)
    param['Ki_list'] = Ki_list
    with open("Ki_param.json", 'w') as file:
            json.dump(param, file)

elif evaluate_kd:
    np.savez('PID_Kd_raw_data', LEDs_vect, time_raw)
    np.savez('PID_Kd_clean_data',LEDs_clean, time_clean)
    param['Kd_list'] = Kd_list
    with open("PID_Kd_param.json", 'w') as file:
            json.dump(param, file)

elif evaluate_ref:
    np.savez('PID_Rf_raw_data',LEDs_vect, time_raw)
    np.savez('PID_Rf_clean_data',LEDs_clean, time_clean)
    param['Ref_list'] = Ref_list
    with open("PID_Ref_param.json", 'w') as file:
            json.dump(param, file)

elif evaluate:
    np.savez('PID_raw_data', LEDs_vect, time_raw)
    np.savez('PID_clean_data',LEDs_clean, time_clean)
    with open("PID_param.json", 'w') as file:
            json.dump(param, file)



#*******************visualistion des données brutes**************************
plt.figure()
plt.xlabel('Temps (s)')
plt.ylabel('Amplitude')
for led_data in LEDs_vect:
    f = interpolate.interp1d(time_raw, led_data, kind='cubic')
    time_new = np.linspace(0,time, 5*len(time_raw))
    plt.plot(time_new, f(time_new))
legend = []

if not evaluate_ref and not evaluate:
    for K in K_list:
        if evaluate_kp:
            legend.append('Kp = '+ str(K))
        elif evaluate_ki:
            legend.append('Ki = '+ str(K))
        elif evaluate_kd:
            legend.append('Kd = '+ str(K))
    plt.plot([0, time], [Ref, Ref],'k--')
    legend.append('Valeur cible')
    plt.legend(legend)

    if evaluate_kp:
        plt.title('Effet la variation de Kp avec '+ 'Ki = '+str(Ki)+' et Kd = '\
                    +str(Kd))
        plt.savefig('figure_kp_raw.eps')
    elif evaluate_ki:
        plt.title('Effet la variation de Ki avec '+ 'Kp = '+str(Kp)+' et Kd = '\
                    +str(Kd) )
        plt.savefig('figure_ki_raw.eps')
    elif evaluate_kd:
        plt.title('Effet la variation de Kd avec '+ 'Kp = '+str(Kp)+' et Ki = '\
                +str(Ki))
        plt.savefig('figure_kd_raw.eps')

elif evaluate_ref:
    for Ref in Ref_list:
        legend.append('Cible = '+ str(Ref))
        plt.plot([0, time], [Ref, Ref],'k--')
    plt.legend(legend)
    plt.title("Efficacité du contrôleur PID avec Kp = "+ str(Kp)+ ', '+'Ki = ' \
                +str(Ki)+' et Kd = ' +str(Kd))
    plt.savefig('figure_ref_raw.eps')

elif evaluate:
    plt.plot([0, time], [Ref, Ref],'k--')
    plt.title("Efficacité du contrôleur PID avec Kp = "+ str(Kp)+ ', '+'Ki = ' \
                +str(Ki)+' et Kd = ' +str(Kd))
    plt.savefig('figure_PID_raw.eps')





#************visualistion des données traitées *******************************
plt.figure()
plt.xlabel('Temps (s)')
plt.ylabel('Amplitude')
for led_data in LEDs_clean:
    f = interpolate.interp1d(time_clean, led_data, kind='cubic')
    time_new = np.linspace(0,time, 5*len(time_clean))
    plt.plot(time_new, f(time_new))
legend = []

if not evaluate_ref and not evaluate:
    for K in K_list:
        if evaluate_kp:
            legend.append('Kp = '+ str(K))
        elif evaluate_ki:
            legend.append('Ki = '+ str(K))
        elif evaluate_kd:
            legend.append('Kd = '+ str(K))

    plt.plot([0, time], [Ref, Ref],'k--')
    legend.append('Valeur cible')
    plt.legend(legend)

    if evaluate_kp:
        plt.title('Effet la variation de Kp avec '+ 'Ki = '+str(Ki)+' et Kd = '\
         +str(Kd) + '\n'+"(utilisation d'une moyenne glissante)")
        plt.savefig('figure_kp_clean.eps')
    elif evaluate_ki:
        plt.title('Effet la variation de Ki avec '+ 'Kp = '+str(Kp)+' et Kd = '\
        +str(Kd) + '\n'+"(utilisation d'une moyenne glissante)")
        plt.savefig('figure_ki_clean.eps')
    elif evaluate_kd:
        plt.title('Effet la variation de Kd avec '+ 'Kp = '+str(Kp)+' et Ki = '\
        +str(Ki)+ '\n'+"(utilisation d'une moyenne glissante)")
        plt.savefig('figure_kd_clean.eps')

elif evaluate_ref:
    for Ref in Ref_list:
        legend.append('Cible = '+ str(Ref))
        plt.plot([0, time], [Ref, Ref],'k--')
    plt.legend(legend)
    plt.title("Efficacité du contrôleur PID avec Kp = " +str(Kp)+ ', ' +'Ki = '\
    +str(Ki)+' et Kd = ' +str(Kd) + '\n'+"(utilisation d'une moyenne glissante)")
    plt.savefig('figure_ref_clean.eps')

elif evaluate:
    plt.plot([0, time], [Ref, Ref],'k--')
    plt.title("Efficacité du contrôleur PID avec Kp = "+ str(Kp)+ ', ' +'Ki = '\
    +str(Ki)+' et Kd = ' +str(Kd)+ '\n'+"(utilisation d'une moyenne glissante)")
    plt.savefig('figure_PID_clean.eps')
