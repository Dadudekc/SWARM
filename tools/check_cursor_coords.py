"""
Script to display cursor coordinates on mouse click using pynput.
"""

from pynput import mouse, keyboard

print("\nCursor Coordinate Checker (pynput version)")
print("----------------------------------------")
print("Click anywhere to see coordinates.")
print("Press Esc to quit.\n")

# Flag to control the listener loop
running = True

def on_click(x, y, button, pressed):
    if pressed:
        print(f"Click detected at: ({x}, {y})")

def on_press(key):
    global running
    if key == keyboard.Key.esc:
        print("\nExiting...")
        running = False
        # Stop both listeners
        return False

# Set up the mouse listener
mouse_listener = mouse.Listener(on_click=on_click)
mouse_listener.start()

# Set up the keyboard listener
with keyboard.Listener(on_press=on_press) as k_listener:
    while running:
        k_listener.join(0.1)

mouse_listener.stop()
print("\nDone!") 
