from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty
from kivy.metrics import dp, sp
from kivy.uix.textinput import TextInput
from kivy.clock import mainthread

from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText, MDListItemTertiaryText, MDListItemLeadingIcon
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.dialog import MDDialog, MDDialogContentContainer, MDDialogButtonContainer, MDDialogHeadlineText, MDDialogIcon, MDDialogSupportingText
from kivymd.uix.widget import Widget

from screens.drugs import fetch_drugs, start_drug_sale
from datetime import datetime
from config import resource_path

Builder.load_file(resource_path("screens/pos.kv"))

class DrugItemRow(MDListItem):
    drug_name = StringProperty("")
    drug_category = StringProperty("")
    drug_quantity = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.category_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.quantity_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="pill", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.category_label)
        self.add_widget(self.quantity_label)
        
        self.bind(drug_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(drug_category=lambda inst, val: setattr(self.category_label, 'text', val))
        self.bind(drug_quantity=lambda inst, val: setattr(self.quantity_label, 'text', val))

class POSScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_drug = {}
        self.current_cart = []
        
    def drugs_mapper(self, drug: dict | None):
        drug = drug or {}

        return {
            'drug_name': (drug.get("drug_name") or "Unknown").strip(),
            'drug_category': (drug.get("drug_category") or "Unknown").strip(),
            'drug_quantity': f"{drug.get('drug_quantity', 0)} available",
            'show_profile': lambda drug_data=drug: self.display_drug(drug_data)
        }

    
    def show_drugs(self):
        self.show_spinner("Please wait as drugs are fetched...")
        self.ids.search_field.unbind(text=self.search_drugs)
        self.ids.search_field.bind(text=lambda instance, value: self.search_drugs())
        
        self.ids.rec_box.clear_widgets()
        def on_drugs_fetched(drugs):
            if not drugs:
                self.show_snack("Drugs not found")
                self.dismiss_spinner()
                return
            self.dismiss_spinner()
            self.display_items("DrugItemRow", drugs, "worker", self.drugs_mapper)
        
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
            self.display_items("DrugItemRow", drugs, "drug", self.drugs_mapper)
        print("Searching drugs...")
        fetch_drugs(
            intent="search",
            search_term=term,
            callback=on_drugs_fetched
        )
    
    def display_items(self, prev_class, items, flag, mapper):
        prev = self.ids.rec_view
        self.ids.rec_box.default_size = (None, dp(80))
        prev.viewclass = prev_class

        data = [mapper(i) for i in items]
        prev.data = data
    
    def display_drug(self, drug_data: dict):
        if not drug_data:
            return
        expriry_date = drug_data.get("drug_expiry")
        if datetime.strptime(expriry_date, "%Y-%m-%d") < datetime.now():
            self.show_snack("Drug Expired")
            return
        if drug_data.get("drug_quantity") <= 0:
            self.show_snack("Drug Depleted")
            return
        self.ids.drug_name.text = drug_data.get("drug_name")
        self.current_drug = drug_data
    
    def make_row_label(self, text):
        return MDLabel(
            text = text,
            theme_text_color = "Custom",
            text_color = "blue",
            halign = "center"
        )
    
    def make_cart_card(self, cart_data: dict):
        self.cart_row = MDCard(
            size_hint_y = None,
            height = dp(40),
            spacing = dp(10),
            padding = dp(10)
        )
        
        self.cart_row.add_widget(self.make_row_label(cart_data.get("item")))
        self.cart_row.add_widget(self.make_row_label(f"{cart_data.get('qty')}"))
        self.cart_row.add_widget(self.make_row_label(f"Ksh. {cart_data.get('net_price')}"))
        
        return self.cart_row
        
    
    def compute_price(self):
        if not self.current_drug:
            self.show_snack("You have not selected a drug to sell")
            return
        
        qty_str = self.ids.drug_qty.text.strip()
        
        try:
            int(qty_str)
        except Exception as e:
            self.show_snack("Enter valid integer for quantity")
            print("An error occurred: ", e)
            return
        qty = int(qty_str)
        if qty <= 0:
            self.show_snack("Quantity must be greater than 0")
            return
        
        if self.current_drug.get("drug_quantity") < qty:
            self.show_snack("Insufficient drugs. Try a lower ammount")
            return
        
        drug_price = self.current_drug.get("drug_price")
        self.ids.qty.text = f"{qty}"
        self.ids.drug_price.text = f"Ksh. {drug_price}"
        net_price = drug_price * qty
        self.ids.net_price.text = f"{net_price}"
        self.current_cart.append({
            "drug_id": self.current_drug.get("drug_id"),
            "item": self.current_drug.get("drug_name"),
            "qty": qty,
            "net_price": net_price
        })
        if not self.current_cart:
            self.show_snack("Cart is empty")
            return
        
        self.ids.cart_prev.clear_widgets()
        for cart_data in self.current_cart:
            self.ids.cart_prev.add_widget(self.make_cart_card(cart_data))
        
        self.compute_grand_total()
    
    def compute_grand_total(self):
        total = 0
        for cart_item in self.current_cart:
            total += cart_item.get("net_price")
        self.ids.grand_total.text = f"Ksh. {total}"
        
    
    def on_enter(self):
        self.show_drugs()
    
    def make_calc_btn(self, text):
        return MDButton(
            MDButtonText(
                text = text,
                theme_text_color = "Custom",
                text_color = "blue",
                halign = "center",
                theme_font_size = "Custom",
                font_size = sp(30),
                bold = True,
                size_hint_x = None,
                width = dp(100)
            ),
            on_release = lambda *a: self.add_text(text)
        )
    def add_text(self, text):
        self.calc_input.text = f"{self.calc_input.text}{text}"
    
    def show_calculator(self):
        calc_box = MDBoxLayout(
            orientation = "vertical",
            spacing = dp(10),
            adaptive_height = True
        )
        self.calc_input = TextInput(
            size_hint_y=None,
            height=dp(60),
            multiline=False,
            font_size=sp(35),
            foreground_color=(0, 0, 1, 1),
            halign="right",
            on_text_validate = lambda *a: self.calculate()
        )
        button_grid = MDGridLayout(
            cols=4,
            spacing=dp(20),
            padding=dp(5),
            adaptive_size = True,
            pos_hint = {"center_x":.5}
        )
        
        button_grid.add_widget(self.make_calc_btn("1"))
        button_grid.add_widget(self.make_calc_btn("2"))
        button_grid.add_widget(self.make_calc_btn("3"))
        button_grid.add_widget(self.make_calc_btn("+"))
        
        button_grid.add_widget(self.make_calc_btn("4"))
        button_grid.add_widget(self.make_calc_btn("5"))
        button_grid.add_widget(self.make_calc_btn("6"))
        button_grid.add_widget(self.make_calc_btn("-"))
        
        button_grid.add_widget(self.make_calc_btn("7"))
        button_grid.add_widget(self.make_calc_btn("8"))
        button_grid.add_widget(self.make_calc_btn("9"))
        button_grid.add_widget(self.make_calc_btn("*"))
        
        button_grid.add_widget(self.make_calc_btn("."))
        button_grid.add_widget(self.make_calc_btn("0"))
        button_grid.add_widget(self.make_calc_btn("%"))
        button_grid.add_widget(self.make_calc_btn("/"))
        
        calc_box.add_widget(self.calc_input)
        calc_box.add_widget(button_grid)
        calc_box.add_widget(
            MDBoxLayout(
                Widget(),
                MDButton(
                    MDButtonText(
                        text = "=",
                        theme_text_color = "Custom",
                        text_color = "blue",
                        halign = "center",
                        theme_font_size = "Custom",
                        font_size = sp(30),
                        bold = True,
                        size_hint_y = None,
                        height = dp(30)
                    ),
                    on_release = lambda *a: self.calculate()
                ),
                MDButton(
                    MDButtonText(
                        text = "Clear",
                        theme_text_color = "Custom",
                        text_color = "red",
                        halign = "center",
                        theme_font_size = "Custom",
                        font_size = sp(30),
                        bold = True,
                        size_hint_y = None,
                        height = dp(30)
                    ),
                    on_release = lambda *a: self.clear_input()
                ),
                Widget(),
                size_hint_y = None,
                height = dp(60),
                spacing = dp(30),
            )
        )
        
        content = MDDialogContentContainer(spacing = dp(10), padding = dp(10))
        content.add_widget(calc_box)
        self.calc_dialog = MDDialog(
            MDDialogIcon(icon = "calculator", theme_icon_color="Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Calculator", theme_text_color = "Custom", text_color = "blue", bold = True),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon = "close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.calc_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            auto_dismiss = False,
        )
        self.calc_dialog.open()
    
    def calculate(self):
        text = self.calc_input.text.strip()
        ans = ""
        try:
            ans = eval(text)
            self.calc_input.text = f"{ans}"
        except Exception as e:
            self.show_snack("Invalid expression passed")
    
    def clear_input(self):
        self.calc_input.text = ""
        
    def clear_cart(self):
        self.current_cart.clear()
        self.ids.cart_prev.clear_widgets()
        self.ids.grand_total.text = "Ksh. 0.0"
    
    def sale_drugs(self):
        if not self.current_cart:
            self.show_snack("Cart is empty")
            return
        for drug_data in self.current_cart:
            start_drug_sale(drug_data)
        self.current_cart.clear()
        self.ids.cart_prev.clear_widgets()
        self.ids.grand_total.text = "Ksh. 0.0"
        self.show_drugs()
        self.current_drug = {}
    
    def show_snack(self, text):
        MDSnackbar(
            MDSnackbarText(text=text), 
            pos_hint={'center_x': 0.5}, 
            size_hint_x=0.5, 
            orientation='horizontal'
        ).open()
    @mainthread
    def show_spinner(self, display_text: str | None = "Please wait as data is fetched..."):
        spinner = MDCircularProgressIndicator(
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            size_hint=(None, None),
            size=(dp(48), dp(48)),
        )
        self.spinner_dialog = MDDialog(
            MDDialogIcon(icon="clock", theme_icon_color="Custom", icon_color="blue"),
            MDDialogHeadlineText(text = "Loading...", theme_text_color = "Custom", text_color="blue", bold=True),
            MDDialogSupportingText(text= display_text, theme_text_color = "Custom", text_color="blue"),
            MDDialogContentContainer(
                spinner,
                orientation="vertical"
            ),
            auto_dismiss = False
        )
        self.spinner_dialog.open()
    
    @mainthread
    def dismiss_spinner(self):
        self.spinner_dialog.dismiss()