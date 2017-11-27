# -*- coding: utf-8 -*-
################################################################################

from modules import cbpi
from modules.core.props import Property
from modules.core.hardware import SensorActive, SensorPassive
import time
import math

################################################################################
@cbpi.sensor
class SimulatedTempSensor(SensorActive):

    a_heat_rate_prop = Property.Number("Heat Rate", configurable=True, default_value=20, description="Units per minute")
    b_heat_actor_prop = Property.Actor("Heater", description="The heating actor this sensor responds to")
    c_cool_rate_prop = Property.Number("Cool Rate", configurable=True, default_value=20, description="Units per minute")
    d_cool_actor_prop = Property.Actor("Cooler", description="The cooling actor this sensor responds to")
    e_drift_rate_prop = Property.Number("Drift Rate", configurable=True, default_value=5, description="Units per minute")
    f_ambient_temp_prop = Property.Number("Ambient Temp", configurable=True, default_value=65, description="Temperature drifted toward")
    g_min_temp_prop = Property.Number("Min Temp", configurable=True, description="Minimum possible temperature, leave blank for freezing")
    h_max_temp_prop = Property.Number("Max Temp", configurable=True, description="Maximum possible temperature, leave blank for boiling")
    i_update_freq_prop = Property.Number("Update Frequency", configurable=True, default_value=5, description="Seconds between value updates")

    #-------------------------------------------------------------------------------
    def init(self):
        try: self.freq = float(self.i_update_freq_prop)
        except: self.freq = 5.0

        try:
            self.heat_rate = float(self.a_heat_rate_prop)/60.0 * self.freq
            self.heat_actorID = int(self.b_heat_actor_prop)
        except:
            self.heat_rate = 0.0
            self.heat_actorID = None
        try:
            self.cool_rate = float(self.c_cool_rate_prop)/60.0 * self.freq
            self.cool_actorID = int(self.d_cool_actor_prop)
        except:
            self.cool_rate = 0.0
            self.cool_actorID = None
        try:
            self.drift_rate = float(self.e_drift_rate_prop)/60.0 * self.freq
            self.ambient_temp = float(self.f_ambient_temp_prop)
        except:
            self.drift_rate = 0.0
            self.ambient_temp = 0.0

        try: self.min_temp = float(self.g_min_temp_prop)
        except: self.min_temp = 0.0 if self.get_config_parameter('unit', 'C') == 'C' else 32.0
        try: self.max_temp = float(self.h_max_temp_prop)
        except: self.max_temp = 100.0 if self.get_config_parameter('unit', 'C') == 'C' else 212.0

        self.last_temp = self.ambient_temp

        SensorActive.init(self)

    #-------------------------------------------------------------------------------
    def execute(self):
        # at startup, wait for actors to initialze
        while cbpi.cache.get("actors") is None:
            self.sleep(5)

        while self.is_running():
            heater = self.api.cache.get("actors").get(self.heat_actorID, None)
            cooler = self.api.cache.get("actors").get(self.cool_actorID, None)

            if heater and int(heater.state):
                temp = self.last_temp + self.heat_rate * (float(heater.power)/100.0)
            elif cooler and int(cooler.state):
                temp = self.last_temp - self.cool_rate * (float(cooler.power)/100.0)
            else:
                diff = self.ambient_temp - self.last_temp
                if abs(diff) <= self.drift_rate:
                    temp = self.ambient_temp
                else:
                    temp = self.last_temp + math.copysign(self.drift_rate, diff)

            temp = max(temp, self.min_temp)
            temp = min(temp, self.max_temp)

            self.data_received("{:.2f}".format(temp))
            self.last_temp = temp

            self.sleep(self.freq)

################################################################################
@cbpi.sensor
class SineWaveSensor(SensorActive):

    min_prop = Property.Number("Minimum", configurable=True, default_value=0, description="Minimum sensor value")
    max_prop = Property.Number("Maximum", configurable=True, default_value=100, description="Maximum sensor value")
    period_prop = Property.Number("Period", configurable=True, default_value=600, description="Time in seconds of a full period")
    freq_prop = Property.Number("Frequency", configurable=True, default_value=5, description="Time in seconds between readings")

    #-------------------------------------------------------------------------------
    def init(self):

        self.min = float(self.min_prop)
        self.max = float(self.max_prop)
        self.period = int(self.period_prop)
        self.freq = int(self.freq_prop)

        self.amplitude = (self.max-self.min)/2.0
        self.mid = self.min + self.amplitude
        self.start_time = time.time()

        SensorActive.init(self)

    #-------------------------------------------------------------------------------
    def execute(self):
        while self.is_running():
            whole, part = divmod(time.time()-self.start_time, self.period)
            radians = part/self.period * math.pi * 2.0
            temp = self.amplitude * math.sin(radians) + self.mid
            self.data_received("{:.2f}".format(temp))
            self.sleep(self.freq)
