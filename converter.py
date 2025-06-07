import tkinter as tk
from tkinter import filedialog, messagebox
from fractions import Fraction
import csv

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


def decimal_to_fraction(decimal, max_denominator=64):
    return Fraction(decimal).limit_denominator(max_denominator)


def metric_to_imperial(metric_mm):
    decimal_inches = metric_mm / 25.4
    fraction = decimal_to_fraction(decimal_inches)
    return round(decimal_inches, 4), fraction

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
            add_output_line(
                f'SAE ({sae_value}) = {result}" ≈ {mm_equiv} mm')
    if metric_value:
        try:
            mm = float(metric_value)
            dec_in, frac = metric_to_imperial(mm)
            add_output_line(
                f'Metric ({mm} mm) = {dec_in}" ≈ {frac}"')
        except ValueError:
            add_output_line("Invalid metric input.")


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
                        output = f"{value} (SAE) = {result}\" ≈ {mm_equiv} mm"
                else:
                    try:
                        mm = float(value)
                        dec_in, frac = metric_to_imperial(mm)
                        output = f"{value} mm = {dec_in}\" ≈ {frac}\""
                    except ValueError:
                        output = f"Invalid input: {value}"
                results.append([value, output])
                add_output_line(output)

        if messagebox.askyesno("Save Results", "Do you want to save the results to a CSV file?"):
            save_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                     filetypes=[("CSV files", "*.csv")])
            if save_path:
                with open(save_path, 'w', newline='') as out_csv:
                    writer = csv.writer(out_csv)
                    writer.writerow(["Input", "Result"])
                    writer.writerows(results)
    except Exception as e:
        messagebox.showerror("Error", f"Could not read file:\n{e}")


def add_output_line(text):
    frame = tk.Frame(output_frame, bg="white")
    frame.pack(fill='x', pady=1, padx=2)

    label = tk.Label(frame, text=text, anchor='w', justify='left', bg="white")
    label.pack(side='left', fill='x', expand=True)

    close_btn = tk.Button(frame, text='x', command=frame.destroy,
                          fg="red", bg="white", bd=0, padx=4, font=("Arial", 10, "bold"))
    close_btn.pack(side='right')


def clear_output():
    for widget in output_frame.winfo_children():
        widget.destroy()


def handle_enter(event):
    convert_inputs()

# ----- GUI Setup -----


root = tk.Tk()
root.title("SAE / Metric Converter")
root.geometry("500x500")
root.resizable(False, False)

tk.Label(root, text="Enter SAE (e.g. 1_1/2 or 3/8):").pack(pady=(10, 0))
sae_entry = tk.Entry(root)
sae_entry.pack()
sae_entry.bind("<Return>", handle_enter)

tk.Label(root, text="Enter Metric (e.g. 20 for 20mm):").pack(pady=(10, 0))
metric_entry = tk.Entry(root)
metric_entry.pack()
metric_entry.bind("<Return>", handle_enter)

tk.Button(root, text="Convert", command=convert_inputs).pack(pady=10)
tk.Button(root, text="Upload File (list)", command=process_file).pack()

output_canvas = tk.Canvas(root, height=250, width=460, bg="white")
output_canvas.pack(pady=10)

scrollbar = tk.Scrollbar(root, orient="vertical", command=output_canvas.yview)
scrollbar.pack(side="right", fill="y")

output_frame = tk.Frame(output_canvas, bg="white")
output_canvas.create_window((0, 0), window=output_frame, anchor='nw')
output_canvas.configure(yscrollcommand=scrollbar.set)


def on_frame_configure(event):
    output_canvas.configure(scrollregion=output_canvas.bbox("all"))


output_frame.bind("<Configure>", on_frame_configure)

tk.Button(root, text="Clear All", command=clear_output).pack(pady=(0, 10))
tk.Button(root, text="Quit", command=root.destroy).pack(pady=(0, 10))

root.mainloop()
