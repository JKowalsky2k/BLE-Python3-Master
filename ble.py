from tkinter import *
import tkinter
from tkinter import messagebox
import customtkinter
import asyncio
import threading
import bleak
import json
from time import sleep
import math
import random

UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

class CubeBleController(customtkinter.CTk):
    def __init__(self, async_loop) -> None:
        super().__init__()

        with open("settings.json", "r") as settings_file:
            self.settings = json.load(settings_file)
            self.title(self.settings["main_window"]["title"])
            self.geometry(f'{self.settings["main_window"]["width"]}x{self.settings["main_window"]["height"]}')
            self.resizable(False,False)

        self.async_loop = async_loop
        self.device = {"name": None, "address": None, "BleakObject": None, "client": None}
        self.security_pattern = None

        self.current_frame = None
        self.switch_frame(ScanConnectFrame)
        # self.switch_frame(SecurityFrame)
        # self.switch_frame(ConfigurationFrame)
  
    def switch_frame(self, new_frame_class):
        try:
            if self.current_frame is not None:
                self.current_frame.destroy()
            self.current_frame = new_frame_class(self)
            self.current_frame.pack(fill=BOTH, expand=True)
        except Exception as error:
            print(f"{error}")

class ScanConnectFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        customtkinter.CTkFrame.__init__(self, master)
        self.master = master

        self.all_devices = dict()
        customtkinter.CTkButton(self, text="Skanuj", command=lambda: self.run_discover_task(self.master.async_loop), width=450, height=50).place(x=25, y=25)
        self.combobox_select_device = customtkinter.CTkComboBox(self, values=["---"], command=self.select_device, width=450, height=50)
        self.combobox_select_device.place(x=25, y=100)
        customtkinter.CTkButton(self, text="Polącz", command=lambda: self.run_connect_task(self.master.async_loop), width=450, height=50).place(x=25, y=175)
        self.label_status = customtkinter.CTkLabel(self, text="", width=450, height=50)
        self.label_status.place(x=25, y=425)
        self.update_status(message="Nie połączony")

    def update_status(self, message):
        self.label_status.configure(text=f"Status: {message}")

    def select_device(self, device_name):
        self.master.device["name"] = device_name
        self.master.device["address"] = self.all_devices[device_name]["address"]
        self.master.device["BleakObject"] = self.all_devices[device_name]["object"]
        print(f"Selected device: {device_name}")

    def update_device_list(self, device_list):
        devices_names = list(device_list.keys())
        self.combobox_select_device.configure(values=devices_names)
        if 0 < len(devices_names):
            self.combobox_select_device.set(devices_names[0])
            self.master.device["name"] = devices_names[0]
            self.master.device["address"] = self.all_devices[devices_names[0]]["address"]
            self.master.device["BleakObject"] = self.all_devices[devices_names[0]]["object"]

    async def discover_devices(self):
        self.update_status(message="Skanowanie...")
        devices = await bleak.BleakScanner.discover()
        for device in devices:
            if device.name != "Unknown":
                 self.all_devices[device.name] = {"address": device.address, "object": device}
        self.update_device_list(device_list=self.all_devices)
        self.update_status(message="Skanowanie zakończone")

    async def connect_to_device(self):
        self.update_status(message="Łączenie...")
        if self.master.device["address"] is not None:
            self.master.device["client"] = bleak.BleakClient(self.master.device["BleakObject"])
            await self.master.device["client"].connect()
            message = "00000000000000000000"
            await self.master.device["client"].write_gatt_char(UUID, message.encode())
            self.master.switch_frame(SecurityFrame)
        else:
            self.update_status("Nie połączono (nie wybrano urządzenia)")

    async def send_to_device(self, message):
        await self.master.device["client"].write_gatt_char(UUID, "".join([str(random.randint(1, 9)) for _ in range(20)]).encode())
        print(f"{message = }")

    def run_discover_task(self, async_loop):
        threading.Thread(target=lambda async_loop: async_loop.run_until_complete(self.discover_devices()), args=(async_loop,)).start()

    def run_connect_task(self, async_loop):
        threading.Thread(target=lambda async_loop: async_loop.run_until_complete(self.connect_to_device()), args=(async_loop,)).start()


class SecurityFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        customtkinter.CTkFrame.__init__(self, master)
        self.master = master

        self.button_next = customtkinter.CTkButton(self, text="Ustaw kod", command=lambda: self.set_security_pattern(), width=141, height=50).place(x=180, y=280)
        self.button_next = customtkinter.CTkButton(self, text="Dalej", command=lambda: self.run_send_task(self.master.async_loop, "CC0000000000"), width=141, height=50)
        self.button_next.place(x=180, y=350)
        self.label_status = customtkinter.CTkLabel(self, text="", width=450, height=50)
        self.label_status.place(x=25, y=425)
        self.update_status(message="Kod bezpieczeństwa nie został ustawiony")
        
        self.checkboxes_security_pattern = dict()
        self.checkboxes_states = list()

        idx = 0
        for row in range(4):
            for col in range(4):
                self.checkboxes_security_pattern[idx] = {"checkbox": None, "state": customtkinter.IntVar(self, 0)}
                self.checkboxes_security_pattern[idx]["checkbox"] = customtkinter.CTkCheckBox(self, text="", variable=self.checkboxes_security_pattern[idx]["state"], onvalue=1, offvalue=0, width=20, height=20)              
                self.checkboxes_security_pattern[idx]["checkbox"].place(x=180+col*40, y=100+row*40)
                idx += 1
        print(f"{self.master.security_pattern = }")

    def str_to_bin_to_dec(self, data):
        return data[0]*128+data[1]*64+data[2]*32+data[3]*16+data[4]*8+data[5]*4+data[6]*2+data[7]*1

    def set_security_pattern(self):
        pattern = ""
        security_pattern_values = list()
        for idx in range(0, len(self.checkboxes_security_pattern.keys())):
            security_pattern_values.append(self.checkboxes_security_pattern[idx]["state"].get())
        self.master.security_pattern = (chr(self.str_to_bin_to_dec(data=security_pattern_values[:8])), chr(self.str_to_bin_to_dec(data=security_pattern_values[8:])))
        print(f"{self.master.security_pattern = }")
        self.update_status(message="Kod bezpieczeństwa został ustawiony")

    def update_status(self, message):
        self.label_status.configure(text=f"Status: {message}")

    async def send_to_device(self, message):
        message = self.master.security_pattern[0]+self.master.security_pattern[1]+message+"000000"
        print(f"{message = }")
        await self.master.device["client"].write_gatt_char(UUID, message.encode())
        self.master.switch_frame(ConfigurationFrame)

    def run_send_task(self, async_loop, message):
        threading.Thread(target=lambda async_loop: async_loop.run_until_complete(self.send_to_device(message=message)), args=(async_loop,)).start()

class ConfigurationFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        customtkinter.CTkFrame.__init__(self, master)
        self.master = master
        self.command = ""
        self.user_data = 100
        with open("settings.json", "r") as settings_file:
            self.settings = json.load(settings_file)

        customtkinter.CTkButton(self, text="PION", command=lambda: self.set_command("M1"), width=210, height=50).place(x=25, y=25)
        customtkinter.CTkButton(self, text="POZIOM", command=lambda: self.set_command("M2"), width=210, height=50).place(x=265, y=25)
        customtkinter.CTkButton(self, text="SKOS", command=lambda: self.set_command("M3"), width=210, height=50).place(x=25, y=100)
        customtkinter.CTkButton(self, text="LAMPKA", command=lambda: self.set_command("M4"), width=210, height=50).place(x=265, y=100)
        customtkinter.CTkButton(self, text="+", command=lambda: self.increment_counter(), width=150, height=50).place(x=25, y=175)
        customtkinter.CTkButton(self, text="-", command=lambda: self.decrement_counter(), width=150, height=50).place(x=325, y=175)
        self.label_user_data = customtkinter.CTkLabel(self, text="", width=100, height=50)
        self.label_user_data.place(x=200, y=175)
        self.label_user_data.configure(text=f"{self.user_data}ms")
        self.button_send = customtkinter.CTkButton(self, text="Wyślij", command=lambda: self.run_send_task(self.master.async_loop), width=450, height=50)
        self.button_send.place(x=25, y=250)
        self.button_back = customtkinter.CTkButton(self, text="Wróć", command=lambda: self.master.switch_frame(SecurityFrame), width=450, height=50)
        self.button_back.place(x=25, y=325)
        self.label_status = customtkinter.CTkLabel(self, text="", width=450, height=50)
        self.label_status.place(x=25, y=425)
        self.update_status(message="Wybierz efekt")

    def increment_counter(self):
        if self.user_data < self.settings["constants"]["delay"]["max"]:
            self.user_data += self.settings["constants"]["delay"]["step"]
        else:
            self.user_data = self.settings["constants"]["delay"]["min"]
        self.label_user_data.configure(text=f"{self.user_data}ms")

    def decrement_counter(self):
        if self.user_data > self.settings["constants"]["delay"]["min"]:
            self.user_data -= self.settings["constants"]["delay"]["step"]
        else:
            self.user_data = self.settings["constants"]["delay"]["max"]
        self.label_user_data.configure(text=f"{self.user_data}ms")

    def set_command(self, command):
        self.command = command
        self.update_status(message=f'Wybrano efekt "{self.settings["constants"]["effects"][command]}"')

    def update_status(self, message):
        self.label_status.configure(text=f"Status: {message}")
    
    def prepare_message(self):
        security_code = self.master.security_pattern[0]+self.master.security_pattern[1]
        data = str(self.user_data).rjust(self.settings["constants"]["msg_data"]["length"], "0")
        msg = security_code+self.command+data
        crc = str(sum([ord(m) for m in msg])).rjust(self.settings["constants"]["msg_crc"]["length"], "0")
        return security_code+self.command+data+crc

    async def send_to_device(self):
        if self.command != "":
            message = self.prepare_message()
            await self.master.device["client"].write_gatt_char(UUID, message.encode())
            self.update_status(message=f'Wysłano konfigurację "{self.settings["constants"]["effects"][self.command]}" i "{self.user_data}ms"')
            print(f"{message = }")
        else:
            self.update_status(message="Nie wybrano efektu")

    def run_send_task(self, async_loop):
        threading.Thread(target=lambda async_loop: async_loop.run_until_complete(self.send_to_device()), args=(async_loop,)).start()

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    app = CubeBleController(async_loop=event_loop)
    app.mainloop()