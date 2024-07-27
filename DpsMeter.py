from PIL import ImageGrab, Image
import tkinter as tk
import pytesseract
import time
import cv2
import numpy as np

### tesseract OCR configuration
### ********** YOU NEED INSTALL TESSERACT https://github.com/UB-Mannheim/tesseract 
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
### pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Python312\Scripts\pytesseract.exe'


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

    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    mask_red1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
    mask_red = cv2.add(mask_red1, mask_red2)

    ### create masks that identify only the yellow and black components
    mask_yellow = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    mask_black = cv2.inRange(hsv_image, lower_black, upper_black)

    ### change yellow components to black and assume other colors as well
    image_np[mask_yellow > 0] = (0, 0, 0)
    image_np[mask_black > 0] = (0, 0, 255)  # Magenta = RGB(255, 0, 255)
    image_np[mask_red > 0] = (0, 0, 0)
 
   
    ### convert to grayscale to improve OCR
    gray_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

    ### apply thresholding
    _, binary_image = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY_INV)
    ### convert back to PIL image for compatibility with Tesseract
    processed_image = Image.fromarray(binary_image)
    processed_image.save('img/captura_procesada.png')
    return processed_image

def extract_health_value(image):
    preprocessed_image = preprocess_image(image)
    image.save('img/captura.png')
    preprocessed_image.save('img/final.png')
    try:
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789,./'
        ### use Tesseract OCR to extract text
        text = pytesseract.image_to_string("img/captura_procesada.png", config=custom_config)
    except Exception as inst:
        text = "Error", inst.args 
    return text

### function to calculate DPS and other values
def update_dps():
    global previous_health, start_time, total_damage
    screen = capture_screen(bbox)
    ### assume you have a function that extracts and converts the health value to integer
    ### change the way values are taken from the image. The improvement will be:
    ### only take the value of the lost health of the dummy and set the maximum health value of the dummy in the UI.
    ### this will help the OCR to better detect the values.
    current_health = extract_health_value(screen)
    cleaned_health = current_health.replace(',', '').replace('.', '').strip()
    print("Extracted value:", cleaned_health)
        
    current_health = int(cleaned_health.split('/')[0])
    
    if previous_health is not None:
        damage = previous_health - current_health
        total_damage += damage
        elapsed_time = time.time() - start_time
        dps = damage / elapsed_time if elapsed_time > 0 else 0
        
        # Update the user interface
        label_dps.config(text=f"DPS: {dps:.2f}")
        label_total_damage.config(text=f"Total Damage: {total_damage}")
        label_time.config(text=f"Time: {elapsed_time:.2f}s")
    
    previous_health = current_health
    start_time = time.time()
    root.after(1000, update_dps)  ### call this function every 1 second

def reset_counters():
    global previous_health, start_time, total_damage
    previous_health = None
    start_time = time.time()
    total_damage = 0
    label_dps.config(text="DPS: 0.00")
    label_total_damage.config(text="Total Damage: 0")
    label_time.config(text="Time: 0.00s")

### UI
### initialize variables
previous_health = None
start_time = time.time()
total_damage = 0
bbox = (449, 123, 610, 139)  ### define the region where the health bar is located

### create the user interface
root = tk.Tk()
root.title("DPS Meter")

label_dps = tk.Label(root, text="DPS: 0.00", font=('Helvetica', 14))
label_dps.pack()

label_total_damage = tk.Label(root, text="Total Damage: 0", font=('Helvetica', 14))
label_total_damage.pack()

label_time = tk.Label(root, text="Time: 0.00s", font=('Helvetica', 14))
label_time.pack()

### start button
start_button = tk.Button(root, text="Hit the dummy!", command=lambda: update_dps())
start_button.pack()

reset_button = tk.Button(root, text="Reset", command=reset_counters)
reset_button.pack()

### run the application
root.mainloop()
