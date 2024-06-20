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
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Initialize an empty list to hold the current marker's data
    current_marker_data = []
    current_marker_name = None

    # Iterate over the lines in the file
    for line in lines:
        # If the line starts with '#', it's a new marker
        if line.startswith("#"):
            # If there's data for the previous marker, add it to the dictionary
            if current_marker_data:
                if current_marker_name not in data.keys():
                    data[current_marker_name] = pd.DataFrame(
                        current_marker_data, columns=["T", "X", "Y"]
                    )
                else:
                    data[current_marker_name] = pd.concat(
                        [
                            data[current_marker_name],
                            pd.DataFrame(current_marker_data, columns=["T", "X", "Y"]),
                        ],
                        axis=0,
                    )
                # data[current_marker_name] = pd.DataFrame(current_marker_data, columns=['T', 'X', 'Y'])

            # Get the new marker's name
            current_marker_name = line.strip("# \n")

            # Reset the current marker data
            current_marker_data = []
        elif line == "\n":
            # Skip empty lines
            continue
        else:
            # Split the line into components
            components = line.strip().split()

            # Convert the components to the correct types and add them to the current marker data
            current_marker_data.append(
                [
                    float(components[0]),
                    float(components[1].replace(",", ".")),
                    float(components[2].replace(",", ".")),
                ]
            )

    # Add the last marker's data to the dictionary
    if current_marker_name not in data.keys():
        data[current_marker_name] = pd.DataFrame(
            current_marker_data, columns=["T", "X", "Y"]
        )
    else:
        data[current_marker_name] = pd.concat(
            [
                data[current_marker_name],
                pd.DataFrame(current_marker_data, columns=["T", "X", "Y"]),
            ],
            axis=0,
        )

    return data


def merge_data(trajectory_data, camera_name):
    # Initialize an empty DataFrame to hold the merged data
    merged_data = pd.DataFrame()

    # Iterate over each marker's DataFrame
    for marker, data in trajectory_data.items():
        # If the merged_data DataFrame is empty, copy the current marker's data to it
        if merged_data.empty:
            merged_data = data.copy()
            merged_data.columns = [
                "T",
                f"{marker}_X_{camera_name}",
                f"{marker}_Y_{camera_name}",
            ]
        else:
            # Otherwise, merge the current marker's data with the existing data
            data.columns = ["T", f"{marker}_X_{camera_name}", f"{marker}_Y_{camera_name}"]
            merged_data = pd.merge(merged_data, data, on="T", how="outer", sort=True)

    # Print the merged data
    return merged_data


# Define a helper function to merge two dataframes with a nearest approach on 'T'
def merge_nearest(df1, df2):
    return pd.merge(df1, df2, on="T", how="outer", sort=True)


def generate_json(task, folder, nb_camera):
    list_merged_data = []
    for i in range(1, nb_camera + 1):
        name_file = f"{task}_camera_0{i}.txt"
        print(name_file)
        camera_name = f"camera_0{i}"
        trajectory_data = read_kinovea_trajectory(f"{folder}/{name_file}")
        merged_data = merge_data(trajectory_data, camera_name)
        list_merged_data.append(merged_data)
    return list_merged_data


def kinovea_to_json(
    task: str,
    folder_path: Path,
    nb_camera: int,
    list_marker: list,
    import_from_excel=False,
    export_excel=False,
) -> None:
    """Convert kinovea data to json format to be used in LBMC marker less
    The file are expected to be in the format task_camera_0i.txt contained in the folder with folder_path
    Data will be directly exported in a folder of the task name containing the pose folder with the json files

    Parameters
    ----------
    task : str
        The task name
    folder_path : Path
        The path to the folder containing the kinovea data
    nb_camera : int
        The number of camera used
    list_marker : list
        The list of marker used in the kinovea data
    import_from_excel : bool, optional
        If True, import the final data from an Excel file, by default False. The file is expected to be in the folder_path
        with the name task.xlsx
    export_excel : bool, optional
        If True, export the final data in an Excel file, by default False

    Returns
    -------
    None

    """
    if import_from_excel:
        # read final data from excel
        filename = f"{task}.xlsx"
        path_file = Path(folder_path, filename)
        final_data = pd.read_excel(path_file)
    else:
        list_merged_data = generate_json(task, folder_path, nb_camera)
        # # Use the reduce function to apply the merge_nearest function to all dataframes in the list
        final_data = reduce(merge_nearest, list_merged_data)

    if export_excel:
        # # Export final data
        final_data.to_excel(f"{task}.xlsx", index=False)

    # Export all the data in json looking like the openpose format
    # for each line we have the time and the x and y coordinates of each marker for each camera
    # Read one line of the final data

    for index, row in final_data.iterrows():
        for i in range(1, nb_camera + 1):
            name_camera = f"camera_0{i}_json"
            folder_to_export = Path(task, "pose", name_camera)
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

                    data_to_export["pose_keypoints_2d"] = data_to_export[
                        "pose_keypoints_2d"
                    ] + [value_X, value_Y, value_confidence]
                else:
                    # si la collumn n'existe pas on met des 0
                    data_to_export["pose_keypoints_2d"] = data_to_export[
                        "pose_keypoints_2d"
                    ] + [0, 0, 0]
            final_dict = dict()
            final_dict["version"] = 1.3

            data = dict()
            data["person_id"] = [-1]
            data["pose_keypoints_2d"] = data_to_export["pose_keypoints_2d"]
            final_dict["people"] = [data]
            filename_json = f"{name_camera}_{index:09}_keypoints.json"
            full_path = Path(folder_to_export, filename_json)
            # Test if folder_path exists
            if not folder_to_export.exists():
                os.makedirs(folder_to_export)
            with open(full_path, "w") as outfile:
                json.dump(final_dict, outfile)


if __name__ == "__main__":
    folder_path = Path("data_kinovea")
    nb_camera = 6
    list_marker = [
        "mÃ©tatarses",
        "tarse",
        "pointe dos",
        "dÃ©but queue",
        "jarret",
        "hanche",
    ]

    kinovea_to_json("pas", folder_path, nb_camera, list_marker)
    kinovea_to_json("trop", folder_path, nb_camera, list_marker)
    kinovea_to_json(
        "nouvelle_origine_trot",
        folder_path,
        nb_camera,
        list_marker,
        import_from_excel=True,
    )
    print("Done!")
