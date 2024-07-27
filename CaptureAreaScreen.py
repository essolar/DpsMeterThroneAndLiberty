import tkinter as tk
from PIL import ImageGrab
import ctypes

def get_screen_size():
    ### get the size of the primary monitor
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()  ### set process DPI aware to get correct screen size
    width = user32.GetSystemMetrics(0)  ### width of primary monitor
    height = user32.GetSystemMetrics(1)  ### height of primary monitor
    return width, height

def on_drag(event):
    global rect, start_x, start_y, canvas
    # update the coordinates of the rectangle as the mouse is dragged
    canvas.coords(rect, start_x, start_y, event.x, event.y)

def on_button_press(event):
    global start_x, start_y, rect, canvas
    start_x, start_y = event.x, event.y
    # create a rectangle (initially a single pixel)
    rect = canvas.create_rectangle(start_x, start_y, start_x + 1, start_y + 1, outline='red', width=2)

def on_button_release(event):
    # capture the coordinates and take a screenshot
    bbox = (start_x, start_y, event.x, event.y)
    take_screenshot(bbox)
    root.quit()  # close the window after taking the screenshot

def take_screenshot(bbox):
    # grab the area defined by bbox
    img = ImageGrab.grab(bbox=bbox)
    img.save("img/selected_area.png")
    img.show()

root = tk.Tk()
root.attributes('-fullscreen', True)  # make the window fullscreen
root.attributes('-alpha', 0.01)  # set window to almost completely transparent
root.configure(bg='white')  # set a white background

screen_width, screen_height = get_screen_size()
canvas = tk.Canvas(root, width=screen_width, height=screen_height, highlightthickness=0, bg='white')
canvas.pack()

# bind mouse events to functions
canvas.bind("<ButtonPress-1>", on_button_press)
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<ButtonRelease-1>", on_button_release)

rect = None
root.mainloop()
