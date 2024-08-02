from PIL import ImageGrab, Image, ImageTk
import tkinter as tk
import pytesseract
import time
import cv2
import numpy as np
import ctypes
import asyncio
import threading
import websockets
import json
from ClientSide import send_dps_data,receive_data
### tesseract OCR configuration
### ********** YOU NEED INSTALL TESSERACT https://github.com/UB-Mannheim/tesseract 
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
### pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Python312\Scripts\pytesseract.exe'

# Global event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Variable global para el WebSocket
websocket = None
client_name = None
host_ip = None
# WebSocket callback function
def on_websocket_data(data):
    print("Received data:", data)
    # Aquí puedes actualizar la interfaz o procesar la información recibida

# Función para iniciar el cliente WebSocket
async def start_websocket_client(name, host_ip):
    global websocket
    websocket = await websockets.connect(f'ws://{host_ip}:8765')
    await websocket.send(json.dumps({'name': name}))
    await receive_data(websocket, on_websocket_data)

def run_websocket_client(name, host_ip):
    loop.run_until_complete(start_websocket_client(name, host_ip))


# Función para enviar datos de DPS
async def send_dps(name, dps, total_damage, elapsed_time):
    await send_dps_data(websocket, name, dps, total_damage, elapsed_time)

def capture_screen(bbox=None):
     return ImageGrab.grab(bbox)

def preprocess_image(image):
    ### convert image to numpy array format
    image_np = np.array(image)
    
    ### convert from RGB to HSV
    hsv_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

    ### define the yellow color range in HSV
    lower_yellow = np.array([20, 100, 100])  # adjust these values as needed
    upper_yellow = np.array([30, 255, 255])

    ### define the black color range in HSV
    lower_black = np.array([0, 0, 0], dtype=np.uint8)
    upper_black = np.array([180, 255, 50], dtype=np.uint8)

    ### create masks that identify only the yellow and black components
    mask_yellow = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    mask_black = cv2.inRange(hsv_image, lower_black, upper_black)

    ### change yellow components to black and assume other colors as well
    image_np[mask_yellow > 0] = (0, 0, 0)
    image_np[mask_black > 0] = (0, 0, 255)  # Magenta = RGB(255, 0, 255)

    #gray_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    # Aumentar el contraste
    # contrast_img = cv2.convertScaleAbs(gray_image, alpha=1.5, beta=0)
    
    # # Mejorar la nitidez
    # kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    # sharp_img = cv2.filter2D(contrast_img, -1, kernel)
    
    # # Aplicar umbralización
    # _, binary_image = cv2.threshold(sharp_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # # Convertir de nuevo a imagen PIL para compatibilidad con Tesseract
    # processed_image = Image.fromarray(binary_image)
    # processed_image.save('img/captura_procesada.png')
   
    ### convert to grayscale to improve OCR
    gray_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

    ### apply thresholding
    _, binary_image = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY_INV)
    ### convert back to PIL image for compatibility with Tesseract
    processed_image = Image.fromarray(binary_image)
    processed_image.save('img/captura_procesada.png')
    return processed_image

def extract_health_value(image):
    preprocess_image(image)
    try:
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        ### use Tesseract OCR to extract text
        text = pytesseract.image_to_string("img/captura_procesada.png", config=custom_config)
    except Exception as inst:
        text = "Error", inst.args 
    return text

### function to calculate DPS and other values
def update_dps(name):
    global previous_health, start_time, total_damage, bbox
    if timer_running:
        screen = capture_screen(bbox)
        display_captured_image(screen)
        ### assume you have a function that extracts and converts the health value to integer
        ### change the way values are taken from the image. The improvement will be:
        ### only take the value of the lost health of the dummy and set the maximum health value of the dummy in the UI.
        ### this will help the OCR to better detect the values.
        current_health = extract_health_value(screen)
        cleaned_health = current_health.replace(',', '').replace('.', '').strip()
        print("Extracted value:", cleaned_health)
            
        current_health = int(cleaned_health)

        if previous_health is not None:
            damage = previous_health - current_health
            total_damage += damage
            elapsed_time = time.time() - start_time
            dps = damage / elapsed_time if elapsed_time > 0 else 0
            
            # Update the user interface

            label_dps.config(text=f"DPS: {dps:.2f}")
            label_total_damage.config(text=f"Total Damage: {total_damage}")
            label_time.config(text=f"Refresh: {elapsed_time:.2f}s")

            # Send data to WebSocket server
            asyncio.run_coroutine_threadsafe(send_dps(name,dps, total_damage, elapsed_time), loop)
        
        
        previous_health = current_health
        start_time = time.time()
        update_timer()
        root.after(800, update_dps,name)  ### call this function every 1 second

