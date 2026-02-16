import json

from .models import CatalogProduct
from .paths import catalog_path


def load_catalog() -> dict[str, CatalogProduct]:
    """
    Load and return the game catalog from catalog.json
    
    Returns
    -------
    products: dict[str, CatalogProduct]
        A dictionary where the key is the ID product and the values are
        CatalogProducts, containig the ID, name in Spanish and English,
        the icon file and the default maximum price (€/1000L)
    """
    
    data = json.loads(catalog_path().read_text(encoding="utf-8"))
    products: dict[str, CatalogProduct] = {}
    for p in data["products"]:
        prod = CatalogProduct(
            id=str(p["id"]),
            name_es=str(p["name_es"]),
            name_en=str(p["name_en"]),
            icon=str(p["icon"]),
            default_max_price_per_1000=int(p["default_max_price_per_1000"]),
        )
        products[prod.id] = prod
        
    return products
