from kivy.clock import Clock
from kivymd.app import MDApp

from fsstock.core.catalog import load_catalog
from fsstock.core.models import CatalogProduct, StockEntry, TripPlan, FarmData
from fsstock.core.paths import icons_dir, custom_icon_path
from fsstock.core.storage import load_state, save_state

from .root import RootLayout
from .screens.add_product import AddProductScreen


class FSStockApp(MDApp):
    """
    Main application for FS Stock.

    Manages the app lifecycle, screen navigation, and persistent farm
    status (multi-farm): base catalog + custom products, stock, and
    latest sales plan/target.

    Additionally, it coordinates long-running operations (e.g., PDF 
    export) in the background and securely updates the UI using Clock.
    """
    
    # =============================================================================================
    # Build
    # =============================================================================================
    
    def build(self) -> RootLayout:
        """
        Builds the application:
        - Sets the style
        - Load the icon path, the dictionary of farms and the catalog
        - Creates the Root Layout
        
        Returns
        -------
        self.root_widget: RootLayout
            Root layout containing the screen manager, screens, top bar,
            navigation bar, and the FAB.
        """
        
        self.farms: dict[str, FarmData]
        self.current_farm_id: str
        
        # Dark theme style: black background + white text
        self.theme_cls.theme_style = "Dark"
        
        # Load catalog 
        self.catalog: dict[str, CatalogProduct] = load_catalog()

        # Icon path cache (avoids recomputing the path on each render)
        self.build_icon_path_cache()

        # Load multi-farm state
        self.farms, self.current_farm_id = load_state(self.user_data_dir)
        self.base_catalog: dict[str, CatalogProduct] = load_catalog()
        # Farm catalog: completed after loading farm
        self.catalog: dict[str, CatalogProduct] = dict(self.base_catalog)  

        # Create Root
        self.root_widget = RootLayout(self)

        # Load farm and save
        self._load_current_farm()
        self._save_state()

        # Pre-load catalog screen
        Clock.schedule_once(self._preload_add_product_screen, 0)

        # Main screen: "stock"
        self.go("stock")
        
        return self.root_widget
    
    # ---------------------------------------------------------------------------------------------
    # Load and save farm
    # ---------------------------------------------------------------------------------------------
    
    def _load_current_farm(self) -> None:
        """
        Loads current farm.
        """
        f: FarmData = self.farms[self.current_farm_id]
        self.farm_name: str = f.name
        self.stock: list[StockEntry] = f.stock
        self.last_plan: TripPlan | None = f.last_plan
        
        self.user_catalog: dict[str, CatalogProduct] = {}
        ups: list[CatalogProduct] = f.user_products or []
        for p in ups:
            self.user_catalog[p.id] = p

        # merge
        self.catalog: dict[str, CatalogProduct] = dict(self.base_catalog)
        self.catalog.update(self.user_catalog)
        
        # Remade stock lines
        self.root_widget.stock_screen._rows_by_product_id = {}
        
    def _persist_current_farm(self)-> None:
        """
        Saves the current farm last data into self.farms
        """
        self.farms[self.current_farm_id] = FarmData(
            name=self.farm_name,
            stock=self.stock,
            last_plan=self.last_plan,
            user_products=list(self.user_catalog.values()),
        )
    
    def _invalidate_plan_and_save(self) -> None:
        """
        Remove objective plan, if it exists and saves
        """
        self.last_plan = None
        self._save_state()
        
    def _save_state(self) -> None:
        """
        Save the state of the application
        """
        self._persist_current_farm()
        save_state(self.user_data_dir, self.farms, self.current_farm_id)
    
    def _preload_add_product_screen(self, dt) -> None:
        """
        Preloads the add product screen.
        """
        scr: AddProductScreen = self.root_widget.add_screen
        scr.build_items_from_catalog()
    
    # -----------------------------
    # Icon paths cache
    # -----------------------------
    def build_icon_path_cache(self) -> None:
        """
        Builds the icon path cache
        """
        self._icon_path_cache: dict[str, str] = {}
        for pid, prod in self.catalog.items():
            if prod and getattr(prod, "icon", ""):
                self._icon_path_cache[pid] = str(icons_dir() / prod.icon)
            else:
                self._icon_path_cache[pid] = ""
    
    def icon_path(self, product_id: str) -> str:
        """
        Gives the icon file of a product, given its ID.
        
        Parameters
        ----------
        product_id: str
            Product ID
        
        Returns
        -------
        str:
            Icon file
        """
        # Custom product -> custom.png
        if product_id.startswith("u_"):
            return str(custom_icon_path())

        # Base product -> file from catalog
        return self._icon_path_cache[product_id]
    
    # =============================================================================================
    # Move screen
    # =============================================================================================
    
    def go(self, screen_name: str) -> None:
        """
        Move to the given screen.
        
        Parameters
        ----------
        screen_name: str
            The destination screen name
        """
        self.root_widget.sm.current = screen_name
        
        # Change active bottom in navigation bar
        if screen_name in ("stock", "objective", "settings"):
            self.root_widget.bottom_nav.set_active(screen_name)

        # Screen title
        self.root_widget.topbar.title = self.root_widget.screen_titles[screen_name]

        # Arrow left (from "add_product" to "stock")
        if screen_name == "add_product":
            self.root_widget.topbar.left_action_items = [
                ["arrow-left", lambda *_: self.go("stock")],
            ]
        else:
            self.root_widget.topbar.left_action_items = []

        # FAB
        if screen_name == "stock":  # FAB to add product
            self.root_widget._set_fab(visible=True, handler=self.root_widget._fab_go_add_product)
            self.root_widget.stock_screen.refresh()
        elif screen_name == "add_product":  # FAB to create product
            self.root_widget._set_fab(visible=True, handler=self.root_widget._fab_add_custom_product)
        else:
            self.root_widget._set_fab(visible=False, handler=None)
            
        if screen_name == "objective" and not self.last_plan: # Refresh last plan
            self.root_widget.objective_screen.refresh()
        
        if screen_name == "settings":
            self.root_widget.settings_screen.refresh()
    
    # =============================================================================================
    # Stop
    # =============================================================================================
        
    def on_stop(self) -> None:
        """
        When stopping the application, save the data.
        """
        self._save_state()
