import pygame
import sys
import math # For rotation and color calculations
import random # For bacteria rumbling and salt particle starting positions

# --- Initialization ---
pygame.init()
pygame.mixer.init()

# --- Constants ---
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (200, 200, 200)
PURPLE_BACKGROUND = (75, 0, 130) # Fallback for OS game background
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

MAX_RUMBLE_OFFSET = 10 # Max pixels the bacteria will shift in X or Y for the rumble.

# Game Mechanics Constants (can be tuned per game if needed)
HEALTH_MAX = 100.0
HEALTH_MIN = 0.0
REGEN_RATE = 0.35  # Health points regenerated per frame (adjust for difficulty)
DAMAGE_PER_TAP = 5.0 # Health points lost per spacebar tap (adjust)

# Oxidative Stress Game Specific Constants
MAX_SCALE_ROTATION_DEGREES = 30

# Osmotic Shock Game Specific Constants
OSMOTIC_GAME_INFO_SLIDE_INDEX = 10  # Slide "17.png"
OSMOTIC_GAME_BOOM_SLIDE_INDEX = 11  # Slide "24.png"
NUM_SALT_PARTICLES = 16
MIN_BACTERIA_OSMO_SCALE = 0.2  # Bacteria shrinks to 20% of its original size at 0 health
SALT_PARTICLE_SPEED_Y = 15      # Speed of salt particles moving up/down

# Enzyme Inhibition Game Specific Constants
ENZYME_GAME_INFO_SLIDE_INDICES = [6, 7]  # Slides "10.png" and "11.png"
ENZYME_GAME_BOOM_SLIDE_INDEX = 8      # Slide "15.png"

# Inhibitor movement parameters
INHIBITOR_START_X = 0
INHIBITOR_END_X = -1200
INHIBITOR_Y = 0

HEALTH_BAR_POS_EI = (SCREEN_WIDTH * 0.6, SCREEN_HEIGHT * 0.3)
HEALTH_BAR_SIZE_EI = (400, 40)

# Flash effect variables
TAP_BUTTON_VISUAL_RECT = pygame.Rect(677, 41, 566, 201)
FLASH_DURATION_FRAMES = 3
FLASH_COLOR = (255, 255, 255, 180) # White flash with some transparency

# --- Load Sound Assets ---
try:
    button_beep_sound = pygame.mixer.Sound("button_beep.wav")
    button_beep_sound.set_volume(0.14)

    space_tap_sound = pygame.mixer.Sound("space_tap.wav")
    space_tap_sound.set_volume(0.16)

    game_finish_sound = pygame.mixer.Sound("game_finish.wav")
    game_finish_sound.set_volume(0.08)

    rumble_loop_sound = pygame.mixer.Sound("rumble_loop.wav")
except pygame.error as e:
    print(f"Warning: Could not load one or more sound effects - {e}")
    class DummySound:
        def play(self, loops=0): pass
        def stop(self): pass
        def set_volume(self, volume): pass
        def get_num_channels(self): return 0
    button_beep_sound = DummySound()
    space_tap_sound = DummySound()
    game_finish_sound = DummySound()
    rumble_loop_sound = DummySound()

# --- Load Background Music ---
background_music_loaded_successfully = False # Flag to track if music loaded
try:
    pygame.mixer.music.load("background_music.mp3")
    background_music_loaded_successfully = True
    print("DEBUG: Background music 'background_music.mp3' loaded successfully.")
except pygame.error as e:
    print(f"Warning: Could not load background music 'background_music.mp3' - {e}")
    print("DEBUG: Background music loading failed.")

# --- Screen Setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Lights Out! Bacteria Game")

# --- Load Assets ---
# Slide Images
slide_images_paths = [
    "1.png", "2.png", "3.png", "4.png", "8.png", "9.png",
    "10.png", "11.png", "15.png", "16.png", "17.png", "24.png",
    "25.png", "26.png"
]
slide_images = []
for path in slide_images_paths:
    try:
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        slide_images.append(image)
    except pygame.error as e:
        print(f"Error loading slide image {path}: {e}")
        placeholder = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        placeholder.fill(LIGHT_GRAY)
        font = pygame.font.Font(None, 72)
        text_surf = font.render(f"Error: Could not load {path}", True, BLACK)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        placeholder.blit(text_surf, text_rect)
        slide_images.append(placeholder)

