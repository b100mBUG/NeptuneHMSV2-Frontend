from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.clock import mainthread, Clock
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.storage.jsonstore  import JsonStore
from kivy.properties import StringProperty

from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog, MDDialogContentContainer, MDDialogButtonContainer, MDDialogHeadlineText, MDDialogIcon, MDDialogSupportingText
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.button import MDIconButton
from kivymd.uix.widget import Widget
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.button import MDButtonText, MDButton
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.divider import MDDivider

from screens.worker import fetch_workers, start_worker_signin
from screens.hospital import start_hospital_signin, start_hospital_creation
import requests
from threading import Thread
from config import SERVER_URL, resource_path
from datetime import datetime
from utils import run_async
import os, platform

Builder.load_file(resource_path("screens/home.kv"))

class HomeScreen(MDScreen):
    image_path = StringProperty("")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.consultants = {}
        self.role = ""
        self.worker_email = ""
        self.image_path = resource_path("assets")

        json_path = self.get_app_data_path("hospital_data.json")
        self.store = JsonStore(json_path)

    def get_app_data_path(self, filename):
        system = platform.system()
        if system == "Windows":
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
        elif system == "Darwin": 
            base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
        else:  
            base = os.path.join(os.path.expanduser("~"), ".local", "share")

        if not os.path.exists(base):
            os.makedirs(base, exist_ok=True)

        return os.path.join(base, filename)

    def resource_path(self, relative_path):
        """Helper to access assets in exe or script"""
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    
    
    @mainthread
    def make_consultants_container(self, role):
        if not self.consultants:
            self.show_snack("No workers found")
            return

        prvb = RecycleBoxLayout(
            default_size=(None, dp(100)),
            default_size_hint=(1, None),
            size_hint_y=None,
            spacing=dp(5),
            orientation="vertical"
        )
        prvb.bind(minimum_height=prvb.setter("height")) 

        self.consultants_prev = RecycleView(
            scroll_type=['bars', 'content'],
            bar_width=0,
            size_hint=(1, None),
            height=dp(300),
        )
        self.consultants_prev.add_widget(prvb)
        self.consultants_prev.layout_manager = prvb 
        self.consultants_prev.viewclass = "ConsultantsRow"

        data = []
        for c in self.consultants:
            if c['worker_role'] == role:
                data.append({
                    'worker_name': c['worker_name'] or "unknown",
                    'worker_email': c['worker_email'] or "unknown",
                    'worker_role': c['worker_role'] or "unknown",
                    'show_profile': lambda x=c['worker_name'], y=c['worker_email']: self.display_consultants(x, y)
                })

        self.consultants_prev.data = data
        self.consultants_display_form(self.consultants_prev)

    def consultants_display_form(self, container):
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10), padding = dp(5))
        self.consultants_search_field = MDTextField(
            MDTextFieldHintText(text="search..."),
            mode = "filled"
        )
        self.consultants_search_field.bind(text=lambda instance, value: self.search_workers("search"))
        content.add_widget(self.consultants_search_field)
        content.add_widget(container)
        
        self.consultants_display_dialog = MDDialog(
            MDDialogIcon(icon="magnify", theme_icon_color = "Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Select Your Account", theme_text_color = "Custom", text_color = "blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.consultants_display_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            size_hint_y = None,
            height = dp(300)
        )
        self.consultants_display_dialog.open()
        self.consultants_display_dialog.auto_dismiss = False
        
    def display_consultants(self, consultant, worker_email):
        self.consultants_display_dialog.dismiss()
        self.ids.username.text = consultant
        self.worker_email = worker_email

    def show_consultants(self):
        def on_workers_fetched(workers):
            if not workers:
                self.show_snack("Accounts not found")
                return
            self.consultants = workers
            self.make_consultants_container(self.role)
        
        fetch_workers("all", "all", "desc", callback=on_workers_fetched)
        

    
    def search_workers(self, *args):
        term = self.consultants_search_field.text.strip()

        def on_workers_fetched(workers):
            if not workers:
                return
            self.consultants = workers
            self.update_consultant_rv()

        if not term:
            self.show_snack("Enter something to search")
            fetch_workers("all", "all", "desc", callback=on_workers_fetched)
            return
        
        fetch_workers(
            intent="search",
            search_term=term,
            callback=on_workers_fetched
        )
    
    @mainthread
    def update_consultant_rv(self):
        if hasattr(self, "consultants_prev"):
            self.consultants_prev.data = [
                {
                    'worker_name': c['worker_name'] or "unknown",
                    'worker_eamil': c['worker_email'] or "example@email.com",
                    'worker_role': c['worker_role'] or "unknown",
                    'show_profile': lambda x=c['worker_name'], y=c['worker_email']: self.display_consultants(x, y)
                }
                for c in self.consultants if c['worker_role'] == self.role
            ]
    
    def populate_workers(self):
        if not self.role:
            self.show_snack("Select a role first")
            return
        self.show_consultants()
    
    def create_role(self, role, disp, img):
        self.role = role
        self.ids.role_label.text = disp
        self.ids.disp_img.source = resource_path(f"assets/{img}")
    
    def signin(self):
        if not self.worker_email:
            self.show_snack("Email is not found")
            return
        password = self.ids.password.text.strip()
        if not password:
            self.show_snack("Enter password")
            return

        data = {
            "worker_email": self.worker_email,
            "worker_password": password
        }

        start_worker_signin(data, callback=self.on_login_success)
    
    def on_login_success(self):
        self.ids.password.text = ""
        self.ids.username.text = ""
        if self.role == "Admin":
            self.manager.current = "admin"
        elif self.role == "Receptionist":
            self.manager.current = "reception"
        elif self.role == "Doctor":
            self.manager.current = "doctor"
        elif self.role == "Lab Tech":
            self.manager.current = "lab"
        elif self.role == "Pharmacy":
            self.manager.current = "pharmacy"
    
    def hosp_signin(self):
        if not self.hospital_name_field.text.strip():
            self.show_snack("Email is not found")
            return
        password = self.hospital_password_field.text.strip()
        if not password:
            self.show_snack("Enter password")
            return

        data = {
            "hospital_email": self.hospital_name_field.text.strip(),
            "hospital_password": password
        }

        start_hospital_signin(data, callback=self.on_hsp_login_success)
    
    def on_hsp_login_success(self, hsp_data: dict):
        self.hospital_signin_dialog.dismiss()
        if not hsp_data:
            self.show_snack("Hospital data not found")
            return
        if self.store.exists("hospital"):
            self.store.delete("hospital")
            
        self.store.put(
            "hospital", 
            hsp_id=hsp_data.get("hospital_id"),
            name=hsp_data.get("hospital_name"), 
            email=hsp_data.get("hospital_email"), 
            phone=hsp_data.get("hospital_contact"),
            diag_fee=hsp_data.get("diagnosis_fee"),
            expiry_date = hsp_data.get("expiry_date")
        )
        
        self.hospital_signin_dialog.dismiss()
        self.current_hosp_data = hsp_data
        self.ids.hospital_name.text = hsp_data.get("hospital_name")
        self.ids.hospital_email.text = hsp_data.get("hospital_email")
        self.ids.hospital_phone.text = hsp_data.get("hospital_contact")
        
        self.show_snack("Hospital data saved")

    def toggle_show_pass(self, value):
        if value:
            self.ids.password.password = False
        else:
            self.ids.password.password = True
    
    def toggle_show_hsp_pass(self, value):
        if value:
            self.hospital_password_field.password = False
        else:
            self.hospital_password_field.password  = True
    
    def toggle_show_nhsp_pass(self, value):
        if value:
            self.new_hospital_password.password = False
            self.new_hospital_password_confirm.password = False
        else:
            self.new_hospital_password.password = True
            self.new_hospital_password_confirm.password = True
    
    def hospital_signin_form(self, dt):
        if self.store.exists("hospital"):
            self.populate_page()
            self.show_snack("Using existing hospital data...")
            return
        self.hospital_name_field = MDTextField(MDTextFieldHintText(text = "Hospital Email"))
        self.hospital_password_field = MDTextField(MDTextFieldHintText(text = "Password"), on_text_validate = lambda *a: self.hosp_signin(), password = True)
        register_button = MDButton(
            MDButtonText(
                text = "Register",
                theme_text_color = "Custom",
                text_color = "blue",
            ),
            on_release = lambda *a: self.new_hospital_form(),
            pos_hint = {"center_x": .5},
            style = "outlined",
        )
        content = MDDialogContentContainer(orientation = "vertical", spacing=dp(10), padding=dp(10))
        content.add_widget(self.hospital_name_field)
        content.add_widget(self.hospital_password_field)
        check = MDCheckbox(
            size_hint = (None, None),
            size = (dp(40), dp(40)),
            size_hint_x = 0.1,
            pos_hint = {"center_y": .5},
            on_active =  lambda *a: self.toggle_show_hsp_pass(check.active)
        )
        content.add_widget(
            MDBoxLayout(
                check,
                MDLabel(
                    text = "Show password?",
                    size_hint_x = 0.9,
                    theme_text_color = "Custom",
                    text_color = "blue"
                ),
                spacing = dp(10),
                size_hint_y = None,
                height = dp(40)
            )
        )
        content.add_widget(
            MDLabel(
                text = "No Account?",
                halign = "center",
                theme_text_color = "Custom",
                text_color = "blue",
                size_hint_y = None,
                height = dp(10)
            )
        )
        content.add_widget(register_button)
        
        self.hospital_signin_dialog = MDDialog(
            MDDialogIcon(icon = "bank", theme_icon_color = "Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Hospital Log In", theme_text_color = "Custom", text_color = "blue"),
            content,
            auto_dismiss = False
        )
        self.hospital_signin_dialog.open()
    
    def populate_page(self):
        if not self.store.exists("hospital"):
            self.show_snack("Hospital data doesnt exis")
            Clock.schedule_once(self.hospital_signin_form, 2)
            return
        
        self.ids.hospital_email.text = self.store.get("hospital")['email']
        self.ids.hospital_phone.text = self.store.get("hospital")['phone']
        self.ids.hospital_name.text = self.store.get('hospital')['name']
    
    def confirm_logout_form(self):
        self.confirm_logout_dialog = MDDialog(
            MDDialogIcon(icon = "logout", theme_icon_color = "Custom", icon_color = "red"),
            MDDialogHeadlineText(text = "Logout", theme_text_color = "Custom", text_color = "red"),
            MDDialogContentContainer(
                MDLabel(
                    text = "Logging out is an irreversible process. Your hospital data will be removed. Do you wish to continue?",
                    theme_text_color = "Custom",
                    text_color = "blue",
                    halign = "center"
                )
            ),
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon = "check",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "blue",
                    on_release = lambda *a: self.logout()
                ),
                MDIconButton(
                    icon = "close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.confirm_logout_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            auto_dismiss = False
        )
        self.confirm_logout_dialog.open()
    
    def logout(self):
        self.confirm_logout_dialog.dismiss()
        
        self.ids.hospital_name.text = "Hospital Name"
        self.ids.hospital_email.text = "example@gmail.com"
        self.ids.hospital_phone.text = "0737841451"
        if not self.store.exists("hospital"):
            self.show_snack("No hospital data found")
            return
        self.store.delete("hospital")
        self.show_snack("Logout successful")
        Clock.schedule_once(self.hospital_signin_form, 2)
    
    def new_hospital_form(self):
        self.hospital_signin_dialog.dismiss()
        self.new_hospital_name = MDTextField(MDTextFieldHintText(text = "Name"))
        self.new_hospital_email = MDTextField(MDTextFieldHintText(text = "Email"))
        self.new_hospital_phone = MDTextField(MDTextFieldHintText(text = "Phone"))
        self.new_hospital_diag_fee = MDTextField(MDTextFieldHintText(text = "Diagnosis Fee"))
        self.new_hospital_password = MDTextField(MDTextFieldHintText(text = "Password"), password = True)
        self.new_hospital_password_confirm = MDTextField(MDTextFieldHintText(text = "Confirm"), password = True)
        check = MDCheckbox(
            size_hint = (None, None),
            size = (dp(40), dp(40)),
            size_hint_x = 0.1,
            pos_hint = {"center_y": .5},
            on_active =  lambda *a: self.toggle_show_nhsp_pass(check.active)
        )
        register_button = MDButton(
            MDButtonText(
                text = "Register",
                theme_text_color = "Custom",
                text_color = "blue",
            ),
            on_release = lambda *a: self.prepare_hospital_data(),
            pos_hint = {"center_x": .5},
            style = "outlined",
        )
        content = MDDialogContentContainer(orientation = "vertical", spacing=dp(10), padding=dp(10))
        content.add_widget(self.new_hospital_name)
        content.add_widget(self.new_hospital_email)
        content.add_widget(self.new_hospital_phone)
        content.add_widget(self.new_hospital_diag_fee)
        content.add_widget(self.new_hospital_password)
        content.add_widget(self.new_hospital_password_confirm)
        content.add_widget(
            MDBoxLayout(
                check,
                MDLabel(
                    text = "Show password?",
                    size_hint_x = 0.9,
                    theme_text_color = "Custom",
                    text_color = "blue"
                ),
                spacing = dp(10),
                size_hint_y = None,
                height = dp(40)
            )
        )
        content.add_widget(register_button)
        
        self.new_hospital_dialog = MDDialog(
            MDDialogIcon(icon = "bank", theme_icon_color = "Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Register Hospital", theme_text_color = "Custom", text_color = "blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon = "close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.close_new_dialog()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            auto_dismiss = False
        )
        self.new_hospital_dialog.open()
    
    def close_new_dialog(self):
        self.new_hospital_dialog.dismiss()
        Clock.schedule_once(self.hospital_signin_form, 1)
    
    def prepare_hospital_data(self):
        if hasattr(self, "hospital_signin_dialog"):
            self.hospital_signin_dialog.dismiss()
            
        hosp_name = self.new_hospital_name.text.strip()
        hosp_email = self.new_hospital_email.text.strip()
        hosp_phone = self.new_hospital_phone.text.strip()
        hosp_diag_fee = self.new_hospital_diag_fee.text.strip()
        hosp_password = self.new_hospital_password.text.strip()
        hosp_password_confirm = self.new_hospital_password_confirm.text.strip()
        
        if not hosp_name:
            self.show_snack("Enter Hospital Name")
            return
        if not hosp_email:
            self.show_snack("Enter Hospital Email")
            return
        if not hosp_phone:
            self.show_snack("Enter Hospital Phone")
            return
        if not hosp_diag_fee:
            self.show_snack("Enter Diagnosis Fee")
            return
        if not hosp_password:
            self.show_snack("Enter Hospital Password")
            return
        if not hosp_password_confirm:
            self.show_snack("Confirm Hospital Password")
            return
        
        if hosp_password != hosp_password_confirm:
            self.show_snack("Password Mismatch")
            return
        
        hosp_data = {
            "hospital_name": hosp_name,
            "hospital_email": hosp_email,
            "hospital_contact": hosp_phone,
            "hospital_password": hosp_password,
            "diagnosis_fee": float(hosp_diag_fee)
        }
        
        start_hospital_creation(hosp_data, callback=self.on_hsp_create_success)
    
    def on_hsp_create_success(self):
        self.new_hospital_dialog.dismiss()
        if hasattr(self, "hospital_signin_dialog"):
            self.hospital_signin_dialog.dismiss()
            
        Clock.schedule_once(self.hospital_signin_form, 2)
    
    def subscription_form(self, dt):
        print("Calling dialog...")
        self.activation_key = MDTextField(MDTextFieldHintText(text = "Enter Activation Key"), on_text_validate = lambda *a: self.renew_plan())

        contact_cont = MDGridLayout(cols = 4, size_hint_y = None, height = dp(60), adaptive_height=True, spacing = dp(40))

        phone_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(60))
        phone_box.add_widget(MDIcon(icon = "phone", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        phone_box.add_widget(MDLabel(text = "0768 724 595", bold = True, pos_hint = {"center_y":.5}, theme_text_color = "Custom", text_color = "navy"))

        whatsapp_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(60))
        whatsapp_box.add_widget(MDIcon(icon = "whatsapp", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "green"))
        whatsapp_box.add_widget(MDLabel(text = "0737 841 451", bold = True, pos_hint = {"center_y":.5}, theme_text_color = "Custom", text_color = "teal"))

        contact_cont.add_widget(Widget(size_hint_x = None, width = dp(50)))
        contact_cont.add_widget(phone_box)
        contact_cont.add_widget(whatsapp_box)
        contact_cont.add_widget(Widget(size_hint_x = None, width = dp(50)))

        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(30))
        content.add_widget(self.activation_key)
        content.add_widget(MDDivider())
        content.add_widget(MDLabel(text = "Get in touch", halign = "center", theme_text_color = "Custom", text_color = "blue"))
        content.add_widget(contact_cont)
        
        self.subscription_dialog = MDDialog(
            MDDialogIcon(icon = "cancel", theme_icon_color = "Custom", icon_color = "red"),
            MDDialogHeadlineText(text = "Plan Renewal", theme_text_color = "Custom", text_color = "blue"),
            MDDialogSupportingText(text = "Your plan expired! Please enter activation key bellow", theme_text_color = "Custom", text_color = "blue"),
            content,
            auto_dismiss = False,
            size_hint_x = .8
            
        )

        self.subscription_dialog.open()
    
    def renew_plan(self):
        key = self.activation_key.text.strip()
        if not key:
            self.show_snack("Activation key empty!")
            return
        Thread(target=self.start_plan_renewal, args=(key,), daemon=True).start()


    def start_plan_renewal(self, key):
        try:
            url = f"{SERVER_URL}hospitals/renew-activation/?hospital_id={self.store.get('hospital')['hsp_id']}&activation_key={key}"
            response = requests.put(url, timeout=3).json()

            if response.get("message") == "renewed":
                self.subscription_dialog.dismiss()
                self.show_snack("Your plan renewed! Enjoy :-)")
                self.update_plan()
            else:
                self.show_snack(response.get("message", "Renewal failed"))
        except Exception as e:
            self.show_snack(f"Error: {e}")


    def update_plan(self):
        Thread(target=self.start_plan_update, daemon=True).start()


    def start_plan_update(self):
        try:
            if not self.store.exists("hospital"):
                return

            url = f"{SERVER_URL}hospitals/hospitals-specific/?hospital_id={self.store.get('hospital')['hsp_id']}"
            response = requests.get(url)

            if response.status_code != 200:
                self.show_snack("Failed to update plan")
                return

            hsp_data = response.json()
            if not hsp_data:
                self.show_snack("Invalid response data")
                return

            self.show_snack("Updating hospital plan...")
            self.store.put(
                "hospital",
                hsp_id=hsp_data.get("hospital_id"),
                name=hsp_data.get("hospital_name"),
                email=hsp_data.get("hospital_email"),
                phone=hsp_data.get("hospital_contact"),
                diag_fee=hsp_data.get("diagnosis_fee"),
                expiry_date=hsp_data.get("expiry_date"),
            )
            self.show_snack("Plan updated successfully!")
        except Exception as e:
            self.show_snack(f"Error updating plan: {e}")

    
    def check_expiry(self):
        if not self.store.exists("hospital"):
            return

        exp_str = self.store.get("hospital")['expiry_date']
        exp = datetime.fromisoformat(exp_str)

        if exp < datetime.now():
            self.show_snack("Your plan expired!")
            Clock.schedule_once(self.subscription_form, 3)

    
    @mainthread
    def show_snack(self, text):
        MDSnackbar(
            MDSnackbarText(text=text), 
            pos_hint={'center_x': 0.5}, 
            size_hint_x=0.5, 
            orientation='horizontal'
        ).open()