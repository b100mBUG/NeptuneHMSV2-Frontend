from kivy.clock import Clock, mainthread
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

import requests
import asyncio

from config import SERVER_URL, STORE
from threading import Thread
from utils import has_internet
from database.actions.hospital import (
    fetch_hospitals, add_hospital, edit_hospital,
    renew_hospital_plan, delete_hospital, change_password,
    signin
)

store = STORE

def start_hospital_signin(hosp_data: dict, callback=None):
    show_snack("Logging in...")
    Thread(target=signin_thread, args=(hosp_data, callback), daemon=True).start()

def signin_thread(hsp_data, callback):
    #url = f"{SERVER_URL}hospitals/hospitals-signin/"
    #response = requests.post(url, json=hsp_data)
    #if response.status_code != 200:
        #show_snack("Login Failed")
        #return
    #hosp = response.json()
    s#how_snack("Login Successful")

    try:
        db_result = asyncio.run(signin(hsp_data))
        show_snack("Login success")

        hosp = {
            "hospital_id": db_result.hospital_id,
            "hospital_name": db_result.hospital_name,
            "hospital_email": db_result.hospital_email,
            "hospital_contact": db_result.hospital_contact,
            "diagnosis_fee": db_result.diagnosis_fee,
            "expiry_date": f"{db_result.expiry_date}"
        }
    except Exception as e:
        show_snack("Failed to log in. Please try again")
        return
    
    if callback:
        Clock.schedule_once(lambda dt: callback(hosp))

def start_hospital_creation(hosp_data: dict, callback=None):
    show_snack("Adding your hospital...")
    Thread(target=create_thread, args=(hosp_data, callback), daemon=True).start()

def create_thread(hsp_data, callback):
    #url = f"{SERVER_URL}hospitals/hospitals-add/"
    #response = requests.post(url, json=hsp_data)
    #if response.status_code != 200:
        #show_snack("Failed to add your hospital")
        #return
    
    #show_snack("Hospital added successfully")
    try:
        asyncio.run(add_hospital(hsp_data))
        show_snack("Hospital added successfully")
    except Exception as e:
        show_snack("An unexpected error occurred. Please try again")
        return

    if callback:
        Clock.schedule_once(lambda dt: callback())

def start_hospital_editing(hosp_data: dict, callback=None):
    show_snack("Editing your hospital...")
    Thread(target=edit_thread, args=(hosp_data, callback), daemon=True).start()

def edit_thread(hsp_data, callback):
    #url = f"{SERVER_URL}hospitals/hospitals-edit/?hospital_id={store.get("hospital")['hsp_id']}"
    #response = requests.put(url, json=hsp_data)
    #if response.status_code != 200:
        #show_snack("Failed to edit your hospital")
        #return
    #data = response.json()
    try:
        db_result = asyncio.run(edit_hospital(store.get("hospital")['hsp_id'], hsp_data))
        show_snack("Hospital edited successfully.")
        data = {
            "hospital_name": db_result.hospital_name,
            "hospital_email": db_result.hospital_email,
            "hospital_contact": db_result.hospital_contact,
            "diagnosis_fee": db_result.diagnosis_fee
        }
    except Exception as e:
        show_snack("An unexpected error occurred. Please try again.")
        return

    if callback:
        Clock.schedule_once(lambda dt: callback(data))

def start_hospital_password_change(hosp_data: dict, callback = None):
    show_snack("Changing your hospital password...")
    Thread(target=pwd_change_thread, args=(hosp_data, callback), daemon=True).start()

def pwd_change_thread(hsp_data, callback):
    #url = f"{SERVER_URL}hospitals/hospitals-change-password/?hospital_id={store.get("hospital")['hsp_id']}"
    #response = requests.put(url, json=hsp_data)
    #if response.status_code != 200:
        #show_snack("Failed to change your hospital password")
        #return
    
    try:
        asyncio.run(change_password(store.get("hospital")['hsp_id'], hsp_data))
        show_snack("Password changed successfully. Changes will apply on your next login")
    except Exception as e:
        show_snack("An unexpected error occurred. Please try again.")
        return

    if callback:
        Clock.schedule_once(lambda dt: callback())

def start_hospital_deletion(callback = None):
    show_snack("Removing your hospital account...")
    Thread(target=delete_hsp_thread, args=(callback,), daemon=True).start()

def delete_hsp_thread(callback):
    #url = f"{SERVER_URL}hospitals/hospitals-delete/?hospital_id={store.get("hospital")['hsp_id']}"
    #response = requests.delete(url)
    #if response.status_code != 200:
        #show_snack("Failed to delete your hospital account")
        #return
    try:
        asyncio.run(delete_hospital(store.get("hospital")['hsp_id']))
        show_snack("Hospital deleted successfully.")
    except Exception as e:
        show_snack("Ann unexpected erro occurred. Please try again")
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