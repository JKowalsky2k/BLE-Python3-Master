from doctest import master
from locale import currency
from tkinter import *
import tkinter
from tkinter import messagebox
import customtkinter
import asyncio
import threading
import random
from bleak import BleakClient, BleakScanner
import bleak
import json
from time import sleep

UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

class CubeBleController(customtkinter.CTk):
    def __init__(self, async_loop) -> None:
        super().__init__()

        with open("settings.json", "r") as settings_file:
            self.settings = json.load(settings_file)
            self.title(self.settings["main_window"]["title"])
            self.geometry(self.settings["main_window"]["resolution"])

        self.async_loop = async_loop
        self.device = {"name": None, "address": None, "BleakObject": None, "client": None}

        self.current_frame = None
        self.switch_frame(ScanConnectFrame)
  
    def switch_frame(self, new_frame_class):
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = new_frame_class(self)
        self.current_frame.pack(fill=BOTH, expand=True)

class ScanConnectFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        customtkinter.CTkFrame.__init__(self, master)
        self.master = master

        self.all_devices = dict()
        customtkinter.CTkButton(self, text="Scan", command=lambda: self.run_discover_task(self.master.async_loop), width=450, height=75).place(x=25, y=25)
        self.combobox_select_device = customtkinter.CTkComboBox(self, values=["---"], command=self.select_device, width=210, height=50)
        self.combobox_select_device.place(x=25, y=125)
        customtkinter.CTkButton(self, text="Connect", command=lambda: self.run_connect_task(self.master.async_loop), width=210, height=50).place(x=265, y=125)
        self.label_status = customtkinter.CTkLabel(self, text="", width=450, height=50)
        self.label_status.place(x=25, y=425)
        self.update_status(message="Not connected")

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
        self.update_status(message="Scanning ...")
        devices = await bleak.BleakScanner.discover()
        for device in devices:
            if device.name != "Unknown":
                 self.all_devices[device.name] = {"address": device.address, "object": device}
        self.update_device_list(device_list=self.all_devices)
        self.update_status(message="Scan finished")

    async def connect_to_device(self):
        if self.master.device["address"] is not None:
            # self.master.device["client"] = await bleak.BleakClient(self.master.device["BleakObject"]).connect()
            self.master.device["client"] = bleak.BleakClient(self.master.device["BleakObject"])
            await self.master.device["client"].connect()
            self.update_status("Connected")
            self.master.switch_frame(ConfigurationFrame)
        else:
            self.update_status("Not Connected (device not selected)")

    def run_discover_task(self, async_loop):
        threading.Thread(target=lambda async_loop: async_loop.run_until_complete(self.discover_devices()), args=(async_loop,)).start()

    def run_connect_task(self, async_loop):
        threading.Thread(target=lambda async_loop: async_loop.run_until_complete(self.connect_to_device()), args=(async_loop,)).start()

class ConfigurationFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        customtkinter.CTkFrame.__init__(self, master)
        self.master = master

        customtkinter.CTkButton(self, text="LED ON", command=lambda: self.run_send_task(self.master.async_loop, "N"), width=210, height=50).place(x=25, y=25)
        customtkinter.CTkButton(self, text="LED OFF", command=lambda: self.run_send_task(self.master.async_loop, "F"), width=210, height=50).place(x=265, y=25)

    async def send_to_device(self, message):
        await self.master.device["client"].write_gatt_char(UUID, message.encode())

    def run_send_task(self, async_loop, message):
        threading.Thread(target=lambda async_loop: async_loop.run_until_complete(self.send_to_device(message=message)), args=(async_loop,)).start()

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    app = CubeBleController(async_loop=event_loop)
    app.mainloop()