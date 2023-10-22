import requests
from requests.exceptions import RequestException
from config import API_KEY
from tabulate import tabulate

# This function makes an API call to WeatherBit
# requesting weather information for a city
# passed to it as an argument.
def get_weather(city):
  
  # The try-except block makes the call to the
  # API in the try block and if successful the
  # response is stored and returned.
  try:
    url = f"https://api.weatherbit.io/v2.0/current?city={city}&key={API_KEY}"
    
    # Send the API request 
    response = requests.get(url, timeout = 8)
    if response.status_code == 200:
      
      # This parses the requested data as JSON
      # and returns a dictionary representing
      # that data
      data = response.json()
      
      # Stores the name of the city in the json
      # data returned
      city_in_json = data["data"][0]["city_name"]
      
      # Check if the city in the response data is
      # the same as what the user requested
      if city.lower() == city_in_json.lower():  
        return data
      else:
        return "The city you entered does not exist or could not be found.\nPlease check the spelling and try again."
    else:
      print("API request failed with status code: ", response.status_code)
  
  # The except blocks handle errors that arise 
  # due to connection errors or timeouts by 
  # returning helpful messages
  except requests.exceptions.ConnectionError:
    return "No network connection. Please check your internet connection."
  except requests.exceptions.Timeout:
    return "Request timed out. Please try again later."

def temperature_fahrenheit(temp):
  return float((temp * 1.8) + 32)

def temperature_kelvin(temp):
  return float(temp + 273.15)

def wind_speed_mph(wnd_spd):
  return float(wnd_spd * 2.23694)

def wind_speed_kmh(wnd_spd):
  return float(wnd_spd * 3.6)

def display_weather(data, temperature_unit,\
                    wind_speed_unit):
  
  # The data from get_weather(), converted from
  # JSON to a dictionary, is accessed and stored
  city = data["data"][0]["city_name"]
  temperature = data["data"][0]["temp"]
  humidity = data["data"][0]["rh"]
  wind_speed = data["data"][0]["wind_spd"]
  description = data["data"][0]["weather"]["description"]
  
  if int(temperature_unit) == 2:
    temperature = temperature_kelvin(temperature)
  else:
    temperature = temperature_fahrenheit(temperature)
  
  if int(wind_speed_unit) == 2:
    wind_speed = wind_speed_mph(wind_speed)
  else:
    wind_speed = wind_speed_kmh(wind_speed)
  
  city_data = [[f"{city}", f"{temperature}", f"{humidity}", f"{wind_speed}", f"{description}"]]
  print(tabulate(city_data, headers = ["City", "Temperature", "Humidity", "Wind Speed", "Description"]))

def get_user_input(prompt):
  while True:
    print(prompt)
    user_input = input("Input either 1, 2 or 3: ")
    
    if len(user_input) == 0:
      return 1
    elif not user_input.isdigit():
      print("Please input an option number!\n")
    elif 1<=int(user_input)<=3:
      return user_input
    else:
      print("Input either 1, 2 or 3\n")


def main():
  print("Welcome to the Weather app.\nFind out what the weather is like in your city or anywhere else in the world!\n")
  input("Press Enter to continue...")
  
  city = input("Enter the city name: ")
  
  temperature_unit = get_user_input("What should be the unit for temperature? You can press Enter to choose the default as indicated:\n1) Celsius (default)\n2) Kelvin\n3) Fahrenheit")
  wind_speed_unit = get_user_input("Wind speed should be what unit:\n1) Metre per second (m/s) (default)\n2) Miles per hour (mph)\n3) Kilometre per hour (km/h)")

  weather_data = get_weather(city)
  
  # The if statement checks the content of 
  # weather_data if it is a string. This would
  # mean it is an error message that was 
  # returned. What is expected is a dictionary.
  # Hence, the message should be printed and 
  # the script ended.
  if isinstance(weather_data, str):
    print(weather_data)
    exit()
  else:
    # Else if weather_data is a dictionary, pass
    # it along with the user's unit selection
    # for display.
    display_weather(weather_data, temperature_unit, wind_speed_unit)

if __name__ == "__main__":
  main()