if not slide_images or len(slide_images) != len(slide_images_paths):
    print("Critical error: Not all slides loaded! Please check image paths and files.")
    pygame.quit()
    sys.exit()

# Fonts
game_font_large = pygame.font.Font(None, 100)
game_font_medium = pygame.font.Font(None, 60)

# Oxidative Stress Game Assets
game_background_os_img = None
scale_balance_img_orig = None
bacteria_os_images = []
try:
    game_background_os_img = pygame.image.load("game_background_os.png").convert()
    game_background_os_img = pygame.transform.scale(game_background_os_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    scale_balance_img_orig = pygame.image.load("scale_balance.png").convert_alpha()

    bacteria_os_images_paths = ["bacteria_os_100.png", "bacteria_os_75.png", "bacteria_os_50.png", "bacteria_os_25.png"]
    bacteria_os_images = [pygame.image.load(p).convert_alpha() for p in bacteria_os_images_paths]
except pygame.error as e:
    print(f"Error loading Oxidative Stress game assets: {e}.")
    if game_background_os_img is None:
        game_background_os_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        game_background_os_img.fill(PURPLE_BACKGROUND)
    if scale_balance_img_orig is None:
        scale_balance_img_orig = pygame.Surface((300, 50), pygame.SRCALPHA); scale_balance_img_orig.fill(WHITE)
    if not bacteria_os_images:
        bacteria_os_images = [pygame.Surface((200, 200), pygame.SRCALPHA) for _ in range(4)]
        for i, surf in enumerate(bacteria_os_images): surf.fill((0, 255, 0, 100))

# Osmotic Shock Game Assets
bacteria_osmo_img_orig = None
salt_particle_img = None
tap_osmo_img = None
try:
    bacteria_osmo_img_orig = pygame.image.load("bacteria_osmo_orig.png").convert_alpha()
    salt_particle_img = pygame.image.load("salt_particle.png").convert_alpha()
    tap_osmo_img = pygame.image.load("tap_osmo.png").convert_alpha()
    salt_particle_img = pygame.transform.smoothscale(salt_particle_img, (70, 70))
except pygame.error as e:
    print(f"Error loading Osmotic Shock game assets: {e}")
    if bacteria_osmo_img_orig is None:
        bacteria_osmo_img_orig = pygame.Surface((150, 150), pygame.SRCALPHA); bacteria_osmo_img_orig.fill((0,0,255,100))
    if salt_particle_img is None:
        salt_particle_img = pygame.Surface((20,20), pygame.SRCALPHA); salt_particle_img.fill(WHITE)
    if tap_osmo_img is None:
        tap_osmo_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        tap_osmo_img.fill((0,0,0,0)) # Fully transparent, assuming it's an overlay

# Load Enzyme Inhibition Game Assets
background_enzyme_img = None # Initialize to None
enzyme_state_images = [] # Initialize to empty list
inhibitor_triangle_img = None # Initialize to None
inhibitor_original_w, inhibitor_original_h = 0, 0 # Initialize

try:
    background_enzyme_img = pygame.image.load("background_enzyme.png").convert()
    background_enzyme_img = pygame.transform.scale(background_enzyme_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

    enzyme_state_paths = ["enzyme_state1.png", "enzyme_state2.png", "enzyme_state3.png"]
    for path in enzyme_state_paths:
        img = pygame.image.load(path).convert_alpha()
        enzyme_state_images.append(pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)))
    
    inhibitor_triangle_img = pygame.image.load("inhibitor_triangle.png").convert_alpha()
    inhibitor_original_w, inhibitor_original_h = inhibitor_triangle_img.get_size()

except pygame.error as e:
    print(f"Error loading Enzyme Inhibition game assets: {e}")
    if background_enzyme_img is None:
        background_enzyme_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); background_enzyme_img.fill(PURPLE_BACKGROUND)
    if not enzyme_state_images:
        for _ in range(3):
            surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            surf.fill((50, 50, 50, 100)); enzyme_state_images.append(surf)
    if inhibitor_triangle_img is None:
        inhibitor_triangle_img = pygame.Surface((50,50), pygame.SRCALPHA); inhibitor_triangle_img.fill(RED)
        inhibitor_original_w, inhibitor_original_h = 50,50

