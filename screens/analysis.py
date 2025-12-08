from kivy.lang import Builder
from kivy.clock import mainthread, Clock
from kivy_garden.matplotlib import FigureCanvasKivyAgg
from kivy.metrics import dp, sp



from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from screens.patients import fetch_patients
from screens.drugs import fetch_drugs
from screens.billings import fetch_billings
from config import resource_path, SERVER_URL, STORE
from utils import PDFDownloader

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import webbrowser
from threading import Thread


Builder.load_file(resource_path("screens/analysis.kv"))

class AnalysisScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.patients = []
        self.drugs = []
        self.billings = []

        self.expired_drugs = []
        self.depleted_drugs = []
        self.sellable_drugs = []
        self.safe_drugs = []
        self.available_drugs = []

        self.store = STORE

        self.pdf_downloader = PDFDownloader()
    
    def fetch_patients_data(self):
        fetch_patients("all", "all", "desc", callback=self.on_patients_fetched)
    
    def fetch_drugs_data(self):
        fetch_drugs("all", "all", "desc", callback=self.on_drugs_fetched)
    
    def fetch_billings_data(self):
        fetch_billings("all", None, callback=self.on_billings_fetched)
    
    def on_billings_fetched(self, billings):
        if not billings:
            self.show_snack("Billings not found")
            return
        self.billings = billings
        self.start_billings_analysis()

    def on_patients_fetched(self, patients):
        if not patients:
            self.show_snack("Patients not found")
            return
        self.patients = patients
        self.start_patient_analysis()
    
    def on_drugs_fetched(self, drugs):
        if not drugs:
            self.show_snack("Drugs not found")
            return
        self.drugs = drugs
        self.start_drug_analysis()
    
    def start_patient_analysis(self):
        if not self.patients:
            self.show_snack("No patients to analyse")
            return
        self.analyse_all_patients()
        self.analyse_new_patients()
        self.analyse_age_patients()
        self.analyse_gender_patients()
        Thread(target=self.plot_weekly_patients, daemon=True).start()
        Thread(target=self.plot_monthly_patients, daemon=True).start()
    
    def analyse_all_patients(self):
        total = len(self.patients)
        self.ids.total_patients_label.text = self.human_readable(total)
    
    def analyse_new_patients(self):
        today = datetime.today().date()
        thirty_days_ago = today - timedelta(days=30)

        new_pats = [
            pat for pat in self.patients
            if thirty_days_ago <= datetime.strptime(pat['date_added'], "%Y-%m-%d").date() <= today
        ]

        self.ids.new_patients_label.text = self.human_readable(len(new_pats))
    
    def analyse_gender_patients(self):
        male_pats = [pat for pat in self.patients if pat['patient_gender'].lower() == "male"]
        female_pats = [pat for pat in self.patients if pat['patient_gender'].lower() == "female"]

        self.ids.male_patients_label.text = self.human_readable(len(male_pats))
        self.ids.female_patients_label.text = self.human_readable(len(female_pats))
    
    def analyse_age_patients(self):
        today = datetime.today().date()
        adult_pats = []
        child_pats = []

        for pat in self.patients:
            dob = datetime.strptime(pat["patient_dob"], "%Y-%m-%d").date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            if age >= 18:
                adult_pats.append(pat)
            else:
                child_pats.append(pat)

        self.ids.adult_patients_label.text = self.human_readable(len(adult_pats))
        self.ids.child_patients_label.text = self.human_readable(len(child_pats))
    
    def plot_weekly_patients(self):
        today = datetime.today().date()
        last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]  

        counts = [
            sum(
                1 for pat in self.patients
                if datetime.strptime(pat["date_added"], "%Y-%m-%d").date() == day
            )
            for day in last_7_days
        ]

        fig, ax = plt.subplots(figsize=(7,4), dpi=100)
        bars = ax.bar(
            [day.strftime("%a") for day in last_7_days],
            counts,
            color="#4A90E2",    
            edgecolor="#2B5DAB",
            linewidth=1,
            alpha=0.9
        )

        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2,
                height + 0.01,
                str(height),
                ha='center',
                va='bottom',
                fontsize=10,
                color="#2B5DAB",
                fontweight='bold'
            )

        ax.set_title("Patients Added in Last 7 Days", fontsize=14, fontweight='bold', color="#4A90E2")
        ax.set_xlabel("Day", fontsize=12, color="#4A90E2")
        ax.set_ylabel("Number of Patients", fontsize=12, color="#4A90E2")
        ax.tick_params(colors="#4A90E2")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color("#4A90E2")
        ax.spines['bottom'].set_color("#4A90E2")
        ax.yaxis.grid(True, linestyle='--', alpha=0.4)

        fig.tight_layout()

        Clock.schedule_once(lambda dt: self._update_weekly_patients(fig))

    def _update_weekly_patients(self, fig):
        self.ids.weekly_patients.clear_widgets()
        self.ids.weekly_patients.add_widget(FigureCanvasKivyAgg(fig))

    def plot_monthly_patients(self):
        today = datetime.today().date()
        first_day = today.replace(day=1)

        month_days = []
        current_day = first_day
        while current_day <= today:
            month_days.append(current_day)
            current_day += timedelta(days=1)

        counts = [
            sum(
                1 for pat in self.patients
                if datetime.strptime(pat["date_added"], "%Y-%m-%d").date() == day
            )
            for day in month_days
        ]

        fig, ax = plt.subplots(figsize=(10,4), dpi=100)
        ax.plot(
            [day.day for day in month_days], 
            counts,
            marker='o',
            linestyle='-',
            color="#4A90E2",
            linewidth=2,
            markersize=6,
            alpha=0.9
        )

        for x, y in zip([day.day for day in month_days], counts):
            if y > 0:
                ax.text(x, y + 0.01, str(y), ha='center', va='bottom', fontsize=9, color="#2B5DAB")

        ax.set_title("Patients Added This Month", fontsize=14, fontweight='bold', color="#4A90E2")
        ax.set_xlabel("Day of Month", fontsize=12, color="#4A90E2")
        ax.set_ylabel("Number of Patients", fontsize=12, color="#4A90E2")
        ax.tick_params(colors="#4A90E2")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color("#4A90E2")
        ax.spines['bottom'].set_color("#4A90E2")
        ax.yaxis.grid(True, linestyle='--', alpha=0.4)

        self.ids.monthly_patients.clear_widgets()

        Clock.schedule_once(lambda dt: self._update_monthly_patients(fig))

    def _update_monthly_patients(self, fig):
        self.ids.monthly_patients.clear_widgets()
        self.ids.monthly_patients.add_widget(FigureCanvasKivyAgg(fig))
    
    def start_drug_analysis(self):
        if not self.drugs:
            return
        self.analyse_all_drugs()
        self.analyse_new_drugs()
        self.analyse_expired_drugs()
        self.analyse_safe_drugs()
        self.analyse_available_drugs()
        self.analyse_depleted_drugs()
        self.analyse_sellable_drugs()
        Thread(target=self.plot_drug_charts, daemon=True).start()
    
    def analyse_all_drugs(self):
        all_drugs = len(self.drugs)
        self.ids.total_drugs_label.text = self.human_readable(all_drugs)
    
    def analyse_new_drugs(self):
        today = datetime.today().date()
        thirty_days_ago = today - timedelta(days=30)

        new_drugs = [
            drug for drug in self.drugs
            if thirty_days_ago <= datetime.strptime(drug['date_added'], "%Y-%m-%d").date() <= today
        ]

        self.ids.new_drugs_label.text = self.human_readable(len(new_drugs))
    
    def analyse_expired_drugs(self):
        today = datetime.today().date()
        expired_drugs = [drug for drug in self.drugs if datetime.strptime(drug["drug_expiry"], "%Y-%m-%d").date() <= today]
        
        self.expired_drugs = expired_drugs

        self.ids.expired_drugs_label.text = self.human_readable(len(expired_drugs))
    
    def analyse_safe_drugs(self):
        today = datetime.today().date()
        safe_drugs = [drug for drug in self.drugs if datetime.strptime(drug["drug_expiry"], "%Y-%m-%d").date() > today]
        
        self.safe_drugs = safe_drugs

        self.ids.safe_drugs_label.text = self.human_readable(len(safe_drugs))

    def analyse_available_drugs(self):
        available_drugs = [drug for drug in self.drugs if drug["drug_quantity"] > 0]

        self.available_drugs = available_drugs

        self.ids.available_drugs_label.text = self.human_readable(len(available_drugs))
    
    def analyse_depleted_drugs(self):
        depleted_drugs = [drug for drug in self.drugs if drug["drug_quantity"] <= 0]

        self.depleted_drugs = depleted_drugs

        self.ids.depleted_drugs_label.text = self.human_readable(len(depleted_drugs))
    
    def analyse_sellable_drugs(self):
        today = datetime.today().date()
        expired_drugs = [drug for drug in self.drugs if datetime.strptime(drug["drug_expiry"], "%Y-%m-%d").date() <= today]

        sellable_drugs  = [
            drug 
            for drug in self.drugs
            if drug['drug_quantity'] > 0 and 
            drug not in expired_drugs
        ]

        self.sellable_drugs = sellable_drugs

        self.ids.sellable_drugs_label.text = self.human_readable(len(sellable_drugs))
    
    def plot_drug_charts(self):
        pie_labels = ["Expired", "Safe", "Sellable"]
        pie_sizes = [len(self.expired_drugs), len(self.safe_drugs), len(self.sellable_drugs)]
        if sum(pie_sizes) == 0: 
            pie_sizes = [1,0,0]
        pie_colors = ["#E74C3C", "#2ECC71", "#3498DB"] 
        explode = (0.05, 0.05, 0.05)  

        fig1, ax1 = plt.subplots(figsize=(6,6), dpi=120)
        wedges, texts, autotexts = ax1.pie(
            pie_sizes,
            labels=pie_labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=pie_colors,
            explode=explode,
            shadow=False,  
            wedgeprops={'edgecolor':'white'}
        )
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(11)
            autotext.set_fontweight('bold')
        ax1.set_title("Drug Status Distribution", fontsize=16, fontweight='bold', color="#34495E")
        ax1.axis('equal')
        fig1.tight_layout()

        donut_labels = ["Available", "Depleted", "Sellable"]
        donut_sizes = [len(self.available_drugs), len(self.depleted_drugs), len(self.sellable_drugs)]
        if sum(donut_sizes) == 0:
            donut_sizes = [1,0,0]
        donut_colors = ["#1ABC9C", "#F39C12", "#3498DB"]
        explode_donut = (0.05, 0.05, 0.05)

        fig2, ax2 = plt.subplots(figsize=(6,6), dpi=120)
        wedges2, texts2, autotexts2 = ax2.pie(
            donut_sizes,
            labels=donut_labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=donut_colors,
            explode=explode_donut,
            shadow=False,
            wedgeprops={'edgecolor':'white', 'width':0.4}  
        )
        for autotext in autotexts2:
            autotext.set_color('magenta')
            autotext.set_fontsize(11)
            autotext.set_fontweight('bold')
        ax2.set_title("Drug Availability", fontsize=16, fontweight='bold', color="#34495E")
        ax2.axis('equal')
        fig2.tight_layout()

        Clock.schedule_once(lambda dt: self._update_drug_charts(fig1, fig2))

    def _update_drug_charts(self, fig1, fig2):
        self.ids.drug_pie_chart.clear_widgets()
        self.ids.drug_pie_chart.add_widget(FigureCanvasKivyAgg(fig1))

        self.ids.drug_donut_chart.clear_widgets()
        self.ids.drug_donut_chart.add_widget(FigureCanvasKivyAgg(fig2))


    def start_billings_analysis(self):
        if not self.billings:
            self.show_snack("No billings to analyse")
            return
        self.compare_monthly_sales()
        Thread(target=self.plot_monthly_revenue_waterfall, daemon=True).start()
    

    def compare_monthly_sales(self):
        today = datetime.today()
        current_month = today.month
        current_year = today.year


        if current_month == 1: 
            last_month = 12
            last_month_year = current_year - 1
        else:
            last_month = current_month - 1
            last_month_year = current_year


        this_month_total = sum(
            bill['total'] for bill in self.billings
            if datetime.strptime(bill['created_at'], "%Y-%m-%d").year == current_year
            and datetime.strptime(bill['created_at'], "%Y-%m-%d").month == current_month
        )

        last_month_total = sum(
            bill['total'] for bill in self.billings
            if datetime.strptime(bill['created_at'], "%Y-%m-%d").year == last_month_year
            and datetime.strptime(bill['created_at'], "%Y-%m-%d").month == last_month
        )


        if last_month_total == 0:
            percentage_diff = None  
        else:
            percentage_diff = ((this_month_total - last_month_total) / last_month_total) * 100

        self.ids.last_month_revenue.text = f"Ksh. {self.human_readable(last_month_total)}"
        self.ids.this_month_revenue.text = f"ksh. {self.human_readable(this_month_total)}"
    
    def plot_monthly_revenue_waterfall(self):
        today = datetime.today().date()
        first_day = today.replace(day=1)
        last_day = today

        month_days = []
        current_day = first_day
        while current_day <= last_day:
            month_days.append(current_day)
            current_day += timedelta(days=1)

        daily_revenue = [
            sum(
                bill['total']
                for bill in self.billings
                if datetime.strptime(bill['created_at'], "%Y-%m-%d").date() == day
            )
            for day in month_days
        ]

        cumulative = [0]
        for rev in daily_revenue:
            cumulative.append(cumulative[-1] + rev)
        starts = cumulative[:-1]

        fig, ax = plt.subplots(figsize=(12, 5), dpi=100)

        for i, day in enumerate(month_days):
            bar_color = "#4A90E2" if daily_revenue[i] >= 0 else "#E74C3C"
            bar = ax.bar(
                day.day,
                daily_revenue[i],
                bottom=starts[i],
                color=bar_color,
                edgecolor="#2B5DAB",
                linewidth=1,
                alpha=0.85
            )

            height = daily_revenue[i]
            if height != 0:
                ax.text(
                    day.day,
                    starts[i] + height/2,
                    f"{height:.0f}",
                    ha='center',
                    va='center',
                    fontsize=10,
                    fontweight='bold',
                    color='white'
                )

        ax.set_title("Daily Revenue (This Month)", fontsize=16, fontweight='bold', color="#34495E")
        ax.set_xlabel("Day of Month", fontsize=12, color="#34495E")
        ax.set_ylabel("Revenue", fontsize=12, color="#34495E")
        ax.tick_params(colors="#34495E")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color("#34495E")
        ax.spines['bottom'].set_color("#34495E")
        ax.yaxis.grid(True, linestyle='--', alpha=0.4)
        ax.set_xticks([day.day for day in month_days])
        ax.set_xticklabels([str(day.day) for day in month_days], rotation=45)
        fig.tight_layout()

        Clock.schedule_once(lambda dt: self._update_monthly_waterfall(fig))

    def _update_monthly_waterfall(self, fig):
        self.ids.monthly_revenue_waterfall.clear_widgets()
        self.ids.monthly_revenue_waterfall.add_widget(FigureCanvasKivyAgg(fig))


    def human_readable(self, num: int) -> str:
        if num < 1_000:
            return str(num)
        elif num < 1_000_000:
            return f"{num/1_000:.0f}K" if num % 1_000 == 0 else f"{num/1_000:.1f}K"
        elif num < 1_000_000_000:
            return f"{num/1_000_000:.0f}M" if num % 1_000_000 == 0 else f"{num/1_000_000:.1f}M"
        else:
            return f"{num/1_000_000_000:.0f}B" if num % 1_000_000_000 == 0 else f"{num/1_000_000_000:.1f}B"

    # Handle mapping, showing and viewing of patients...
    def patients_mapper(self, pat: dict):
        return {
            'patient_name': pat.get("patient_name", "unknown") or "Unknown",
            'patient_email': pat.get("patient_email", "example@gmail.com") or "example@gmail.com",
            'patient_phone': pat.get("patient_phone", "0712345678") or "071234567",
            'show_profile': lambda x = "Cannot view details in this screen": self.show_snack(x)
        }

    def display_patients(self, filter):
        self.ids.rec_box.clear_widgets()
        if not self.patients:
            self.show_snack("No patients to display")
            return
        if filter == "total":
            patients = self.patients
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("patients", "all")

        elif filter == "new":
            today = datetime.today().date()
            thirty_days_ago = today - timedelta(days=30)

            patients = [
                pat for pat in self.patients
                if thirty_days_ago <= datetime.strptime(pat['date_added'], "%Y-%m-%d").date() <= today
            ]
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("patients", "new")

        elif filter == "adults":
            today = datetime.today().date()
            adult_pats = []

            for pat in self.patients:
                dob = datetime.strptime(pat["patient_dob"], "%Y-%m-%d").date()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                
                if age >= 18:
                    adult_pats.append(pat)
            
            patients = adult_pats

            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("patients", "adults")
        
        elif filter == "children":
            today = datetime.today().date()
            child_pats = []

            for pat in self.patients:
                dob = datetime.strptime(pat["patient_dob"], "%Y-%m-%d").date()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                
                if age < 18:
                    child_pats.append(pat)
            
            patients = child_pats
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("patients", "children")
        elif filter == "male":
            patients = [pat for pat in self.patients if pat['patient_gender'].lower() == "male"]
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("patients", "male")
        
        elif filter == "female":
            patients = [pat for pat in self.patients if pat['patient_gender'].lower() == "female"]
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("patients", "female")

        self.display_items("PatientsRow", patients, "patient", self.patients_mapper)
        
    def drugs_mapper(self, drug: dict):
        return {
            'drug_name': drug.get("drug_name", "unknown") or "Unknown",
            'drug_category': drug.get("drug_category", "unknown") or "unknown",
            'drug_quantity': f"{drug.get("drug_quantity", 0)} available" or "0",
            'show_profile': lambda x = "Cannot view details in this screen": self.show_snack(x)
        }

    def display_drugs(self, filter):
        self.ids.rec_box.clear_widgets()
        if filter == "total":
            drugs = self.drugs
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("drugs", "all")
        elif filter == "new":
            today = datetime.today().date()
            thirty_days_ago = today - timedelta(days=30)

            drugs = [
                drug for drug in self.drugs
                if thirty_days_ago <= datetime.strptime(drug['date_added'], "%Y-%m-%d").date() <= today
            ]
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("drugs", "new")
        elif filter == "expired":
            today = datetime.today().date()
            drugs = [drug for drug in self.drugs if datetime.strptime(drug["drug_expiry"], "%Y-%m-%d").date() <= today]
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("drugs", "expired")
        
        elif filter == "safe":
            today = datetime.today().date()
            drugs = [drug for drug in self.drugs if datetime.strptime(drug["drug_expiry"], "%Y-%m-%d").date() > today]
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("drugs", "safe")

        elif filter == "available":
            drugs = [drug for drug in self.drugs if drug["drug_quantity"] > 0]
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("drugs", "available")
        
        elif filter == "depleted":
            drugs = [drug for drug in self.drugs if drug["drug_quantity"] <= 0]
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("drugs", "depleted")
        
        elif filter == "sellable":
            today = datetime.today().date()
            expired_drugs = [drug for drug in self.drugs if datetime.strptime(drug["drug_expiry"], "%Y-%m-%d").date() <= today]

            drugs  = [
                drug 
                for drug in self.drugs
                if drug['drug_quantity'] > 0 and 
                drug not in expired_drugs
            ]
            self.ids.pdf_downloader.on_release = lambda *a: self.pdf_downloader.download_document("drugs", "sellable")

        self.display_items("DrugsRow", drugs, "worker", self.drugs_mapper)

    # Making a universal preview display section...
    def display_items(self, prev_class, items, flag, mapper):
        prev = self.ids.rec_view
        self.ids.rec_box.default_size = (None, dp(80))
        prev.viewclass = prev_class

        data = [mapper(i) for i in items]
        prev.data = data
    
    @mainthread
    def show_snack(self, text):
        MDSnackbar(
            MDSnackbarText(text=text),
            pos_hint={'center_x': 0.5},
            size_hint_x=0.5,
            orientation='horizontal'
        ).open()

    def refresh_content(self):
        self.show_snack("Starting refreshing...")
        self.fetch_billings_data()
        self.fetch_drugs_data()
        self.fetch_patients_data()
        self.initialize_analysis()
        self.show_snack("Done refreshing.")

    def initialize_analysis(self):
        self.start_patient_analysis()
        self.start_drug_analysis()
        self.start_billings_analysis()

    def on_enter(self):
        self.fetch_patients_data()
        self.fetch_drugs_data()
        self.fetch_billings_data()
        self.initialize_analysis()