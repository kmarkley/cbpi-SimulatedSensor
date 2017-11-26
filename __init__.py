# -*- coding: utf-8 -*-
################################################################################

from modules import cbpi
from modules.core.props import Property
from modules.core.hardware import SensorActive
import time
import math

################################################################################
@cbpi.sensor
class SimulatedSensor(SensorActive):

    a_heat_rate_prop = Property.Number("Heat Rate", configurable=True, default_value=10, description="Units per minute")
    b_heat_actor_prop = Property.Actor("Heater", description="The heating actor this sensor responds to")
    c_cool_rate_prop = Property.Number("Cool Rate", configurable=True, default_value=10, description="Units per minute")
    d_cool_actor_prop = Property.Actor("Heater", description="The cooling actor this sensor responds to")
    e_drift_rate_prop = Property.Number("Drift Rate", configurable=True, default_value=2, description="Units per minute")
    f_ambient_temp_prop = Property.Number("Ambient Temp", configurable=True, default_value=65, description="Temperature drifted toward")
    g_update_freq_prop = Property.Number("Frequency", configurable=True, default_value=5, description="Time in seconds between readings")

    #-------------------------------------------------------------------------------
    def init(self):
        super(SimulatedSensor, self).init()

        try:
            self.freq = float(self.g_update_freq_prop)
        except:
            self.freq = 5.0
        try:
            self.heat_rate = float(self.a_heat_rate_prop)/60.0 * self.freq
            self.heat_act = int(self.b_heat_actor_prop)
        except:
            self.heat_rate = 0.0
            self.heat_act = None
        try:
            self.cool_rate = float(self.c_cool_rate_prop)/60.0 * self.freq
            self.cool_act = int(self.d_cool_actor_prop)
        except:
            self.cool_rate = 0.0
            self.cool_act = None
        try:
            self.drift_rate = float(self.e_drift_rate_prop)/60.0 * self.freq
            self.ambient_temp = float(self.f_ambient_temp_prop)
        except:
            self.drift_rate = 0.0
            self.ambient_temp = 0.0

        self.last_temp = self.ambient_temp

    #-------------------------------------------------------------------------------
    def stop(self):
        super(SimulatedSensor, self).stop()

    #-------------------------------------------------------------------------------
    def execute(self):
        while self.is_running():
            heat_on = cool_on = False
            if self.heat_act is not None:
                heat_on = cbpi.cache.get("actors")[self.heat_act].state
            if self.cool_act is not None:
                cool_on = cbpi.cache.get("actors")[self.cool_act].state

            if heat_on:
                temp = self.last_temp + self.heat_rate
            elif cool_on:
                temp = self.last_temp - self.cool_rate
            else:
                diff = self.ambient_temp - self.last_temp
                if abs(diff) <= self.drift_rate:
                    temp = self.ambient_temp
                else:
                    temp = self.last_temp + math.copysign(self.drift_rate, diff)

            self.data_received(round(temp, 2))
            self.last_temp = temp
            self.sleep(self.freq)

    #-------------------------------------------------------------------------------
    def get_unit(self):
        return "°C" if self.get_config_parameter("unit", "C") == "C" else "°F"

################################################################################
@cbpi.sensor
class SineWaveSensor(SensorActive):

    min_prop = Property.Number("Minimum", configurable=True, default_value=0, description="Minimum sensor value")
    max_prop = Property.Number("Maximum", configurable=True, default_value=100, description="Maximum sensor value")
    period_prop = Property.Number("Period", configurable=True, default_value=600, description="Time in seconds of a full period")
    freq_prop = Property.Number("Frequency", configurable=True, default_value=5, description="Time in seconds between readings")

    #-------------------------------------------------------------------------------
    def init(self):
        super(SineDummySensor, self).init()

        self.min = float(self.min_prop)
        self.max = float(self.max_prop)
        self.period = int(self.period_prop)
        self.freq = int(self.freq_prop)

        self.amplitude = (self.max-self.min)/2.0
        self.mid = self.min + self.amplitude
        self.start_time = time.time()

    #-------------------------------------------------------------------------------
    def stop(self):
        super(SineDummySensor, self).stop()

    #-------------------------------------------------------------------------------
    def execute(self):
        while self.is_running():
            whole, part = divmod(time.time()-self.start_time, self.period)
            radians = part/self.period * math.pi * 2.0
            temp = self.amplitude * math.sin(radians) + self.mid
            self.data_received(round(temp, 2))
            self.sleep(self.freq)

    #-------------------------------------------------------------------------------
    def get_unit(self):
        return "°C" if self.get_config_parameter("unit", "C") == "C" else "°F"
