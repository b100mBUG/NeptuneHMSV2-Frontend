from kivy.properties import StringProperty, ObjectProperty
from kivy.metrics import dp, sp
from kivy.clock import mainthread
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout

from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.divider import MDDivider
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemLeadingIcon, MDListItemSupportingText, MDListItemTertiaryText
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog, MDDialogButtonContainer, MDDialogContentContainer, MDDialogHeadlineText, MDDialogIcon, MDDialogSupportingText
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText, MDTextFieldLeadingIcon
from kivymd.uix.button import MDIconButton
from kivymd.uix.pickers import MDDockedDatePicker
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from threading import Thread
import requests
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict

from config import SERVER_URL, STORE
from screens.patients import fetch_patients
from screens.drugs import fetch_drugs
from database.actions import prescription


def agglomerate_prescriptions(prescriptions):
    grouped = defaultdict(list)
    for presc in prescriptions:
        grouped[presc.patient.patient_name].append(presc)

    output = []
    for patient_name, presc_group in grouped.items():
        entries = []
        for presc in presc_group:
            presc_id = presc.prescription_id
            for item in presc.items:
                entries.append({
                    "drug_name": item.drug.drug_name,
                    "quantity": item.drug_qty,
                    "notes": item.notes
                })

        output.append({
            "prescription_id": presc_id,
            "patient_name": patient_name,
            "entries": entries,
            "dates": sorted({str(p.date_added).split(" ")[0] for p in presc_group}),
        })

    return output

