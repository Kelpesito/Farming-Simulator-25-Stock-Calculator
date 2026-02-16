from uuid import uuid4


def new_farm_id() -> str:
    """
    Creates an ID for a new farm.
    
    Returns
    -------
    str:
        A 10 character hexadecimal ID
    """
    return uuid4().hex[:10]
