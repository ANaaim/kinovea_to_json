# kinovea_to_json
Convert kinovea data to json format to be used in LBMC marker less
The file are expected to be in the format task_camera_0i.txt contained in the folder with folder_path
Data will be directly exported in a folder of the task name containing the pose folder with the json files



## Example of the code
````python
import kinovea_to_json as ktj
from pathlib import Path
import shutil

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

ktj.kinovea_to_json("pas", folder_path, nb_camera, list_marker, export_excel=True)
# define source and destination
source = Path("pas.xlsx")
destination = folder_path / "pas.xlsx"

    # check if source file exists
if source.exists():
        # move the file to the new location
    shutil.move(str(source), str(destination))
else:
    print(f"Source file {source} does not exist.")
# Regenerate the data from a excel file that has been generated
ktj.kinovea_to_json(
        "pas",
        folder_path,
        nb_camera,
        list_marker,
        import_from_excel=True,
    )

ktj.kinovea_to_json("trop", folder_path, nb_camera, list_marker)

print("Done!")


````