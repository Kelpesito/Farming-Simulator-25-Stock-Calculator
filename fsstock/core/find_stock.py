from __future__ import annotations

from typing import TYPE_CHECKING

from .models import StockEntry

if TYPE_CHECKING:
    from fsstock.ui.app import FSStockApp


def find_stock(app: FSStockApp, product_id: str) -> StockEntry | None:
        """
        Checks if a product is in stock. In positive case, returns it.
        
        Parameters
        ----------
        product_id: str
            The ID product
        
        Returns
        -------
        e: StockEntry | None
            The StockEntry, in case product is in stock, otherwise None
        """
        for e in app.stock:
            if e.product_id == product_id:
                return e
        return None
    