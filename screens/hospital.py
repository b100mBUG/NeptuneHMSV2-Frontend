from kivy.clock import Clock, mainthread
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
import requests
from config import SERVER_URL, STORE
from threading import Thread

store = STORE

def start_hospital_signin(hosp_data: dict, callback=None):
    show_snack("Logging in...")
    Thread(target=signin_thread, args=(hosp_data, callback), daemon=True).start()

def signin_thread(hsp_data, callback):
    url = f"{SERVER_URL}hospitals/hospitals-signin/"
    response = requests.post(url, json=hsp_data)
    if response.status_code != 200:
        show_snack("Login Failed")
        return
    hosp = response.json()
    show_snack("Login Successful")
    
    if callback:
        Clock.schedule_once(lambda dt: callback(hosp))

def start_hospital_creation(hosp_data: dict, callback=None):
    show_snack("Adding your hospital...")
    Thread(target=create_thread, args=(hosp_data, callback), daemon=True).start()

def create_thread(hsp_data, callback):
    url = f"{SERVER_URL}hospitals/hospitals-add/"
    response = requests.post(url, json=hsp_data)
    if response.status_code != 200:
        show_snack("Failed to add your hospital")
        return
    
    show_snack("Hospital added successfully")
    
    if callback:
        Clock.schedule_once(lambda dt: callback())

def start_hospital_editing(hosp_data: dict, callback=None):
    show_snack("Editing your hospital...")
    Thread(target=edit_thread, args=(hosp_data, callback), daemon=True).start()

def edit_thread(hsp_data, callback):
    url = f"{SERVER_URL}hospitals/hospitals-edit/?hospital_id={store.get("hospital")['hsp_id']}"
    response = requests.put(url, json=hsp_data)
    if response.status_code != 200:
        show_snack("Failed to edit your hospital")
        return
    data = response.json()
    
    show_snack("Hospital edited successfully. Changes will apply on your next login")
    
    if callback:
        Clock.schedule_once(lambda dt: callback(data))

def start_hospital_password_change(hosp_data: dict, callback = None):
    show_snack("Changing your hospital password...")
    Thread(target=pwd_change_thread, args=(hosp_data, callback), daemon=True).start()

def pwd_change_thread(hsp_data, callback):
    url = f"{SERVER_URL}hospitals/hospitals-change-password/?hospital_id={store.get("hospital")['hsp_id']}"
    response = requests.put(url, json=hsp_data)
    if response.status_code != 200:
        show_snack("Failed to change your hospital password")
        return
    
    show_snack("Password changed successfully. Changes will apply on your next login")

    if callback:
        Clock.schedule_once(lambda dt: callback())

def start_hospital_deletion(callback = None):
    show_snack("Removing your hospital account...")
    Thread(target=delete_hsp_thread, args=(callback,), daemon=True).start()

def delete_hsp_thread(callback):
    url = f"{SERVER_URL}hospitals/hospitals-delete/?hospital_id={store.get("hospital")['hsp_id']}"
    response = requests.delete(url)
    if response.status_code != 200:
        show_snack("Failed to delete your hospital account")
        return
    
    if callback:
        Clock.schedule_once(lambda dt: callback())

@mainthread
def show_snack(text):
    MDSnackbar(
        MDSnackbarText(text=text), 
        pos_hint={'center_x': 0.5}, 
        size_hint_x=0.5, 
        orientation='horizontal'
    ).open()