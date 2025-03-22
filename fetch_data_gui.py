import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
from tkcalendar import DateEntry  # Import DateEntry from tkcalendar

def fetchDataUsingGui():
    # Load station data
    with open('station.json', 'r') as file:
        station_data = json.load(file)

    # Load train data
    with open('train.json', 'r') as file:
        train_data = json.load(file)

    # Global variable to store the booking info
    train_booking_info = None

    def toggle_password_visibility():
        if password_entry.cget('show') == '':
            password_entry.config(show='*')
            toggle_btn.config(text='Show')
        else:
            password_entry.config(show='')
            toggle_btn.config(text='Hide')

    def on_station_type(event, entry, listbox):
        typed = entry.get()
        listbox.delete(0, tk.END)
        if typed:
            for station in station_data['stations']:
                if typed.lower() in station.lower():
                    listbox.insert(tk.END, station)
        listbox.lift()  # Ensure the listbox is on top
        listbox.place(x=entry.winfo_x(), y=entry.winfo_y() + entry.winfo_height())

    def on_station_select(event, entry, listbox):
        entry.delete(0, tk.END)
        entry.insert(0, listbox.get(tk.ACTIVE))
        listbox.place_forget()

    def on_train_type(event, entry, listbox):
        typed = entry.get()
        listbox.delete(0, tk.END)
        if typed:
            for number, name in train_data.items():
                if typed.lower() in name.lower():
                    listbox.insert(tk.END, f"{name}({number})")
        listbox.lift()  # Ensure the listbox is on top
        listbox.place(x=entry.winfo_x(), y=entry.winfo_y() + entry.winfo_height())

    def on_train_select(event, entry, listbox):
        entry.delete(0, tk.END)
        entry.insert(0, listbox.get(tk.ACTIVE))
        listbox.place_forget()

    def on_date_select(event, entry, cal):
        entry.delete(0, tk.END)
        entry.insert(0, cal.get_date().strftime("%d-%b-%Y"))  # Format the date as desired
        cal.place_forget()

    def validate_form():
        if all([phone_entry.get(), password_entry.get(), origin_entry.get(), destination_entry.get(), date_entry.get(), class_var.get(), train_entry.get(), seat_var.get()]):
            submit_btn.config(state=tk.NORMAL)
        else:
            submit_btn.config(state=tk.DISABLED)

    def submit_form():
        global train_booking_info  # Access the global variable
        train_booking_info = {
            'mobile_number': phone_entry.get(),
            'password': password_entry.get(),
            'from_station': origin_entry.get(),
            'to_station': destination_entry.get(),
            'journey_date': date_entry.get(),
            'seat_class': class_var.get(),
            'train_number': train_entry.get().split('(')[-1].rstrip(')'),
            'seat': seat_var.get(),
            'desired_seats': []
        }
        print("Booking Information:", train_booking_info)  # Print the dictionary
        root.quit()  # Close the form

    root = tk.Tk()
    root.title("Train Booking Information")

    # Add margins to the entire form
    root.configure(padx=20, pady=20)

    # Phone Number
    tk.Label(root, text="Phone Number*").grid(row=0, column=0, sticky='w', pady=(0, 10))  # Add margin below the label
    phone_entry = tk.Entry(root)
    phone_entry.grid(row=0, column=1, pady=(0, 10))  # Add margin below the entry
    phone_entry.bind('<KeyRelease>', lambda event: validate_form())

    # Password
    tk.Label(root, text="Password*").grid(row=1, column=0, sticky='w', pady=(0, 10))  # Add margin below the label
    password_entry = tk.Entry(root, show='*')
    password_entry.grid(row=1, column=1, pady=(0, 10))  # Add margin below the entry
    toggle_btn = tk.Button(root, text='Show', command=toggle_password_visibility)
    toggle_btn.grid(row=1, column=2, pady=(0, 10))  # Add margin below the button
    password_entry.bind('<KeyRelease>', lambda event: validate_form())

    # Origin Station
    tk.Label(root, text="Origin Station*").grid(row=2, column=0, sticky='w', pady=(0, 10))  # Add margin below the label
    origin_entry = tk.Entry(root)
    origin_entry.grid(row=2, column=1, pady=(0, 10))  # Add margin below the entry
    origin_listbox = tk.Listbox(root)
    origin_entry.bind('<KeyRelease>', lambda event: on_station_type(event, origin_entry, origin_listbox))
    origin_listbox.bind('<<ListboxSelect>>', lambda event: on_station_select(event, origin_entry, origin_listbox))

    # Destination Station
    tk.Label(root, text="Destination Station*").grid(row=3, column=0, sticky='w', pady=(0, 10))  # Add margin below the label
    destination_entry = tk.Entry(root)
    destination_entry.grid(row=3, column=1, pady=(0, 10))  # Add margin below the entry
    destination_listbox = tk.Listbox(root)
    destination_entry.bind('<KeyRelease>', lambda event: on_station_type(event, destination_entry, destination_listbox))
    destination_listbox.bind('<<ListboxSelect>>', lambda event: on_station_select(event, destination_entry, destination_listbox))

    # Journey Date
    tk.Label(root, text="Journey Date*").grid(row=4, column=0, sticky='w', pady=(0, 10))  # Add margin below the label
    date_entry = tk.Entry(root)
    date_entry.grid(row=4, column=1, pady=(0, 10))  # Add margin below the entry
    cal = DateEntry(root, date_pattern="y-mm-dd")  # Use a valid date pattern
    date_entry.bind('<1>', lambda event: cal.place(x=date_entry.winfo_x(), y=date_entry.winfo_y() + date_entry.winfo_height()))
    cal.bind('<<DateEntrySelected>>', lambda event: on_date_select(event, date_entry, cal))
    date_entry.bind('<KeyRelease>', lambda event: validate_form())

    # Seat Class
    tk.Label(root, text="Seat Class*").grid(row=5, column=0, sticky='w', pady=(0, 10))  # Add margin below the label
    class_var = tk.StringVar()
    class_dropdown = ttk.Combobox(root, textvariable=class_var)
    class_dropdown['values'] = ("AC_B", "AC_S", "SNIGDHA", "F_BERTH", "F_SEAT", "F_CHAIR", "S_CHAIR", "SHOVAN", "SHULOV", "AC_CHAIR")
    class_dropdown.grid(row=5, column=1, pady=(0, 10))  # Add margin below the dropdown
    class_dropdown.bind('<<ComboboxSelected>>', lambda event: validate_form())

    # Train Name
    tk.Label(root, text="Train Name*").grid(row=6, column=0, sticky='w', pady=(0, 10))  # Add margin below the label
    train_entry = tk.Entry(root)
    train_entry.grid(row=6, column=1, pady=(0, 10))  # Add margin below the entry
    train_listbox = tk.Listbox(root)
    train_entry.bind('<KeyRelease>', lambda event: on_train_type(event, train_entry, train_listbox))
    train_listbox.bind('<<ListboxSelect>>', lambda event: on_train_select(event, train_entry, train_listbox))

    # Seat Type
    tk.Label(root, text="Seat Type*").grid(row=7, column=0, sticky='w', pady=(0, 10))  # Add margin below the label
    seat_var = tk.StringVar()
    seat_dropdown = ttk.Combobox(root, textvariable=seat_var)
    seat_dropdown['values'] = tuple(range(1, 5))
    seat_dropdown.grid(row=7, column=1, pady=(0, 10))  # Add margin below the dropdown
    seat_dropdown.bind('<<ComboboxSelected>>', lambda event: validate_form())

    # Submit Button
    submit_btn = tk.Button(root, text="Submit", command=submit_form, state=tk.DISABLED)
    submit_btn.grid(row=8, column=1, pady=(10, 0))  # Add margin above the button

    root.mainloop()

    # After the form is closed, you can access the global variable
    if train_booking_info:
        return train_booking_info
    else:
        print("No booking information was stored.")


fetchDataUsingGui()