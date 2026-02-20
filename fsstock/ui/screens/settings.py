from __future__ import annotations

from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Callable, Self
import webbrowser

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.utils import platform
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import IconLeftWidget, MDList, OneLineAvatarIconListItem, OneLineListItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField

from fsstock.core.models import FarmData, TripPlan
from fsstock.core.pdf_export import export_pdf_report
from fsstock.core.storage import new_farm_id, save_app_settings
from fsstock.ui.colors.colors import BG_DARK, BLACK, PRIMARY_GREEN, RED, WHITE

if TYPE_CHECKING:
    from fsstock.ui.app import FSStockApp


LANGUAGE_OPTIONS = [
    ("es", "Español"),
    ("en", "English"),
]


class SettingsScreen(MDScreen):
    """
    Settings screen:
    - Label farm name
    - Export to PDF
    - Create farm
    - Change farm
    - Change farm name
    - Reset farm
    - Erase farm
    - Language (English / Spanish)
    - About (go to github page)
    """
    
    # =============================================================================================
    # Build
    # =============================================================================================
    
    def __init__(self, app: FSStockApp, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app: FSStockApp = app
        
        self.md_bg_color: str = BG_DARK  # Background color

        # Layout
        root = MDBoxLayout(
            orientation="vertical",
            padding=(dp(12), dp(12)),
            spacing=dp(10),
        )
        # Farm name
        self.farm_label = MDLabel(
            text=f"{self.app.t("settings.farm_name")} —",
            halign="left",
            font_style="H6",
            size_hint_y=None,
            height=dp(32),
        )
        root.add_widget(self.farm_label)

        scroll = MDScrollView()
        self.list_view = MDList()
        scroll.add_widget(self.list_view)
        root.add_widget(scroll)

        self.add_widget(root)
        self._build_items()
    
    def _build_items(self) -> None:
        """
        Builds the items (title sections + buttons) of settings screen
        """
        self.list_view.clear_widgets()

        # Report section
        self._add_section(self.app.t("settings.titles.report"))
        self._add_item(self.app.t("settings.buttons.report"), "file-pdf-box", self.on_export_pdf)

        # Farm section
        self._add_section(self.app.t("settings.titles.farm"))
        self._add_item(self.app.t("settings.buttons.create_farm"), "plus-box", self.on_create_farm)
        self._add_item(
            self.app.t("settings.buttons.change_farm"),
            "swap-horizontal",
            self.on_switch_farm
        )
        self._add_item(self.app.t("settings.buttons.rename_farm"), "pencil", self.on_rename_farm)
        self._add_item(self.app.t("settings.buttons.reset_farm"), "restart", self.on_reset_farm)
        self._add_item(
            self.app.t("settings.buttons.delete_farm"),
            "trash-can-outline",
            self.on_delete_farm
        )

        # Languaje section
        self._add_section(self.app.t("settings.titles.language"))
        self._add_item(self.app.t("settings.buttons.language"), "translate", self.on_language)

        # About section
        self._add_section(self.app.t("settings.titles.about"))
        self._add_item(self.app.t("settings.buttons.about"), "information-outline", self.on_about)
        
    def _add_section(self, title: str) -> None:
        """
        Adds a section into the settings screen
        
        Parameters
        ----------
        title: str
            The section title
        """
        item = OneLineListItem(text=title, disabled=True)
        self.list_view.add_widget(item)
        
    def _add_item(self, text: str, left_icon: str, on_release: Callable[[Self], None]) -> None:
        """
        Adds a button into the settings screen.
        
        Parameters
        ----------
        text: str
            Button text
        left_icon: str
            Icon button
        on_release: Callable[[Self], None]
            SettingsScreen's method: action button
        """
        item = OneLineAvatarIconListItem(text=text, on_release=lambda *_: on_release())
        item.add_widget(IconLeftWidget(icon=left_icon))
        self.list_view.add_widget(item)
        
    # =============================================================================================
    # Export PDF
    # =============================================================================================
        
    def on_export_pdf(self) -> None:
        """
        Generates the PDF report.
        """
        # If a PDF is already being created, do nothing.
        if getattr(self.app, "_pdf_busy", False):
            return

        self.app._pdf_busy = True
        
        # Generating report dialog...
        progress = MDDialog(
            title=self.app.t("pdf.generating.title"),
            text=self.app.t("pdf.generating.content"),
        )
        progress.open()
        
        # Generate it in another thread, to not block the program
        Thread(target=lambda *_: self._pdf_worker(progress), daemon=True).start()
        
    def _pdf_worker(self, progress: MDDialog) -> None:
        """
        Creates the PDF in background, in another thread.
        
        Parameters
        ----------
        progress: MDDialog
            Dialog of generating the pdf report
        """
        plan: TripPlan | None = self.app.last_plan

        # Generate the PDF report
        try: 
            out_path: Path = export_pdf_report(
                user_data_dir=self.app.user_data_dir,
                catalog=self.app.catalog,
                stock=self.app.stock,
                i18n=self.app.i18n,
                last_plan=plan,
                title="FS Stock Report",
                farm_name=self.app.farm_name,
            )
            ok: bool = True
            err: str = ""
        except Exception as e:
            out_path = None
            ok: bool = False
            err: str = str(e)
            
        Clock.schedule_once(lambda *_: self._pdf_done(progress, ok, out_path, err, 0), 0)
        
    def _pdf_done(
        self,
        progress: MDDialog,
        ok: bool,
        out_path: Path | None,
        err: str,
        _dt
    ) -> None:
        """
        After processing the PDF report, show the show pdf dialog, if
        there has not been an error, or the error PDF, otherwise.
        
        Parameters
        ----------
        progress: MDDialog
            Dialog of generating the pdf report
        ok: bool
            True if there were no exceptions, False otherwise
        out_path: Path | None
            The pdf path, if there were no exceptions, None otherwise
        err: str
            The error, if there was a exception
        """
        progress.dismiss()
        self.app._pdf_busy = False

        if ok and out_path:
            self._show_pdf_success(Path(out_path))
        else:
            self._show_pdf_error(err)
    
    def _show_pdf_success(self, pdf_path: Path) -> None:
        """
        Shows the dialog when the PDF has been correctly generated.
        
        Parameters
        ----------
        pdf_path: Path
            The output PDF path
        """
        txt: str = self.app.t("pdf.success.content", value=pdf_path)

        # Buttons
        close_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.close"),
            on_release=lambda *_: dlg.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        )
        copy_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.copy_path"),
            on_release=lambda *_: Clipboard.copy(str(pdf_path)),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        ) 
        buttons: list[MDRectangleFlatButton] = [close_btn, copy_btn]

        if platform == "win":
            open_btn = MDRectangleFlatButton(
                text=self.app.t("buttons.open_pdf"),
                on_release=lambda *_: self._open_path_native(pdf_path),
                line_color=PRIMARY_GREEN,
                text_color=BLACK,
                md_bg_color=PRIMARY_GREEN
            )
            open_folder_btn = MDRectangleFlatButton(
                text=self.app.t("buttons.open_folder"),
                on_release=lambda *_: self._open_path_native(pdf_path.parent),
                line_color=PRIMARY_GREEN,
                text_color=PRIMARY_GREEN
            )
            buttons.insert(1, open_btn)
            buttons.insert(2, open_folder_btn)

        dlg = MDDialog(title=self.app.t("pdf.success.title"), text=txt, buttons=buttons)
        dlg.open()
        
    def _open_path_native(self, path: Path) -> None:
        """
        Opens folder or file.
        
        Parameters
        ----------
        path: Path
            The directory or file path
        """
        try:
            if platform == "win":
                import os
                os.startfile(str(path))
        except Exception as e:
            self._show_pdf_error(str(e))
    
    def _show_pdf_error(self, err: str) -> None:
        """
        Shows the dialog if there has been an error generating or
        opening the pdf report.
        
        Parameters
        ----------
        err: str
            The error message
        """
        close_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.close"),
            on_release=lambda *_: dlg.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        )
        dlg = MDDialog(
            title=self.app.t("pdf.error.title"),
            text=self.app.t("pdf.error.content", value=err),
            buttons=[close_btn],
        )
        dlg.open()
        
    # =============================================================================================
    # Create farm
    # =============================================================================================
        
    def on_create_farm(self) -> None:
        """
        Creates a new farm
        """
        field = MDTextField(
            hint_text=self.app.t("new_farm.textfield"),
            mode="rectangle",
            text="",
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
        content.add_widget(field)

        cancel_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.cancel"),
            on_release=lambda *_: dlg.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        )
        create_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.create"),
            on_release=lambda *_: self._do_create_farm(field, dlg),
            line_color=PRIMARY_GREEN,
            md_bg_color=PRIMARY_GREEN, 
            text_color=BLACK
        )
        dlg = MDDialog(
            title=self.app.t("new_farm.title"),
            type="custom",
            content_cls=content,
            size_hint=(0.92, None),
            height=dp(260),
            buttons=[cancel_btn, create_btn],
        )
        dlg.open()
        
    def _do_create_farm(self, field: MDTextField, dlg: MDDialog) -> None:
        """
        Creates a new farm.
        
        Parameters
        ----------
        field: MDTextField
            Text field containing the name of the farm.
        dlg: MDDialog
            The dialog requesting a new farm
        """
        name: str = (field.text or "").strip() or "Nueva granja"
        self.app._persist_current_farm()  # Save current farm

        # Create a new and load it
        fid: str = new_farm_id()
        self.app.farms[fid] = FarmData(
            name=name,
            stock=[],
            last_plan=None
        )
        self.app.current_farm_id = fid
        self.app._load_current_farm()
        self.app._save_state()

        dlg.dismiss()
        self.app.go("stock")
    
    # =============================================================================================
    # Switch farm
    # =============================================================================================
    
    def on_switch_farm(self) -> None:
        """
        Changes farm
        """
        # Save current farm
        self.app._persist_current_farm()

        # Dialog change farm
        title_lbl = MDLabel(
            text=self.app.t("change_farm.content"),
            halign="left",
            size_hint_y=None,
            height=dp(28),
        )

        scroll = MDScrollView(size_hint_y=None, height=dp(340))
        lst = MDList()
        lst.size_hint_y = None
        lst.bind(minimum_height=lst.setter("height"))
        scroll.add_widget(lst)

        content = MDBoxLayout(
            orientation="vertical",
            padding=(dp(12), dp(12)),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(390),
        )
        content.add_widget(title_lbl)
        content.add_widget(scroll)

        # Farms list
        farms_sorted: list[tuple[str, FarmData]] = sorted(
            self.app.farms.items(),
            key=lambda kv: (kv[1].name.lower(), kv[0]),
        )
        # Create item for each farm
        for fid, f in farms_sorted:
            name: str = f.name

            item = OneLineAvatarIconListItem(
                text=name,
                on_release = lambda *_, _fid=fid: self._select_farm(_fid, dlg)
            )

            icon_name = "check-circle" if fid == self.app.current_farm_id else "circle-outline"
            left = IconLeftWidget(
                icon=icon_name,
                on_release = lambda *_, _fid=fid: self._select_farm(_fid, dlg)
            )
            
            item.add_widget(left)
            lst.add_widget(item)

        # Dialog buttons
        create_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.create"),
            on_release=lambda *_: self._create_farm_from_here(dlg),
            line_color=PRIMARY_GREEN,
            md_bg_color=PRIMARY_GREEN,
            text_color=BLACK
        )
        cancel_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.close"),
            on_release=lambda *_: dlg.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        )
        dlg = MDDialog(
            title=self.app.t("change_farm.title"),
            type="custom",
            content_cls=content,
            size_hint=(0.92, None),
            height=dp(560),
            buttons=[create_btn, cancel_btn],
        )
        dlg.open()
    
    def _select_farm(self, fid: str, dlg: MDDialog) -> None:
        """
        When selecting a farm, loads it.
        
        Parameters
        ----------
        fid: str
            Farm ID
        
        dlg: MDDialog
            Dialog requesting the change of farm
        """
        self.app.current_farm_id = fid
        self.app._load_current_farm()
        self.app._save_state()
        dlg.dismiss()
        self.app.go("stock")
    
    def _create_farm_from_here(self, dlg, *args) -> None:
        """
        Create farm from change farm dialog
        """
        dlg.dismiss()
        self.on_create_farm()
        
    # =============================================================================================
    # Rename farm
    # =============================================================================================
    
    def on_rename_farm(self) -> None:
        """
        Changes the farm name
        """
        field = MDTextField(
            hint_text=self.app.t("rename_farm.textfield"),
            mode="rectangle",
            text=self.app.farm_name or "",
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
        content.add_widget(field)

        # Buttons
        cancel_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.cancel"),
            on_release=lambda *_: dlg.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        )
        save_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.save"),
            on_release=lambda *_: self._do_save_farmname(field, dlg),
            md_bg_color=PRIMARY_GREEN,
            line_color=PRIMARY_GREEN,
            text_color=BLACK
        )
        dlg = MDDialog(
            title=self.app.t("rename_farm.title"),
            type="custom",
            content_cls=content,
            size_hint=(0.92, None),
            height=dp(260),
            buttons=[cancel_btn, save_btn],
        )
        dlg.open()
    
    def _do_save_farmname(self, field, dlg) -> None:
        """
        Change the farm name into data app
        """
        name: str = (field.text or "").strip() or "Mi granja"
        self.app.farm_name = name
        self.app._save_state()
        dlg.dismiss()
        self.refresh()
    
    # =============================================================================================
    # Reset farm
    # =============================================================================================

    def on_reset_farm(self):
        """
        Reset farm
        """
        cancel_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.cancel"),
            on_release=lambda *_: dlg.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN
        )
        delete_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.reset"),
            on_release=lambda *_: self._do_reset_farm(dlg),
            md_bg_color=RED,
            line_color=RED,
            text_color=WHITE
        )
        dlg = MDDialog(
            title=self.app.t("reset_farm.title"),
            text=self.app.t("reset_farm.content"),
            buttons=[cancel_btn, delete_btn],
        )
        dlg.open()
    
    def _do_reset_farm(self, dlg) -> None:
        """
        Reset farm
        """
        dlg.dismiss()
        self.app.stock = []
        self.app.last_plan = None
        self.app._save_state()
        self.app.go("stock")
    
    # =============================================================================================
    # Delete farm
    # =============================================================================================
    
    def on_delete_farm(self) -> None:
        """
        Delete farm
        """
        cancel_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.cancel"),
            on_release=lambda *_: dlg.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN,
            )
        delete_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.delete"),
            on_release=lambda *_: self._do_delete_farm(dlg),
            md_bg_color=RED,
            line_color=RED,
            text_color=WHITE
        )
        dlg = MDDialog(
            title=self.app.t("delete_farm.title"),
            text=self.app.t("delete_farm.content"),
            buttons=[cancel_btn, delete_btn],
        )
        dlg.open()
    
    def _do_delete_farm(self, dlg) -> None:
        """
        Delete farm from app data
        """
        dlg.dismiss()

        fid: str = self.app.current_farm_id
        if fid in self.app.farms:
            self.app.farms.pop(fid, None)

        # Change to the next farm or create one
        if self.app.farms:
            self.app.current_farm_id = next(iter(self.app.farms.keys()))
        else:
            new_id: str = new_farm_id()
            self.app.farms[new_id] = FarmData(
                name="Mi granja",
                stock=[], 
                last_plan=None
            )
            self.app.current_farm_id = new_id

        self.app._load_current_farm()
        self.app._save_state()
        self.app.go("stock")
    
    # =============================================================================================
    # Language
    # =============================================================================================
    
    def on_language(self) -> None:
        """
        Change the language.
        """
        # Dialog        
        title_lbl = MDLabel(
            text=self.app.t("language.content"),
            halign="left",
            size_hint_y=None,
            height=dp(28),
        )

        scroll = MDScrollView(size_hint_y=None, height=dp(340))
        lst = MDList()
        lst.size_hint_y = None
        lst.bind(minimum_height=lst.setter("height"))
        scroll.add_widget(lst)

        content = MDBoxLayout(
            orientation="vertical",
            padding=(dp(12), dp(12)),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(390),
        )
        content.add_widget(title_lbl)
        content.add_widget(scroll)

        # Buttons
        for code, label in LANGUAGE_OPTIONS:
            item = OneLineAvatarIconListItem(
                text=label,
                on_release=lambda *a, c=code: self._pick_language(c, dlg)
            )
            icon: str = "check-circle" if code == getattr(self.app, "lang", "es") else "circle-outline"
            item.add_widget(IconLeftWidget(
                icon=icon,
                on_release=lambda *a, c=code: self._pick_language(c, dlg)
            ))
            lst.add_widget(item)

        close_btn = MDRectangleFlatButton(
            text=self.app.t("buttons.close"),
            on_release=lambda *a: dlg.dismiss(),
            line_color=PRIMARY_GREEN,
            text_color=PRIMARY_GREEN,
        )
        dlg = MDDialog(
            title="Idioma / Language",
            type="custom",
            content_cls=content,
            size_hint=(0.92, None),
            height=dp(320),
            buttons=[close_btn],
        )
        dlg.open()
        
    def _pick_language(self, lang_code: str, dlg: MDDialog) -> None:
        """
        Selects and sets a language.
        
        Parameters
        ----------
        lang_code: str
            The language code ("es", "en")
        dlg: MDDialog
            The language change dialog
        """
        self._set_language(lang_code)
        dlg.dismiss()


    def _set_language(self, lang_code: str) -> None:
        """
        Sets the language
        """
        self.app.lang = lang_code
        save_app_settings(self.app.user_data_dir, {"language": self.app.lang})

        # Recarga traductor + refresca UI visible
        self.app._load_i18n()
        self._apply_language()


    def _apply_language(self) -> None:
        """
        Apply the language, refreshing the screens
        """
        # Refresh navigation bar
        for key, item in self.app.root_widget.bottom_nav._items.items():
            item.label.text = self.app.t(f"titles.{key}")
            
        # Refresh screen titles
        self.app.root_widget.screen_titles = {
            "stock": self.app.t("titles.stock"),
            "add_product": self.app.t("titles.add_product"),
            "objective": self.app.t("titles.objective"),
            "settings": self.app.t("titles.settings"),
        }

        # Recreate the screeens
        self.__init__(self.app, name="settings")
        self.app.root_widget.stock_screen.__init__(self.app, name="stock")
        self.app.root_widget.objective_screen.__init__(self.app, name="objective")
        self.app.root_widget.add_screen.__init__(self.app, name="add_product")

        # Preload catalog screen
        Clock.schedule_once(self.app._preload_add_product_screen, 0)
        
        # Refresh settings screen
        self.refresh()

    
    # =============================================================================================
    # About
    # =============================================================================================

    def on_about(self) -> None:
        """
        Go to github page
        """
        webbrowser.open("https://github.com/Kelpesito/Farming-Simulator-25-Stock-Calculator")
    
    # =============================================================================================
    # pre enter
    # =============================================================================================
    
    def on_pre_enter(self, *args) -> None:
        self.refresh()
        return super().on_pre_enter(*args)
    
    # =============================================================================================
    # Refresh
    # =============================================================================================
    
    def refresh(self) -> None:
        """
        Updates the farm name in settings screen
        """
        name: str = self.app.farm_name
        self.farm_label.text = f"{self.app.t("settings.farm_name")} {name}"
