import fastf1
import os
import numpy as np
import pandas as pd
import time

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

all_races_data = []

for year in range(2020, 2027):
    schedule = fastf1.get_event_schedule(year)
    for _, event in schedule.iterrows():
        if(event["EventFormat"] == "testing"):
            continue
        location = event["Location"]
        round_num = event['RoundNumber']
        try:
            time.sleep(1)
            q_session = fastf1.get_session(year, round_num, 'Q')
            q_session.load(telemetry=False, weather=False)
            q_results = q_session.results[['Abbreviation', 'Q1', 'Q2', 'Q3']].copy()
            q_results['Best_Q_Time'] = q_results[['Q1', 'Q2', 'Q3']].min(axis=1)
            pole_time_sec = q_results['Best_Q_Time'].min().total_seconds()
            q_results['Quali_Gap_Ratio'] = q_results['Best_Q_Time'].dt.total_seconds() / pole_time_sec
            q_features = q_results[['Abbreviation', 'Quali_Gap_Ratio']]

            session = fastf1.get_session(year, round_num, 'R')
            session.load(telemetry=False, weather=True)
            results = session.results[
                ['Abbreviation', 'TeamName', 'GridPosition', 'Position', 'Status', 'Time', 'Points']].copy()
            results = results.merge(q_features, on='Abbreviation', how='left')
            weather = session.weather_data
            avg_track_temp = weather['TrackTemp'].mean()
            avg_air_temp = weather['AirTemp'].mean()
            rain_occurred = int(weather['Rainfall'].any())
            results['TrackTemp'] = avg_track_temp
            results['AirTemp'] = avg_air_temp
            results['IsRain'] = rain_occurred


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
            results['Is_DNF'] = (~results['Status'].str.contains('Finished|Lap', regex=True, na=False)).astype(int)
            results['Year'] = year
            results['RoundNumber'] = round_num
            results['Location'] = location
            all_races_data.append(results)
            print(f"Successfully processed: {year} - {location}")
        except Exception as e:
            print(f"Failed to process {year} - {location}. Error: {e}")

if all_races_data:
    final_df = pd.concat(all_races_data, ignore_index=True)

    final_df.sort_values(by=['Year', 'RoundNumber'], inplace=True)
    final_df['Driver_Form_5Races'] = (
        final_df.groupby('Abbreviation')['Position']
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=1).mean())
    )
    team_race_points = final_df.groupby(['TeamName', 'Year', 'RoundNumber'])['Points'].sum().reset_index()
    team_race_points.sort_values(by=['Year', 'RoundNumber'], inplace=True)
    team_race_points['Team_Form_5Races'] = (
        team_race_points.groupby('TeamName')['Points']
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=1).sum())
    )
    final_df = final_df.merge(
        team_race_points[['TeamName', 'Year', 'RoundNumber', 'Team_Form_5Races']],
        on=['TeamName', 'Year', 'RoundNumber'],
        how='left'
    )
    final_df['Driver_DNF_Rate'] = (
        final_df.groupby('Abbreviation')['Is_DNF']
        .transform(lambda x: x.shift(1).rolling(window=10, min_periods=1).mean())
    )
    final_df.dropna(subset=['Time_Ratio', 'Driver_Form_5Races', 'Team_Form_5Races', 'Driver_DNF_Rate', 'Quali_Gap_Ratio'], inplace=True)
    final_df = pd.get_dummies(final_df, columns=['Location'], dtype=int)
    circuit_columns = [col for col in final_df.columns if col.startswith('Location_') and col != 'Location_Monza']
    final_features = ['GridPosition', 'Quali_Gap_Ratio', 'TrackTemp', 'AirTemp', 'IsRain', 'Driver_Form_5Races', 'Team_Form_5Races', 'Driver_DNF_Rate'] + circuit_columns + ['Time_Ratio']
    matrix_ready_df = final_df[final_features].copy()
    cols_to_normalize = ['GridPosition', 'TrackTemp', 'AirTemp', 'Driver_Form_5Races', 'Team_Form_5Races', 'Quali_Gap_Ratio', 'Driver_DNF_Rate']
    for col in cols_to_normalize:
        col_min = matrix_ready_df[col].min()
        col_max = matrix_ready_df[col].max()
        if col_max > col_min:
            matrix_ready_df[col] = (matrix_ready_df[col] - col_min) / (col_max - col_min)
    matrix_ready_df.to_csv('f1_matrix_data.csv', index=False, sep=';')
    print("\nDataset successfully cleaned, normalized, and saved to 'f1_matrix_data.csv'!")
else:
    print("No data available to merge and process.")