class PrescriptionsRow(MDListItem):
    patient_name = StringProperty("")
    items_count = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.item_count_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="medical-bag", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.item_count_label)
        
        self.bind(patient_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(items_count=lambda inst, val: setattr(self.item_count_label, 'text', val))

class PrescriptionsInfo:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.patients = {}
        self.drugs = {}
        self.store = STORE
        
    def make_display_label(self, text, color="blue"):
        lbl = MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=color,
            halign="left",
            adaptive_height = True,
        )
        return lbl

    def display_prescriptions_info(
        self,
        presc_data: dict,
    ):
        name_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        name_box.add_widget(MDIcon(icon="account-heart", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        name_box.add_widget(self.make_display_label(f"   Patient: {presc_data.get('patient_name', "Unknown").upper()}"))
        
        presc_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        presc_box.add_widget(MDIcon(icon="medical-bag", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        presc_box.add_widget(
            MDLabel(
                text = "PRESCRIPTIONS", 
                size_hint_y = None, 
                height = dp(30),
                halign = "center",
                theme_text_color = "Custom",
                text_color = "blue"
            )
        )
        grid = MDGridLayout(size_hint_y = None, adaptive_height = True, cols=1, padding = dp(10), spacing = dp(10))
        scroll = MDScrollView()
        scroll.add_widget(grid)
        
        grid.add_widget(Widget(size_hint_y = None, height = dp(10)))
        grid.add_widget(name_box)

        count = 1
        for presc in presc_data.get("entries", None):
            count_label = MDLabel(
                text = f"{count}. ", 
                size_hint_y = None, 
                height = dp(30),
                theme_text_color = "Custom",
                text_color = "blue"
            )
            grid.add_widget(count_label)
            drug_label = MDLabel(
                text = f"     Drug: {presc['drug_name']}", 
                size_hint_y = None, 
                height = dp(30),
                theme_text_color = "Custom",
                text_color = "blue"
            )
            grid.add_widget(drug_label)
            qty_label = MDLabel(
                text = f"      Qty: {presc['quantity']}", 
                size_hint_y = None, 
                height = dp(30),
                theme_text_color = "Custom",
                text_color = "blue"
            )
            grid.add_widget(qty_label)
            presc_label = MDLabel(
                text = f"    Notes: {presc['notes']}", 
                size_hint_y = None, 
                height = dp(30),
                theme_text_color = "Custom",
                text_color = "blue",
                adaptive_height = True
            )
            grid.add_widget(presc_label)
            count += 1
        
        
        date_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        date_box.add_widget(MDIcon(icon="calendar", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        date_box.add_widget(self.make_display_label(f"   Added On: {presc_data.get('date_added', "YY-MM-DD")}"))
        
        grid.add_widget(date_box)
        
        return scroll

    def fetch_prescription(self, intent="all", sort_term="all", sort_dir="desc", search_term="ss", callback=None):
        #Thread(target=self.fetch_and_return_online_prescs, args=(intent, sort_term, sort_dir, search_term, callback), daemon=True).start()
        Thread(target=self.fetch_and_return_offline_prescs, args=(intent, sort_term, sort_dir, search_term, callback), daemon=True).start()

    def fetch_and_return_online_prescs(self, intent, sort_term, sort_dir, search_term, callback):
        url = ""
        if intent == "search":
            url = f"{SERVER_URL}prescription/prescriptions-search/?hospital_id={self.store.get('hospital')['hsp_id']}&search_term={search_term}"
        elif intent == "all":
            url = f"{SERVER_URL}prescription/prescriptions-fetch/?hospital_id={self.store.get('hospital')['hsp_id']}&sort_term={sort_term}&sort_dir={sort_dir}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
            else:
                data = None
        except Exception:
            data = None

        if callback:
            self.run_on_main_thread(callback, data)
    
    def fetch_and_return_offline_prescs(self, intent, sort_term, sort_dir, search_term, callback):
        try:
            if intent == "all":
                db_result = asyncio.run(prescription.fetch_prescriptions(self.store.get('hospital')['hsp_id'], sort_term, sort_dir))
            elif intent == "search":
                db_result = asyncio.run(prescription.search_prescriptions(self.store.get('hospital')['hsp_id'], search_term))
            
            data = agglomerate_prescriptions(db_result)
        except Exception:
            data = None

        if callback:
            self.run_on_main_thread(callback, data)

    @mainthread
    def run_on_main_thread(self, callback, data):
        callback(data)

    def prescriptions_add_form(self):
        self.new_patient_name = MDTextField(
            MDTextFieldHintText(text = "Patient"),
            MDTextFieldLeadingIcon(icon="account-heart")
        )
        self.new_drug = MDTextField(
            MDTextFieldHintText(text = "Drug"),
            MDTextFieldLeadingIcon(icon="pill")
        )
        self.new_quantity = MDTextField(
            MDTextFieldHintText(text = "Quantity"),
            MDTextFieldLeadingIcon(icon="counter")
        )
        self.new_notes = MDTextField(
            MDTextFieldHintText(text = "Notes"),
            MDTextFieldLeadingIcon(icon="clipboard-text")
        )
        self.new_patient_id = None
        self.new_drug_id = None
        
        name_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        name_box.add_widget(self.new_patient_name)
        name_btn = MDIconButton(
            icon="chevron-down", theme_icon_color="Custom", 
            icon_color="blue", on_release = lambda *a: self.show_patients()
        )
        name_box.add_widget(name_btn)
        
        drug_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        drug_box.add_widget(self.new_drug)
        drug_btn = MDIconButton(
            icon="chevron-down", theme_icon_color="Custom", 
            icon_color="blue", on_release = lambda *a: self.show_drugs()
        )
        drug_box.add_widget(drug_btn)
        
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
        content.add_widget(name_box)
        content.add_widget(drug_box)
        content.add_widget(self.new_quantity)
        content.add_widget(self.new_notes)
        
        self.prescription_dialog = MDDialog(
            MDDialogIcon(icon = "medical-bag", theme_icon_color="Custom", icon_color="blue"),
            MDDialogHeadlineText(text = "Add Prescription", bold=True, theme_text_color="Custom", text_color="blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="check", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "blue",
                    on_release = lambda *a: self.prepare_presc_data()
                ),
                MDIconButton(
                    icon="close", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.prescription_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10),
            ),
            auto_dismiss = False
        )
        self.prescription_dialog.open()
        
    def prepare_presc_data(self):
        if not self.new_patient_name.text.strip():
            self.show_snack("Enter patient name")
            return
        if not self.new_drug.text.strip():
            self.show_snack("Enter drug name")
            return
        if not self.new_quantity.text.strip():
            self.show_snack("Enter quantity")
            return
        if not self.new_notes.text.strip():
            self.show_snack("Enter notes")
            return
        
        data = {
            "patient_id": self.new_patient_id,
            'drug_id': self.new_drug_id,
            'drug_qty': self.new_quantity.text.strip(),
            'notes': self.new_notes.text.strip(),
        }
        self.submit_presc_data(data)
    def submit_presc_data(self, data):
        self.show_snack("Please wait as prescription is added")
        Thread(target=self.add_presc, args=(data,), daemon=True).start()

    def add_presc(self, data):
        #url = f"{SERVER_URL}prescription/prescriptions-add/?hospital_id={self.store.get('hospital')['hsp_id']}"
        #response = requests.post(url, json=data)
        #if response.status_code != 200:
            #self.show_snack("Failed to add prescription")
            #return
        #self.show_snack("Prescription added successfully. You can refresh the page to view them")

        try:
            asyncio.run(prescription.add_prescription(self.store.get('hospital')['hsp_id'], data))
            self.show_snack("Prescription added successfully")
        except Exception as e:
            self.show_snack("An unexpected error occurred. Please try again")
            return

    def confirm_deletion_form(self, presc_id):
        confirm_delete_dialog = MDDialog(
            MDDialogIcon(icon="trash-can", theme_icon_color="Custom", icon_color="red"),
            MDDialogHeadlineText(text="Delete Prescription", theme_text_color="Custom", text_color="red"),
            MDDialogContentContainer(
                MDLabel(
                    text = "Deleting a prescription is an irreversible process. Are you sure you wish to procede?",
                    theme_text_color = "Custom", text_color = "blue",
                    bold = True, halign="center"
                )
            ),
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="check", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "blue",
                    on_release = lambda *a: self.start_presc_deletion(presc_id)
                ),
                MDIconButton(
                    icon="close", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: confirm_delete_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10),
            ),
            auto_dismiss = False
                
        )
        confirm_delete_dialog.open()        

    def start_presc_deletion(self, presc_id):
        self.show_snack("Please wait as prescription is deleted")
        Thread(target=self.delete_prescription, args=(presc_id,), daemon=True).start()

    def delete_prescription(self, presc_id):
        #url = f"{SERVER_URL}prescription/prescriptions-delete/?hospital_id={self.store.get('hospital')['hsp_id']}&prescription_id={diag_id}"
        #response = requests.delete(url)
        #if response.status_code != 200:
            #self.show_snack("Failed to delete prescription")
            #return
        #self.show_snack("Prescription deleted successfully. You can refresh the page to view them")
        try:
            asyncio.run(prescription.delete_prescription(self.store.get('hospital')['hsp_id'], presc_id))
            self.show_snack("Prescription deleted successfully.")
        except Exception as e:
            self.show_snack("An unexpected error occurred. Please try again.")
            return
        
    @mainthread
    def make_patients_container(self):
        if not self.patients:
            self.show_snack("No patients found")
            return

        prvb = RecycleBoxLayout(
            default_size=(None, dp(100)),
            default_size_hint=(1, None),
            size_hint_y=None,
            spacing=dp(5),
            orientation="vertical"
        )
        prvb.bind(minimum_height=prvb.setter("height")) 

        self.patients_prev = RecycleView(
            scroll_type=['bars', 'content'],
            bar_width=0,
            size_hint=(1, None),
            height=dp(300),
        )
        self.patients_prev.add_widget(prvb)
        self.patients_prev.layout_manager = prvb 
        self.patients_prev.viewclass = "PatientsRow"

        data = []
        for patient in self.patients:
            data.append({
                'patient_name': patient['patient_name'] or "unknown",
                'patient_email': patient['patient_email'] or "example@gmail.com",
                'patient_phone': patient['patient_phone'] or "0712345678",
                'show_profile': lambda x=patient['patient_name'], y=patient['patient_id']: self.display_patient(x, y)
            })

        self.patients_prev.data = data
        self.patients_display_form(self.patients_prev)

    def patients_display_form(self, container):
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10), padding = dp(5))
        self.patient_search_field = MDTextField(
            MDTextFieldHintText(text="search..."),
            mode = "filled"
        )
        self.patient_search_field.bind(text=lambda instance, value: self.search_patients("search"))
        content.add_widget(self.patient_search_field)
        content.add_widget(container)
        
        self.patients_display_dialog = MDDialog(
            MDDialogIcon(icon="magnify", theme_icon_color = "Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Select Patient", theme_text_color = "Custom", text_color = "blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.patients_display_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            size_hint_y = None,
            height = dp(300)
        )
        self.patients_display_dialog.open()
        self.patients_display_dialog.auto_dismiss = False
        
    def display_patient(self, patient, patient_id):
        self.patients_display_dialog.dismiss()
        self.new_patient_name.text = patient
        self.new_patient_id = patient_id
    
    @mainthread
    def make_drugs_container(self):
        if not self.drugs:
            self.show_snack("No drugs found")
            return

        prvb = RecycleBoxLayout(
            default_size=(None, dp(100)),
            default_size_hint=(1, None),
            size_hint_y=None,
            spacing=dp(5),
            orientation="vertical"
        )
        prvb.bind(minimum_height=prvb.setter("height")) 

        self.drugs_prev = RecycleView(
            scroll_type=['bars', 'content'],
            bar_width=0,
            size_hint=(1, None),
            height=dp(300),
        )
        self.drugs_prev.add_widget(prvb)
        self.drugs_prev.layout_manager = prvb 
        self.drugs_prev.viewclass = "DrugsRow"

        data = []
        for drug in self.drugs:
            data.append({
                'drug_name': drug['drug_name'] or "unknown",
                'drug_category': drug['drug_category'] or "unknown",
                'drug_quantity': f"{drug['drug_quantity']} available" or "0",
                'show_profile': lambda x=drug['drug_name'], y=drug['drug_id']: self.display_drugs(x, y)
            })

        self.drugs_prev.data = data
        self.drugs_display_form(self.drugs_prev)

    def drugs_display_form(self, container):
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10), padding = dp(5))
        self.drugs_search_field = MDTextField(
            MDTextFieldHintText(text="search..."),
            mode = "filled"
        )
        self.drugs_search_field.bind(text=lambda instance, value: self.search_drugs("search"))
        content.add_widget(self.drugs_search_field)
        content.add_widget(container)
        
        self.drugs_display_dialog = MDDialog(
            MDDialogIcon(icon="magnify", theme_icon_color = "Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Select Drug", theme_text_color = "Custom", text_color = "blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.drugs_display_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            size_hint_y = None,
            height = dp(300)
        )
        self.drugs_display_dialog.open()
        self.drugs_display_dialog.auto_dismiss = False
        
    def display_drugs(self, drug, drug_id):
        self.drugs_display_dialog.dismiss()
        self.new_drug.text = drug
        self.new_drug_id = drug_id
    

    @mainthread
    def show_snack(self, text):
        MDSnackbar(
            MDSnackbarText(text=text), 
            pos_hint={'center_x': 0.5}, 
            size_hint_x=0.5, 
            orientation='horizontal'
        ).open()

    def show_patients(self):
        def on_patients_fetched(patients):
            if not patients:
                return
            self.patients = patients
            self.make_patients_container()
        
        fetch_patients("all", "all", "desc", callback=on_patients_fetched)
        

    
    def search_patients(self, *args):
        term = self.patient_search_field.text.strip()

        def on_patients_fetched(patients):
            if not patients:
                print("Patients not found")
                return
            self.patients = patients
            self.update_patient_rv()

        if not term:
            self.show_snack("Enter something to search")
            fetch_patients("all", "all", "desc", callback=on_patients_fetched)
            return
        
        fetch_patients(
            intent="search",
            search_by="name" or "email" or "phone",
            search_term=term,
            callback=on_patients_fetched
        )
    
    @mainthread
    def update_patient_rv(self):
        if hasattr(self, "patients_prev"):
            self.patients_prev.data = [
                {
                    'patient_name': p['patient_name'] or "unknown",
                    'patient_email': p['patient_email'] or "example@gmail.com",
                    'patient_phone': p['patient_phone'] or "0712345678",
                    'show_profile': lambda x=p['patient_name'], y=p['patient_id']: self.display_patient(x, y)
                }
                for p in self.patients
            ]
    
    def show_drugs(self):
        def on_drugs_fetched(drugs):
            if not drugs:
                return
            self.drugs = drugs
            self.make_drugs_container()
        
        fetch_drugs("all", "all", "desc", callback=on_drugs_fetched)


    
    def search_drugs(self, *args):
        term = self.drugs_search_field.text.strip()

        def on_drugs_fetched(drugs):
            if not drugs:
                print("drugs not found")
                return
            self.drugs = drugs
            self.update_drug_rv()

        if not term:
            self.show_snack("Enter something to search")
            fetch_drugs("all", "all", "desc", callback=on_drugs_fetched)
            return
        
        fetch_drugs(
            intent="search",
            search_term=term,
            callback=on_drugs_fetched
        )
    
    @mainthread
    def update_drug_rv(self):
        if hasattr(self, "drugs_prev"):
            self.drugs_prev.data = [
                {
                    'drug_name': d['drug_name'] or "unknown",
                    'drug_category': d['drug_category'] or "unknown",
                    'drug_quantity': f"{d['drug_quantity']} available" or "0",
                    'show_profile': lambda x=d['drug_name'], y=d['drug_id']: self.display_drugs(x, y)
                }
                for d in self.drugs
            ]