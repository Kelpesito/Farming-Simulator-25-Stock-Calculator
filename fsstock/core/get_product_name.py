from .models import CatalogProduct

def get_product_name(product_id: str, catalog: dict[str, CatalogProduct]) -> str:
        """
        Given the ID of a product, returns its name
        
        Parameters
        ----------
        product_id: str
            Product ID
        catalog: dict[str, CatalogProduct]
            Catalog of all items
        
        Returns
        -------
        str:
            Product name
        """
        prod = catalog[product_id]
        return prod.name_es
    