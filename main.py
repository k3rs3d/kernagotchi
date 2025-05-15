from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import utime

from input_handler import start_thread as start_input_thread, get_buttons, get_button_events, play_sound
from pet import Pet

# TODO: Unique stats, ie, pet DNA
# TODO: Save/load pet stats
# TODO: Count number of generations 

WIDTH = const(128)
HEIGHT = const(64)

# Define pins
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

# UI parameters
divider_y = const(8)
face_offset = const(6)
face_x = const(WIDTH // 2 - face_offset)
face_y = const(HEIGHT // 2 - face_offset)
panel_y = 0

# ---- Launch input handler thread
start_input_thread()

# ---- Create pet
pet = Pet()
menu_mode = False # Start in pet view mode
menu_items = [] # Will be populated later 
menu_idx = 0 

def draw_pet_view():
    oled.fill(0)
    oled.text(pet.get_face(), face_x, face_y)
    #for x in range(HEIGHT): oled.pixel(x, divider_y, 1)
    oled.text(pet.get_stats_text(), 0, 0)
    oled.text(pet.get_status_line(), 0, 10)
    #oled.text("M:Menu", 0, HEIGHT-8)
    
def draw_menu():
    oled.fill(0)
    oled.text("MENU", 0, 0)
    for i, (name, _) in enumerate(menu_items):
        y = 10 + i*10
        sel = ">" if i == menu_idx else " "
        if y < HEIGHT-8:  # Stay on screen
            oled.text(f"{sel}{name}", 0, y)
            
def beep():
    play_sound({
        "freq_start":800, "freq_end":600, "vol_start":1000, "vol_end":0, "length":50
    })

while True:
    now = utime.ticks_ms()

    # input
    events = get_button_events()
    held = get_buttons()

    # menu navigation
    if menu_mode:
        # ENTER MENU MODE if not already 
        if not menu_items:
            menu_items = pet.get_menu_list()
            menu_idx = 0
        # Draw menu
        draw_menu()
        oled.show()
        # Button controls
        if events.get('L_down'):
            menu_idx = (menu_idx - 1) % len(menu_items)
            beep()
        elif events.get('R_down'):
            menu_idx = (menu_idx + 1) % len(menu_items)
            beep()
        elif events.get('M_down'):
            name, action = menu_items[menu_idx]
            action()  # call pet's action
            play_sound({"freq_start": 400, "freq_end": 800, "vol_start": 1000, "vol_end": 0, "length": 140})
            utime.sleep_ms(180)  # Delay to allow user to see the face change
            # Re-fetch menu in case actions changed the list (optional, safety)
            menu_items = pet.get_menu_list()
            # Exit menu after action (tamagotchi style)
            menu_mode = False
        # Remain in menu mode next loop
        utime.sleep_ms(50)
    else:
        # --- Main pet view
        pet.update()
        draw_pet_view()
        oled.show()
        
        # Forward sound requests from pet to audio thread
        req = pet.get_cry_request()
        if req:  # req is a string, e.g. 'hunger'
            # Play sound appropriate to the cry type
            if req == 'hunger':
                play_sound({"freq_start": 900, "freq_end": 600, "vol_start": 1000, "vol_end": 0, "length": 180})
            elif req == 'dirty':
                play_sound({"freq_start": 300, "freq_end": 600, "vol_start": 300, "vol_end": 700, "length": 120})
            elif req == 'sad':
                play_sound({"freq_start": 800, "freq_end": 400, "vol_start": 700, "vol_end": 300, "length": 180})
            elif req == 'dead':
                play_sound({"freq_start": 600, "freq_end": 100, "vol_start": 1000, "vol_end": 800, "length": 90})
                # TODO: pre-define sound 'files' elsewhere and call them by name instead of this 

        # Menu open
        if events.get('M_down'):
            menu_mode = True
            menu_items = pet.get_menu_list()
            menu_idx = 0
            beep()

        # DEBUG: Shortcut actions with L/R
        elif events.get('L_down') and not menu_mode:
            # feed quickly
            pet.feed()
            play_sound({"freq_start": 220, "freq_end": 400, "vol_start": 1200, "vol_end": 0, "length": 90})
        elif events.get('R_down') and not menu_mode:
            # play
            pet.play()
            play_sound({"freq_start": 400, "freq_end": 900, "vol_start": 1200, "vol_end": 0, "length": 90})

        utime.sleep_ms(40) # 32? 