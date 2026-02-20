from pathlib import Path

def fsstock_dir() -> Path:
    """
    Returns the project path (fsstock).
    
    Returns
    -------
    Path: 
        Project path
    """
    # .../fsstock/core/paths.py -> parents[1] = .../fsstock
    return Path(__file__).resolve().parents[1]

def assets_dir() -> Path:
    """
    Returns the assets path: fsstock/assets.
    
    Returns
    -------
    Path: 
        Assets path
    """
    return fsstock_dir() / "assets"

def icons_dir() -> Path:
    """
    Returns the icons path: fsstock/assets/icons.
    
    Returns
    -------
    Path: 
        Icons path
    """
    return assets_dir() / "icons"

def catalog_path() -> Path:
    """
    Returns the catalog path: fsstock/assets/catalog/catalog.json
    
    Returns
    -------
    Path:
        Catalog .json path
    """
    return assets_dir() / "catalog" / "catalog.json"

def custom_icon_path() -> Path:
    """
    Returns the icon path for custom items:
    fsstock/assets/icons/custom.png
    
    Returns
    -------
    Path:
        Custom item icon
    """
    return icons_dir() / "custom.png"

def i18n_dir() -> Path:
    """
    Returns the i18n path: fsstock/assets/i18n
    
    Returns
    -------
    Path:
        Catalog .json path
    """
    return assets_dir() / "i18n"
