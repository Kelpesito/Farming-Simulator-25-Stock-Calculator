from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDIcon, MDLabel

from fsstock.ui.colors.colors import PRIMARY_GREEN

if TYPE_CHECKING:
    from fsstock.ui.app import FSStockApp


class BottomNavItem(ButtonBehavior, MDBoxLayout):
    """
    Item in the Navigation Bar.
    """
    def __init__(
        self,
        key: str,
        icon: str,
        text: str,
        on_select: Callable[[str], None],
        **kwargs
    ) -> None:
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(60),
            padding=(0, dp(6), 0, dp(6)),
            spacing=dp(0),
            **kwargs,
        )
        self.key: str = key
        self._on_select: Callable[[str], None] = on_select

        # Centered icon
        self.icon = MDIcon(
            icon=icon,
            font_size=sp(22),
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            halign="center",
            valign="middle",
        )
        self.icon.text_size = self.icon.size

        icon_wrap = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(1, None),
            height=dp(32),
        )
        icon_wrap.add_widget(self.icon)

        self.label = MDLabel(
            text=text,
            font_size=sp(12),
            halign="center",
            size_hint=(1, None),
            height=dp(16),
        )
        self.label.bind(size=lambda inst, *_: setattr(inst, "text_size", (inst.width, None)))

        self.add_widget(icon_wrap)
        self.add_widget(self.label)

        self.set_active(False)

    def set_active(self, active: bool) -> None:
        """
        Set the item active or inactive.
        
        Parameters
        ----------
        active: bool
            If we want to set the item active
        """
        primary: str = PRIMARY_GREEN
        inactive: tuple[float, float, float, float] = (1., 1., 1., 0.6)

        col: str | tuple[float, float, float, float] = primary if active else inactive
        for w in (self.icon, self.label):
            w.theme_text_color = "Custom"
            w.text_color = col
    
    def on_press(self) -> None:
        """
        When pressing the item, select it.
        """
        self._on_select(self.key)


class BottomNavigationBar(MDBoxLayout):
    """
    Bottom Navigation Bar.
    Used to change screen.
    The current screen is selected
    """
    
    # =============================================================================================
    # Build
    # =============================================================================================
    
    def __init__(self, app: FSStockApp, **kwargs) -> None:
        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(60),
            padding=(dp(8), 0, dp(8), 0),
            **kwargs,
        )
        self.app: FSStockApp = app
        self._items: dict[str, BottomNavItem] = {}

        self._add("stock", "warehouse", "titles.stock")
        self._add("objective", "target", "titles.objective")
        self._add("settings", "cog-outline", "titles.settings")

        self.set_active("stock")

    def _add(self, key: str, icon: str, text: str) -> None: 
        """
        Add an item to the Navigation Bar.
        
        Parameters
        ----------
        key: str
            Screen key
        icon: str
            Icon name
        text: str
            Title screen
        """
        item = BottomNavItem(key, icon, self.app.t(text), on_select=self._on_item)
        self._items[key] = item
        self.add_widget(item)

    # =============================================================================================
    # Move to screen
    # =============================================================================================
    
    def _on_item(self, key: str) -> None:
        """
        When selecting an item, go to its screen and set the item on.
        
        Parameters
        ----------
        key: str
            The screen key
        """
        self.set_active(key)
        if callable(getattr(self.app, "go", None)):
            self.app.go(key)

    def set_active(self, key: str) -> None:
        """
        Sets the navigation button of the current screen on.
        
        Parameters
        ----------
        key: str
            Screen name
        """
        for k, item in self._items.items():
            item.set_active(k == key)
