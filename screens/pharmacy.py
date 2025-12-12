from kivy.lang import Builder
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from screens.drugs import (
    drug_edit_form,
    drugs_add_form,
    confirm_deletion_form,
    display_drugs_info,
    fetch_drugs
)
from screens.prescriptions import PrescriptionsInfo
from config import resource_path

Builder.load_file(resource_path("screens/pharmacy.kv"))


class PharmacyScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.search_field.bind(text=self._on_search_field_text)

    def _on_search_field_text(self, instance, value):
        if self.current_search_callback:
            self.current_search_callback(value)
    
    def display_items(self, prev_class, items, flag, mapper):
        prev = self.ids.rec_view
        self.ids.rec_box.default_size = (None, dp(80))
        prev.viewclass = prev_class

        data = [mapper(i) for i in items]
        prev.data = data
    
    
    # Making drugs mapper
    def drugs_mapper(self, drug: dict | None):
        drug = drug or {}

        return {
            'drug_name': (drug.get("drug_name") or "Unknown").strip(),
            'drug_category': (drug.get("drug_category") or "Unknown").strip(),
            'drug_quantity': f"{drug.get('drug_quantity', 0)} available",
            'show_profile': lambda drug_data=drug: self.display_drugs(drug_data)
        }


    def show_drugs(self):
        self.current_search_callback = self.search_drugs
        self.ids.add_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: drugs_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_drug_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        def on_drugs_fetched(drugs):
            if not drugs:
                self.show_snack("Drugs not found")
                return
            self.display_items("DrugsRow", drugs, "worker", self.drugs_mapper)
        
        fetch_drugs("all", "all", "desc", callback=on_drugs_fetched)

    
    def search_drugs(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_drugs()
            return

        def on_drugs_fetched(drugs):
            if not drugs:
                print("Drugs not found")
                return
            self.display_items("DrugsRow", drugs, "drug", self.drugs_mapper)

        fetch_drugs(
            intent="search",
            search_term=term,
            callback=on_drugs_fetched
        )
        
    def show_drug_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_drugs("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_drugs("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_drugs("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_drugs("Date (Old to New)")
            }
        ]

        self.sort_drug_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_drug_menu.open()
    
    def sort_drugs(self, val):
        self.sort_drug_menu.dismiss()
        def on_drugs_fetched(drugs):
            if not drugs:
                self.show_snack("Drugs not found")
                return
            self.display_items("DrugsRow", drugs, "drug", self.drugs_mapper)
        if val == "Name (A to Z)":
            fetch_drugs(sort_term="name", sort_dir="asc", callback=on_drugs_fetched)
        elif val == "Name (Z to A)":
            fetch_drugs(intent="all", sort_term="name", sort_dir="desc", callback=on_drugs_fetched)
        elif val == "Date (New to Old)":
            fetch_drugs(intent="all", sort_term="date", sort_dir="desc", callback=on_drugs_fetched)
        elif val == "Date (Old to New)":
            fetch_drugs(sort_term="date", sort_dir="asc", callback=on_drugs_fetched)
    
    def display_drugs(self, drug_data: dict):
        self.preview_display(
            display_drugs_info(
                drug_data
            ),
            MDBoxLayout(
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: drug_edit_form(drug_data)
                ),
                MDLabel(
                    text = "Drug Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: confirm_deletion_form(drug_data.get("drug_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )

    # Making prescription mapper
    def prescriptions_mapper(self, presc: dict | None):
        presc = presc or {}
        entries = presc.get("entries") or []

        return {
            'patient_name': (presc.get("patient_name") or "Unknown").strip(),
            'items_count': f"{len(entries)} Items",
            'show_profile': lambda presc_data=presc: self.display_prescriptions(presc_data)
        }

        
    def show_prescriptions(self):
        self.current_search_callback = self.search_prescriptions
        self.ids.add_btn.disabled = True
        self.ids.sort_btn.on_release = lambda *a: self.show_prescs_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        def on_prescs_fetched(prescs):
            if not prescs:
                self.show_snack("prescription not found")
                return
            self.display_items("PrescriptionsRow", prescs, "diag", self.prescriptions_mapper)
        
        PrescriptionsInfo().fetch_prescription("all", "all", "desc", callback=on_prescs_fetched)

    
    def search_prescriptions(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_prescriptions()
            return

        def on_prescs_fetched(prescs):
            if not prescs:
                print("prescription not found")
                return
            self.display_items("PrescriptionsRow", prescs, "diag", self.prescriptions_mapper)

        PrescriptionsInfo().fetch_prescription(
            intent="search",
            search_term=term,
            callback=on_prescs_fetched
        )
        
    def show_prescs_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_prescriptions("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_prescriptions("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_prescriptions("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_prescriptions("Date (Old to New)")
            }
        ]

        self.sort_presc_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_presc_menu.open()
    
    def sort_prescriptions(self, val):
        self.sort_presc_menu.dismiss()
        def on_diags_fetched(diags):
            if not diags:
                self.show_snack("prescription not found")
                return
            self.display_items("PrescriptionsRow", diags, "drug", self.prescriptions_mapper)
        if val == "Name (A to Z)":
            PrescriptionsInfo().fetch_prescription(sort_term="name", sort_dir="asc", callback=on_diags_fetched)
        elif val == "Name (Z to A)":
            PrescriptionsInfo().fetch_prescription(intent="all", sort_term="name", sort_dir="desc", callback=on_diags_fetched)
        elif val == "Date (New to Old)":
            PrescriptionsInfo().fetch_prescription(intent="all", sort_term="date", sort_dir="desc", callback=on_diags_fetched)
        elif val == "Date (Old to New)":
            PrescriptionsInfo().fetch_prescription(sort_term="date", sort_dir="asc", callback=on_diags_fetched)
    
    def display_prescriptions(self, presc_data: dict):
        self.preview_display(
            PrescriptionsInfo().display_prescriptions_info(
                presc_data
            ),
            MDBoxLayout(
                MDLabel(
                    text = "Presc. Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    
    def preview_display(self, container, prev_header):
        self.ids.disp_view.clear_widgets()
        self.ids.disp_view.add_widget(prev_header)
        self.ids.disp_view.add_widget(container)
    
    
    def show_snack(self, text):
        MDSnackbar(
            MDSnackbarText(text=text), 
            pos_hint={'center_x': 0.5}, 
            size_hint_x=0.5, 
            orientation='horizontal'
        ).open()