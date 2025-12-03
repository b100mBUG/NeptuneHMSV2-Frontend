from kivy.lang import Builder
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText


from screens.prescriptions import PrescriptionsInfo
from screens.diagnoses import DiagnosisInfo
from screens.lab_requests import RequestsInfo
from screens.lab_results import ResultsInfo
from config import resource_path

Builder.load_file(resource_path("screens/doctor.kv"))


class DoctorScreen(MDScreen):
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
    
    
    
    # Making diagnosis mapper
    def diagnosis_mapper(self, diag: dict):
        return {
            'patient_name': diag.get("patient", "unknown")['patient_name'] or "Unknown",
            'symptoms': diag.get("symptoms", "unknown") or "unknown",
            'diagnosis': f"{diag.get("suggested_diagnosis", 0)}" or "unknown",
            'show_profile': lambda diag_data = diag: self.display_diagnosis(diag_data)
        }

    def show_diagnosis(self):
        self.current_search_callback = self.search_diagnosis

        self.ids.add_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: DiagnosisInfo().diagnoses_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_diags_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        def on_diags_fetched(diags):
            if not diags:
                self.show_snack("Diagnosis not found")
                return
            self.display_items("DiagnosisRow", diags, "diag", self.diagnosis_mapper)
        
        DiagnosisInfo().fetch_diagnoses("all", "all", "desc", callback=on_diags_fetched)

    
    def search_diagnosis(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_diagnosis()
            return

        def on_diags_fetched(diags):
            if not diags:
                print("Diagnosis not found")
                return
            self.display_items("DiagnosisRow", diags, "diag", self.diagnosis_mapper)

        DiagnosisInfo().fetch_diagnoses(
            intent="search",
            search_term=term,
            callback=on_diags_fetched
        )
        
    def show_diags_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_diagnosis("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_diagnosis("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_diagnosis("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_diagnosis("Date (Old to New)")
            }
        ]

        self.sort_diag_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_diag_menu.open()
    
    def sort_diagnosis(self, val):
        self.sort_diag_menu.dismiss()
        def on_diags_fetched(diags):
            if not diags:
                self.show_snack("Diagnosis not found")
                return
            self.display_items("DiagnosisRow", diags, "drug", self.diagnosis_mapper)
        if val == "Name (A to Z)":
            DiagnosisInfo().fetch_diagnoses(sort_term="name", sort_dir="asc", callback=on_diags_fetched)
        elif val == "Name (Z to A)":
            DiagnosisInfo().fetch_diagnoses(intent="all", sort_term="name", sort_dir="desc", callback=on_diags_fetched)
        elif val == "Date (New to Old)":
            DiagnosisInfo().fetch_diagnoses(intent="all", sort_term="date", sort_dir="desc", callback=on_diags_fetched)
        elif val == "Date (Old to New)":
            DiagnosisInfo().fetch_diagnoses(sort_term="date", sort_dir="asc", callback=on_diags_fetched)
    
    def display_diagnosis(self, diag_data: dict):
        self.preview_display(
            DiagnosisInfo().display_diagnosis_info(
                diag_data
            ),
            MDBoxLayout(
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: DiagnosisInfo().diagnosis_edit_form(diag_data)
                ),
                MDLabel(
                    text = "Diagnosis Preview",
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
                    on_release = lambda *a: DiagnosisInfo().confirm_deletion_form(diag_data.get("diagnosis_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    
    # Making prescription mapper
    def prescriptions_mapper(self, presc: dict):
        return {
            'patient_name': presc.get("patient_name", "unknown") or "Unknown",
            'items_count': f"{len(presc.get("entries", "unknown"))} Items" or "0",
            'show_profile': lambda presc_data = presc: self.display_prescriptions(presc_data)
        }
        
    def show_prescriptions(self):
        self.current_search_callback = self.search_prescriptions

        self.ids.add_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: PrescriptionsInfo().prescriptions_add_form()
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
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: PrescriptionsInfo().confirm_deletion_form(presc_data.get("prescription_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    
    # Making requests mapper
    def requests_mapper(self, request: dict):
        return {
            'patient_name': request.get("patient", "unknown")['patient_name'] or "Unknown",
            'test': request.get("test", "unknown")['test_name'] or "unknown",
            'desc': f"{request.get("test", 0)['test_desc']}" or "unknown",
            'show_profile': lambda request_data = request: self.display_requests(request_data)
        }

    def show_requests(self):
        self.current_search_callback = self.search_requests

        self.ids.add_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: RequestsInfo().requests_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_request_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        def on_requests_fetched(drugs):
            if not drugs:
                self.show_snack("Requests not found")
                return
            self.display_items("RequestsRow", drugs, "request", self.requests_mapper)
        
        RequestsInfo().fetch_requests("all", "all", "desc", callback=on_requests_fetched)

    
    def search_requests(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_requests()
            return

        def on_requests_fetched(requests):
            if not requests:
                print("Requests not found")
                return
            self.display_items("RequestsRow", requests, "drug", self.requests_mapper)

        RequestsInfo().fetch_requests(
            intent="search",
            search_term=term,
            callback=on_requests_fetched
        )
        
    def show_request_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_requests("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_requests("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_requests("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_requests("Date (Old to New)")
            }
        ]

        self.sort_request_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_request_menu.open()
    
    def sort_requests(self, val):
        self.sort_request_menu.dismiss()
        def on_requests_fetched(requests):
            if not requests:
                self.show_snack("requests not found")
                return
            self.display_items("RequestsRow", requests, "request", self.requests_mapper)
        if val == "Name (A to Z)":
            RequestsInfo().fetch_requests(sort_term="name", sort_dir="asc", callback=on_requests_fetched)
        elif val == "Name (Z to A)":
            RequestsInfo().fetch_requests(intent="all", sort_term="name", sort_dir="desc", callback=on_requests_fetched)
        elif val == "Date (New to Old)":
            RequestsInfo().fetch_requests(intent="all", sort_term="date", sort_dir="desc", callback=on_requests_fetched)
        elif val == "Date (Old to New)":
            RequestsInfo().fetch_requests(sort_term="date", sort_dir="asc", callback=on_requests_fetched)
    
    def display_requests(self, req_data: dict):
        self.preview_display(
            RequestsInfo().display_requests_info(
                req_data
            ),
            MDBoxLayout(
                MDLabel(
                    text = "Lab Request Preview",
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
                    on_release = lambda *a: RequestsInfo().confirm_deletion_form(req_data.get("request_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    
    # Making results mapper
    def results_mapper(self, result: dict):
        return {
            'patient_name': result.get("patient", "unknown")['patient_name'] or "Unknown",
            'observations': result.get("observations", "unknown") or "unknown",
            'conclusions': f"{result.get("conclusion", "unknown")}" or "unknown",
            'show_profile': lambda result_data = result: self.display_results(result_data)
        }

    def show_results(self):
        self.current_search_callback = self.search_results

        self.ids.add_btn.disabled = True
        self.ids.add_btn.on_release = lambda *a: ResultsInfo().results_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_result_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        def on_results_fetched(drugs):
            if not drugs:
                self.show_snack("results not found")
                return
            self.display_items("ResultsRow", drugs, "result", self.results_mapper)
        
        ResultsInfo().fetch_results("all", "all", "desc", callback=on_results_fetched)

    
    def search_results(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_results()
            return

        def on_results_fetched(results):
            if not results:
                print("results not found")
                return
            self.display_items("ResultsRow", results, "drug", self.results_mapper)

        ResultsInfo().fetch_results(
            intent="search",
            search_term=term,
            callback=on_results_fetched
        )
        
    def show_result_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_results("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_results("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_results("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_results("Date (Old to New)")
            }
        ]

        self.sort_result_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_result_menu.open()
    
    def sort_results(self, val):
        self.sort_result_menu.dismiss()
        def on_results_fetched(results):
            if not results:
                self.show_snack("results not found")
                return
            self.display_items("ResultsRow", results, "result", self.results_mapper)
        if val == "Name (A to Z)":
            ResultsInfo().fetch_results(sort_term="name", sort_dir="asc", callback=on_results_fetched)
        elif val == "Name (Z to A)":
            ResultsInfo().fetch_results(intent="all", sort_term="name", sort_dir="desc", callback=on_results_fetched)
        elif val == "Date (New to Old)":
            ResultsInfo().fetch_results(intent="all", sort_term="date", sort_dir="desc", callback=on_results_fetched)
        elif val == "Date (Old to New)":
            ResultsInfo().fetch_results(sort_term="date", sort_dir="asc", callback=on_results_fetched)
    
    def display_results(self, res_data: dict):
        self.preview_display(
            ResultsInfo().display_results_info(
                res_data
            ),
            MDBoxLayout(
                MDLabel(
                    text = "Lab result Preview",
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