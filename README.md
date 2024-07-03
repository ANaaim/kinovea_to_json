# kinovea_to_json
Convert kinovea data to json format to be used in LBMC marker less
The file are expected to be in the format task_camera_0i.txt contained in the folder with folder_path
Data will be directly exported in a folder of the task name containing the pose folder with the json files



## Example of the code
````python
import kinovea_to_json as ktj
from pathlib import Path

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


ktj.kinovea_to_json("pas", folder_path, 6, list_marker, import_from_excel=True)

````