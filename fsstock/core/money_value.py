def money_value(qty_l: float, max_price_per_1000: float) -> float:
    """
    Returns the value of a product:
    quantity * price/L
    
    Parameters
    ----------
    qty_l: float
        Quantity of product, in L
    max_price_per_1000: float
        Maximum price, in €/1000L
    
    Returns
    -------
    float:
        Total value of a product
    """
    return qty_l * (max_price_per_1000 / 1000.0)
