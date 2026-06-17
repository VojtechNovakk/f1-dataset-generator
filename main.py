import fastf1
import os
import numpy as np
import pandas as pd

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

all_races_data = []

for year in range(2024, 2025):
    schedule = fastf1.get_event_schedule(year)
    for _, event in schedule.iterrows():
        if(event["EventFormat"] == "testing"):
            continue
        location = event["Location"]
        round_num = event['RoundNumber']
        try:
            session = fastf1.get_session(year, round_num, 'R')
            session.load()
            results = session.results[['Abbreviation', 'GridPosition', 'Position', 'Status', 'Time']].copy()
            winner_time = results.iloc[0]["Time"].total_seconds()
            results['TotalTime_sec'] = np.nan
            for index, row in results.iterrows():
                if(row['Status'] == 'Finished'):
                    if row['Position'] == 1.0:
                        results.at[index, 'TotalTime_sec'] = winner_time
                    else:
                        gap_sec = row['Time'].total_seconds()
                        results.at[index, 'TotalTime_sec'] = winner_time + gap_sec
            results['Time_Ratio'] = results['TotalTime_sec'] / winner_time
            results['Year'] = year
            results['Location'] = location
            all_races_data.append(results)
        except Exception as e:
            print(f"Error: {e}")

if all_races_data:
    final_df = pd.concat(all_races_data, ignore_index=True)
    final_df.dropna(subset=['Time_Ratio'], inplace=True)
    final_df = pd.get_dummies(final_df, columns=['Location'], dtype=int)
    circuit_columns = [col for col in final_df.columns if col.startswith('Location_')]
    final_features = ['GridPosition', 'Time_Ratio'] + circuit_columns
    matrix_ready_df = final_df[final_features]
    matrix_ready_df.to_csv('f1_matrix_data.csv', index=False)
    print("\nDataset úspěšně vyčištěn a uložen do 'f1_matrix_data.csv'!")
else:
    print("Nebyla nalezena žádná data ke sloučení.")