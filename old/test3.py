import tkinter as tk

root = tk.Tk()
root.geometry("200x100")

f1 = tk.Frame(root, background="bisque", width=10, height=100)
f2 = tk.Frame(root, background="pink", width=10, height=100)
main_frame = tk.Frame(root, background="blue", width=90, height=50)

f1.grid(row=0, column=0, sticky="nsew")
f2.grid(row=0, column=1, sticky="nsew")
main_frame.grid(row=0, column=2, sticky="nsew")

root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=0)

root.mainloop()