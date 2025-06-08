import tkinter as tk
from tkinter import filedialog, messagebox
from fractions import Fraction
import csv
import webbrowser
import ctypes

# ----- Conversion Functions -----


def sae_to_decimal(sae_input):
    sae_input = sae_input.replace('_', ' ').replace('-', ' ')
    try:
        if ' ' in sae_input:
            whole, frac = sae_input.split()
            result = float(whole) + float(Fraction(frac))
        else:
            result = float(Fraction(sae_input))
        return round(result, 4)
    except Exception as e:
        return f"Invalid SAE input: {e}"


def nearest_power2_fraction(decimal):
    powers_of_2 = [2, 4, 8, 16, 32, 64]
    best_frac = None
    best_diff = float('inf')
    for denom in powers_of_2:
        numer = round(decimal * denom)
        f = Fraction(numer, denom)
        diff = abs(float(f) - decimal)
        if diff < best_diff:
            best_diff = diff
            best_frac = f
    return best_frac


def metric_to_imperial(metric_mm):
    return round(metric_mm / 25.4, 4)


def decimal_to_sae_approx(decimal):
    frac = nearest_power2_fraction(decimal)
    whole = frac.numerator // frac.denominator
    remainder = frac - whole
    if remainder == 0:
        return f"{whole}"
    elif whole == 0:
        return f"{remainder}"
    else:
        return f"{whole} {remainder}"


# ----- Theme Setup -----
is_dark_mode = False
light_colors = {
    "bg": "#f0f0f0",
    "fg": "#000000",
    "btn_bg": "#e0e0e0",
    "input_bg": "#ffffff",
    "output_bg": "#ffffff"
}

dark_colors = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "btn_bg": "#2d2d2d",
    "input_bg": "#3c3c3c",
    "output_bg": "#3c3c3c"
}

current_colors = light_colors


def toggle_dark_mode():
    global is_dark_mode, current_colors
    is_dark_mode = not is_dark_mode
    current_colors = dark_colors if is_dark_mode else light_colors

    root.configure(bg=current_colors["bg"])

    try:
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        use_dark = 1 if is_dark_mode else 0
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(ctypes.c_int(use_dark)),
            ctypes.sizeof(ctypes.c_int)
        )
    except Exception:
        pass

    for widget in root.winfo_children():
        update_widget_colors(widget)
    update_widget_colors(output_frame)


def update_widget_colors(widget):
    cls = widget.__class__.__name__

    if cls == 'Entry':
        widget.configure(
            bg=current_colors["input_bg"], fg=current_colors["fg"], insertbackground=current_colors["fg"])
    elif cls == 'Label':
        widget.configure(bg=current_colors["bg"], fg=current_colors["fg"])
    elif cls == 'Button':
        widget.configure(bg=current_colors["btn_bg"], fg=current_colors["fg"],
                         activebackground=current_colors["btn_bg"], relief='flat', highlightthickness=0)
    elif cls == 'Frame':
        widget.configure(bg=current_colors["bg"])
    elif cls == 'Canvas':
        widget.configure(bg=current_colors["output_bg"])

    for child in widget.winfo_children():
        update_widget_colors(child)

# ----- GUI Logic -----


def convert_inputs():
    sae_value = sae_entry.get().strip()
    metric_value = metric_entry.get().strip()

    if sae_value:
        result = sae_to_decimal(sae_value)
        if isinstance(result, str):
            add_output_line(result)
        else:
            mm_equiv = round(result * 25.4, 4)
            sae_approx = decimal_to_sae_approx(result)
            add_output_line(
                f'SAE ({sae_value}) = {result}" ≈ {sae_approx}" = {mm_equiv} mm')

    if metric_value:
        try:
            mm = float(metric_value)
            dec_in = metric_to_imperial(mm)
            frac = decimal_to_sae_approx(dec_in)
            op_symbol = "=" if str(frac).replace(" ", "") == str(
                Fraction(dec_in).limit_denominator(64)) else "≈"
            add_output_line(
                f'Metric ({mm} mm) = {dec_in}" {op_symbol} {frac}"')
        except ValueError:
            add_output_line("Invalid metric input.")

    sae_entry.delete(0, tk.END)
    metric_entry.delete(0, tk.END)


