# This is the unit conversions module for converting temperature and wind speed 
# to appropriate units
# Isn't necessary but it felt cool to implement

def temperature_fahrenheit(temp):
  return (temp * 1.8) + 32

def temperature_kelvin(temp):
  return temp + 273.15

def wind_speed_mph(wnd_spd):
  return wnd_spd * 2.23694

def wind_speed_kmh(wnd_spd):
  return wnd_spd * 3.6