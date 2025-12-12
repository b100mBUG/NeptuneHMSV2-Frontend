from kivy.lang import Builder
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText


from screens.lab_requests import RequestsInfo
from screens.lab_results import ResultsInfo
from screens.lab_tests import (
    display_tests_info,
    fetch_tests,
    tests_add_form,
    test_edit_form,
    confirm_deletion_form
)
from config import resource_path

Builder.load_file(resource_path("screens/lab.kv"))


class LabScreen(MDScreen):
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
    
    
    # Making tests mapper
    def tests_mapper(self, test: dict | None):
        test = test or {}

        return {
            'test_name': (test.get("test_name") or "Unknown").strip(),
            'test_desc': (test.get("test_desc") or "Unknown").strip(),
            'test_price': f"Ksh. {test.get('test_price', 0)}",
            'show_profile': lambda test_data=test: self.display_tests(test_data)
        }


    def show_tests(self):
        self.current_search_callback = self.search_tests

        self.ids.add_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: tests_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_test_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        def on_tests_fetched(drugs):
            if not drugs:
                self.show_snack("tests not found")
                return
            self.display_items("TestsRow", drugs, "test", self.tests_mapper)
        
        fetch_tests("all", "all", "desc", callback=on_tests_fetched)

    
    def search_tests(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_tests()
            return

        def on_tests_fetched(tests):
            if not tests:
                print("tests not found")
                return
            self.display_items("TestsRow", tests, "drug", self.tests_mapper)

        fetch_tests(
            intent="search",
            search_term=term,
            callback=on_tests_fetched
        )
        
    def show_test_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_tests("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_tests("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_tests("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_tests("Date (Old to New)")
            }
        ]

        self.sort_test_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_test_menu.open()
    
    def sort_tests(self, val):
        self.sort_test_menu.dismiss()
        def on_tests_fetched(tests):
            if not tests:
                self.show_snack("tests not found")
                return
            self.display_items("TestsRow", tests, "test", self.tests_mapper)
        if val == "Name (A to Z)":
            fetch_tests(sort_term="name", sort_dir="asc", callback=on_tests_fetched)
        elif val == "Name (Z to A)":
            fetch_tests(intent="all", sort_term="name", sort_dir="desc", callback=on_tests_fetched)
        elif val == "Date (New to Old)":
            fetch_tests(intent="all", sort_term="date", sort_dir="desc", callback=on_tests_fetched)
        elif val == "Date (Old to New)":
            fetch_tests(sort_term="date", sort_dir="asc", callback=on_tests_fetched)
    
    def display_tests(self, test_data: dict):
        self.preview_display(
            display_tests_info(
                test_data
            ),
            MDBoxLayout(
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: test_edit_form(test_data)
                ),
                MDLabel(
                    text = "Test Preview",
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
                    on_release = lambda *a: confirm_deletion_form(test_data.get("test_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    
    
    # Making requests mapper
    def requests_mapper(self, request: dict | None):
        request = request or {}
        patient = request.get("patient") or {}
        test = request.get("test") or {}

        return {
            'patient_name': (patient.get("patient_name") or "Unknown").strip(),
            'test': (test.get("test_name") or "Unknown").strip(),
            'desc': (test.get("test_desc") or "Unknown").strip(),
            'show_profile': lambda request_data=request: self.display_requests(request_data)
        }


    def show_requests(self):
        self.current_search_callback = self.search_requests

        self.ids.add_btn.disabled = True
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

        self.ids.add_btn.disabled = False
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
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: ResultsInfo().result_edit_form(res_data)
                ),
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
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: ResultsInfo().confirm_deletion_form(res_data.get("result_id"))
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