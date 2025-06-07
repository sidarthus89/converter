import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from fractions import Fraction

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


def imperial_to_metric(inches):
    return round(inches * 25.4, 2)

# ----- GUI Logic -----


def add_output_line(text):
    line_frame = tk.Frame(output_frame, bg="white")
    line_label = tk.Label(line_frame, text=text,
                          anchor='w', justify='left', bg="white")
    close_button = tk.Button(
        line_frame, text="✕", command=line_frame.destroy, bg="white", fg="red", bd=0)

    line_label.pack(side="left", fill="x", expand=True, padx=(2, 4))
    close_button.pack(side="right")
    line_frame.pack(fill="x", pady=1)


def convert_inputs(event=None):
    sae_value = sae_entry.get().strip()
    metric_value = metric_entry.get().strip()

    if sae_value:
        result = sae_to_decimal(sae_value)
        if isinstance(result, str):
            add_output_line(result)
        else:
            metric_equiv = imperial_to_metric(result)
            out = f"SAE ({sae_value}) = {format(result, '.4f')}\" = {metric_equiv} mm"
            add_output_line(out)

    if metric_value:
        try:
            mm = float(metric_value)
            dec_in, frac = metric_to_imperial(mm)
            out = f"Metric ({mm} mm) = {format(dec_in, '.4f')}\" ≈ {frac}\""
            add_output_line(out)
        except ValueError:
            add_output_line("Invalid metric input.")


def clear_output():
    for child in output_frame.winfo_children():
        child.destroy()
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
                        metric_equiv = imperial_to_metric(result)
                        output = f"{value} (SAE) = {format(result, '.4f')}\" = {metric_equiv} mm"
                else:
                    try:
                        mm = float(value)
                        dec_in, frac = metric_to_imperial(mm)
                        output = f"{value} mm = {format(dec_in, '.4f')}\" ≈ {frac}\""
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

# ----- GUI Setup -----


root = tk.Tk()
root.title("SAE / Metric Converter")
root.geometry("450x500")
root.resizable(False, False)

tk.Label(root, text="Enter SAE (e.g. 1_1/2 or 3/8):").pack(pady=(10, 0))
sae_entry = tk.Entry(root)
sae_entry.pack(fill="x", padx=10)
sae_entry.bind("<Return>", convert_inputs)

tk.Label(root, text="Enter Metric (e.g. 20 for 20mm):").pack(pady=(10, 0))
metric_entry = tk.Entry(root)
metric_entry.pack(fill="x", padx=10)
metric_entry.bind("<Return>", convert_inputs)

tk.Button(root, text="Convert", command=convert_inputs).pack(pady=10)
tk.Button(root, text="Upload File (list)", command=process_file).pack()

# Scrollable frame for outputs
output_canvas = tk.Canvas(root, height=220, bg="white",
                          highlightthickness=1, highlightbackground="gray")
output_scroll = tk.Scrollbar(
    root, orient="vertical", command=output_canvas.yview)
output_frame = tk.Frame(output_canvas, bg="white")

output_frame.bind(
    "<Configure>",
    lambda e: output_canvas.configure(scrollregion=output_canvas.bbox("all"))
)

canvas_window = output_canvas.create_window(
    (0, 0), window=output_frame, anchor="nw")
output_canvas.configure(yscrollcommand=output_scroll.set)

output_canvas.pack(fill="both", padx=10, pady=(10, 0), expand=False)
output_scroll.pack(fill="y", side="right", in_=output_canvas)

tk.Button(root, text="Clear All", command=clear_output).pack(pady=(5, 2))
tk.Button(root, text="Quit", command=root.destroy).pack(pady=(0, 10))

root.mainloop()
