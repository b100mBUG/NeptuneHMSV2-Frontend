from kivy.lang import Builder
from kivy.clock import mainthread
from kivy_garden.matplotlib import FigureCanvasKivyAgg



from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from screens.patients import fetch_patients
from config import resource_path

from datetime import datetime, timedelta
import matplotlib.pyplot as plt


Builder.load_file(resource_path("screens/analysis.kv"))

class AnalysisScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.patients = []
        self.fetch_data()
    
    def fetch_data(self):
        fetch_patients("all", "all", "desc", callback=self.on_patients_fetched)
    
    def on_patients_fetched(self, patients):
        if not patients:
            self.show_snack("Patients not found")
            return
        self.patients = patients
        self.start_patient_analysis()
    
    def start_patient_analysis(self):
        if not self.patients:
            self.show_snack("No patients to analyse")
            return
        self.analyse_all_patients()
        self.analyse_new_patients()
        self.analyse_age_patients()
        self.analyse_gender_patients()
        self.plot_weekly_patients()
        self.plot_monthly_patients()
    
    def analyse_all_patients(self):
        total = len(self.patients)
        self.ids.total_patients_label.text = self.human_readable(total)
    
    def analyse_new_patients(self):
        new_pats = [pat for pat in self.patients if datetime.strptime(pat['date_added'], "%Y-%m-%d").date() <= datetime.today().date()]

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
        self.ids.monthly_patients.add_widget(FigureCanvasKivyAgg(fig))
    
    def human_readable(self, num: int) -> str:
        if num < 1_000:
            return str(num)
        elif num < 1_000_000:
            return f"{num/1_000:.0f}K" if num % 1_000 == 0 else f"{num/1_000:.1f}K"
        elif num < 1_000_000_000:
            return f"{num/1_000_000:.0f}M" if num % 1_000_000 == 0 else f"{num/1_000_000:.1f}M"
        else:
            return f"{num/1_000_000_000:.0f}B" if num % 1_000_000_000 == 0 else f"{num/1_000_000_000:.1f}B"


    @mainthread
    def show_snack(self, text):
        MDSnackbar(
            MDSnackbarText(text=text),
            pos_hint={'center_x': 0.5},
            size_hint_x=0.5,
            orientation='horizontal'
        ).open()

    def initialize_analysis(self):
        self.start_patient_analysis()

    def on_enter(self):
        self.initialize_analysis()