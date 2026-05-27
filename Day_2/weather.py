import os
import sys
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_KEY = os.getenv('WEATHER_API_KEY')
if not API_KEY:
    print("Error: API key missing from .env")
    sys.exit(1)

base_url = 'https://api.openweathermap.org/data/2.5'

def get_weather(city):
    
    params = {
        'q' : city,
        'appid' : API_KEY,
        'units' : 'metric'
    }
    url = f'{base_url}/weather'
    response = requests.get(url, params = params)
    response.raise_for_status()
    return response.json()

def get_forecast(city):
    url = f'{base_url}/forecast'
    params = {
        'q' : city,
        'appid' : API_KEY,
        'units' : 'metric',
        'cnt' : 5
    }
    response = requests.get(url, params = params)
    response.raise_for_status()
    return response.json()
    
def display_weather(data):
    city = data['name']
    country = data['sys']['country']
    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    humidity = data['main']['humidity']
    description = data['weather'][0]['description'].title()
    wind_speed = data['wind']['speed']


    print("\n" + "="*45)
    print(f"  Weather in {city}, {country}")
    print("="*45)
    print(f"  Condition   : {description}")
    print(f"  Temperature : {temp}°C  (Feels like {feels_like}°C)")
    print(f"  Humidity    : {humidity}%")
    print(f"  Wind Speed  : {wind_speed} m/s")
    print("="*45)


def display_forecast(data, city):
    print(f"\n  Forecast of {city}")
    print("-"*45)
    
    for entry in data['list']:
        time        = datetime.fromtimestamp(entry['dt']).strftime('%d %b, %I:%M %p')
        temp        = entry['main']['temp']
        description = entry['weather'][0]['description'].title()
        print(f"  {time}  |  {temp}°C  |  {description}")
    
    print("-"*45)


if __name__ == '__main__':

    city = input("Enter City: ")
    if not city:
        print("Error: City name cannot be empty.")
        sys.exit(1)
    try:
        weather = get_weather(city)
        forecast = get_forecast(city)

        display_weather(weather)
        display_forecast(forecast, city)
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("ERROR: City not found. Please check the city name and try again.")
        elif e.response.status_code == 401:
            print("ERROR: Wrong API KEY")
        else:
            print(f'ERROR: HTTP error occured: {e}')
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Network conneection error.")
