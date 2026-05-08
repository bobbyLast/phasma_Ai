import requests

# Get all event series to see what weather-related markets exist
response = requests.get("https://api.elections.kalshi.com/trade-api/v2/series")
if response.status_code == 200:
    series = response.json().get('series', [])
    
    # Find weather-related series
    weather_keywords = ['weather', 'temperature', 'rain', 'snow', 'hurricane', 'tornado', 'precipitation', 'heat', 'cold', 'flood', 'drought', 'wind']
    
    print(f"Total series: {len(series)}")
    print("\nWeather-related series:")
    
    for s in series:
        title = s.get('title', '').lower()
        for keyword in weather_keywords:
            if keyword in title:
                print(f"  - {s.get('ticker')}: {s.get('title')}")
                break
