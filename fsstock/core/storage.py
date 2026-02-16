import json
import os
from pathlib import Path
from typing import Any

from .models import FarmData
from .new_farm_id import new_farm_id


# =================================================================================================
# Constants
# =================================================================================================

DATA_VERSION = 4
DEFAULT_FARM_NAME = "Mi granja"

# =================================================================================================
# Helpers
# =================================================================================================

def _data_path(user_data_dir: str) -> Path:
    """
    Creates the save file json (if it does not exist) and returns the
    file name.
    
    Parameters
    ----------
    user_data_dir: str
        Directory to save data files
        
    Returns
    -------
    Path: 
        .json file where to save the state app
    """
    
    d = Path(user_data_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d / "fs_stock_state.json"

# =================================================================================================
# Main loader and saver
# =================================================================================================

def load_state(user_data_dir: str) -> tuple[dict[str, FarmData], str]:
    """
    Loads the saved data of the application.
    
    Parameters
    ----------
    user_data_dir: str
        Directory to save data files

    Returns
    -------
    farms: dict[str, FarmData]
        Dictionary with the data of the saved farms. The keys are the
        farm's ID and the values are FarmData instances. 
    current_farm_id | fid: str
        Current farm's ID.
    """
    path: Path = _data_path(user_data_dir)  # saved data json

    # No saved data
    if not path.exists():  
        fid: str = new_farm_id()
        farms: dict[str, FarmData] = {fid: FarmData(
            name=DEFAULT_FARM_NAME,
            stock=[],
            last_plan=None,
            user_products=[],
        )}
        return farms, fid

    # If saved data
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))  # load .json
    farms_raw: dict[str, dict] = raw["farms"]
    farms: dict[str, FarmData] = {}
    for fid, fdata in farms_raw.items():
        if not isinstance(fdata, dict):
            continue
        farms[fid] = FarmData.from_dict(fdata, default_name=DEFAULT_FARM_NAME)

    current: str = raw["current_farm_id"]

    return farms, current


def save_state(user_data_dir: str, farms: dict[str, FarmData], current_farm_id: str) -> None:
    """
    Saves data application into a json.
    
    Parameters
    ----------
    user_data_dir: str
        Directory to save data files
    
    farms: dict[str, FarmData]
        Dictionary with the data of the saved farms. The keys are the
        farm's ID and the values are FarmData instances.
    
    current_farm_id: str
        Current farm's ID
    """
    path: Path = _data_path(user_data_dir)  # fs_stock_state.json

    # Convert FarmData to dict
    farms_out: dict[str, dict] = {}
    for fid, farm in (farms or {}).items():
        if farm is None:
            continue
        farms_out[fid] = farm.to_dict()

    # json content
    payload: dict[str, Any] = {
        "version": DATA_VERSION,
        "current_farm_id": current_farm_id,
        "farms": farms_out,
    }

    # save json
    tmp: Path = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
