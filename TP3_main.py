"""
@author: Paul Xing
date : october 2020
Polytechnique Montreal
"""
#*****************************************************************************
#importation of python librairies and connections to rasberry pi
#*****************************************************************************
from gpiozero import PWMLED, MCP3008
from time import sleep
import matplotlib.pyplot as plt
import json
from PID_LED import PID_LED
#sensor = LightSensor(pin=18, queue_len=5)
sensor = MCP3008(channel=0, clock_pin=11, mosi_pin=10, miso_pin=9, select_pin=8)
led = PWMLED(16)
#*****************************************************************************


#*****************************************************************************
#User parameters
#*****************************************************************************
duration = 300 # recording duration in seconds
delta_t = 1 #time between each recording

#*************Parameters for default analysis*********************************
Ref = 0.5 # target value for LED luminosity
Ku =0.02
Tu = 4
Kp = 0.6*Ku #default =0
Ki = 0.8*round(1.2*Ku/Tu, 6) #default =0
Kd = 1.2*round(3*Ku*Tu/40, 6) #default=0
#*****************************************************************************

#************************Analysis of Kp, Ki, Kd, Ref**************************
Kp_list = [0.05, 0.1]
Ki_list = [round(1.2*Ku/Tu*value, 8) for value in [0.8, 1, 1.2] ]
Kd_list = [round(3*Ku*Tu/40*value, 8) for value in [0.8, 1,1.2] ]
Ref_list = [0.40, 0.60, 0.70, 0.80]

#*******************bool variable for analysis activation*********************
#*******(Only ONE True)************
evaluate_kp = False
evaluate_ki = False
evaluate_kd = False
evaluate_ref = False
evaluate = True
#*****************************************************************************
#*****************************************************************************



#create object list
if evaluate_kp:
    LED_list = [PID_LED(led, sensor, Ref, Kp_list[i])\
                    for i in range(len(Kp_list)) ]
    filenames = ["PID_LED_data_Kp_"+ str(Kp_list[i]).replace('.','_')\
                    for i in range(len(Kp_list))]
elif evaluate_ki:
    LED_list = [PID_LED(led, sensor, Ref, Kp, Ki_list[i], Kd)\
                    for i in range(len(Ki_list)) ]
    filenames = ["PID_LED_data_Ki_"+ str(Ki_list[i]).replace('.','_')\
                    for i in range(len(Ki_list))]
elif evaluate_kd:
    LED_list = [PID_LED(led, sensor, Ref, Kp, Ki, Kd_list[i])\
                    for i in range(len(Kd_list)) ]
    filenames = ["PID_LED_data_Kd_"+ str(Kd_list[i]).replace('.','_')\
                    for i in range(len(Kd_list))]
elif evaluate_ref:
    LED_list = [PID_LED(led, sensor, Ref_list[i], Kp, Ki, Kd)\
                    for i in range(len(Ref_list)) ]
    filenames = ["PID_LED_data_Ref_"+ str(Ref_list[i]).replace('.','_')\
                    for i in range(len(Ref_list))]
elif evaluate:
    LED_list = [PID_LED(led, sensor, Ref, Kp, Ki, Kd)]
    filenames = ["PID_LED_data"]


for i in range(len(LED_list)):
    led.value = 0 #reset LED to off
    print("Évaluation du paramètre numéro " + str(i+1))
    LED_list[i].apply(duration, delta_t) #run the PID
    LED_list[i].noise_reduction()
    LED_list[i].interpolate()
    LED_list[i].analysis()
    LED_list[i].save(filenames[i]) # save data
    sleep(1)

#plot result
fig = plt.figure()
plt.xlim([0, LED_list[0].duration])
plt.ylim([0, 1])
plt.xlabel('Temps (s)')
plt.ylabel('Amplitude')
#use the plot_photoresistance from PID_LED class
for i in range(len(LED_list)):
    LED_list[i].plot(linewidth = 2)
if evaluate_kp:
    plt.title('Effet la variation de Kp avec ' + 'Ki = ' + str(LED_list[0].Ki) \
                + ' et Kd = '+ str(LED_list[0].Kd))
    legend = (['Kp = '+ str(val) for val in Kp_list])
    plt.plot([0, LED_list[0].duration], [LED_list[0].Ref, LED_list[0].Ref],'k--')
    legend.append('Valeur cible')
    save_file_name = 'Courbe_PID_analyse_kp'
elif evaluate_ki:
    plt.title('Effet la variation de Ki avec ' + 'Kp = ' + str(LED_list[0].Kp) \
                + ' et Kd = ' + str(LED_list[0].Kd) )
    legend = (['Ki = '+ str(val) for val in Ki_list])
    plt.plot([0, LED_list[0].duration], [LED_list[0].Ref, LED_list[0].Ref],'k--')
    legend.append('Valeur cible')
    save_file_name = 'Courbe_PID_analyse_ki'
elif evaluate_kd:
    plt.title('Effet la variation de Kd avec ' + 'Kp = ' + str(LED_list[0].Kp) \
                + ' et Ki = ' + str(LED_list[0].Ki))
    legend = (['Kd = '+ str(val) for val in Kd_list])
    plt.plot([0, LED_list[0].duration], [LED_list[0].Ref, LED_list[0].Ref],'k--')
    legend.append('Valeur cible')
    save_file_name = 'Courbe_PID_analyse_kd'
elif evaluate_ref:
    plt.title("Efficacité du contrôleur PID avec Kp = " + str(LED_list[0].Kp) \
                + ', ' + 'Ki = ' + str(LED_list[0].Ki)+' et Kd = ' + \
                str(LED_list[0].Kd))
    legend = (['Valeur cible = '+ str(val) for val in Ref_list])
    for Ref in Ref_list:
        plt.plot([0, duration], [Ref, Ref],'k--')
    save_file_name = 'Courbe_PID_analyse_ref'
elif evaluate:
    #plt.title("Efficacité du contrôleur PID avec Kp = " + str(LED_list[0].Kp) \
    #            + ', ' + 'Ki = ' + str(LED_list[0].Ki) + ' et Kd = ' + \
    #            str(LED_list[0].Kd))
    plt.plot([0, LED_list[0].duration], [LED_list[0].Ref, LED_list[0].Ref],'k--')
    plt.plot([0, LED_list[0].duration], [LED_list[0].Ref + LED_list[0].eps, \
                    LED_list[0].Ref + LED_list[0].eps],'r--')
    plt.plot([0, LED_list[0].duration], [LED_list[0].Ref - LED_list[0].eps,\
                    LED_list[0].Ref -  LED_list[0].eps],'r--')
    legend=['Photorésistance','Valeur cible', 'Tolérance']
    save_file_name = 'Courbe_PID_analyse_2cm_final'
plt.legend(legend)

fig.savefig(save_file_name +".eps", bbox_inches = 'tight')
fig.savefig(save_file_name +".png", bbox_inches = 'tight', dpi = 600)
