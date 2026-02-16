from __future__ import annotations

from typing import Any, Callable, Self, TYPE_CHECKING
from uuid import uuid4

from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFloatingActionButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar

from .screens.stock import StockScreen
from .screens.add_product import AddProductScreen
from .screens.objective import ObjectiveScreen
from .screens.settings import SettingsScreen
from .widgets.navigation_bar import BottomNavigationBar
from .colors.colors import PRIMARY_GREEN, BLACK

from fsstock.core.models import CatalogProduct, StockEntry

if TYPE_CHECKING:
    from .app import FSStockApp


class RootLayout(MDBoxLayout):
    """
    Main root layout of application.
    Contains:
    - Top bar
    - Screen Manager
    - Screens: "stock", "add_product", "objective", "settings"
    - Floating Action Button (FAB)
    - Navigation bar
    """
    
    # =============================================================================================
    # Build
    # =============================================================================================
    
    def __init__(self, app: FSStockApp, **kwargs) -> None:
        """
        Parameters
        ----------
        app: FSStockApp
            Main application for FS Stock.
        """
        super().__init__(orientation="vertical", **kwargs)
        self.app: FSStockApp = app

        # Topbar
        self.topbar = MDTopAppBar(
            title="Stock",
            elevation=2,
            md_bg_color=PRIMARY_GREEN,
        )
        self.topbar.specific_text_color = BLACK
        self.add_widget(self.topbar)

        # Center Layout
        self.center_area = MDRelativeLayout()
        self.add_widget(self.center_area)

        # Screens
        self.sm = ScreenManager()
        self.stock_screen = StockScreen(app, name="stock")
        self.add_screen = AddProductScreen(app, name="add_product")
        self.objective_screen = ObjectiveScreen(app, name="objective")
        self.settings_screen = SettingsScreen(app, name="settings")
        self.screen_titles = {
            "stock": "Stock",
            "add_product": "Añadir producto",
            "objective": "Objetivo",
            "settings": "Ajustes",
        }

        self.sm.add_widget(self.stock_screen)
        self.sm.add_widget(self.add_screen)
        self.sm.add_widget(self.objective_screen)
        self.sm.add_widget(self.settings_screen)
        
        self.center_area.add_widget(self.sm)

        # FAB
        self.fab = MDFloatingActionButton(
            icon="plus",
            md_bg_color=PRIMARY_GREEN,
            icon_color=BLACK,
            on_release=lambda *_: app.go("add_product")
        )
        self.center_area.add_widget(self.fab)
        self.center_area.bind(size=self._position_fab, pos=self._position_fab)
        self._position_fab()

        # Navigation bar
        self.bottom_nav = BottomNavigationBar(app)
        self.add_widget(self.bottom_nav)

    # =============================================================================================
    # FAB handlers
    # =============================================================================================
    
    def _position_fab(self, *_) -> None:
        """
        Define the FAB position:
        X = Screen width - FAB width - margin
        Y = margin
        
        margin = 30 dp
        """
        margin: float = dp(30)
        self.fab.x = self.center_area.width - self.fab.width - margin
        self.fab.y = margin
    
    def _set_fab(
        self,
        *,
        visible: bool,
        handler: Callable[[Self, Any], None] | None = None
    ) -> None:
        """
        Creates or hides the Floating Action Button and binds action
        
        Parameters
        """
        fab: MDFloatingActionButton = self.fab

        # Erase the last handler
        old: Callable[[Self, Any], None] | None = getattr(self, "_fab_handler", None)
        if old is not None:
            fab.unbind(on_release=old)

        # Bind action to FAB
        self._fab_handler: Callable[[Self, Any], None] | None = handler
        if handler is not None:
            fab.bind(on_release=handler)

        # Shows or hides FAB
        fab.opacity = 1 if visible else 0
        fab.disabled = not visible
        
    # =============================================================================================
    # Add product
    # =============================================================================================
    
    def _fab_go_add_product(self, *args):
        """
        Go to "add_product" screen
        """
        self.app.go("add_product")
    
    # =============================================================================================
    # Create custom product
    # =============================================================================================
        
    def _fab_add_custom_product(self, *args) -> None:
        """
        Go to request adding a custom product with the name in the
        search field.
        """
        prefill: str = (self.add_screen.search.text or "").strip()
        self.request_add_custom_product(prefill)
    
    def request_add_custom_product(self, prefill_name: str = "") -> None:
        """
        Asks for a new product to introduce (name + price) and creates it.
        
        Parameters
        ----------
        prefill_name: str
            Name of the product, if it has been searched
        """
        # Textfields
        name_field = MDTextField(
            hint_text="Nombre del producto",
            mode="rectangle",
            text=prefill_name,
            line_color_focus=PRIMARY_GREEN,
            hint_text_color_focus=PRIMARY_GREEN,
            text_color_focus=PRIMARY_GREEN,
        )
        price_field = MDTextField(
            hint_text="Precio máx (€/1000L)",
            mode="rectangle",
            input_filter="float",
            text="0",
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
        content.add_widget(name_field)
        content.add_widget(price_field)

        # Buttons 
        cancel_btn = MDRectangleFlatButton(
            text="Cancelar",
            on_release=lambda *a: dlg.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN,
        )
        create_btn = MDRectangleFlatButton(
            text="Crear",
            on_release=lambda *_: self.create_custom_product(name_field, price_field, dlg),
            md_bg_color=PRIMARY_GREEN,
            line_color=PRIMARY_GREEN,
            text_color=BLACK
        )
        dlg = MDDialog(
            title="Añadir producto manual",
            type="custom",
            content_cls=content,
            size_hint=(0.92, None),
            height=dp(320),
            buttons=[cancel_btn, create_btn],
        )
        dlg.open()
    
    def create_custom_product(
        self,
        name_field: MDTextField,
        price_field: MDTextField,
        dlg: MDDialog,
        *args
    ) -> None:
        """
        Creates a custom products and introduces it in the stock list.
        
        Parameters
        ----------
        name_field: MDTextField
            Text field including the name of the new product
        prince_field: MDTextField
            Text field including the price of the new product
        dlg: MDDialog
            Dialog containing the buttons create product or cancel
        """
        # If name is empty, do not do anything
        name: str = (name_field.text or "").strip()
        if not name:
            return

        price: float = float(price_field.text or "0")

        # New ID
        pid: str = "u_" + uuid4().hex[:8]

        # New Catalog Product
        prod = CatalogProduct(
            id=pid,
            name_es=name,
            name_en=name,
            icon="custom.png",
            default_max_price_per_1000=price,
        )

        # Save in user catalog (current farm)
        self.app.user_catalog[pid] = prod
        self.app.catalog = self.app.base_catalog
        self.app.catalog.update(self.app.user_catalog)

        # Create new stock entry
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

        dlg.dismiss()
        self.app._invalidate_plan_and_save()
        self.app.go("stock")
