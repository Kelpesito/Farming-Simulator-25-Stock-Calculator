from .models import CatalogProduct

def get_product_name(product_id: str, catalog: dict[str, CatalogProduct], lang: str) -> str:
        """
        Given the ID of a product, returns its name
        
        Parameters
        ----------
        product_id: str
            Product ID
        catalog: dict[str, CatalogProduct]
            Catalog of all items
        lang: str
            Language
        
        Returns
        -------
        str:
            Product name
        """
        prod = catalog[product_id]
        return prod.name_es if lang == "es" else prod.name_en
    