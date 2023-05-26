from datetime import datetime, date
import os
import config
import pandas as pd

if __name__ == '__main__':
    outputDirectory = config.outputDirectory

    # Create an empty list to store the DataFrames
    dfs = []


    for filename in os.listdir(outputDirectory):
        # Check if the filename matches either pattern
        if '.csv' in filename:
            # Determine the file format based on the extension
            file_format = 'csv' if filename.endswith('.csv') else 'tsv'
            # Read the file into a DataFrame
            df = pd.read_csv(os.path.join(outputDirectory, filename), delimiter='\t' if file_format == 'tsv' else ',')
            # Extract the ID and date from the folder name
            id = filename.split('_')[0]
            date_str = filename.split('_')[1][0:8]
            year = date_str[:4]
            month = date_str[4:6]
            day = date_str[6:8]
            time_rdt = datetime.strptime(date_str, '%Y%m%d').date()
            series_name = filename[len(id) + len(date_str) + 1:-4]
            # Add the ID, date, and series names as columns to the DataFrame
            df.insert(0, 'ID_MERGE', id)
            df.insert(1, 'time_rdt', time_rdt)
            df.insert(2, 'series_name', series_name)
            # Append the modified DataFrame to the list
            dfs.append(df)

    # Concatenate the DataFrames into a single DataFrame
    combined_df = pd.concat(dfs, ignore_index=True).rename(columns={
        'Segment': 'segment',
        'LabelmapSegmentStatisticsPlugin.voxel_count': 'voxels1',
        'LabelmapSegmentStatisticsPlugin.volume_mm3': 'volmm3_1',
        'LabelmapSegmentStatisticsPlugin.volume_cm3': 'volcm3_1',
        'ScalarVolumeSegmentStatisticsPlugin.voxel_count': 'voxels2',
        'ScalarVolumeSegmentStatisticsPlugin.volume_mm3': 'volmm3_2',
        'ScalarVolumeSegmentStatisticsPlugin.volume_cm3': 'volcm3_2',
        'ScalarVolumeSegmentStatisticsPlugin.min': 'hfu_min',
        'ScalarVolumeSegmentStatisticsPlugin.max': 'hfu_max',
        'ScalarVolumeSegmentStatisticsPlugin.mean': 'hfu_mean',
        'ScalarVolumeSegmentStatisticsPlugin.median': 'hfu_median',
        'ScalarVolumeSegmentStatisticsPlugin.stdev': 'hfu_sd',
    })

    # done
    print(combined_df.head())
    combined_df.to_csv('combinedData.csv')
