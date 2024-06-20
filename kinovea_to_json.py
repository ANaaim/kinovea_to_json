import pandas as pd
from functools import reduce
import json
import numpy as np
from pathlib import Path
import os


def read_kinovea_trajectory(file_path):
    # Initialize an empty dictionary to hold the data
    data = {}

    # Open the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Initialize an empty list to hold the current marker's data
    current_marker_data = []
    current_marker_name = None

    # Iterate over the lines in the file
    for line in lines:
        # If the line starts with '#', it's a new marker
        if line.startswith('#'):
            # If there's data for the previous marker, add it to the dictionary
            if current_marker_data:
                if current_marker_name not in data.keys():
                    data[current_marker_name] = pd.DataFrame(current_marker_data, columns=['T', 'X', 'Y'])
                else:
                    data[current_marker_name] = pd.concat([data[current_marker_name], pd.DataFrame(current_marker_data, columns=['T', 'X', 'Y'])], axis=0)
                #data[current_marker_name] = pd.DataFrame(current_marker_data, columns=['T', 'X', 'Y'])

            # Get the new marker's name
            current_marker_name = line.strip('# \n')

            # Reset the current marker data
            current_marker_data = []
        elif line == '\n':
            # Skip empty lines
            continue
        else:
            # Split the line into components
            components = line.strip().split()

            # Convert the components to the correct types and add them to the current marker data
            current_marker_data.append([float(components[0]), float(components[1].replace(',', '.')), float(components[2].replace(',', '.'))])

    # Add the last marker's data to the dictionary
    if current_marker_name not in data.keys():
        data[current_marker_name] = pd.DataFrame(current_marker_data, columns=['T', 'X', 'Y'])
    else:
        data[current_marker_name] = pd.concat(
            [data[current_marker_name], pd.DataFrame(current_marker_data, columns=['T', 'X', 'Y'])], axis=0)

    return data

def merge_data(data,camera_name):
    # Initialize an empty DataFrame to hold the merged data
    merged_data = pd.DataFrame()

    # Iterate over each marker's DataFrame
    for marker, data in trajectory_data.items():
        # If the merged_data DataFrame is empty, copy the current marker's data to it
        if merged_data.empty:
            merged_data = data.copy()
            merged_data.columns = ['T', f'{marker}_X_{camera_name}', f'{marker}_Y_{camera_name}']
        else:
            # Otherwise, merge the current marker's data with the existing data
            data.columns = ['T', f'{marker}_X_{camera_name}', f'{marker}_Y_{camera_name}']
            merged_data = pd.merge(merged_data, data, on='T', how='outer', sort=True)

    # Print the merged data
    return merged_data

# Define a helper function to merge two dataframes with a nearest approach on 'T'
def merge_nearest(df1, df2):
    return pd.merge(df1, df2, on='T', how='outer', sort=True)

def generate_json(task, folder, nb_camera):
    for i in range(1, nb_camera + 1):
        name_file = f"{task}_camera_0{i}.txt"
        print(name_file)
        camera_name = f"camera_0{i}"
        trajectory_data = read_kinovea_trajectory(f"{folder}/{name_file}")
        merged_data = merge_data(trajectory_data, camera_name)
        list_merged_data.append(merged_data)

task = "pas"
folder = "data_kinovea"
nb_camera = 6
list_merged_data = []
for i in range(1, nb_camera+1):
    name_file = f"{task}_camera_0{i}.txt"
    print(name_file)
    camera_name = f"camera_0{i}"
    trajectory_data = read_kinovea_trajectory(f"{folder}/{name_file}")
    merged_data = merge_data(trajectory_data, camera_name)
    list_merged_data.append(merged_data)

#
#
# # Use the reduce function to apply the merge_nearest function to all dataframes in the list
final_data = reduce(merge_nearest, list_merged_data)
#
# # Export final data
final_data.to_excel(f'final_data_{task}.xlsx', index=False)

# read final data from excel
final_data = pd.read_excel(f'final_data_{task}.xlsx')

# # Print the final merged data
# print(final_data)

# Export all the data in json looking like the openpose format
# for each line we have the time and the x and y coordinates of each marker for each camera

list_marker = ["mÃ©tatarses","tarse","pointe dos","dÃ©but queue","jarret","hanche"]
# Read one line of the final data

for index, row in final_data.iterrows():
    for i in range(1, nb_camera + 1):
        name_camera = f"camera_0{i}_json"
        folder_to_export = Path(task,'pose',name_camera)
        data_to_export = dict()
        data_to_export["pose_keypoints_2d"] = []
        for marker in list_marker:

             collumn_name_X = f"{marker}_X_camera_0{i}"
             collumn_name_Y = f"{marker}_Y_camera_0{i}"
             value_confidence = 1.0

             # test if both collumns exist
             if collumn_name_X in row and collumn_name_Y in row:
                value_X = row[collumn_name_X]
                value_Y = row[collumn_name_Y]
                if np.isnan(value_X) or np.isnan(value_Y):
                    value_X = 0
                    value_Y = 0
                    value_confidence = 0

                data_to_export["pose_keypoints_2d"] = data_to_export["pose_keypoints_2d"]+[value_X,value_Y,value_confidence]
             else:
                # si la collumn n'existe pas on met des 0
                 data_to_export["pose_keypoints_2d"] = data_to_export["pose_keypoints_2d"]+[0,0,0]
        final_dict = dict()
        final_dict["version"] = 1.3

        data = dict()
        data["person_id"] = [-1]
        data["pose_keypoints_2d"] = data_to_export["pose_keypoints_2d"]
        final_dict["people"] = [data]
        filename_json = f"{name_camera}_{index:09}_keypoints.json"
        full_path = Path(folder_to_export,filename_json)
        # Test if folder exists
        if not folder_to_export.exists():
            os.makedirs(folder_to_export)
        with open(full_path, "w") as outfile:
            json.dump(final_dict, outfile)
        # print(data_to_export)

# {"version":1.3,
#   "people":[{"person_id":[-1],
#              "pose_keypoints_2d":[515.715,684.065,0.909389,526.538,662.987,0.892756,0,0,0,599.684,694.547,0.894643,0,0,0,615.625,820.537,0.860613,568.389,789.141,0.708682,620.84,952.014,0.829629,0,0,0,610.373,1104.52,0.939207,0,0,0,557.762,1120.44,0.72859,520.966,1115.25,0.645879,542.112,1404.33,0.863521,526.33,1362.33,0.737915,521.208,1614.58,0.941796,521.046,1514.76,0.825616,589.289,773.341,0.877314,573.633,584.147,0.808749,405.378,1625.23,0.748194,437.06,1656.57,0.831269,536.751,1630.4,0.867261,436.752,1525.14,0.98391,442.061,1509.36,0.926854,531.587,1535.51,0.486605],
#              "face_keypoints_2d":[],
#               "hand_left_keypoints_2d":[],
#               "hand_right_keypoints_2d":[],
#               "pose_keypoints_3d":[],
#               "face_keypoints_3d":[],
#               "hand_left_keypoints_3d":[],
#               "hand_right_keypoints_3d":[]}]}
