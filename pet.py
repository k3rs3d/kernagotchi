import utime
import urandom

# TODO: Sprite instead of text
# TODO: Animate face
# TODO: Species / Different Phenotypes
# TODO: DNA / Offspring take after parents

FACES = {
    "neutral":   "o_o",
    "blink":     "-_-",
    "happy":     "^_^",
    "wide":      "O_O",
    "weird":     "o_O",
    "sick":      "x_x",
    "sad":       "u_u",
    "hungry":    "o.o",
    "very_happy":"OwO",
    "old":       "O_o",
    "sleepy":    "-o-",
    "asleep":    "z_z",
    "angry":     ">_<",
    "dirty":     "._.",
    # ...add more
}

class Pet:
    def __init__(self, name="Eggy"):
        # Core persistent stats
        self.name = name
        self.age = 0   # in seconds
        self.hunger = 0   # 0=full
        self.happiness = 100
        self.cleanliness = 100
        self.energy = 100
        self.health = 100
        self.discipline = 50   # 0 = totally unruly, 100 = strict angel
        self.alive = True
        self.state = "alive"  # "alive", "asleep", "sick", "dead", 

        # Timestamps (ms)
        self.last_update = utime.ticks_ms()
        self.last_fed = 0
        self.last_played = 0
        self.last_cleaned = 0
        self.last_slept = 0
        self.last_cry_time = 0
        self.cry_request = None # for different types of cry outs

        # Emote
        self.current_face = "neutral"
        self.face_duration = 1000    # milliseconds
        self.last_face_change = utime.ticks_ms()

        # Expansion hooks/events
        self.after_action_hooks = []
        self.per_tick_hooks = []
        self.face_override_funcs = []

        # Action registry (for menu, also allows plug-in!)
        self.actions = {
            "Feed": self.feed,
            "Play": self.play,
            "Clean": self.clean,
            "Sleep": self.sleep,
            "Medicine": self.give_medicine
        }

    #------------- Action methods --------------
    # TODO: Add more arguments (instead of hardcoded values) 
    def feed(self):
        if self.alive and self.state == "alive":
            self.hunger = max(0, self.hunger - 30)
            self.happiness = min(100, self.happiness + 8)
            self.energy = min(100, self.energy + 4)
            self.last_fed = utime.ticks_ms()
            self.set_face("happy", 900)
            self.trigger_after_action("feed")

    def play(self):
        if self.alive and self.state == "alive":
            if self.energy > 10 and self.hunger < 80:
                self.happiness = min(100, self.happiness + 14)
                self.energy = max(0, self.energy - 16)
                self.last_played = utime.ticks_ms()
                self.set_face("very_happy", 900)
            else:
                self.set_face("sad", 900)
            self.trigger_after_action("play")

    def clean(self):
        if self.alive and self.state == "alive":
            self.cleanliness = 100
            self.happiness = min(100, self.happiness + 4)
            self.last_cleaned = utime.ticks_ms()
            self.set_face("neutral", 700)
            self.trigger_after_action("clean")

    def sleep(self):
        if not self.alive:
            return
        if self.state == "alive":
            self.state = "asleep"
            self.set_face("asleep", 9999999)
            self.last_slept = utime.ticks_ms()
            self.trigger_after_action("sleep")
        elif self.state == "asleep":
            self.state = "alive"
            self.energy = 100
            self.set_face("happy", 700)
            self.trigger_after_action("wakeup")

    def give_medicine(self):
        if self.alive:
            self.health = min(100, self.health + 30)
            self.set_face("sick", 500)
            self.set_face("neutral", 700)
            self.trigger_after_action("medicine")
            
    def get_cry_request(self):
        req = self.cry_request
        self.cry_request = None
        return req

    def discipline_pet(self):
        self.discipline = min(100, self.discipline + 10)
        self.set_face("angry", 400)    # Or any other reaction you want

    def custom_action(self, name, func):
        """Allow add-on actions, e.g. extra menu items."""
        self.actions[name] = func

    #------------ Main Brain -----------
    def update(self):
        now = utime.ticks_ms()
        dt = utime.ticks_diff(now, self.last_update)
        if not self.alive:
            self.set_face("sick", 0)
            return

        # Stat tick every 2 seconds
        if dt >= 2000:
            self.age += dt // 1000
            self.last_update = now

            # ----- Natural Decay ----- 
            self.hunger = min(100, self.hunger + 2)
            self.cleanliness = max(0, self.cleanliness - 1)
            if self.state == "alive":
                self.energy = max(0, self.energy - 1)
            if self.hunger > 70: # Hungry
                self.happiness = max(0, self.happiness - 3)
            if self.cleanliness < 40:
                self.happiness = max(0, self.happiness - 7)
            if self.energy < 20:
                self.happiness = max(0, self.happiness - 8)
            # Health penality if stats bad
            if self.hunger > 90 or self.cleanliness < 30 or self.energy < 10:
                self.health = max(0, self.health - 1)
            # Autowake after enough sleep
            if self.state == "asleep" and self.energy >= 96:
                self.sleep()  # wake up

            # Die if dead x_x
            if self.happiness == 0 or self.health == 0:
                self.alive = False
                self.state = "dead"
                self.set_face("sick", 0)
                self.cry_request = "dead"
                self.last_cry_time = now
        # Per-tick hooks (plug-ins???? idk)
        for h in self.per_tick_hooks:
            h(self)

        # Face/emote logic (hookable)
        if utime.ticks_diff(now, self.last_face_change) > self.face_duration:
            overrideface = None
            # any registered dynamic face logic?
            for func in self.face_override_funcs:
                f = func(self)
                if f: overrideface = f
            if not overrideface:
                # generic mood-based emotes
                if self.state == "asleep":
                    self.set_face("asleep", 500)
                elif self.happiness < 25:
                    self.set_face("sad", 1200)
                elif self.hunger > 75:
                    self.set_face("hungry", 1500)
                elif self.cleanliness < 25:
                    self.set_face("dirty", 1500)
                elif urandom.getrandbits(3) == 0:
                    self.set_face("blink", 150)
                elif urandom.getrandbits(4) == 0:
                    self.set_face("wide", 600)
                elif urandom.getrandbits(5) == 0:
                    self.set_face("happy", 400)
                else:
                    self.set_face("neutral", 1200)
            else:
                self.set_face(overrideface, 1200)

        can_cry = self.alive and self.state not in ("asleep", "dead")
        recently_cried = utime.ticks_diff(now, self.last_cry_time) < 6000
        # Discipline cry probability: high discipline=less often
        disc_chance = max(2, 7 - int(self.discipline / 20))

        if can_cry and not recently_cried:
            if self.hunger > 70 and urandom.getrandbits(disc_chance) == 0:
                self.cry_request = "hunger"
                self.last_cry_time = now
            elif self.cleanliness < 35 and urandom.getrandbits(disc_chance + 1) == 0:
                self.cry_request = "dirty"
                self.last_cry_time = now
            elif self.happiness < 25 and urandom.getrandbits(disc_chance) == 0:
                self.cry_request = "sad"
                self.last_cry_time = now


    #------------- Face -------------------
    def set_face(self, face, duration):
        if face in FACES:
            self.current_face = face
            self.face_duration = duration
            self.last_face_change = utime.ticks_ms()

    def get_face(self):
        return FACES.get(self.current_face, "o_o")

    #------------- Text and HUD ------------------
    def get_stats_text(self):
        if not self.alive:
            return "RIP"
        # Shortened display for OLED
        return (f"A{self.age} H{self.happiness} F{self.hunger} "
                f"E:{self.energy} Cl:{self.cleanliness} Hp:{self.health}")

    def get_menu_list(self):
        """Return actions as list of (name, func)."""
        items = []
        for n, f in self.actions.items():
            items.append((n, f))
        return items

    # Player-facing short status
    def get_status_line(self):
        if not self.alive:
            return f"{self.name} died."
        if self.state == "asleep":
            return "Sleeping..."
        if self.hunger > 75:
            return "Hungry!"
        if self.cleanliness < 25:
            return "Dirty!"
        if self.energy < 20:
            return "Very Tired..."
        if self.health < 60:
            return "Unwell..."
        if self.happiness < 30:
            return "Sad..."
        return "Happy!"

    #------------- Expansion hooks/events --------------
    def add_after_action_hook(self, fn):
        """fn(pet, action_name). Called after actions."""
        self.after_action_hooks.append(fn)

    def add_per_tick_hook(self, fn):
        """fn(pet). Called on every tick after update logic."""
        self.per_tick_hooks.append(fn)
        
    def add_face_override(self, fn):
        """fn(pet) -> face_name|None. Called before face fallback logic."""
        self.face_override_funcs.append(fn)

    # ------------ Event/Action hook utilities -----------
    def trigger_after_action(self, action_name):
        """Call hooks after an action (feed, play, etc)."""
        for hook in self.after_action_hooks:
            try:
                hook(self, action_name)
            except Exception as e:
                print(f"After action hook error: {e}")

    # ------------ Reset pet -----------
    def reset(self, name=None):
        self.__init__(name if name else self.name)

    # ------------ For Save/Load (sketch, not implemented yet) -----------
    def get_state(self):
        # Return dict of all key stats you'd want to save
        return {
            "name": self.name,
            "age": self.age,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "cleanliness": self.cleanliness,
            "energy": self.energy,
            "health": self.health,
            "discipline": self.discipline,
            "alive": self.alive,
            "state": self.state
        }

    def set_state(self, state):
        for k, v in state.items():
            if hasattr(self, k):
                setattr(self, k, v)

    # Factory/helper 
    def make_default_pet(name="Eggy"):
        return Pet(name)

    # DEBUG: log actions
    def log_action_hook(pet, action):
        print(f"Pet did action: {action}")

    # HACK: custom face override that makes the pet angry at 6pm
    def angry_at_night_hook(pet):
        hour = ((utime.time() // 3600) % 24)
        if hour >= 18:
            return "angry"
        return None

# Register hooks like:
# pet = Pet()
# pet.add_after_action_hook(log_action_hook)
# pet.add_face_override(angry_at_night_hook)