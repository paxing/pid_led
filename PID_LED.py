"""
@author: Paul Xing
date : october 2020
Polytechnique Montreal
"""

from time import sleep
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy import interpolate
import json



class PID_LED():
    def __init__(self, led, sensor, Ref, Kp, Ki = 0, Kd = 0, Ku = None, Tu = None):
        """
        Parameters
        ----------------------
        led : PWMLED() object from gpiozero
            controls the led intensity
        sensor :  MCP3008 object from gpiozero
            gives the mesured light intensity
        Kp : float
            proportionnal term of the controler
        Ki : float
            intgral term of the controler
        Kd : float
            differential term of the controler
        Ku: float
            Ziegler-Nichols term.
        Tu: float
            Ziegler-Nichols term.
        """
        #parameters
        self.led = led
        self.sensor = sensor
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.Ref = Ref
        self.Ku = Ku
        self.Tu = Tu

        #for PID loop
        self.background = 0
        self.max=1
        self.previous_error = 0
        self.sum_error = 0
        self.present_out = 0
        self.photoresistance = list()
        self.out = list()
        self.time = list()

        #for analysis
        self.photoresistance_raw = None
        self.out_raw = None
        self.time_raw = None
        self.duration = None
        self.delta_t = None
        self.dy_max = None
        self.t_r = None
        self.t_s = None
        self.eps = None



    def apply(self, duration=120, delta_t=1, bin_size = 5, zn_tuning = False, live = True):
        """
        This function excute the PID loop.

        Parameters
        ----------------------
            Ref: float
                target value of the controler
            duration: float
                recording duration
            delta_t : float
                time between recordings
            bin_size : int
                number of samples to average for each delta_t
                use for real time ploting
            zn_tuning: bool
                using the Ziegler-Nichols tunning
            live: bool
                for real time ploting
        """


        def calibrate():
            """
            this function measure the light background and maximum for 5s
            """
            self.led.value = 0
            sleep(0.5)
            background = 0
            for i in range(10):
                background += self.sensor.value
                sleep(0.5)
            self.background = background/10 #mean value


            self.led.value = 1
            sleep(0.5)
            max = 0
            for i in range(10):
                max += self.sensor.value
                sleep(0.5)
            self.max = max/10 #mean value

            self.led.value =0
            sleep(0.5)



        def execute_PID(i):
            """
            this code execute the PID control for iteration i
            """
            self.time.append(i*self.delta_t)
            photoresistance = 0
            for j in range(bin_size):
                photoresistance += self.sensor.value
                sleep(self.delta_t/bin_size)
            photoresistance = photoresistance/bin_size #mean value
            photoresistance =(photoresistance - self.background)/(self.max-self.background)
            #print(photoresistance)
            self.photoresistance.append(photoresistance)
            present_error = self.Ref - photoresistance
            self.sum_error += present_error

            # PID control algorithm
            P = self.Kp * present_error
            I = self.Ki * self.sum_error*self.delta_t
            D = self.Kd * (present_error - self.previous_error)/self.delta_t

            #increment the output value of the LED
            self.present_out += P+I+D
            #limit the value between 0 and 1
            self.present_out = max(min(1, self.present_out ), 0)
            self.out.append(self.present_out)
            #update value
            self.led.value = self.present_out
            self.previous_error = present_error



        """
        main loop calculation of the PID
        """
        self.duration = duration
        self.delta_t = delta_t
        calibrate()
        #activate Ziegler-Nichols tunning only if parameters are defined
        if zn_tuning and self.Ku is not None and self.Tu is not None:
            self.Kp = 0.6*self.Ku
            self.Ki = 1.2*self.Ku/self.Tu
            self.Kd = 3*self.Ku*self.Tu/40

        #initiate axis for live plotting of data
        # if live:
        #     fig = plt.figure()
        #     ax = fig.add_subplot(1, 1, 1)
        #
        #     def animate_PID(i):
        #         execute_PID(i)
        #         ax.scatter(self.time, self.photoresistance, c='r', s=5)
        #         ax.plot([0, self.duration], [self.Ref, self.Ref], 'k--')
        #         plt.axis([0, self.duration, 0, 1])
        #         plt.title("PID controler with Kp = " + str(self.Kp) \
        #             + ', ' + 'Ki = ' + str(self.Ki) + ' and Kd = ' + str(self.Kd))
        #         plt.xlabel('Time (s)')
        #         plt.ylabel('Amplitude')
        #         plt.legend(['Target value'])
        #         if i == int(self.duration/self.delta_t)+1:
        #             print('end')
        #
        #             plt.close() #clear graph after
        #
        #
        #     ani = animation.FuncAnimation(fig, animate_PID,\
        #         frames = int(self.duration/self.delta_t)+2, interval=10,repeat = False)
        #     plt.show()

        if live:
            plt.axis([0, self.duration, 0, 1])
            plt.plot([0, self.duration], [self.Ref, self.Ref], 'k--')
            plt.legend(['Target value'])
            for i in range(int(duration/delta_t)+1):
                execute_PID(i)
                plt.scatter(i*self.delta_t, self.photoresistance[i], c='r', s=5)
                plt.xlabel('Time (s)')
                plt.ylabel('Amplitude')
                plt.title("PID controler with Kp = " + str(self.Kp) \
                    + ', ' + 'Ki = ' + str(self.Ki) + ' and Kd = ' + str(self.Kd))
                plt.pause(0.1)
                if i == int(duration/delta_t):
                    print('end')
            plt.show(block=False)
            plt.clf() #clear graph after

        else:
            for i in range(int(duration/delta_t)+1):
                execute_PID(i)

        #deep copy to preserve raw data
        self.photoresistance_raw = self.photoresistance.copy()
        self.out_raw = self.out.copy()
        self.time_raw = self.time.copy()




    def interpolate(self, factor=5, kind = 'cubic'):
        """
        this function interpolate the data and update self.photoresistance,
        self.out and self.time

        Parameters
        ------------------------------
        factor : int or float
            interpolation factor
        kind : string
            interpolation kind
        """

        f_photoresistance = interpolate.interp1d(self.time, self.photoresistance, kind='cubic')
        f_out = interpolate.interp1d(self.time, self.out, kind='cubic')
        time_interp = np.linspace(0, self.duration, int(factor*len(self.time)))

        self.photoresistance = f_photoresistance(time_interp).tolist()
        self.out = f_out(time_interp).tolist()
        self.time = time_interp.tolist()



    def noise_reduction(self, avg_size=3):
        """
        This function reduce the noise with a sliding averaging

        parameters
        --------------------
        avg_size : int
            numbers of index for sliding average
        """

        def sliding(data_raw, avg_size):
            data = (avg_size-1)*[0]+ data_raw #zero padding
            data_nr = []
            for i in range(len(data)+1-avg_size):
                avg = 0
                for j in range(avg_size):
                    avg = avg + data[i+j]
                avg = avg/avg_size
                data_nr.append(avg)
            return data_nr

        self.photoresistance = sliding(self.photoresistance, avg_size)
        self.out = sliding(self.out, avg_size)
        #self.time = np.linspace(0, self.duration, len(self.out)).tolist()



    def plot(self, data_set = 'photoresistance', **kwargs):
        """
        this function plot the data with matplotlib.plt

        Parameters
        -------------------
        data_set : str
            select which dataset to plot
        factor: int or float
            interpolation factor
        """

        if data_set == 'photoresistance':
            plt.plot(self.time, self.photoresistance, label ='Photorésistance', **kwargs)
        elif data_set == 'out':
            plt.plot(self.time, self.out, label ='LED', **kwargs)
        elif data_set == 'ref':
            plt.plot([0, self.duration], [self.Ref, self.Ref],'k--', label = 'Valeur cible', **kwargs)
            plt.plot([0, self.duration], [self.Ref + self.eps, self.Ref + self.eps],\
                    'r--', label = '_nolegend_', **kwargs)
            plt.plot([0, self.duration], [self.Ref - self.eps, self.Ref -  self.eps],\
                    'r--', label = 'Tolérance $\pm$'+ str(self.eps*100) + '$\%$', **kwargs)

    def scatter(self, data_set = 'photoresistance', **kwargs):
        """
        this function plot the scatter of data with matplotlib.plt

        Parameters
        -------------------
        data_set : str
            select which dataset to plot
        factor: int or float
            interpolation factor
        """

        if data_set == 'photoresistance':
            plt.scatter(self.time, self.photoresistance, **kwargs)
        elif data_set == 'out':
            plt.scatter(self.time, self.out, **kwargs)

    def analysis(self, eps=0.025, min_time = 10):
        """
        This function execute the analysis for dy_max, t_r and t_s

        Parameters
        --------------------
        eps : float
            tolerance for analysis calculation

        min_time : minimal time for consideration of steady state

        """


        def checkConsecutive(array):
            """
            this function check if a given array as consecutive number
            """
            if len(array) < int(min_time/self.delta_t):
                return False
            else:
                # return true if consecutive (derivate of y=x)
                return (sum(np.diff(array))/(len(array) - 1) ==1)


        def steady_state(index_array):
            """
            this function find the index for steady state
            """
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

        """
        main analysis
        """

        self.eps = eps
        time_samples = np.array(self.time)
        data_samples = np.array(self.photoresistance)

        #calculate Overshooting
        dy_max = np.max(data_samples) - self.Ref

        #calculate rise time
        index_t_r = np.where(data_samples >= self.Ref)[0]
        if len(index_t_r) ==0:
            t_r = None
        else:
            t_r = time_samples[index_t_r[0]]

        #calculate steady state time
        index_t_s =  np.where((data_samples < self.Ref + eps) & \
                                (data_samples > self.Ref - eps))[0]

        if len(index_t_s) == 0 or t_r == None:
            t_s = None
        else:
            idx = steady_state(index_t_s)
            if idx is None:
                t_s = None
            else:
                t_s = time_samples[index_t_s[idx]] - t_r
                if t_s < 0:
                    t_s = None

        self.dy_max = dy_max
        self.t_r = t_r
        self.t_s = t_s

        print("Overshooting is: " + str(dy_max))
        print("Rise time is : " + str(t_r) + " seconds.")
        print("Stabilization time is : " + str(t_s) + " seconds.")



    def reset_all(self):
        """
        This function reset the PID values to back __init__
        """
        self.background = 0
        self.max = 1
        self.previous_error = 0
        self.sum_error = 0
        self.present_out = 0
        self.photoresistance = list()
        self.out = list()
        self.time = list()
        self.photoresistance_raw = None
        self.out_raw = None
        self.time_raw = None
        self.duration = None
        self.delta_t = None
        self.dy_max = None
        self.t_r = None
        self.t_s = None
        self.eps = None



    def reset_analysis(self):
        """
        This function reset the analysis values
        """
        self.photoresistance = self.photoresistance_raw.copy()
        self.out = self.out_raw.copy()
        self.time = self.time_raw.copy()
        self.dy_max = None
        self.t_r = None
        self.t_s = None
        self.eps = None



    def save(self, filename):
        """
        This function save all the data to json file as a dict

        Parameters
        filename : str
            json filname in which to dump the dict
        """

        data = {'Ref':self.Ref}
        data['duration'] = self.duration
        data['delta_t'] = self.delta_t
        data['Ku'] = self.Ku
        data['Tu'] = self.Tu
        data['Kp'] = self.Kp
        data['Ki'] = self.Ki
        data['Kd'] = self.Kd
        data['background'] = self.background
        data['max'] = self.max
        data['photoresistance'] = self.photoresistance
        data['out'] = self.out
        data['time'] = self.time
        data['photoresistance_raw'] = self.photoresistance_raw
        data['out_raw'] = self.out_raw
        data['time_raw'] = self.time_raw
        data['dy_max'] = self.dy_max
        data['t_r'] = self.t_r
        data['t_s']= self.t_s
        data['eps']= self.eps

        with open(filename + ".json", 'w') as file:
                json.dump(data, file)
