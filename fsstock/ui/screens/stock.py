from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kivy.input.motionevent import MotionEvent
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import IconRightWidget, ImageLeftWidget, MDList, TwoLineAvatarIconListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.textfield import MDTextField

from fsstock.core.get_product_name import get_product_name
from fsstock.core.models import CatalogProduct, StockEntry 
from fsstock.core.money_value import money_value
from fsstock.ui.colors.colors import BG_DARK, BLACK, PRIMARY_GREEN, RED, WHITE

if TYPE_CHECKING:
    from fsstock.ui.app import FSStockApp
    
    
MODE_SORT_NAMES: dict[str, str] = {
    "added": "Añadido",
    "stock": "Stock",
    "money": "Dinero",
    "name": "Nombre",
}


class StockScreen(MDScreen):
    """
    Stock screen.
    Contains:
    - Top row: Total stock (€) + sort button
    - List of stock items (editable)
    """
    
    # =============================================================================================
    # Build
    # =============================================================================================
    
    
    def __init__(self, app: FSStockApp, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app: FSStockApp = app
        
        self.md_bg_color: str = BG_DARK  # Background color

        # Cache rows by product_id
        self._rows_by_product_id: dict[str, TwoLineAvatarIconListItem] = {}  

        # sort_mode: "added", "stock", "money", "name"
        self.sort_mode: str = "added"
        self.sort_ascending: bool = False  # by default: added (desc.)

        ## Layout
        self.layout = MDBoxLayout(
            orientation="vertical",
            padding=(dp(8), dp(8)),
            spacing=dp(8)
        )
        
        # Top row: Total + sort
        self.top_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_x=1,
            size_hint_y=None,
            height=dp(48),
            spacing=dp(6),
            padding=(dp(8), 0),
        )
        # Total (1 línea + ellipsis si hace falta)
        self.total_label = MDLabel(
            text="Total: 0 €",
            halign="left",
            valign="middle",
            font_style="H6",
            size_hint=(None, 1),
            max_lines=1,
            shorten=True,
            shorten_from="right",
        )
        self.top_row.add_widget(self.total_label)

        # Sort (icon + text) ancho fijo
        self.sort_area = MDBoxLayout(
            orientation="horizontal",
            size_hint=(None, 1),
            width=dp(200),
            spacing=dp(4),
        )
        self.sort_btn = MDIconButton(
            icon="sort",
            pos_hint={"center_y": 0.5},
            on_release=self.open_sort_menu,
        )
        self.sort_area.add_widget(self.sort_btn)

        self.sort_label = MDLabel(
            text="Añadido (desc.)",
            halign="left",
            valign="middle",
            size_hint=(None, 1),
            max_lines=1,
            shorten=True,
            shorten_from="right",
        )
        self.sort_label.bind(on_touch_down=self.sort_label_touch)
        self.sort_area.add_widget(self.sort_label)

        self.top_row.add_widget(self.sort_area)
        self.layout.add_widget(self.top_row)

        # Products list
        self.list_view = MDList()
        self.scroll = MDScrollView()
        self.scroll.add_widget(self.list_view)
        self.layout.add_widget(self.scroll)

        self.add_widget(self.layout)

        # Menú de ordenación
        self._sort_menu: MDDropdownMenu | None = None
        self._build_sort_menu()

        # Re-layout with change of width
        self.top_row.bind(width=self._relayout_top_row)
        self.sort_area.bind(width=self._relayout_top_row)
        
    def _build_sort_menu(self) -> None:
        """
        Builds the sort menu.
        """
        items: list[dict[str, Any]] = [
            self._sort_menu_item("Añadido (primero - último)", "added", True),
            self._sort_menu_item("Añadido (último - primero)", "added", False),
            self._sort_menu_item("Stock (menor - mayor)", "stock", True),
            self._sort_menu_item("Stock (mayor - menor)", "stock", False),
            self._sort_menu_item("Dinero (menor - mayor)", "money", True),
            self._sort_menu_item("Dinero (mayor - menor)", "money", False),
            self._sort_menu_item("Nombre (A - Z)", "name", True),
            self._sort_menu_item("Nombre (Z - A)", "name", False),
        ]
        self._sort_menu = MDDropdownMenu(
            caller=self.sort_btn,
            items=items,
            width_mult=4,
        )
    
    def _sort_menu_item(self, text: str, mode: str, asc: bool) -> dict[str, Any]:
        """
        Given a text (str), a sort mode (str) and if it is ascending
        (bool), returns a dictionary with the information of the sort button.
        
        Parameters
        ----------
        text: str
            Button text
        mode: str
            Sort mode ("added", "stock", "money" or "name")
        asc: bool
            If sorting is ascending (True) or not (False)
        
        Returns
        -------
        dict[str, Any]
            Dictionary with two entries, representing the buttons of
            the menu:
            - text: str
                Button text
            - on_release: Callable[[str, bool], None]
                Function to sort the products according to the sort
                mode and the order.
        """
        return {
            "text": text,
            "on_release": lambda m=mode, a=asc: self.set_sort(m, a),
        }
    
    def _build_row(self, entry: StockEntry) -> TwoLineAvatarIconListItem:
        """
        Builds the row for an entry in the stock screen.
        
        Parameters
        ----------
        entry: StockEntry
            Item in stock to be added (editable)
        
        Returns
        -------
        row: TwoLineAvatarIconListItem
            Element (row) in the list
        """
        row = TwoLineAvatarIconListItem()

        icon_path: str = self.app.icon_path(entry.product_id)
        row.add_widget(ImageLeftWidget(source=icon_path))

        right = IconRightWidget(
            icon="pencil",
            on_release = lambda *_, e=entry: self.open_edit_dialog(e))
        row.add_widget(right)
        row.on_release = (lambda *_, e=entry: self.open_edit_dialog(e))
        
        return row
    
    # =============================================================================================
    # Sort menu
    # =============================================================================================
        
    def open_sort_menu(self, *args) -> None:
        """
        Open the sort menu.
        """
        if self._sort_menu:
            self._sort_menu.open()
    
    def sort_label_touch(self, instance: MDLabel, touch: MotionEvent) -> bool:
        """
        Open the sort menu when touching the label. If the touch
        position is inside instance, open the sort menu and consume
        the event.

        Parameters
        ----------
        instance: MDLabel
            The widget receiving the touch event: sort_label
        touch: MotionEvent
            The touch/mouse event.

        Returns
        -------
        bool: 
            True if the touch was handled (event consumed), False
            otherwise.
        """
        if instance.collide_point(*touch.pos):
            self.open_sort_menu()
            return True
        return False
    
    def set_sort(self, mode: str, ascending: bool) -> None:
        """
        Given the sort mode and the order, gives the new label sort.
        Finally, refreshes the screen.
        
        Parameters
        ----------
        mode: str
            Sort mode ("added", "stock", "money" or "name")
        ascending: bool
            If sorting is ascending (True) or not (False)
        """
        self.sort_mode = mode
        self.sort_ascending = ascending
        
        mode_name: str = MODE_SORT_NAMES[mode]

        order = "asc." if ascending else "desc."
        self.sort_label.text = f"{mode_name} ({order})"

        if self._sort_menu:
            self._sort_menu.dismiss()

        self.refresh()
    
    def _sorted_entries(self) -> list[StockEntry]:
        """
        Returns the sorted list of products.
        
        Returns
        -------
        entries: list[StockEntry]
            Sorted list of products in stock
        """
        entries: list[StockEntry] = self.app.stock

        # Sort according to added time
        if self.sort_mode == "added":
            return entries if self.sort_ascending else reversed(entries)
        # Sort according to amount (L)
        if self.sort_mode == "stock":
            entries.sort(key=lambda e: e.qty_l, reverse=not self.sort_ascending)
            return entries
        # Sort according to earnings (€)
        if self.sort_mode == "money":
            entries.sort(
                key=lambda e: money_value(e.qty_l, e.max_price_per_1000),
                reverse=not self.sort_ascending,
            )
            return entries
        # Sort according to alphabetic order
        if self.sort_mode == "name":
            entries.sort(
                key=lambda x: get_product_name(x.product_id, self.app.catalog),
                reverse=not self.sort_ascending
            )
            return entries

        return entries

    # =============================================================================================
    # Edit product
    # =============================================================================================
    
    def open_edit_dialog(self, entry: StockEntry) -> None:
        """
        Open the dialog to edit a product in stock
        
        Parameters
        ----------
        entry: StockEntry
            The product to be modified
        """
        # Title
        self.app._edit_entry = entry
        title: str = f"Editar: {get_product_name(entry.product_id, self.app.catalog)}"

        # Textfields
        self.app._qty_field = MDTextField(
            hint_text="Cantidad (L)",
            input_filter="float",
            mode="rectangle",
            text=str(entry.qty_l),
            line_color_focus=PRIMARY_GREEN,
            hint_text_color_focus=PRIMARY_GREEN,
            text_color_focus=PRIMARY_GREEN,
        )
        self.app._price_field = MDTextField(
            hint_text="Precio máx (€/1000L)",
            input_filter="float",
            mode="rectangle",
            text=str(entry.max_price_per_1000),
            line_color_focus=PRIMARY_GREEN,
            hint_text_color_focus=PRIMARY_GREEN,
            text_color_focus=PRIMARY_GREEN,
        )
        self.app._cap_field = MDTextField(
            hint_text="Capacidad por viaje (L)",
            input_filter="float",
            mode="rectangle",
            text=str(entry.cap_per_trip_l),
            line_color_focus=PRIMARY_GREEN,
            hint_text_color_focus=PRIMARY_GREEN,
            text_color_focus=PRIMARY_GREEN,
        )
        self.app._min_keep_field = MDTextField(
            hint_text="Stock mínimo a mantener (L)",
            input_filter="float",
            mode="rectangle",
            text=str(entry.min_keep_l),
            line_color_focus=PRIMARY_GREEN,
            hint_text_color_focus=PRIMARY_GREEN,
            text_color_focus=PRIMARY_GREEN,
        )
        
        # Checkbox + label
        toggle_row = MDBoxLayout(
            size_hint_y=None,
            height=dp(40),
            spacing=dp(12),
            padding=(0, dp(6)),
        )
        toggle_row.add_widget(MDLabel(text="Usar en optimización", halign="left"))

        self.app._enabled_toggle = MDCheckbox(
            active=bool(entry.enabled_for_optimization),
            size_hint = (None, None),
            size = (dp(48), dp(48)),
        )
        self.app._enabled_toggle.color_active = PRIMARY_GREEN
        toggle_row.add_widget(self.app._enabled_toggle)

        content = MDBoxLayout(
            orientation="vertical",
            padding=(dp(20), dp(20), dp(20), dp(12)),
            spacing=dp(12),
            adaptive_height=True,
        )
        content.add_widget(self.app._qty_field)
        content.add_widget(self.app._price_field)
        content.add_widget(self.app._cap_field)
        content.add_widget(self.app._min_keep_field)
        content.add_widget(toggle_row)

        # Buttons
        delete_btn = MDRectangleFlatButton(
            text="Eliminar",
            on_release=lambda *_: self._ask_delete_current(),
            md_bg_color=RED,
            line_color=RED,
            text_color=WHITE
        )
        cancel_btn = MDRectangleFlatButton(
            text="Cancelar",
            on_release=lambda *_: self.app._dialog.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        )
        save_btn = MDRectangleFlatButton(
            text="Guardar",
            on_release=lambda *_: self._confirm_edit(),
            md_bg_color=PRIMARY_GREEN,
            line_color=PRIMARY_GREEN,
            text_color=BLACK
        )
        
        self.app._dialog = MDDialog(
            title=title,
            type="custom",
            content_cls=content,
            size_hint=(0.92, None),
            height=dp(520),
            buttons=[delete_btn, cancel_btn, save_btn],
        )
        self.app._dialog.open()
    
    def _confirm_edit(self):
        """
        Confirms and saves the edited product from stock
        """
        qty: float = float(self.app._qty_field.text or "0")
        price: float = float(self.app._price_field.text or "0")
        cap: float = float(self.app._cap_field.text or "0")
        min_keep: float = float(self.app._min_keep_field.text or "0")
        enabled: bool = bool(getattr(self.app._enabled_toggle, "active", True))

        # Normalization (non negatives)
        qty: float = max(qty, 0.0)
        price: float = max(price, 0.0)
        cap: float = max(cap, 0.0)
        min_keep: float = max(min_keep, 0.0)

        self.app._edit_entry.qty_l = qty
        self.app._edit_entry.max_price_per_1000 = price
        self.app._edit_entry.cap_per_trip_l = cap
        self.app._edit_entry.min_keep_l = min_keep
        self.app._edit_entry.enabled_for_optimization = enabled

        self.app._dialog.dismiss()
        self.app._invalidate_plan_and_save()
        self.refresh()
    
    # =============================================================================================
    # Delete product
    # =============================================================================================
        
    def _ask_delete_current(self) -> None:
        """
        Ask to confirm delete of an item in stock
        """
        self.app._dialog.dismiss()
        name: str = get_product_name(self.app._edit_entry.product_id, self.app.catalog)

        cancel_btn = MDRectangleFlatButton(
            text="Cancelar",
            on_release=lambda *_: self.app._confirm_dialog.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        )
        delete_btn = MDRectangleFlatButton(
            text="Eliminar",
            on_release=lambda *_: self._delete_current(),
            md_bg_color=RED,
            line_color=RED,
            text_color=WHITE
        )
        self.app._confirm_dialog = MDDialog(
            title="Eliminar del stock",
            text=f"¿Seguro que quieres eliminar '{name}' del stock?",
            buttons=[cancel_btn, delete_btn],
        )
        self.app._confirm_dialog.open()
    
    def _delete_current(self):
        """
        Delect the current item from stock
        """
        pid: str = self.app._edit_entry.product_id
        self.app.stock = [e for e in self.app.stock if e.product_id != pid]
        # If custom, also remove from user catalog
        if pid.startswith("u_"):
            self.app.user_catalog.pop(pid, None)
            self.app.catalog.pop(pid, None)  
            
        self.app._confirm_dialog.dismiss()
        self.app._invalidate_plan_and_save()
        self.app.go("stock")
    
    def delete_entry(self, entry: StockEntry) -> None:
        """
        Delete entry when is completely consumed by the trip plan.
        
        Parameters
        ----------
        entry: StockEntry

        """
        self.app.stock = [e for e in self.app.stock if e.product_id != entry.product_id]
        # If custom, also remove from user catalog
        if entry.product_id.startswith("u_"):
            self.user_catalog.pop(entry.product_id, None)
            self.catalog.pop(entry.product_id, None)
    
    # =============================================================================================
    # Refresh
    # =============================================================================================
        
    def refresh(self):
        """
        Refreshes the stock screen:
        - Calculates the total
        - Rearanges the items in the products list
        """
        self.list_view.clear_widgets()
        total: float = 0.0
        for entry in self._sorted_entries():
            pid: str = entry.product_id
            row: TwoLineAvatarIconListItem | None = self._rows_by_product_id.get(pid)
            if row is None:
                row = self._build_row(entry)
                self._rows_by_product_id[pid] = row

            total += self._update_row_labels(row, entry)
            self.list_view.add_widget(row)

        self.total_label.text = f"Total: {total:,.0f} €"
        self._relayout_top_row()
    
    def _update_row_labels(self, row: TwoLineAvatarIconListItem, entry: StockEntry) -> float:
        """
        Updates the row text of an entry in the stock and returns the
        corresponding value (in €).
        
        Parameters
        ----------
        row: TwoLineAvatarIconListItem
            Row to be updated
        entry: StockEntry
            Stock entry to be updated
        
        Returns
        -------
        val: float
            The money value of the product (€)
        """
        prod: CatalogProduct = self.app.catalog[entry.product_id]
        name: str = prod.name_es if prod else entry.product_id

        val: float = money_value(entry.qty_l, entry.max_price_per_1000)

        row.text = f"{name}  —  {val:,.0f} €"
        row.secondary_text = (
            f"Qty: {entry.qty_l:,.0f} L | "
            f"Máx: {entry.max_price_per_1000:g} €/1000L"
        )
        return val
    
    # =============================================================================================
    # Relayout 
    # =============================================================================================

    def _relayout_top_row(self, *args) -> None:
        """
        Recalculates the widths and text size of the total and sort
        block to avoid overlaps.
        
        Dynamically adjusts the available space in the top row so that
        total_label and the sort area coexist without overlapping:
        - if the total text fits, its natural width is used to keep the
        sort "attached";
        - otherwise, it is limited to the available width and the label
        is cropped with "...".
        
        It also calculates the usable width of the sort text
        (subtracting button and spacing) and applies minimums to ensure
        readability.
        """
        # maximum space that the total can use without stepping on the sort
        avail: float = (
            self.top_row.width \
            - self.sort_area.width \
            - self.top_row.spacing \
            - self._pad_x_total()
        )
        if avail < dp(120):
            avail = dp(120)

        # REAL natural width of the total (without shortening)
        natural_total: float = self._measure_text_width_no_shorten(self.total_label) + dp(2)

        # If possible, we use natural width (so that the sort is 
        # attached);
        # If it doesn't fit, we use the available option and the label
        # is cropped with "..."
        total_w: float = min(avail, natural_total)
        if total_w < dp(80):
            total_w = dp(80)

        self.total_label.width = total_w
        self.total_label.text_size = (total_w, None)

        # text width inside sort_area
        sort_text_w = self.sort_area.width - self.sort_btn.width - self.sort_area.spacing
        if sort_text_w < dp(60):
            sort_text_w = dp(60)

        self.sort_label.width = sort_text_w
        self.sort_label.text_size = (sort_text_w, None)
        
    def _pad_x_total(self) -> float:
        """
        Returns the total horizontal padding (left + right) of
        top_row.
        Interprets self.top_row.padding according to Kivy's standard
        formats:
        - (x, y) -> uses x on both sides (2*x)
        - (l, t, r, b) -> sums l + r
        - If the padding is not a sequence or does not have a
        recognized format, returns 0.0.

        Returns
        -------
        float
            Sum of the horizontal padding
        """
        pad = self.top_row.padding
        if isinstance(pad, (list, tuple)):
            if len(pad) == 2:
                return float(pad[0]) * 2.0
            if len(pad) == 4:
                return float(pad[0]) + float(pad[2])
        return 0.0
    
    def _measure_text_width_no_shorten(self, lbl: MDLabel) -> float:
        """
        Measure the actual width of the text without being affected by
        shortening/text_size.
        This prevents the 'Total: ...' bug even when there is space.
        
        Parameters
        ----------
        lbl: MDLabel
            Total label
        
        Returns
        -------
        float
            The actual width of the text
        """
        old_shorten = getattr(lbl, "shorten", False)
        old_text_size = getattr(lbl, "text_size", (None, None))
        try:
            lbl.shorten = False
            lbl.text_size = (None, None)
            lbl.texture_update()
            return float(lbl.texture_size[0])
        finally:
            lbl.text_size = old_text_size
            lbl.shorten = old_shorten
