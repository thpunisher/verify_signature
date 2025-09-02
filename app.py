import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import requests
from datetime import datetime

# ==========================
# Función para llamar a FastAPI
# ==========================
def verify_signatures():
    if not ref_path.get() or not test_path.get():
        messagebox.showwarning("Error", "Both signature images are required!")
        return

    try:
        with open(ref_path.get(), "rb") as f1, open(test_path.get(), "rb") as f2:
            files = {"file_ref": f1, "file_test": f2}
            response = requests.post("http://127.0.0.1:8000/verify", files=files)
        
        if response.status_code == 200:
            data = response.json()
            decision = data['decision'].upper()
            if decision == "GENUINE":
                decision = "ORIGINAL SIGNATURE"
                
            else:
                decision = "FAKE SIGNATURE"
            
            # Mostrar resultado grande
            color = "#4CAF50" if decision=="ORIGINAL SIGNATURE" else "#F44336"
            symbol = "✅" if decision=="ORIGINAL SIGNATURE" else "❌"
            result_label.config(text=f"{symbol} {decision}", fg=color)

            # Agregar al historial solo Original/Fake con hora
            timestamp = datetime.now().strftime("%H:%M:%S")
            display_text = f"{timestamp} | {decision}"
            history_list.insert(tk.END, display_text)
        else:
            messagebox.showerror("Error", "API Error: " + str(response.status_code))
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ==========================
# Funciones para cargar imágenes
# ==========================
def load_ref_image():
    path = filedialog.askopenfilename(title="Select Reference Signature", filetypes=[("Image files", "*.png *.jpg *.jpeg")])
    if path:
        ref_path.set(path)
        img = Image.open(path)
        img.thumbnail((500, 300))  # tamaño visible grande
        img = ImageTk.PhotoImage(img)
        ref_canvas.create_image(0,0, anchor="nw", image=img)
        ref_canvas.image = img  # mantener referencia

def load_test_image():
    path = filedialog.askopenfilename(title="Select Test Signature", filetypes=[("Image files", "*.png *.jpg *.jpeg")])
    if path:
        test_path.set(path)
        img = Image.open(path)
        img.thumbnail((500, 300))  # tamaño visible grande
        img = ImageTk.PhotoImage(img)
        test_canvas.create_image(0,0, anchor="nw", image=img)
        test_canvas.image = img

def reset_all():
    ref_path.set("")
    test_path.set("")
    ref_canvas.delete("all")
    test_canvas.delete("all")
    result_label.config(text="")
    history_list.delete(0, tk.END)

# ==========================
# Ventana principal
# ==========================
root = tk.Tk()
root.title("Bank Signature Verification Dashboard")
root.geometry("1100x700")
root.resizable(False, False)

ref_path = tk.StringVar()
test_path = tk.StringVar()

# ==========================
# Frames
# ==========================
frame_top = tk.Frame(root, pady=10)
frame_top.pack()

frame_images = tk.Frame(root, pady=10)
frame_images.pack()

frame_buttons = tk.Frame(root, pady=20)
frame_buttons.pack()

frame_result = tk.Frame(root)
frame_result.pack(pady=10)

frame_history = tk.Frame(root)
frame_history.pack(pady=10, fill="both", expand=True)

# ==========================
# Título
# ==========================
title = tk.Label(frame_top, text="Bank Signature Verification Dashboard", font=("Arial", 22, "bold"))
title.pack()

# ==========================
# Canvas para previews grandes
# ==========================
ref_canvas = tk.Canvas(frame_images, width=500, height=300, bg="#f0f0f0", relief="ridge")
ref_canvas.grid(row=0, column=0, padx=20, pady=10)
ref_canvas.create_text(250,150,text="Reference Signature", font=("Arial",16))

test_canvas = tk.Canvas(frame_images, width=500, height=300, bg="#f0f0f0", relief="ridge")
test_canvas.grid(row=0, column=1, padx=20, pady=10)
test_canvas.create_text(250,150,text="Test Signature", font=("Arial",16))

# ==========================
# Botones
# ==========================
btn_load_ref = tk.Button(frame_buttons, text="Load Reference", command=load_ref_image, width=25)
btn_load_ref.grid(row=0, column=0, padx=10, pady=5)

btn_load_test = tk.Button(frame_buttons, text="Load Test", command=load_test_image, width=25)
btn_load_test.grid(row=0, column=1, padx=10, pady=5)

btn_verify = tk.Button(frame_buttons, text="Verify Signatures", command=verify_signatures, width=30,font=("Arial", 12, "bold"))
btn_verify.grid(row=1, column=0, columnspan=2, pady=10)

btn_reset = tk.Button(frame_buttons, text="Reset All", command=reset_all, width=30, font=("Arial", 12, "bold"))
btn_reset.grid(row=2, column=0, columnspan=2, pady=5)

# ==========================
# Resultado grande
# ==========================
result_label = tk.Label(frame_result, text="", font=("Arial", 28, "bold"))
result_label.pack()

# ==========================
# Historial
# ==========================
history_label = tk.Label(frame_history, text="Verification History", font=("Arial", 16, "bold"))
history_label.pack()

history_list = tk.Listbox(frame_history, width=60, height=10, font=("Courier", 14))
history_list.pack(pady=5)

# ==========================
root.mainloop()
