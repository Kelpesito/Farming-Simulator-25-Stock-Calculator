from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.list import ImageLeftWidget, MDList, TwoLineAvatarIconListItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField

from fsstock.core.models import OptProduct, StockEntry, TripPlan
from fsstock.core.find_stock import find_stock
from fsstock.core.get_product_name import get_product_name
from fsstock.core.optimizer import optimize_min_trips  
from fsstock.ui.colors.colors import BG_DARK, PRIMARY_GREEN

if TYPE_CHECKING:
    from fsstock.ui.app import FSStockApp


class ObjectiveScreen(MDScreen):
    """
    Objective screen.
    Input an objective value to sell (€).
    The program calculates what to sell in order to minimize the number
    of trips. In case there exist many possibilities with the minimum
    number of trips, the final stock of the involved products is
    maximized.
    """
    
    # =============================================================================================
    # Build
    # =============================================================================================
    
    def __init__(self, app: FSStockApp, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app: FSStockApp = app
        
        self.md_bg_color: str = BG_DARK  # Background color

        # Layout (label + textfield)
        self.root = MDBoxLayout(orientation="vertical", padding=(dp(12), dp(12)), spacing=dp(12))

        self.info = MDLabel(
            text="Introduce una cuota (€) y pulsa Calcular.",
            halign="left",
            size_hint_y=None,
            height=dp(24)
        )
        self.root.add_widget(self.info)

        self.target_field = MDTextField(
            hint_text="Cuota objetivo (€)",
            input_filter="float",
            mode="rectangle",
            line_color_focus=PRIMARY_GREEN,
            hint_text_color_focus=PRIMARY_GREEN,
            text_color_focus=PRIMARY_GREEN,
        )
        self.root.add_widget(self.target_field)

        # Buttons
        buttons = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(12))
        self.calc_btn = MDRectangleFlatButton(
            text="Calcular",
            on_release=lambda *_: self.on_calculate(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        )
        self.apply_btn = MDRectangleFlatButton(
            text="Aplicar plan",
            disabled=True,
            on_release=lambda *_: self.on_apply(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        )
        buttons.add_widget(self.calc_btn)
        buttons.add_widget(self.apply_btn)
        self.root.add_widget(buttons)

        # Summary plan + list
        self.summary = MDLabel(text="", halign="left", size_hint_y=None, height=dp(24))
        self.root.add_widget(self.summary)

        self.list_view = MDList()
        scroll = MDScrollView()
        scroll.add_widget(self.list_view)
        self.root.add_widget(scroll)

        self.add_widget(self.root)
    
    def on_calculate(self) -> None:
        """
        Calculates the trip plan, given the target €, and shows it.
        """
        target: float = float(self.target_field.text or "0")
        plan: TripPlan = self.calculate_objective_plan(target)
        self.show_plan(plan)
        
    def show_plan(self, plan) -> None:
        """
        Given the trip plan, shows it in the screen
        
        Parameters
        ----------
        plan: TripPlan
            The trip plan
        """
        self.list_view.clear_widgets()

        # If the plan is not feasible, show why
        if not plan.feasible:
            self.apply_btn.disabled = True
            self.summary.text = ""
            self.info.text = plan.reason
            return
        
        # If the plan is feasible
        self.apply_btn.disabled = False  # Enable apply plan button
        self.info.text = "Plan calculado. Revisa y aplica si quieres."

        self.summary.text = (
            f"Viajes: {plan.total_trips} | "
            f"Ingreso: {plan.total_revenue_eur:,.0f} € "
            f"(objetivo: {plan.target_eur:,.0f} €)"
        )
        # Build the list lines
        for line in plan.lines:
            name: str = get_product_name(line.product_id, self.app.catalog)
            trips: int = line.full_trips + (1 if line.last_partial_used else 0)

            row = TwoLineAvatarIconListItem(
                text=f"{name} — {trips} viaje(s) — {line.revenue_eur:,.0f} €",
                secondary_text=f"Vender: {line.sold_l:g} L",
            )
            row.add_widget(ImageLeftWidget(source=self.app.icon_path(line.product_id)))
            self.list_view.add_widget(row)

    def on_apply(self) -> None:
        """
        Apply plan to stock
        """
        ok: bool
        msg: str
        ok, msg = self.apply_last_plan()
        # feedback simple
        self.info.text = msg
        if ok:
            self.apply_btn.disabled = True
            self.list_view.clear_widgets()
            self.summary.text = ""
    
    # =============================================================================================
    # Pre enter
    # =============================================================================================

    def on_pre_enter(self, *args) -> None:
        """
        Show plan if exists
        """
        plan: TripPlan | None = self.app.last_plan
        if plan:
            self.show_plan(plan)
        return super().on_pre_enter(*args)
    
    # =============================================================================================
    # Refresh
    # =============================================================================================
    
    def refresh(self) -> None:
        """
        Refresh page in case there is not a plan
        """
        self.list_view.clear_widgets()
        self.summary.text = ""
        self.info.text = "Introduce una cuota (€) y pulsa Calcular."
        self.apply_btn.disabled = True
        
    # =============================================================================================
    # Calculate objective plan
    # =============================================================================================
    
    def calculate_objective_plan(self, target_eur: float) -> TripPlan:
        """
        Gets the target revenue and designs a trip plan.
        
        Parameters
        ----------
        target_eur: float
            The target revenue
        
        Returns
        -------
        TripPlan:
            The trip plan
        """
        # 0 or negative: not selected plan
        if target_eur <= 0.0:
            self.app.last_plan = None
            self.app._save_state()
            return TripPlan(
                feasible=False,
                target_eur=target_eur,
                total_revenue_eur=0.0,
                total_trips=0,
                lines=[],
                reason="No se ha seleccionado plan",
            )

        # Optimization products: StockEntry -> OptProduct
        opt_products: list[OptProduct] = []
        for e in self.app.stock:
            opt_products.append(
                OptProduct(
                    product_id=e.product_id,
                    stock_l=e.qty_l,
                    min_keep_l=e.min_keep_l,
                    cap_per_trip_l=e.cap_per_trip_l,
                    price_per_1000=e.max_price_per_1000,
                    enabled=e.enabled_for_optimization,
                )
            )

        # Optimization
        plan = optimize_min_trips(opt_products, target_eur)

        # If plan is feasible, save it
        # Otherwise, not.
        if plan.feasible:
            self.app.last_plan = plan
            self.app._save_state()
        else:
            self.app.last_plan = None
            self.app._save_state()

        return plan

    # =============================================================================================
    # Apply plan
    # =============================================================================================
    
    def apply_last_plan(self) -> tuple[bool, str]:
        """
        Apply the saved plan to stock
        
        Returns
        -------
        bool:
            If there is a feasible plan
        str:
            Message to show
        """
        # If there is no plan
        if not self.app.last_plan:
            return False, "No hay plan para aplicar."

        plan: TripPlan | None = self.app.last_plan
        for line in plan.lines:
            entry: StockEntry | None = find_stock(self.app, line.product_id)
            if not entry:
                continue

            new_qty: float = entry.qty_l - line.sold_l
            entry.qty_l = new_qty
            if new_qty == 0.0:
                self.app.root_widget.stock_screen.delete_entry(entry)

        self.app.last_plan = None
        self.app._save_state()
        self.app.go("stock")
        return True, "Plan aplicado: stock actualizado."
    