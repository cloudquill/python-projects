import requests
from configuration import API_KEY
from requests.exceptions import RequestException
import unit_conversions
from tabulate import tabulate

def make_api_request(city):
  # The try-except block attempts to call the API and, upon success, stores and 
  # returns the response.
  try:
    url = f"https://api.weatherbit.io/v2.0/current?city={city}&key={API_KEY}"
    
    # Send the API request with a timeout of 8 seconds
    response = requests.get(url, timeout = 8)
    
    if response.status_code == 200:
      # Parse and return the received JSON data as a dictionary
      return response.json()
    else:
      return "API request failed with status code: " + str(response.status_code)
  except requests.exceptions.ConnectionError:
    return "Couldn't complete your request because you are not connected to the internet. Please check your internet connection and try again."
  except requests.exceptions.Timeout:
    return "Your request timed out. Please try again later."
  except requests.exceptions.RequestException as e:
    return "An error occurred during the API request: " + str(e)

def validate_city_in_response(city, data):
  # Retrieve the city name from the response data
  city_in_json = data["data"][0]["city_name"]
      
  # Compares the city name in the response data to what the user provided
  if city.lower() == city_in_json.lower():  
    return data
  else:
    return "The city you entered does not exist or could not be found.\nPlease check the spelling and try again."

# This function makes an API call to WeatherBit to retrieve weather information 
# for a specified city.
# It relies on the previously defined functions for sending the request and parsing the response.
def get_weather(city):
  data = make_api_request(city)
  
  # The if statement checks if the content of data is a string, indicating an 
  # error message.
  # In such a case, the error message is printed, and the script is terminated 
  # since a dictionary response is expected.
  if isinstance(data, str):
    print(data)
    exit()
  else:
    return validate_city_in_response(city, data)

def display_weather(data, temperature_unit, wind_speed_unit):
  # The data from get_weather(), converted from JSON to a dictionary, is 
  # accessed and stored
  city_data = data["data"][0]
  city = city_data["city_name"]
  temperature = city_data["temp"]
  humidity = city_data["rh"]
  wind_speed = city_data["wind_spd"]
  description = city_data["weather"]["description"]

  # Map the integer values of the last two function arguments to their 
  # corresponding conversion functions.
  # For key = 1, use a lambda function that returns the value itself since the 
  # response data is already in the default units.
  # The lambda function is an inline function defined without using 'def'. It 
  # takes the argument 'x' and returns it unchanged.
  temperature_conversion = {
    2: unit_conversions.temperature_kelvin,
    3: unit_conversions.temperature_fahrenheit,
    1: lambda x: x,
  }
  
  # temperature_conversion is a dictionary where temperature_unit serves as the 
  # key to retrieve the corresponding conversion function.
  # The retrieved conversion function is then invoked with the temperature 
  # value (temperature) as an argument.
  temperature = temperature_conversion[temperature_unit](temperature)

  wind_speed_conversion = {
    2: unit_conversions.wind_speed_mph,
    3: unit_conversions.wind_speed_kmh,
    1: lambda x: x,
  }
    
  wind_speed = wind_speed_conversion[wind_speed_unit](wind_speed)
  
  city_data = [[f"{city}", f"{temperature}", f"{humidity}", f"{wind_speed}", f"{description}"]]
  print(tabulate(city_data, headers = ["City", "Temperature", "Humidity", "Wind Speed", "Description"]))

def get_user_input(prompt):
  while True:
    print(prompt)
    user_input = input("Input either 1, 2 or 3: ")
    
    if len(user_input) == 0:
      return 1
    elif not user_input.isdigit():
      print("Please input a valid option number.\n")
    else:
      chosen_option = int(user_input)
      if 1<=chosen_option<=3:
        return chosen_option
      else:
        print("Input out of range. Please input either 1, 2 or 3\n")


def main():
  print("Welcome to the Weather app.\nFind out what the weather is like in your city or anywhere else in the world!\n")
  input("Press Enter to continue...")
  
  city = input("Enter the city name: ")
  
  temperature_unit = get_user_input("Select temperature unit. You can press Enter to choose the default as indicated:\n1) Celsius (default)\n2) Kelvin\n3) Fahrenheit")
  wind_speed_unit = get_user_input("Select wind speed unit:\n1) Metre per second (default)\n2) Miles per hour \n3) Kilometre per hour")

  weather_data = get_weather(city)
  display_weather(weather_data, temperature_unit, wind_speed_unit)

if __name__ == "__main__":
  main()