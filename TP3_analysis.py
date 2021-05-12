
from time import sleep
import matplotlib.pyplot as plt
import json
import numpy as np

with open('PID_LED_data.json') as json_file:
    data = json.load(json_file)

time = data['time']

photoresistance = data['photoresistance']



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

moy=5
photo_clean = sliding_avg(photoresistance,moy)
photo_clean[0]=0

#plot result
fig= plt.figure(figsize=(7,5))
plt.xlabel('Temps (s)', fontsize=12)
plt.ylabel('Amplitude', fontsize=12)
plt.ylim([0, 1])
plt.xlim([0,300])
plt.plot(time[:+1-moy],photo_clean, 'b', linewidth=3)
plt.plot([0, data['duration']], [data['Ref'], data['Ref']],'k--',linewidth=3)
plt.plot([0, data['duration']], [data['Ref']+0.025, data['Ref'] + 0.025],'r--',linewidth=2)
plt.plot([0, data['duration']], [data['Ref'] - 0.025,data['Ref'] - 0.025],'r--',linewidth=2)
legend=['Photorésistance','Valeur cible', 'Tolérance']
save_file_name = 'Courbe_PID_analyse_2cm_v9'
plt.legend(legend, fontsize=12)
fig.savefig('PID2.png', dpi=600)
plt.show()

print(np.max(photo_clean)-0.6)



#this function check if a given array as consecutive number
def checkConsecutive(array):
    if len(array) < 10:
        return False
    else:
        # return true if consecutive (derivate of y=x)
        return (sum(np.diff(array))/(len(array) - 1) ==1)

#this function find the index for steady state
def steady_state(index_array):
    if len(index_array) == 0:
        return None
    else:
        i = 0
        _continue = True
        while _continue:
            if checkConsecutive(index_array[i:]):
                _continue = False # steady_state is achieve
                return i
            elif i == len(index_array)-1:
                _continue = False
                return None # no steady state
            else:
                i+=1
eps=0.025
index_t_r = np.where(np.array(photo_clean) >= 0.6)[0]
t_r = time[index_t_r[0]]
index_t_s =  np.where((np.array(photo_clean) < 0.6 + eps) & \
                        (np.array(photo_clean) > 0.6 - eps))[0]
indx = steady_state(index_t_s)

t_s = time[index_t_s[indx]] - t_r

print(t_r)
print(t_s)
