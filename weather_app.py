import requests
from config import API_KEY
from tabulate import tabulate

def get_weather(city):
  url = f"https://api.weatherbit.io/v2.0/current?city={city}&key={API_KEY}"
  response = requests.get(url)
  data = response.json()
  return data

def display_weather(data):
  city = data["data"][0]["city_name"]
  temperature = data["data"][0]["temp"]
  humidity = data["data"][0]["rh"]
  wind_speed = data["data"][0]["wind_spd"]
  description = data["data"][0]["weather"]["description"]
  
  city_data = [[f"{city}", f"{temperature}", f"{humidity}", f"{wind_speed}", f"{description}"]]
  print(tabulate(city_data, headers = ["City", "Temperature", "Humidity", "Wind Speed", "Description"]))

def main():
  city = input("Enter the city name: ")
  weather_data = get_weather(city)
  display_weather(weather_data)

if __name__ == "__main__":
  main()