def process_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Text or CSV Files", "*.txt *.csv")])
    if not file_path:
        return

    clear_output()
    is_csv = file_path.lower().endswith('.csv')
    results = []

    try:
        with open(file_path, 'r', newline='') as file:
            reader = csv.reader(file) if is_csv else (
                (line.strip(),) for line in file)
            for row in reader:
                if not row or not row[0].strip():
                    continue
                value = row[0].strip()
                if any(x in value for x in ['/', '_', '-']):
                    result = sae_to_decimal(value)
                    if isinstance(result, str):
                        output = result
                    else:
                        mm_equiv = round(result * 25.4, 4)
                        sae_approx = decimal_to_sae_approx(result)
                        output = f"{value} (SAE) = {result}\" ≈ {sae_approx}\" = {mm_equiv} mm"
                else:
                    try:
                        mm = float(value)
                        dec_in = metric_to_imperial(mm)
                        frac = decimal_to_sae_approx(dec_in)
                        op_symbol = "=" if str(frac).replace(" ", "") == str(
                            Fraction(dec_in).limit_denominator(64)) else "≈"
                        output = f"{value} mm = {dec_in}\" {op_symbol} {frac}\""
                    except ValueError:
                        output = f"Invalid input: {value}"
                results.append([value, output])
                add_output_line(output)

        if messagebox.askyesno("Save Results", "Do you want to save the results to a CSV file?"):
            save_path = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if save_path:
                with open(save_path, 'w', newline='') as out_csv:
                    writer = csv.writer(out_csv)
                    writer.writerow(["Input", "Result"])
                    writer.writerows(results)
    except Exception as e:
        messagebox.showerror("Error", f"Could not read file:\n{e}")


def add_output_line(text):
    frame = tk.Frame(output_frame, bg=current_colors["output_bg"])
    frame.pack(fill='x', pady=1, padx=2)

    label = tk.Label(frame, text=text, anchor='w', justify='left',
                     bg=current_colors["output_bg"], fg=current_colors["fg"])
    label.pack(side='left', fill='x', expand=True)

    close_btn = tk.Button(frame, text='x', command=frame.destroy, fg="red", bg=current_colors["output_bg"],
                          bd=0, padx=4, font=("Arial", 10, "bold"))
    close_btn.pack(side='right')


def clear_output():
    for widget in output_frame.winfo_children():
        widget.destroy()


def handle_enter(event):
    convert_inputs()


def open_donation_link():
    webbrowser.open_new("https://paypal.me/pologoalie8908")


# ----- GUI Setup -----
root = tk.Tk()
root.title("SAE / Metric Converter")
root.geometry("540x560")
root.resizable(False, False)
root.configure(bg=current_colors["bg"])

dark_btn = tk.Button(root, text="🌙", command=toggle_dark_mode, bg=current_colors["btn_bg"],
                     fg=current_colors["fg"], borderwidth=0, relief='flat')
dark_btn.place(x=510, y=2, width=25, height=25)

tk.Label(root, text="Enter SAE (e.g. 1_1/2 or 3/8):").pack(pady=(10, 0))
sae_entry = tk.Entry(root, bg=current_colors["input_bg"],
                     fg=current_colors["fg"], insertbackground=current_colors["fg"])
sae_entry.pack()
sae_entry.bind("<Return>", handle_enter)

tk.Label(root, text="Enter Metric (e.g. 20 for 20mm):").pack(pady=(10, 0))
metric_entry = tk.Entry(
    root, bg=current_colors["input_bg"], fg=current_colors["fg"], insertbackground=current_colors["fg"])
metric_entry.pack()
metric_entry.bind("<Return>", handle_enter)

tk.Button(root, text="Convert", command=convert_inputs).pack(pady=10)
tk.Button(root, text="Upload File (list)", command=process_file).pack()

output_frame_container = tk.Frame(root, bg=current_colors["bg"])
output_frame_container.pack(fill="both", expand=True, padx=10, pady=10)

output_canvas = tk.Canvas(output_frame_container, height=280,
                          bg=current_colors["output_bg"], highlightthickness=0)
scrollbar = tk.Scrollbar(output_frame_container,
                         orient="vertical", command=output_canvas.yview)
output_canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
output_canvas.pack(side="left", fill="both", expand=True)

output_frame = tk.Frame(output_canvas, bg=current_colors["output_bg"])
output_canvas.create_window((0, 0), window=output_frame, anchor='nw')


def on_frame_configure(event):
    output_canvas.configure(scrollregion=output_canvas.bbox("all"))


output_frame.bind("<Configure>", on_frame_configure)

button_frame = tk.Frame(root, bg=current_colors["bg"])
button_frame.pack(pady=(0, 10))

tk.Button(button_frame, text="Clear All", command=clear_output,
          width=10).pack(side="left", padx=10)
tk.Button(button_frame, text="Quit", command=root.destroy,
          width=10).pack(side="right", padx=10)

donate_link = tk.Label(root, text="Donate", fg="blue", cursor="hand2", font=("Arial", 10, "underline"),
                       bg=current_colors["bg"])
donate_link.pack(pady=(0, 10))
donate_link.bind("<Button-1>", lambda e: open_donation_link())

root.mainloop()
