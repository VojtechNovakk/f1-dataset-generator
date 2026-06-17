import fastf1
import os

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

session = fastf1.get_session(2024, 'Monaco', 'R')
session.load()

laps_data = session.laps[['DriverNumber', 'LapNumber', 'LapTime', 'IsPersonalBest']]

print(laps_data.head())

laps_data.to_csv('monaco_laps.csv', index=False)