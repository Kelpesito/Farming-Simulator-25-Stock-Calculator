from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.clock import Clock
from kivy._clock import ClockEvent
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import ImageLeftWidget, MDList, OneLineAvatarIconListItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField

from fsstock.core.find_stock import find_stock
from fsstock.core.models import CatalogProduct, StockEntry
from fsstock.ui.colors.colors import BG_DARK, BLACK, PRIMARY_GREEN

if TYPE_CHECKING:
    from fsstock.ui.app import FSStockApp


class AddProductScreen(MDScreen):
    """
    Add product screen.
    List of all products in base catalog.
    Search for a product to include it in stock.
    """
    
    # =============================================================================================
    # Build
    # =============================================================================================
    
    def __init__(self, app: FSStockApp, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app = app
        
        self.md_bg_color: str = BG_DARK  # Background color

        # cache de items y de iconos
        self._items_by_id: dict[str, OneLineAvatarIconListItem] = {}
        self._icon_cache: dict[str, ImageLeftWidget] = {} 
        self._search_event: ClockEvent | None = None

        # Layout
        self.root = MDBoxLayout(
            orientation="vertical",
            padding=(dp(12), dp(12)),
            spacing=dp(12),
        )
        self.search = MDTextField(
            hint_text=self.app.t("add_product.textfield"),
            mode="rectangle",
            line_color_focus=PRIMARY_GREEN,
            hint_text_color_focus=PRIMARY_GREEN,
            text_color_focus=PRIMARY_GREEN,
        )
        # Debounce on text field
        self.search.bind(text=self.on_search_text)
        self.root.add_widget(self.search)

        # List + Scroll text
        self.list_view = MDList()
        scroll = MDScrollView()
        scroll.add_widget(self.list_view)
        self.root.add_widget(scroll)

        self.add_widget(self.root)
    
    def on_search_text(self, instance, value) -> None:
        """
        Search engine text change callback with debounce.
        
        Parameters
        ----------
        instance: MDTextField
            The widget that triggered the callback
        value: str
            The new text value of the search field.
        """
        # Cancel any pending refreshments, if there are any.
        if self._search_event is not None:
            self._search_event.cancel()

        # Schedule a new refresh in 0.2 seconds.
        self._search_event: ClockEvent = Clock.schedule_once(self.refresh_list, 0.2)
    
    def _catalog_values(self) -> list[CatalogProduct]:
        """
        From the base catalog, return the list of products
        
        Returns
        -------
        list[CatalogProduct]
            List with all the base products
        """
        # Base catalog
        base: dict[str, CatalogProduct] = self.app.base_catalog
        return base.values()
        
    def refresh_list(self, *args) -> None:
        """
        Refresh the list based on the current search term.
        """
        term: str = (self.search.text or "").strip().lower()

        # Empty the MDList
        self.list_view.clear_widgets()
        # Add back only the items that match the search
        for prod in self._catalog_values():
            name: str = prod.name_es if self.app.lang == "es" else prod.name_en
            if term and term not in name.lower():
                continue

            # Retrieve the cached item
            item: OneLineAvatarIconListItem = self._items_by_id.get(prod.id)
            self.list_view.add_widget(item)
    
    # =============================================================================================
    # Pre enter
    # =============================================================================================
    
    def _get_icon_widget(self, prod: CatalogProduct) -> ImageLeftWidget:
        """
        Returns the icon widget for a product, caching it.
        If the widget already has a parent, we release it before adding
        it to another.
        
        Parameters
        ----------
        prod: CatalogProduct
            The product to get its icon
        
        Returns
        -------
        widget
        """
        widget: ImageLeftWidget | None = self._icon_cache.get(prod.id)
        # If not in cache, create it
        if widget is None:
            source: str = self.app.icon_path(prod.id)  # Icon path
            widget = ImageLeftWidget(source=source)  # Icon object
            self._icon_cache[prod.id] = widget  # Add to icon cache

        return widget
            
    def _create_item_for_product(self, prod: CatalogProduct) -> OneLineAvatarIconListItem:
        """
        Create a OneLineAvatarIconListItem for a specific product,
        reusing the icon if it's already cached.
        
        Parameters
        ----------
        prod: CatalogProduct
            Product from the catalog to be created
        
        Returns
        -------
        item: OneLineAvatarIconListItem

        """
        item = OneLineAvatarIconListItem(
            text=prod.name_es if self.app.lang == "es" else prod.name_en,
            on_release = lambda *_: self.select_catalog_product(prod.id))

        # Icon in cache
        icon_widget: ImageLeftWidget = self._get_icon_widget(prod)
        item.add_widget(icon_widget)

        return item
    
    def build_items_from_catalog(self):
        """
        Creates the items of the list for all the catalog products
        once.
        """
        # Clear widgets
        self._items_by_id.clear()
        self.list_view.clear_widgets()

        # Create item for each product and add to the list view
        for prod in self._catalog_values():
            item: OneLineAvatarIconListItem = self._create_item_for_product(prod)
            self._items_by_id[prod.id] = item
            self.list_view.add_widget(item)
            
    def on_pre_enter(self, *args) -> None:
        """
        After enter the screen, build all the items from the catalog
        and show them.
        """
        self.search.text = ""
 
        # Build all items (only once)
        if not self._items_by_id:
            self.build_items_from_catalog()

        # Show products
        self.refresh_list()

        return super().on_pre_enter(*args)
    
    # =============================================================================================
    # Select catalog product dialog
    # =============================================================================================
    
    def select_catalog_product(self, product_id: str) -> None:
        """
        Selects a product from catalog and adds to stock list.
        
        Parameters
        ----------
        product_id: str
            ID product
        """
        # If the product exists in stock, open edit dialog
        existing: StockEntry | None = find_stock(self.app, product_id)
        if existing:
            self.app.go("stock")
            self.app.root_widget.stock_screen.open_edit_dialog(existing)
            return

        prod: CatalogProduct = self.app.catalog[product_id]
        self.app._pending_product_id = product_id

        # Text field: price
        self.app._price_field = MDTextField(
            hint_text=self.app.t("add_product.edit.max_price"),
            input_filter="float",
            mode="rectangle",
            text=str(prod.default_max_price_per_1000 or 0),
            line_color_focus=PRIMARY_GREEN,
            hint_text_color_focus=PRIMARY_GREEN,
            text_color_focus=PRIMARY_GREEN,
        )
        content = MDBoxLayout(
            orientation="vertical",
            padding=(dp(20), dp(20), dp(20), dp(12)),
            spacing=dp(12),
            adaptive_height=True,
        )
        content.add_widget(self.app._price_field)

        # Buttons dialog
        cancel_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.cancel"),
            on_release=lambda *_: self.app._dialog.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        )
        add_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.add"),
            on_release=lambda *_: self.confirm_add_from_catalog(),
            md_bg_color=PRIMARY_GREEN,
            line_color=PRIMARY_GREEN,
            text_color = BLACK
        )
        self.app._dialog = MDDialog(
            title=self.app.t(
                "add_product.edit.title",
                value=prod.name_es if self.app.lang == "es" else prod.name_en
            ),
            type="custom",
            content_cls=content,
            size_hint=(0.92, None),
            height=dp(260),
            buttons=[cancel_btn, add_btn],
        )
        self.app._dialog.open()
    
    # =============================================================================================
    # Confirm add product from catalog
    # =============================================================================================

    def confirm_add_from_catalog(self) -> None:
        """
        Add an item from catalog to stock
        """
        pid: str = self.app._pending_product_id
        price: float = float(self.app._price_field.text or "0")

        # Add item to stock
        self.app.stock.append(
            StockEntry(
                product_id=pid,
                qty_l=0.0,
                max_price_per_1000=price,
                cap_per_trip_l=0.0,
                min_keep_l=0.0,
                enabled_for_optimization=True,
            )
        )

        # Close dialog, save and go to stock screen
        self.app._dialog.dismiss()
        self.app._invalidate_plan_and_save()
        self.app.go("stock")
        