def reset_counters():
    global previous_health, start_time, total_damage
    previous_health = 1000000
    start_time = time.time()
    total_damage = 0
    stop_timer()
    label_dps.config(text="DPS: 0.00")
    label_total_damage.config(text="Total Damage: 0")
    label_time.config(text="Refresh: 0.00s")

def get_screen_size():
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    return width, height

def on_drag(event):
    global rect, start_x, start_y, canvas
    # Actualizar las coordenadas del rectángulo mientras se arrastra el ratón
    if rect is not None:
        canvas.coords(rect, start_x, start_y, event.x, event.y)

def on_button_press(event):
    global start_x, start_y, rect, canvas
    if rect is not None:
        canvas.delete(rect)

    start_x, start_y = event.x, event.y
    # Crear un rectángulo (inicialmente un solo píxel)
    rect = canvas.create_rectangle(start_x, start_y, start_x + 1, start_y + 1, outline='red', width=2)

def on_button_release(event):
    global bbox, root, display_image_label
    bbox = (start_x, start_y, event.x, event.y)
    img = capture_screen(bbox)
    display_captured_image(img)
    root.attributes('-alpha', 1)
    root.attributes('-fullscreen', False)
    root.deiconify()

def display_captured_image(img):
    global display_image_label
    img_tk = ImageTk.PhotoImage(img)
    display_image_label.config(image=img_tk)
    display_image_label.image = img_tk 


def select_area():
    global root, canvas
    root.withdraw()  # Ocultar la ventana principal temporalmente
    root.attributes('-alpha', 0.2)  # Hacer la ventana ligeramente visible
    root.attributes('-fullscreen', True)  # Pantalla completa para la selección
    root.deiconify()  # Mostrar la ventana para selección
    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_button_release)
    root.deiconify()

def start_timer():
    global timer_running, timer_start_time,start_time,previous_health
    screen = capture_screen(bbox)
    previous_health = int(extract_health_value(screen).replace(',', '').replace('.', '').strip())
    if not client_name:
        print("Please enter your client name.")
        return
    if not timer_running and client_name:
        timer_running = True
        timer_start_time = time.time()
        start_time = time.time()
        update_dps(client_name)
        update_timer()

def stop_timer():
    global timer_running
    timer_running = False 


def update_timer():
    global timer_start_time
    if timer_running:
        formart_time= int(time.time() - timer_start_time)
        label_timeformat.config(text=f"Time: {formart_time} seconds")


### UI
### initialize variables
previous_health = 1000000
total_damage = 0
timer_running = False
timer_start_time = 0
rect = None 
##bbox = (467, 119, 530, 134)  ### define the region where the health bar is located
#bbox = None

### create the user interface
root = tk.Tk()
root.title("DPS Meter")
root.attributes('-topmost', True)
get_screen_size()
canvas = tk.Canvas(root, highlightthickness=0)
canvas.pack(fill=tk.BOTH, expand=True)

# Entry para el nombre del cliente
tk.Label(root, text="Usuario:").pack()
client_name_entry = tk.Entry(root)
client_name_entry.pack()

# Entry para la IP del host
tk.Label(root, text="Host IP:").pack()
host_ip_entry = tk.Entry(root)
host_ip_entry.pack()
def on_connect():
    print("Starting WebSocket client...")
    global client_name, host_ip
    client_name = client_name_entry.get()
    host_ip = host_ip_entry.get()
    if client_name and host_ip:
        # Iniciar el cliente WebSocket en un hilo separado
        websocket_thread = threading.Thread(target=run_websocket_client, args=(client_name, host_ip), daemon=True)
        websocket_thread.start()


# print("Starting WebSocket client...")
#     # Start WebSocket client in a separate thread
# websocket_thread = threading.Thread(target=run_websocket_client, daemon=True)
# websocket_thread.start()

print("Starting Tkinter application...")

connect_button = tk.Button(root, text="Connect", command=on_connect)
connect_button.pack()



display_image_label = tk.Label(root)
display_image_label.pack(fill=tk.BOTH, expand=True)


select_area_button = tk.Button(root, text="Select Area", command=select_area)
select_area_button.pack()


label_dps = tk.Label(root, text="DPS: 0.00", font=('Helvetica', 14))
label_dps.pack()

label_total_damage = tk.Label(root, text="Total Damage: 0", font=('Helvetica', 14))
label_total_damage.pack()

label_time = tk.Label(root, text="Refresh: 0.00s", font=('Helvetica', 14))
label_time.pack()


    ### start button
start_button = tk.Button(root, text="Hit the dummy!", command=lambda: start_timer())
start_button.pack()

reset_button = tk.Button(root, text="Reset", command=reset_counters)
reset_button.pack()

stop_button = tk.Button(root, text="Stop", command=stop_timer)
stop_button.pack()

label_timeformat = tk.Label(root, text="Time: 0 seconds", font=('Helvetica', 14))
label_timeformat.pack()
        
    # Tu configuración de Tkinter aquí
root.mainloop()
print("Tkinter application started")