# --- Start Background Music ---
if background_music_loaded_successfully:
    try:
        pygame.mixer.music.set_volume(0.1)  # Adjust initial volume (0.0 to 1.0)
        pygame.mixer.music.play(-1)         # Play indefinitely (loop)
        print("DEBUG: Attempting to play background music.")
        if pygame.mixer.music.get_busy():
            print("DEBUG: Background music is now playing.")
        else:
            # This might happen if the volume is 0, or the file is valid but silent, or another issue.
            print("DEBUG: Background music was started but pygame.mixer.music.get_busy() is False.")
    except pygame.error as e:
        print(f"Error playing background music: {e}")
else:
    print("DEBUG: Background music was not loaded, so not attempting to play.")


# --- Game State Variables ---
current_slide_index = 0
total_slides = len(slide_images)
current_mode = "slideshow"
active_game_type = None
health = HEALTH_MAX
tap_button_flash_timer = 0
salt_particles = []

# Positions for Oxidative Stress game elements
BACTERIA_POS_OS = (340, 700)
SCALE_POS_OS = (1330, 870)
HEALTH_BAR_POS_OS = (SCREEN_WIDTH // 2 + 500, SCREEN_HEIGHT * 0.30 + 20)
HEALTH_BAR_SIZE_OS = (400, 40)

# Positions for Osmotic Shock game elements
BACTERIA_OSMO_CENTER_POS = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
SALT_X_POSITIONS = [
    SCREEN_WIDTH * 0.1, SCREEN_WIDTH * 0.15, SCREEN_WIDTH * 0.2, SCREEN_WIDTH * 0.25,
    SCREEN_WIDTH * 0.3, SCREEN_WIDTH * 0.35, SCREEN_WIDTH * 0.4, SCREEN_WIDTH * 0.45,
    SCREEN_WIDTH * 0.55, SCREEN_WIDTH * 0.6, SCREEN_WIDTH * 0.65, SCREEN_WIDTH * 0.7,
    SCREEN_WIDTH * 0.75, SCREEN_WIDTH * 0.8, SCREEN_WIDTH * 0.85, SCREEN_WIDTH * 0.9
]

# --- Button Definitions (for slideshow) ---
buttons = [
    {"id": "start_button", "rect": pygame.Rect(680, 780, 560, 180), "action": "goto_slide", "target_slide": 1, "visible_on_slides": [0]},
    {"id": "ready_button", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 2, "visible_on_slides": [1]},
    {"id": "choose_method_1", "rect": pygame.Rect(160, 400, 460, 460), "action": "goto_slide", "target_slide": 3, "visible_on_slides": [2]},
    {"id": "choose_method_2", "rect": pygame.Rect(730, 400, 460, 460), "action": "goto_slide", "target_slide": 6, "visible_on_slides": [2]},
    {"id": "choose_method_3", "rect": pygame.Rect(1330, 400, 460, 460), "action": "goto_slide", "target_slide": 10, "visible_on_slides": [2]},
    {"id": "finish_button", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 13, "visible_on_slides": [2]}, # Assuming slide 2 is the "choose method" slide
    {"id": "tap_button_os_info", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 4, "visible_on_slides": [3]},
    {"id": "next_after_boom_button_os", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 5, "visible_on_slides": [4]},
    {"id": "back_to_choose_button_os", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 2, "visible_on_slides": [5]},
    {"id": "tap_button_enzyme_info1", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 7, "visible_on_slides": [6]},
    {"id": "tap_button_enzyme_info2", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 8, "visible_on_slides": [7]},
    {"id": "next_after_boom_button_enzyme", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 9, "visible_on_slides": [8]},
    {"id": "back_to_choose_button_enzyme", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 2, "visible_on_slides": [9]},
    {"id": "tap_button_osmotic_info", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 11, "visible_on_slides": [10]},
    {"id": "next_after_boom_button_osmotic", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 12, "visible_on_slides": [11]},
    {"id": "back_to_choose_button_osmotic", "rect": pygame.Rect(800, 920, 320, 120), "action": "goto_slide", "target_slide": 2, "visible_on_slides": [12]},
    {"id": "start_over_button_end", "rect": pygame.Rect(680, 780, 560, 180), "action": "goto_slide", "target_slide": 0, "visible_on_slides": [13]}
]

# --- Helper Functions for Game ---
def start_game(game_type_to_start):
    global current_mode, health, active_game_type, salt_particles, tap_button_flash_timer
    health = HEALTH_MAX
    active_game_type = game_type_to_start
    tap_button_flash_timer = 0 # Reset flash timer

    if active_game_type == "oxidative_stress":
        current_mode = "game_oxidative_stress"
        rumble_loop_sound.set_volume(0) # Start silent, volume increases with damage
        if rumble_loop_sound.get_num_channels() == 0: # Play only if not already playing
            rumble_loop_sound.play(-1)
    elif active_game_type == "osmotic_shock":
        current_mode = "game_osmotic_shock"
        salt_particles = []
        if salt_particle_img:
            for i in range(NUM_SALT_PARTICLES):
                salt_particles.append({
                    'x': SALT_X_POSITIONS[i],
                    'y': random.randint(0, SCREEN_HEIGHT - salt_particle_img.get_height()),
                    'vy': random.choice([-SALT_PARTICLE_SPEED_Y, SALT_PARTICLE_SPEED_Y]),
                    'image': salt_particle_img
                })
        rumble_loop_sound.set_volume(0)
        if rumble_loop_sound.get_num_channels() == 0:
            rumble_loop_sound.play(-1)
    elif active_game_type == "enzyme_inhibition":
        current_mode = "game_enzyme_inhibition"
        rumble_loop_sound.set_volume(0)
        if rumble_loop_sound.get_num_channels() == 0:
            rumble_loop_sound.play(-1)
    print(f"DEBUG: Starting game: {current_mode}")

def update_oxidative_stress_game():
    global health, current_mode, current_slide_index, active_game_type

    if health < HEALTH_MAX and health > HEALTH_MIN:
        health += REGEN_RATE
        health = min(health, HEALTH_MAX)
    
    if active_game_type == "oxidative_stress":
        health_ratio_for_rumble = max(0, health / HEALTH_MAX)
        rumble_volume = (1.0 - health_ratio_for_rumble)**2 
        rumble_loop_sound.set_volume(min(1.0, max(0.0, rumble_volume)))

    if health <= HEALTH_MIN:
        health = HEALTH_MIN
        current_mode = "slideshow"
        rumble_loop_sound.stop()
        game_finish_sound.play()
        if active_game_type == "oxidative_stress":
            current_slide_index = 4 # OS_BOOM_SLIDE_INDEX (assuming slide 4 is "boom" for OS)
        active_game_type = None
        print("DEBUG: Oxidative Stress game ended.")

def draw_oxidative_stress_game_elements():
    global tap_button_flash_timer
    screen.blit(game_background_os_img, (0, 0))

    bacteria_img_to_draw = None
    if health > 75: bacteria_img_to_draw = bacteria_os_images[0]
    elif health > 50: bacteria_img_to_draw = bacteria_os_images[1]
    elif health > 25: bacteria_img_to_draw = bacteria_os_images[2]
    else: bacteria_img_to_draw = bacteria_os_images[3]

    if bacteria_img_to_draw:
        base_bacteria_rect = bacteria_img_to_draw.get_rect(center=BACTERIA_POS_OS)
        current_rumble_x, current_rumble_y = 0, 0
        if health < HEALTH_MAX and health > HEALTH_MIN: # Rumble only when not full or min health
            rumble_intensity_factor = (HEALTH_MAX - health) / HEALTH_MAX
            effective_intensity = rumble_intensity_factor ** 2 
            max_offset = MAX_RUMBLE_OFFSET * effective_intensity
            if max_offset > 0.5 : # Only rumble if offset is somewhat significant
                current_rumble_x = random.randint(-int(max_offset), int(max_offset))
                current_rumble_y = random.randint(-int(max_offset), int(max_offset))
        final_draw_topleft = (base_bacteria_rect.left + current_rumble_x, base_bacteria_rect.top + current_rumble_y)
        screen.blit(bacteria_img_to_draw, final_draw_topleft)

    health_ratio = max(0, health / HEALTH_MAX)
    bar_width = int(HEALTH_BAR_SIZE_OS[0] * health_ratio)
    
    # Smooth color transition for health bar
    if health_ratio > 0.5: # Green to Yellow (100% to 50%)
        g = 255
        r = int(255 * (1 - (health_ratio - 0.5) * 2)) 
    else: # Yellow to Red (50% to 0%)
        r = 255
        g = int(255 * (health_ratio * 2))
    bar_color = (max(0, min(255, r)), max(0, min(255, g)), 0)


    pygame.draw.rect(screen, BLACK, (HEALTH_BAR_POS_OS[0]-2, HEALTH_BAR_POS_OS[1]-2, HEALTH_BAR_SIZE_OS[0]+4, HEALTH_BAR_SIZE_OS[1]+4))
    pygame.draw.rect(screen, bar_color, (HEALTH_BAR_POS_OS[0], HEALTH_BAR_POS_OS[1], bar_width, HEALTH_BAR_SIZE_OS[1]))

    health_text_surf = game_font_large.render(f"{int(health)}%", True, WHITE)
    health_text_rect = health_text_surf.get_rect(midright=(HEALTH_BAR_POS_OS[0] - 30, HEALTH_BAR_POS_OS[1] + HEALTH_BAR_SIZE_OS[1] // 2))
    screen.blit(health_text_surf, health_text_rect)

    if scale_balance_img_orig:
        rotation = -MAX_SCALE_ROTATION_DEGREES * (health_ratio * 2 - 1) # maps 0-1 to -MAX to +MAX
        rotated_scale = pygame.transform.rotate(scale_balance_img_orig, rotation)
        scale_rect = rotated_scale.get_rect(center=SCALE_POS_OS)
        screen.blit(rotated_scale, scale_rect.topleft)

    if tap_button_flash_timer > 0:
        flash_surface = pygame.Surface(TAP_BUTTON_VISUAL_RECT.size, pygame.SRCALPHA)
        flash_surface.fill(FLASH_COLOR)
        screen.blit(flash_surface, TAP_BUTTON_VISUAL_RECT.topleft)
        tap_button_flash_timer -= 1

def update_osmotic_shock_game():
    global health, current_mode, current_slide_index, active_game_type, salt_particles
    if health < HEALTH_MAX and health > HEALTH_MIN:
        health += REGEN_RATE
        health = min(health, HEALTH_MAX)

    if salt_particle_img:
        for particle in salt_particles:
            particle['y'] += particle['vy']
            particle_height = particle['image'].get_height()
            if particle['y'] < -particle_height: # Particle fully off screen top
                 particle['y'] = SCREEN_HEIGHT # Reappear at bottom
            elif particle['y'] > SCREEN_HEIGHT: # Particle fully off screen bottom
                 particle['y'] = -particle_height # Reappear at top
            # Keep bouncing logic if preferred, or use wrap-around like above
            # if particle['y'] < 0 or particle['y'] + particle_height > SCREEN_HEIGHT:
            #     particle['vy'] *= -1
            #     particle['y'] = max(0, min(particle['y'], SCREEN_HEIGHT - particle_height))

    if active_game_type == "osmotic_shock":
        health_ratio_for_rumble = max(0, health / HEALTH_MAX)
        rumble_volume = (1.0 - health_ratio_for_rumble)**2 
        rumble_loop_sound.set_volume(min(1.0, max(0.0, rumble_volume)))

    if health <= HEALTH_MIN:
        health = HEALTH_MIN
        current_mode = "slideshow"
        rumble_loop_sound.stop()
        game_finish_sound.play()
        if active_game_type == "osmotic_shock":
            current_slide_index = OSMOTIC_GAME_BOOM_SLIDE_INDEX
        active_game_type = None
        print("DEBUG: Osmotic Shock game ended.")


def draw_osmotic_shock_game_elements():
    global tap_button_flash_timer
    health_ratio = max(0, health / HEALTH_MAX)
    
    # Background color transition: Cyan (full health) -> Purple (mid health) -> Red (low health)
    current_hue = 0 # Default to Red
    if health_ratio > 0.5: # Cyan to Purple
        # health_ratio from 0.5 to 1.0 maps to hue from 240 (Purple) to 180 (Cyan)
        # Or more simply, lerp hue. Let's try: Hue 180 (Cyan) at 100%, Hue 0 (Red) at 0%
        current_hue = 180 * health_ratio # This goes from 0 (Red) to 180 (Cyan)
    else: # Purple to Red
        # health_ratio from 0 to 0.5 maps to hue from 0 (Red) to some mid-value if desired
        # For simplicity, let's stick to a direct mapping:
        current_hue = 180 * health_ratio # This makes it go Red -> Greenish-Yellow -> Cyan

    # Let's try a different hue mapping for better visual feedback:
    # 100% health: Cyan (Hue 180)
    # 50% health: Purple (Hue 270 or 300)
    # 0% health: Red (Hue 0 or 360)
    if health_ratio > 0.5: # From Purple (270) to Cyan (180)
        # (health_ratio - 0.5) * 2 gives a 0-1 range for the top 50% health
        # We want to go from 270 down to 180, a range of -90
        current_hue = 270 - (90 * (health_ratio - 0.5) * 2)
    else: # From Red (0/360) to Purple (270)
        # health_ratio * 2 gives a 0-1 range for the bottom 50% health
        # We want to go from 0 up to 270
        current_hue = 270 * (health_ratio * 2)


    background_color = pygame.Color(0); background_color.hsla = (current_hue % 360, 100, 50, 100)
    screen.fill(background_color)

    if tap_osmo_img: # Draw UI overlay
        # Ensure tap_osmo_img is scaled to SCREEN_WIDTH, SCREEN_HEIGHT if it's a full overlay
        # If it's just a small element, position it correctly. Assuming it's full screen.
        screen.blit(tap_osmo_img, (0,0))


    if bacteria_osmo_img_orig:
        current_scale = MIN_BACTERIA_OSMO_SCALE + (1.0 - MIN_BACTERIA_OSMO_SCALE) * health_ratio
        orig_w, orig_h = bacteria_osmo_img_orig.get_size()
        scaled_w, scaled_h = int(orig_w * current_scale), int(orig_h * current_scale)
        
        if scaled_w > 0 and scaled_h > 0: # Ensure dimensions are valid
            scaled_bacteria = pygame.transform.smoothscale(bacteria_osmo_img_orig, (scaled_w, scaled_h))
            base_rect = scaled_bacteria.get_rect(center=BACTERIA_OSMO_CENTER_POS)
            
            rumble_x, rumble_y = 0, 0
            if health < HEALTH_MAX * 0.85 and health > HEALTH_MIN: # Rumble below 85% health
                intensity_factor = (HEALTH_MAX - health) / HEALTH_MAX 
                effective_intensity = intensity_factor ** 2.0 # Adjust power for feel
                max_offset = MAX_RUMBLE_OFFSET * 2 * effective_intensity # More rumble for this game
                if max_offset > 0.5:
                    rumble_x = random.randint(-int(max_offset), int(max_offset))
                    rumble_y = random.randint(-int(max_offset), int(max_offset))
            final_topleft = (base_rect.left + rumble_x, base_rect.top + rumble_y)
            screen.blit(scaled_bacteria, final_topleft)

    if salt_particle_img:
        # Show more salt particles as health decreases
        num_to_show = int(((HEALTH_MAX - health) / HEALTH_MAX) * NUM_SALT_PARTICLES * 1.5) # Show up to 1.5x NUM_SALT_PARTICLES
        num_to_show = min(num_to_show, NUM_SALT_PARTICLES) # Cap at the actual number of particles available
        
        for i in range(num_to_show):
            if i < len(salt_particles): # Check index bounds
                particle = salt_particles[i]
                screen.blit(particle['image'], (particle['x'], particle['y']))

    # No separate health bar for osmotic shock, visual is bacteria size and background color
    # But "TAP!" flash is still relevant
    if tap_button_flash_timer > 0:
        # TAP_BUTTON_VISUAL_RECT should be defined for this game's "TAP!" button area
        # Reusing the global one, ensure it makes sense or define a new one for this game
        flash_surface = pygame.Surface(TAP_BUTTON_VISUAL_RECT.size, pygame.SRCALPHA)
        flash_surface.fill(FLASH_COLOR)
        screen.blit(flash_surface, TAP_BUTTON_VISUAL_RECT.topleft)
        tap_button_flash_timer -= 1

def update_enzyme_inhibition_game():
    global health, current_mode, current_slide_index, active_game_type
    if health < HEALTH_MAX and health > HEALTH_MIN:
        health += REGEN_RATE 
        health = min(health, HEALTH_MAX)
            
    if active_game_type == "enzyme_inhibition":
        health_ratio_for_rumble = max(0, health / HEALTH_MAX)
        rumble_volume = (1.0 - health_ratio_for_rumble)**2 
        rumble_loop_sound.set_volume(min(1.0, max(0.0, rumble_volume)))

    if health <= HEALTH_MIN:
        health = HEALTH_MIN
        current_mode = "slideshow"
        rumble_loop_sound.stop()
        game_finish_sound.play()
        if active_game_type == "enzyme_inhibition":
            current_slide_index = ENZYME_GAME_BOOM_SLIDE_INDEX
        active_game_type = None
        print("DEBUG: Enzyme Inhibition game ended.")

def draw_enzyme_inhibition_game_elements():
    global tap_button_flash_timer

    if background_enzyme_img:
        screen.blit(background_enzyme_img, (0, 0))
    else:
        screen.fill((30,30,30))

    current_enzyme_img_to_draw = None
    if health > 66: # State 1 (healthiest)
        if len(enzyme_state_images) > 0: current_enzyme_img_to_draw = enzyme_state_images[0]
    elif health > 33: # State 2 (medium)
        if len(enzyme_state_images) > 1: current_enzyme_img_to_draw = enzyme_state_images[1]
    else: # State 3 (lowest health)
        if len(enzyme_state_images) > 2: current_enzyme_img_to_draw = enzyme_state_images[2]
    
    if current_enzyme_img_to_draw:
        rumble_x, rumble_y = 0, 0
        if health < 60.0 and health > HEALTH_MIN: # Rumble below 60% health
            rumble_intensity_factor = (60.0 - max(HEALTH_MIN, health)) / 60.0 
            effective_intensity = rumble_intensity_factor ** 1.5
            max_offset = MAX_RUMBLE_OFFSET * effective_intensity
            if max_offset > 0.5:
                rumble_x = random.randint(-int(max_offset), int(max_offset))
                rumble_y = random.randint(-int(max_offset), int(max_offset))
        screen.blit(current_enzyme_img_to_draw, (rumble_x, rumble_y))


    if inhibitor_triangle_img:
        inhibitor_current_x = INHIBITOR_END_X # Default to "in" position
        # Inhibitor moves out as health increases from 0 to 100
        # Health 0: inhibitor at END_X
        # Health 100: inhibitor at START_X
        health_ratio_for_movement = health / HEALTH_MAX
        inhibitor_current_x = INHIBITOR_END_X + (INHIBITOR_START_X - INHIBITOR_END_X) * health_ratio_for_movement
        
        screen.blit(inhibitor_triangle_img, (inhibitor_current_x, INHIBITOR_Y))

    health_ratio = max(0, health / HEALTH_MAX)
    current_bar_width_ei = int(HEALTH_BAR_SIZE_EI[0] * health_ratio)

    if health_ratio > 0.5:
        g = 255
        r = int(255 * (1 - (health_ratio - 0.5) * 2))
    else:
        r = 255
        g = int(255 * (health_ratio * 2))
    bar_color_ei = (max(0, min(255, r)), max(0, min(255, g)), 0)
    
    pygame.draw.rect(screen, BLACK, (HEALTH_BAR_POS_EI[0]-2, HEALTH_BAR_POS_EI[1]-2, HEALTH_BAR_SIZE_EI[0]+4, HEALTH_BAR_SIZE_EI[1]+4))
    pygame.draw.rect(screen, bar_color_ei, (HEALTH_BAR_POS_EI[0], HEALTH_BAR_POS_EI[1], current_bar_width_ei, HEALTH_BAR_SIZE_EI[1]))

    health_text_surf_ei = game_font_large.render(f"{int(health)}%", True, WHITE)
    health_text_rect_ei = health_text_surf_ei.get_rect(midright=(HEALTH_BAR_POS_EI[0] - 30, HEALTH_BAR_POS_EI[1] + HEALTH_BAR_SIZE_EI[1] // 2))
    screen.blit(health_text_surf_ei, health_text_rect_ei)

    if tap_button_flash_timer > 0:
        # Ensure TAP_BUTTON_VISUAL_RECT is defined appropriately for this game's "TAP!" button
        flash_surface = pygame.Surface(TAP_BUTTON_VISUAL_RECT.size, pygame.SRCALPHA)
        flash_surface.fill(FLASH_COLOR)
        screen.blit(flash_surface, TAP_BUTTON_VISUAL_RECT.topleft)
        tap_button_flash_timer -= 1

# --- Main Game Loop ---
clock = pygame.time.Clock()
running = True
DEBUG_DRAW_BUTTON_RECTS = False # Set to True to see button hitboxes

while running:
    mouse_pos = pygame.mouse.get_pos()
    # dt = clock.tick(60) / 1000.0 # dt is not used, can be removed if not planned for physics

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            if current_mode == "slideshow":
                game_to_start_now = None
                # Check if current slide is one of the game info slides
                # Slide 3: Oxidative Stress Info (then game starts on slide 4 implicitly by space)
                # Slide OSMOTIC_GAME_INFO_SLIDE_INDEX (10): Osmotic Shock Info
                # Slide ENZYME_GAME_INFO_SLIDE_INDICES (6, 7): Enzyme Inhibition Info
                if event.key == pygame.K_SPACE:
                    if current_slide_index == 3: # Info for Oxidative Stress
                        start_game("oxidative_stress")
                        # No slide change here, game mode handles drawing
                    elif current_slide_index == OSMOTIC_GAME_INFO_SLIDE_INDEX: # Info for Osmotic
                        start_game("osmotic_shock")
                    elif current_slide_index in ENZYME_GAME_INFO_SLIDE_INDICES: # Info for Enzyme
                        start_game("enzyme_inhibition")
                    # If game started, continue to next iteration of main loop
                    if active_game_type:
                        continue
            
            elif current_mode in ["game_oxidative_stress", "game_osmotic_shock", "game_enzyme_inhibition"]:
                if event.key == pygame.K_SPACE:
                    if space_tap_sound.get_num_channels() < 8 : # Limit concurrent plays
                         space_tap_sound.play()
                    health -= DAMAGE_PER_TAP
                    health = max(health, HEALTH_MIN) # Clamp health
                    tap_button_flash_timer = FLASH_DURATION_FRAMES


        if event.type == pygame.MOUSEBUTTONDOWN and current_mode == "slideshow":
            if event.button == 1: # Left click
                for button_data in buttons:
                    # Check if button is visible on the current slide
                    if current_slide_index in button_data.get("visible_on_slides", []):
                        if button_data["rect"].collidepoint(mouse_pos):
                            if button_beep_sound.get_num_channels() < 4:
                                button_beep_sound.play()
                            
                            action = button_data.get("action")
                            if action == "goto_slide":
                                target_slide_index = button_data.get("target_slide")
                                
                                # Special handling for game start slides to prevent accidental skip via button
                                # if current_slide_index == 3 and target_slide_index == 4: # OS info to OS boom
                                #     # This button should ideally lead to the game, not boom slide directly
                                #     # Or, spacebar starts game, button click on info slide is disabled or also starts game
                                #     pass # Let spacebar handle game start
                                # elif current_slide_index == OSMOTIC_GAME_INFO_SLIDE_INDEX and target_slide_index == OSMOTIC_GAME_BOOM_SLIDE_INDEX:
                                #     pass
                                # elif current_slide_index in ENZYME_GAME_INFO_SLIDE_INDICES and target_slide_index == ENZYME_GAME_BOOM_SLIDE_INDEX:
                                #     pass
                                # else: # Default button action
                                if 0 <= target_slide_index < total_slides:
                                    current_slide_index = target_slide_index
                                else:
                                    print(f"Warning: Button '{button_data['id']}' target {target_slide_index} out of bounds.")
                            break # Found clicked button

    # Game Logic Update
    if current_mode == "game_oxidative_stress":
        update_oxidative_stress_game()
    elif current_mode == "game_osmotic_shock":
        update_osmotic_shock_game()
    elif current_mode == "game_enzyme_inhibition":
        update_enzyme_inhibition_game()

    # Drawing
    screen.fill(BLACK) # Default background, might be overwritten
    if current_mode == "slideshow":
        if 0 <= current_slide_index < total_slides:
            screen.blit(slide_images[current_slide_index], (0, 0))
            if DEBUG_DRAW_BUTTON_RECTS: # Draw button rects if debug is on
                for btn_data in buttons:
                    if current_slide_index in btn_data.get("visible_on_slides", []):
                        pygame.draw.rect(screen, (255,0,0,100), btn_data["rect"], 2) # Semi-transparent red border
        else: # Fallback if slide index is out of bounds
            screen.fill(LIGHT_GRAY)
            error_font = pygame.font.Font(None, 72)
            text_surf = error_font.render(f"Error: Invalid slide index {current_slide_index}", True, BLACK)
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text_surf, text_rect)
            
    elif current_mode == "game_oxidative_stress":
        draw_oxidative_stress_game_elements()
    elif current_mode == "game_osmotic_shock":
        draw_osmotic_shock_game_elements()
    elif current_mode == "game_enzyme_inhibition":
        draw_enzyme_inhibition_game_elements()

    pygame.display.flip()
    clock.tick(60) # Cap FPS

pygame.quit()
sys.exit()