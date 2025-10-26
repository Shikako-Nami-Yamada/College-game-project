import os
import random
import math
import pygame
# Import specific modules from os for clarity and robustness
from os import listdir
from os.path import isfile, join, dirname, abspath

pygame.init()

pygame.display.set_caption("Uga-Buga Platformer")

# --- Constants ---
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
BLOCK_SIZE = 96 # Consistent size for terrain blocks

window = pygame.display.set_mode((WIDTH, HEIGHT))

# --- Utility Functions ---

def get_base_path(relative_path):
    """Returns the absolute path, starting from the script's directory. 
    This is much more reliable than using '..' relative paths."""
    try:
        # Get the directory where the script is located
        base_dir = dirname(abspath(__file__))
    except NameError:
        # Fallback for environments where __file__ is not defined
        base_dir = os.getcwd()
        
    return join(base_dir, relative_path)


def load_image(relative_path, scale_factor=1):
    """Loads a single image from a relative path and scales it."""
    path = get_base_path(relative_path)
    try:
        image = pygame.image.load(path).convert_alpha()
        if scale_factor != 1:
            return pygame.transform.scale(image, (int(image.get_width() * scale_factor), int(image.get_height() * scale_factor)))
        return image
    except pygame.error as e:
        # Fallback for missing assets
        print(f"Error loading image at {path}: {e}")
        size = 100 * scale_factor
        placeholder = pygame.Surface((size, size))
        placeholder.fill((255, 0, 255)) # Bright pink placeholder
        return placeholder


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    """Loads sprites from a sheet in the assets directory."""
    path = get_base_path(join("assets", dir1, dir2))
    
    try:
        images = [f for f in listdir(path) if isfile(join(path, f))]
    except FileNotFoundError:
        print(f"Error: Could not find sprite directory at {path}")
        return {} 

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size, tile_col=1, tile_row=0): 
    """
    Loads a single 32x32 terrain block from Terrain.png based on (col, row) index,
    and scales it to the target size (e.g., 96x96).
    """
    # The path is now correctly pointing to the Terrain.png file.
    path = get_base_path(join("assets", "Terrain", "Terrain.png"))
    image = pygame.image.load(path).convert_alpha()
    
    # Calculate source rectangle based on column (x) and row (y) in the 32x32 grid
    src_x = tile_col * 32 
    src_y = tile_row * 32
    
    # 1. Grab the 32x32 source image
    source_surface = pygame.Surface((32, 32), pygame.SRCALPHA, 32)
    rect = pygame.Rect(src_x, src_y, 32, 32) 
    source_surface.blit(image, (0, 0), rect)
    
    # 2. Scale it to the BLOCK_SIZE (96x96)
    scaled_surface = pygame.transform.scale(source_surface, (size, size))
    
    # 3. Create the final surface for the Block object
    final_surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    final_surface.blit(scaled_surface, (0, 0))
    
    return final_surface


# --- Player Class ---

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    # Main Character Sprites - MaskDude
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True) 
    ANIMATION_DELAY = 3
    POINTS_PER_COLLECTIBLE = 10 

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        
        # --- Game Variables ---
        self.max_health = 5 # Starting max health is 5
        self.health = self.max_health 
        self.invincibility_time = FPS * 2 
        self.score = 0
        
        # --- Checkpoint/Respawn Data ---
        self.respawn_x = x
        self.respawn_y = y
        self.respawn_health = self.max_health
        # -----------------------------

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        if not self.hit: 
            self.hit = True
            self.hit_count = 0
            self.health -= 1
            print(f"Player hit! Health remaining: {self.health}")
            
    def respawn(self):
        """Resets player position and health to the last saved checkpoint state."""
        self.rect.x = self.respawn_x
        self.rect.y = self.respawn_y
        self.health = self.respawn_health
        self.x_vel = 0
        self.y_vel = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        print(f"Respawned at ({self.respawn_x}, {self.respawn_y}) with {self.respawn_health} health.")

    def heal(self):
        if self.health < self.max_health:
            self.health = min(self.max_health, self.health + 1)
            print(f"Player healed! Health: {self.health}")
            
    def add_score(self):
        self.score += self.POINTS_PER_COLLECTIBLE
        print(f"Banana collected! Score: {self.score}")

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > self.invincibility_time: 
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        # Player flashing when hit
        if self.hit and self.hit_count // 5 % 2 == 0: 
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                             self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        # Draw player only if not hit or during the flash part of the hit animation
        if not self.hit or self.hit_count // 5 % 2 == 0:
            win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


# --- Object/Block/Fire Classes ---

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    # Terrain Types (col, row) based on common platformer sprite sheets
    TERRAIN_TYPES = {
        # Grass/Dirt
        "GRASS_TOP": (1, 0), 	
        "DIRT_FILL": (1, 1), 	
        "GRASS_TOP_L": (0, 0), 	
        "GRASS_TOP_R": (2, 0), 	
        
        # Stone/Cave
        "STONE_TOP": (3, 0), 	
        "STONE_FILL": (3, 1), 	
        
        # Sand/Desert 
        "SAND_TOP": (4, 0),
        "SAND_FILL": (4, 1),
        
        # Snow/Ice
        "ICE_TOP": (9, 0),
        "ICE_FILL": (9, 1),
    }
    
    def __init__(self, x, y, size, terrain_key="GRASS_TOP"):
        super().__init__(x, y, size, size, "block")
        
        if terrain_key not in self.TERRAIN_TYPES:
            print(f"Warning: Unknown terrain key '{terrain_key}'. Using GRASS_TOP.")
            terrain_key = "GRASS_TOP"
            
        col, row = self.TERRAIN_TYPES[terrain_key]
        block_image = get_block(size, tile_row=row, tile_col=col) 
        
        self.image.blit(block_image, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3
    FIRE_WIDTH = 32
    FIRE_HEIGHT = 64

    def __init__(self, x, y):
        super().__init__(x, y, self.FIRE_WIDTH, self.FIRE_HEIGHT, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", 16, 32)
        self.image = self.fire["on"][0] 
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "on" 

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                              self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY >= len(sprites):
            self.animation_count = 0
            
            
class Spikes(Object):
    SPIKE_WIDTH = BLOCK_SIZE
    SPIKE_HEIGHT = BLOCK_SIZE
    
    def __init__(self, x, y):
        super().__init__(x, y, self.SPIKE_WIDTH, self.SPIKE_HEIGHT, "spikes")
        
        path = get_base_path(join("assets", "Traps", "Spikes", "Idle.png"))
        original_image = pygame.image.load(path).convert_alpha()
        
        scaled_image = pygame.transform.scale(original_image, (self.SPIKE_WIDTH, self.SPIKE_HEIGHT))
        
        self.image.blit(scaled_image, (0, 0))
        self.mask = pygame.mask.from_surface(self.image) 
        
        
class Lava(Object):
    """Represents a hazardous lava/liquid block, using the same collision logic as spikes/fire."""
    LAVA_WIDTH = BLOCK_SIZE
    LAVA_HEIGHT = BLOCK_SIZE
    
    def __init__(self, x, y):
        super().__init__(x, y, self.LAVA_WIDTH, self.LAVA_HEIGHT, "lava")
        
        # Using a solid color or simple sprite for lava/toxic liquid
        self.image.fill((255, 100, 0)) # Bright Orange/Red for lava
        self.mask = pygame.mask.from_surface(self.image)


class Collectible(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "collectible")
        # Assuming "Bananas.png" is a sheet of 32x32 frames
        path = get_base_path(join("assets", "Items", "Fruits", "Bananas.png")) 
        
        sprite_sheet = pygame.image.load(path).convert_alpha()
        
        # Load the first frame (32x32)
        original_width = 32
        original_height = 32
        
        cropped_surface = pygame.Surface((original_width, original_height), pygame.SRCALPHA, 32)
        crop_rect = pygame.Rect(0, 0, original_width, original_height)
        cropped_surface.blit(sprite_sheet, (0, 0), crop_rect)

        # Scale it to the target size (96x96)
        self.image = pygame.transform.scale(cropped_surface, (96, 96))
        self.mask = pygame.mask.from_surface(self.image)
        self.width = self.image.get_width()
        self.height = self.image.get_height()


# --- START CHECKPOINT ---
class StartCheckpoint(Object):
    CHECKPOINT_FRAME_WIDTH = 64
    CHECKPOINT_FRAME_HEIGHT = 64
    
    def __init__(self, x, y):
        super().__init__(x, y, self.CHECKPOINT_FRAME_WIDTH * 2, self.CHECKPOINT_FRAME_HEIGHT * 2, "checkpoint")
        
        self.idle_image = self._load_idle_image()
        self.moving_sprites = self._load_moving_sprites()
        
        self.animation_count = 0
        self.ANIMATION_DELAY = 4 
        self.is_active = False 
        self.activate_on_init = False # New flag for level loading
        
        self.image = self.idle_image
        self.mask = pygame.mask.from_surface(self.image)
        
    def _load_idle_image(self):
        """Loads and scales the single idle checkpoint image (64x64 -> 128x128) from Start folder."""
        path = get_base_path(join("assets", "Items", "Checkpoints", "Start", "Start (Idle).png"))
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale2x(image)
        
    def _load_moving_sprites(self):
        """Loads and scales the animated checkpoint sprite sheet (64x64 frames -> 128x128) from Start folder."""
        path = get_base_path(join("assets", "Items", "Checkpoints", "Start", "Start (Moving) (64x64).png"))
        sprite_sheet = pygame.image.load(path).convert_alpha()
        
        sprites = []
        width = self.CHECKPOINT_FRAME_WIDTH
        height = self.CHECKPOINT_FRAME_HEIGHT
        
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))
        return sprites

    def activate(self, player):
        """Sets the checkpoint to its active (moving) state and saves player state."""
        if not self.is_active:
            self.is_active = True
            player.respawn_x = self.rect.x + (self.width // 2) - (player.rect.width // 2) 
            player.respawn_y = self.rect.y - player.rect.height
            player.respawn_health = player.health
            print(f"Checkpoint activated! Respawn set to ({player.respawn_x}, {player.respawn_y})")
        
    def loop(self):
        """Updates the checkpoint animation."""
        if self.is_active:
            sprites = self.moving_sprites
            sprite_index = (self.animation_count //
                             self.ANIMATION_DELAY) % len(sprites)
            self.image = sprites[sprite_index]
            self.animation_count += 1
            if self.animation_count // self.ANIMATION_DELAY >= len(sprites):
                self.animation_count = 0
        else:
            self.image = self.idle_image
            
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

# --- END CHECKPOINT ---
class EndCheckpoint(Object):
    CHECKPOINT_FRAME_WIDTH = 64
    CHECKPOINT_FRAME_HEIGHT = 64
    
    def __init__(self, x, y):
        super().__init__(x, y, self.CHECKPOINT_FRAME_WIDTH * 2, self.CHECKPOINT_FRAME_HEIGHT * 2, "endpoint") 
        
        self.idle_image = self._load_idle_image()
        self.moving_sprites = self._load_moving_sprites() 
        
        self.animation_count = 0
        self.ANIMATION_DELAY = 4 
        self.is_active = False 
        
        self.image = self.idle_image
        self.mask = pygame.mask.from_surface(self.image)
        
    def _load_idle_image(self):
        """Loads and scales the single idle checkpoint image (64x64 -> 128x128) from End folder."""
        path = get_base_path(join("assets", "Items", "Checkpoints", "End", "End (Idle).png"))
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale2x(image)
        
    def _load_moving_sprites(self):
        """Loads and scales the animated checkpoint sprite sheet (64x64 frames -> 128x128) from End folder."""
        sprites = []
        path = get_base_path(join("assets", "Items", "Checkpoints", "End", "End (Pressed) (64x64).png"))
        
        try:
            sprite_sheet = pygame.image.load(path).convert_alpha()
            
            width = self.CHECKPOINT_FRAME_WIDTH
            height = self.CHECKPOINT_FRAME_HEIGHT
            
            for i in range(sprite_sheet.get_width() // width):
                surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
                rect = pygame.Rect(i * width, 0, width, height)
                surface.blit(sprite_sheet, (0, 0), rect)
                sprites.append(pygame.transform.scale2x(surface))
        except pygame.error:
            print(f"WARNING: End Checkpoint moving sprite not found. Using idle image as fallback.")
            sprites.append(self.idle_image)
            
        return sprites

    def activate(self):
        self.is_active = True
        
    def loop(self):
        if self.is_active:
            sprites = self.moving_sprites
            sprite_index = (self.animation_count //
                             self.ANIMATION_DELAY) % len(sprites)
            self.image = sprites[sprite_index]
            self.animation_count += 1
            if self.animation_count // self.ANIMATION_DELAY >= len(sprites):
                self.animation_count = 0
        else:
            self.image = self.idle_image
            
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)


# --- BOSS CLASS: RockHead ---

class RockHead(Object):
    BOSS_FRAME_WIDTH = 42
    BOSS_FRAME_HEIGHT = 42
    ANIMATION_DELAY = 5
    # Boss scale increased to 3
    BOSS_SCALE_FACTOR = 3 
    
    def __init__(self, x, y):
        # Use the new scale factor to set the object's width and height
        super().__init__(x, y, self.BOSS_FRAME_WIDTH * self.BOSS_SCALE_FACTOR, self.BOSS_FRAME_HEIGHT * self.BOSS_SCALE_FACTOR, "rockhead_boss")
        self.health = 5 # Boss health
        self.max_health = 5
        self.animation_count = 0
        self.hit = False
        self.hit_count = 0
        self.invincibility_time = FPS * 0.5 # 0.5 second invincibility after taking damage
        self.current_animation = "idle"
        self.sprites = self._load_boss_sprites()
        self.image = self.sprites["idle"][0]
        self.mask = pygame.mask.from_surface(self.image)
        
        # Movement/AI
        self.patrol_distance = BLOCK_SIZE * 3 # Boss patrols 3 blocks left/right
        self.start_x = x
        self.x_vel = 1.5 
        
        # NEW: Visibility flag for post-defeat state
        self.is_visible = True
        
    def _load_boss_sprites(self):
        """Loads and scales the specific Rock Head sprite sheets using BOSS_SCALE_FACTOR."""
        base_path = join("assets", "Traps", "Rock Head")
        
        # Asset mapping: (filename, is_sheet)
        sprite_data = {
            "blink": ("Blink (42x42).png", True),
            "bottom_hit": ("Bottom Hit (42x42).png", True),
            "left_hit": ("Left Hit (42x42).png", True),
            "right_hit": ("Right Hit (42x42).png", True),
            "top_hit": ("Top Hit (42x42).png", True),
            "idle": ("Idle.png", False) 
        }
        
        all_sprites = {}
        scaled_size = (self.BOSS_FRAME_WIDTH * self.BOSS_SCALE_FACTOR, self.BOSS_FRAME_HEIGHT * self.BOSS_SCALE_FACTOR)
        
        for name, (filename, is_sheet) in sprite_data.items():
            path = get_base_path(join(base_path, filename))
            
            try:
                sprite_sheet = pygame.image.load(path).convert_alpha()
            except pygame.error as e:
                print(f"Error loading boss sprite sheet {filename}: {e}")
                continue

            sprites = []
            
            if is_sheet:
                # Load as a sheet of 42x42 frames
                width, height = self.BOSS_FRAME_WIDTH, self.BOSS_FRAME_HEIGHT
                for i in range(sprite_sheet.get_width() // width):
                    surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
                    rect = pygame.Rect(i * width, 0, width, height)
                    surface.blit(sprite_sheet, (0, 0), rect)
                    # Scale it using the new factor
                    sprites.append(pygame.transform.scale(surface, scaled_size))
            else:
                # Load as a single image (Idle)
                # Scale it using the new factor
                sprites.append(pygame.transform.scale(sprite_sheet, scaled_size))
                
            all_sprites[name] = sprites
            
        return all_sprites
        
    def set_animation(self, name):
        """Sets the current animation and resets the frame counter."""
        # Only switch if we are not already playing a hit/blink animation or if we are forced to
        if name != self.current_animation:
            self.current_animation = name
            self.animation_count = 0
            
    def take_hit(self, hit_side):
        """Called when the player successfully hits the boss."""
        if self.hit:
            return False # Ignore hit if invincible
            
        self.health -= 1
        self.hit = True
        self.hit_count = 0
        
        # Set animation based on hit side (usually top_hit for player success)
        if hit_side == "top":
            self.set_animation("top_hit")
        elif hit_side == "left":
            self.set_animation("left_hit") 
        elif hit_side == "right":
            self.set_animation("right_hit")
        elif hit_side == "bottom":
            self.set_animation("bottom_hit")
            
        print(f"Boss hit from {hit_side}! Health: {self.health}")
        return True

    def loop(self):
        if not self.is_visible: # Stop all movement and animation if defeated
            return
            
        # 1. Boss Movement (Patrol)
        self.rect.x += self.x_vel
        # Reverse direction if hitting patrol boundaries
        if self.rect.x >= self.start_x + self.patrol_distance or self.rect.x <= self.start_x:
            self.x_vel *= -1
            
        # 2. Handle invincibility
        if self.hit:
            self.hit_count += 1
            if self.hit_count > self.invincibility_time:
                self.hit = False
                self.hit_count = 0
                self.set_animation("idle")

        # 3. Animation update
             
        # Random Blink trigger while idling (approx. once every 5 seconds)
        if self.current_animation == "idle" and random.randint(1, FPS * 5) == 1: 
             self.set_animation("blink")
             
        sprites = self.sprites[self.current_animation]
        
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        # Reset animation counter for one-shot animations (Hit/Blink)
        if self.current_animation != "idle" and self.animation_count // self.ANIMATION_DELAY >= len(sprites):
            self.set_animation("idle") 
            
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)
        
    def draw(self, win, offset_x):
        """Draws the boss, with flashing effect if it's currently hit (invincible)."""
        if not self.is_visible:
            return # Boss is hidden after defeat
            
        # Draw only if not hit or during the flash part of the hit animation (to ensure visibility)
        if not self.hit or self.hit_count // 5 % 2 == 0:
            win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


# --- Level Creation Functions ---

def create_level_objects(level_id, block_size, floor_y):
    """
    Creates and returns the player, object list, and starting coordinates 
    based on the given level ID.
    """
    objects = []
    
    # Common helper variables
    player_height = 64 
    collectible_size = 96
    fire_y = floor_y - Fire.FIRE_HEIGHT
    
    start_checkpoint = StartCheckpoint(0, 0) # Temporary init

    if level_id == "level_01":
        # --- LEVEL 1: EXTENDED GAUNTLET WITH MORE TRAPS AND PLATFORMS ---
        
        # 1. STARTING PLATFORM & CHECKPOINT (X=0 to X=6, GRASS)
        for i in range(7):
            objects.append(Block(i * block_size, floor_y, block_size, "GRASS_TOP"))
            objects.append(Block(i * block_size, floor_y + block_size, block_size, "DIRT_FILL"))
            
        start_checkpoint = StartCheckpoint(block_size * 1, floor_y - StartCheckpoint.CHECKPOINT_FRAME_HEIGHT * 2)
        objects.append(start_checkpoint)
        
        # 2. GAP and Floating Island (X=9 to X=11)
        island_y = floor_y - block_size * 2
        for i in range(9, 12):
            objects.append(Block(i * block_size, island_y, block_size, "GRASS_TOP"))
            
        objects.append(Collectible(block_size * 9, island_y - collectible_size, collectible_size, collectible_size)) # NEW Banana
        objects.append(Collectible(block_size * 11, island_y - collectible_size, collectible_size, collectible_size)) # NEW Banana

        # 3. MIDDLE PLATFORM (X=15 to X=18) - Higher jump to reach
        middle_platform_y = floor_y - block_size * 4
        for i in range(15, 19): 
            objects.append(Block(i * block_size, middle_platform_y, block_size, "GRASS_TOP"))
            
        objects.append(Collectible(block_size * 16, middle_platform_y - collectible_size, collectible_size, collectible_size))
        objects.append(Collectible(block_size * 17, middle_platform_y - collectible_size, collectible_size, collectible_size)) # NEW Banana

        # 4. Stepping Stones Gap (X=21 to X=26)
        # Small floating blocks requiring precise jumps over a pit (floor assumed).
        
        # Stone 1 (Low)
        stone1_y = floor_y - block_size * 1.5
        objects.append(Block(block_size * 21, stone1_y, block_size, "STONE_TOP"))
        objects.append(Collectible(block_size * 21, stone1_y - collectible_size, collectible_size, collectible_size)) # NEW Banana
        
        # Stone 2 (High)
        stone2_y = floor_y - block_size * 3.5
        objects.append(Block(block_size * 24, stone2_y, block_size, "STONE_TOP"))
        
        # Stone 3 (Medium)
        stone3_y = floor_y - block_size * 2.5
        objects.append(Block(block_size * 26, stone3_y, block_size, "STONE_TOP"))


        # 5. Fire Gauntlet Platform (X=28 to X=31) - Requires timing
        fire_platform_y = floor_y - block_size 
        for i in range(28, 32): 
            objects.append(Block(i * block_size, fire_platform_y, block_size, "DIRT_FILL"))
            
        objects.append(Collectible(block_size * 28, fire_platform_y - collectible_size, collectible_size, collectible_size)) # NEW Banana
        objects.append(Fire(block_size * 29, fire_platform_y - Fire.FIRE_HEIGHT))
        objects.append(Fire(block_size * 30 + Fire.FIRE_WIDTH, fire_platform_y - Fire.FIRE_HEIGHT))


        # 6. Spikes Platform (X=33 to X=36) - Requires cautious landing/movement
        spike_platform_y = floor_y - block_size * 2
        
        for i in range(33, 37): # Platform from 33 to 36
            objects.append(Block(i * block_size, spike_platform_y, block_size, "STONE_TOP"))
            
        # Add Spikes
        spikes_y = spike_platform_y - Spikes.SPIKE_HEIGHT 
        objects.append(Spikes(block_size * 34, spikes_y))
        objects.append(Spikes(block_size * 35, spikes_y))
        
        objects.append(Collectible(block_size * 33, spikes_y - collectible_size, collectible_size, collectible_size)) # Existing Banana


        # 7. Double Fire Jump (X=38 to X=41) - Long jump over gap with fires
        # The landing platform is at X=41
        objects.append(Block(block_size * 41, floor_y, block_size, "GRASS_TOP"))
        objects.append(Block(block_size * 41, floor_y + block_size, block_size, "DIRT_FILL"))
        
        objects.append(Collectible(block_size * 41, floor_y - collectible_size - 10, collectible_size, collectible_size)) # NEW Banana
        
        # Two fires in the pit 
        objects.append(Fire(block_size * 38, fire_y))
        objects.append(Fire(block_size * 39 + Fire.FIRE_WIDTH, fire_y))


        # 8. Lava Pit Jump (X=43 to X=46) - Final big hazard
        # Fill the floor below this section with lava (death pit)
        for i in range(43, 47):
            objects.append(Lava(i * block_size, floor_y))
        
        
        # 9. FINAL PLATFORM (X=47 to X=49) and END CHECKPOINT
        final_platform_y = floor_y - block_size * 2
        for i in range(47, 50):
            objects.append(Block(i * block_size, final_platform_y, block_size, "STONE_TOP"))
            
        end_checkpoint_height = EndCheckpoint.CHECKPOINT_FRAME_HEIGHT * 2 
        end_checkpoint_x = block_size * 48 
        end_checkpoint_y = final_platform_y - end_checkpoint_height
        end_checkpoint = EndCheckpoint(end_checkpoint_x, end_checkpoint_y)
        objects.append(end_checkpoint)
        
        # Set player spawn location for this level
        start_x = block_size + 20
        start_y = floor_y - player_height
        start_checkpoint.activate_on_init = True
        
        
    elif level_id == "level_02":
        # --- LEVEL 2: TRAP GAUNTLET LEADING TO ROCKHEAD BOSS ARENA ---
        
        # Level dimensions 
        TRAP_SECTION_END = 8 # Blocks 0-7
        GAP_START = 8
        ARENA_START = 10     # Blocks 10-15
        ARENA_END = 15
        
        # 1. TRAP SECTION GROUND (X=0 to X=8)
        for i in range(TRAP_SECTION_END):
            objects.append(Block(i * block_size, floor_y, block_size, "STONE_TOP"))
            objects.append(Block(i * block_size, floor_y + block_size, block_size, "STONE_FILL"))
            
        start_x = block_size * 1
        start_y = floor_y - player_height
        
        # START CHECKPOINT
        start_checkpoint = StartCheckpoint(start_x - 50, floor_y - StartCheckpoint.CHECKPOINT_FRAME_HEIGHT * 2)
        objects.append(start_checkpoint)
        start_checkpoint.activate_on_init = True
        
        # TRAP SECTION ELEMENTS 
        spikes_height = Spikes.SPIKE_HEIGHT
        
        # Floating Platform 1 (High, for jumping over the spike pit)
        platform1_y = floor_y - block_size * 3
        objects.append(Block(block_size * 3, platform1_y, block_size, "STONE_TOP"))
        objects.append(Collectible(block_size * 3, platform1_y - collectible_size, collectible_size, collectible_size)) # Banana 1
        
        # Spike Pit 
        objects.append(Spikes(block_size * 5, floor_y - spikes_height))
        objects.append(Spikes(block_size * 6, floor_y - spikes_height))
        objects.append(Collectible(block_size * 5, floor_y - spikes_height - collectible_size, collectible_size, collectible_size)) # Banana 2
        
        # Final platform of the trap section (Block 7)
        objects.append(Block(block_size * 7, floor_y, block_size, "STONE_TOP"))
        objects.append(Collectible(block_size * 7, floor_y - collectible_size, collectible_size, collectible_size)) # Banana 3
        
        # 2. BOSS ARENA PLATFORM (X=10 to X=15) - Dedicated Boss Fight Zone
        for i in range(ARENA_START, ARENA_END + 1): 
            objects.append(Block(i * block_size, floor_y, block_size, "STONE_TOP"))
            objects.append(Block(i * block_size, floor_y + block_size, block_size, "STONE_FILL"))
        
        # Arena Platforms (for combat mobility)
        objects.append(Block(block_size * 13, floor_y - block_size * 2, block_size, "STONE_TOP")) # Low platform
        objects.append(Block(block_size * 11, floor_y - block_size * 4, block_size, "STONE_TOP")) # High platform
        
        # Arena Traps (Fire at both ends)
        fire_y = floor_y - Fire.FIRE_HEIGHT
        objects.append(Fire(block_size * 10, fire_y))
        objects.append(Fire(block_size * 15, fire_y)) 
        
        # 3. BOSS PLACEMENT (Center of the new arena section)
        boss = RockHead(0, 0) 
        
        boss_x = block_size * 12
        boss_y = floor_y - boss.height 
        
        boss.rect.x = boss_x
        boss.rect.y = boss_y
        boss.start_x = boss_x - block_size * 1.5 
        boss.patrol_distance = BLOCK_SIZE * 3 
        objects.append(boss)
        
        # 4. Hidden End Goal (Placed off-screen, activated upon boss defeat)
        end_checkpoint = EndCheckpoint(-500, -500)
        objects.append(end_checkpoint)
        
    else:
        # Fallback to level 1 if an invalid ID is used
        return create_level_objects("level_01", block_size, floor_y)

    # Initialize player outside the specific level block so we can set the start position
    player = Player(start_x, start_y, 50, 50) 
    
    # Manually activate the start checkpoint on level load for initial respawn setup
    if start_checkpoint.activate_on_init:
        start_checkpoint.activate(player)
        
    return player, objects, player.respawn_x, player.respawn_y


# --- Game Functions ---

def get_background(name):
    # Uses robust path finding for the background image
    image = pygame.image.load(get_base_path(join("assets", "Background", name))).convert()
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

def draw_text(window, text, size, x, y, color=(255, 255, 255)):
    font = pygame.font.SysFont("comicsans", size, bold=True)
    text_surface = font.render(text, 1, color)
    text_rect = text_surface.get_rect(center=(x, y))
    window.blit(text_surface, text_rect)

def draw_boss_health(window, boss, offset_x):
    """Draws the boss health bar and name above the boss."""
    # Only draw if the boss is visible and has health
    if not boss.is_visible or boss.health <= 0: 
        return
        
    bar_width = boss.width 
    bar_height = 10
    
    # Calculate screen coordinates
    x = boss.rect.x - offset_x
    y = boss.rect.y - bar_height - 10
    
    # Background bar (red/dark)
    pygame.draw.rect(window, (50, 50, 50), (x, y, bar_width, bar_height), 0, 3)
    
    # Foreground bar (green)
    health_ratio = boss.health / boss.max_health
    current_health_width = bar_width * health_ratio
    
    pygame.draw.rect(window, (0, 255, 0), (x, y, current_health_width, bar_height), 0, 3)
    
    draw_text(window, "Rock Head", 20, x + bar_width / 2, y - 15, (255, 255, 255))


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    # Draw UI (Health and Score)
    draw_text(window, f"Health: {player.health}/{player.max_health}", 30, WIDTH - 150, 30)
    draw_text(window, f"Score: {player.score}", 30, WIDTH - 350, 30)

    # Check and draw boss health if available
    boss = next((obj for obj in objects if obj.name == "rockhead_boss"), None)
    if boss:
        draw_boss_health(window, boss, offset_x)


    pygame.display.update()

def display_start_screen(window):
    """
    Shows the title screen, now using Play.png as the main visual element 
    and waits for ENTER to proceed.
    """
    
    BG_COLOR = (25, 50, 60) 	
    
    # Load the specified image for the Title Screen
    play_img = load_image(join("assets", "Menu", "Buttons", "Play.png"), scale_factor=3.5) 
    play_img_rect = play_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    clock = pygame.time.Clock()
    
    waiting = True
    while waiting:
        clock.tick(FPS)
        
        window.fill(BG_COLOR)
        
        # Draw the Play.png image
        window.blit(play_img, play_img_rect.topleft)
        
        # Draw Title Text
        draw_text(window, "UGA-BUGA PLATFORMER", 60, WIDTH // 2, 50, (255, 165, 0))
        
        # Draw prompt over the image
        draw_text(window, "Press ENTER to Select Level", 40, WIDTH // 2, HEIGHT - 100, (255, 255, 255))
        
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return "level_select" # Transition to level select
                if event.key == pygame.K_ESCAPE:
                    return "quit"
    return "quit"


def display_level_select(window):
    """
    Shows the level selection screen. Uses a simple background now, 
    and displays 01.png and 02.png as level icons.
    """
    BG_COLOR = (25, 50, 60) # Dark Blue/Green Background
    
    clock = pygame.time.Clock()
    
    # Increased scale_factor to 2.5 for larger icons
    LEVEL_ICON_SCALE = 2.5 

    # Load level icons
    level_icons = {
        "level_01": load_image(join("assets", "Menu", "Levels", "01.png"), scale_factor=LEVEL_ICON_SCALE),
        "level_02": load_image(join("assets", "Menu", "Levels", "02.png"), scale_factor=LEVEL_ICON_SCALE),
    }

    # Define button placement
    ICON_SPACING = 250 # Adjusted spacing for larger icons
    CENTER_Y = HEIGHT // 2 + 50
    
    LEVEL_BUTTONS = [
        # Level 1 icon placed to the left of center
        {"id": "level_01", "img": level_icons["level_01"], "rect": level_icons["level_01"].get_rect(center=(WIDTH // 2 - ICON_SPACING, CENTER_Y))},
        # Level 2 icon placed to the right of center
        {"id": "level_02", "img": level_icons["level_02"], "rect": level_icons["level_02"].get_rect(center=(WIDTH // 2 + ICON_SPACING, CENTER_Y))},
    ]

    waiting = True
    while waiting:
        clock.tick(FPS)
        
        window.fill(BG_COLOR)
        
        # Draw Title
        draw_text(window, "SELECT LEVEL", 70, WIDTH // 2, 150, (255, 255, 255))

        
        for button in LEVEL_BUTTONS:
            # Draw the level icon (01.png or 02.png)
            icon = button["img"]
            window.blit(icon, button["rect"].topleft)
            
            # Draw level number label
            label = button["id"].split("_")[1]
            if label == "02":
                 draw_text(window, f"BOSS ARENA", 30, button["rect"].centerx, button["rect"].bottom + 20, (255, 100, 100))
            else:
                 draw_text(window, f"Level {label}", 30, button["rect"].centerx, button["rect"].bottom + 20, (255, 255, 255))
            
            # Highlight on hover
            if button["rect"].collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(window, (255, 255, 255), button["rect"], 3, 5)


        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "title_screen" # Go back to title
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    for button in LEVEL_BUTTONS:
                        if button["rect"].collidepoint(event.pos):
                            return button["id"]

    return "quit" # Should not be reached


def run_level(window, level_id):
    """
    Main game loop, now dedicated to running a specific level.
    """
    
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    # --- Level Constants ---
    block_size = BLOCK_SIZE 
    floor_y = HEIGHT - block_size
    
    # --- LEVEL INITIALIZATION ---
    player, objects, start_x, start_y = create_level_objects(level_id, block_size, floor_y)
    
    # Calculate the total width of the level based on the rightmost object 
    max_world_x = max((obj.rect.right for obj in objects if obj.name in ["block", "endpoint"]), default=WIDTH)
    # If it's a boss level (fixed arena), ensure the level width is just the screen width
    if level_id == "level_02":
        level_width = max_world_x + block_size # Ensure we can scroll slightly past the arena end
    else:
        # Give a little buffer space after the end checkpoint
        level_width = max(WIDTH, max_world_x + block_size) 
    
    # Set initial camera offset to center the player
    offset_x = player.rect.centerx - WIDTH // 2
    
    # Apply initial clamping for the start of the level
    if offset_x < 0:
        offset_x = 0
    elif offset_x > level_width - WIDTH:
        offset_x = level_width - WIDTH
        
    game_state = "running"
    
    # Game Loop
    while game_state == "running":
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_state = "quit"
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        
        # Loop over animatable objects (Fire, Checkpoints, Boss)
        for obj in objects:
            if hasattr(obj, "loop"):
                obj.loop()
                
        # --- Fall-to-Death Check ---
        # If the player falls 100 pixels below the screen, they lose instantly.
        if player.rect.y > HEIGHT + 100:
            player.health = 0
            
        # Check for death and transition to lose screen if health is 0
        if player.health <= 0:
            game_state = "lose"
            continue
            
        # Handle movement and collisions
        move_result = handle_move(player, objects)
        
        # BOSS LEVEL WIN CONDITION
        if level_id == "level_02":
            boss = next((obj for obj in objects if obj.name == "rockhead_boss"), None)
            end_checkpoint = next((obj for obj in objects if obj.name == "endpoint"), None)
            
            # Win if the boss is defeated!
            if boss and boss.health <= 0 and end_checkpoint: 
                
                # 1. Make boss invisible and stop its logic
                if boss.is_visible:
                    boss.is_visible = False
                    boss_center_x = boss.rect.centerx
                    boss_bottom_y = boss.rect.bottom
                    
                    # 2. Move the goal to where the boss was, slightly above the floor
                    end_checkpoint.rect.x = boss_center_x - end_checkpoint.width // 2
                    end_checkpoint.rect.y = boss_bottom_y - end_checkpoint.height - 20 # 20px buffer
                    end_checkpoint.activate()
                
                # Check for collision with the now-active, visible endpoint
                if pygame.sprite.collide_mask(player, end_checkpoint):
                    game_state = "win"

        # STANDARD LEVEL WIN CONDITION
        elif move_result == "win":
            game_state = "win"
            
        # Handle scrolling (camera movement)
        
        # 1. Calculate the ideal offset to perfectly center the player
        target_offset_x = player.rect.centerx - WIDTH // 2
        
        # 2. Clamp the offset against the left edge of the world (0)
        clamped_offset_x = max(0, target_offset_x)
        
        # 3. Clamp the offset against the right edge of the world
        max_offset_x = max(0, level_width - WIDTH)
        
        # Set the final offset, ensuring it doesn't exceed the right boundary
        offset_x = min(max_offset_x, clamped_offset_x)
            
        # Draw everything
        draw(window, background, bg_image, player, objects, offset_x)

    # After the main loop, handle game state transitions
    if game_state == "win":
        result = display_game_over(window, "win", f"YOU WON! Score: {player.score}")
    elif game_state == "lose":
        result = display_game_over(window, "lose", "GAME OVER")
    elif game_state == "quit":
        # Returning "level_select" here ensures the main loop transitions back to the menu
        result = "level_select" 
    else:
        result = "level_select"
        
    return result


def main(window):
    """The new main function manages the overall game state flow."""
    game_screen = "title_screen" # Start here
    level_to_run = None
    
    while game_screen != "quit":
        if game_screen == "title_screen":
            game_screen = display_start_screen(window) # Returns "level_select" or "quit"
            
        elif game_screen == "level_select":
            # Returns "level_01", "level_02", "title_screen", or "quit"
            selected_level_id = display_level_select(window) 
            
            if selected_level_id in ["level_01", "level_02"]:
                level_to_run = selected_level_id
                game_screen = "running_level"
            else:
                game_screen = selected_level_id # "title_screen" or "quit"
                
        elif game_screen == "running_level":
            # run_level returns "restart" or "level_select"
            result = run_level(window, level_to_run) 
            
            if result == "restart":
                # Restart the same level by staying in the current state
                game_screen = "running_level" 
            elif result == "level_select":
                # Go back to the level selection screen
                game_screen = "level_select"
            elif result == "quit":
                game_screen = "quit"

    pygame.quit()
    quit()


# --- Collision Handling (re-included for completeness) ---

def handle_vertical_collision(player, objects, dy):
    """Handles collision in the Y-direction (jumping/falling)."""
    collided_objects = []
    
    # Check against blocks (terrain)
    for obj in objects:
        if isinstance(obj, Block):
            if pygame.sprite.collide_mask(player, obj):
                if dy > 0: # Falling
                    player.rect.bottom = obj.rect.top
                    player.landed()
                elif dy < 0: # Jumping/hitting head
                    player.rect.top = obj.rect.bottom
                    player.hit_head()
                collided_objects.append(obj)
                
    return collided_objects

def handle_horizontal_collision(player, objects, dx):
    """Handles collision in the X-direction (running)."""
    collided = False
    
    for obj in objects:
        if isinstance(obj, Block):
            if pygame.sprite.collide_mask(player, obj):
                collided = True
                if dx > 0: # Moving right
                    player.rect.right = obj.rect.left
                elif dx < 0: # Moving left
                    player.rect.left = obj.rect.right
                break # Stop at the first collision
                
    return collided
    
def check_hit_trap(player, objects):
    """Checks for collision with hazardous traps (Fire, Spikes, Lava)."""
    for obj in objects:
        if obj.name in ["fire", "spikes", "lava"]:
            if pygame.sprite.collide_mask(player, obj):
                if not player.hit:
                    player.make_hit()
                    return True # Player was hit
    return False

def check_collectible(player, objects):
    """Checks for collision with collectibles (Bananas)."""
    collected = []
    for obj in objects:
        if obj.name == "collectible":
            if pygame.sprite.collide_mask(player, obj):
                player.add_score()
                collected.append(obj)
    
    # Remove collected items from the objects list
    for item in collected:
        objects.remove(item)

def check_checkpoint(player, objects):
    """Checks for collision with start/end checkpoints."""
    for obj in objects:
        if obj.name == "checkpoint":
            if pygame.sprite.collide_mask(player, obj):
                obj.activate(player)
        elif obj.name == "endpoint":
            if pygame.sprite.collide_mask(player, obj):
                # The win condition is handled in run_level for the boss level, 
                # but we activate the checkpoint here for animation
                obj.activate()
                # For standard levels, this will return "win"
                return "win" 
    return None

def handle_boss_collision(player, objects):
    """Handles all interaction with the RockHead boss."""
    boss = next((obj for obj in objects if obj.name == "rockhead_boss" and obj.is_visible), None)
    
    if not boss:
        return 

    if pygame.sprite.collide_mask(player, boss):
        # Determine the collision side 
        
        # Calculate player position one step prior to the vertical move
        player_rect_before_y_move = player.rect.move(0, -player.y_vel) 

        # --- Check for TOP HIT (Stomp) ---
        # A successful stomp happens IF:
        # a) Player is currently falling (player.y_vel > 0)
        # b) The player's bottom edge *was* above the boss's top edge in the last frame.
        if player.y_vel > 0 and player_rect_before_y_move.bottom <= boss.rect.top + 10: 
            
            # --- STOMP SUCCESS: Player Bounces, Boss Takes Damage ---
            
            # 1. Reposition player exactly on top of the boss to prevent sinking
            player.rect.bottom = boss.rect.top 
            
            # 2. Bounce the player up 
            # Increased knockback to match regular jump height for a satisfying bounce.
            player.y_vel = -Player.GRAVITY * 8 
            player.landed() 
            
            # 3. Boss takes damage
            boss.take_hit("top")
            
        # 2. Side or Bottom Hit (Player takes damage)
        # This executes if the collision is NOT a successful stomp.
        else:
            if not player.hit:
                player.make_hit() # Player takes damage here
                
                # Boss reacts to being hit by player's side/bottom (animation)
                if player.rect.centerx < boss.rect.centerx:
                    boss.set_animation("right_hit") # Boss reacts to hit coming from player's left side
                else:
                    boss.set_animation("left_hit") # Boss reacts to hit coming from player's right side
                    
                # Knockback the player
                knockback_vel = 15
                if player.rect.centerx < boss.rect.centerx:
                    player.move(-knockback_vel, 0)
                else:
                    player.move(knockback_vel, 0)

def handle_move(player, objects):
    """Updates player position and checks all collision types."""
    keys = pygame.key.get_pressed()
    
    # 1. Reset horizontal velocity
    player.x_vel = 0
    if keys[pygame.K_LEFT]:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT]:
        player.move_right(PLAYER_VEL)
    
    # 2. Level Boundary Check 
    if player.x_vel < 0 and player.rect.x + player.x_vel < 0:
        player.x_vel = 0         
        player.rect.x = 0        
        
    # Apply vertical movement and check collision
    player.move(0, player.y_vel)
    handle_vertical_collision(player, objects, player.y_vel)
    
    # Apply horizontal movement and check collision
    player.move(player.x_vel, 0)
    handle_horizontal_collision(player, objects, player.x_vel)
    
    # Check for hazards, collectibles, and checkpoints
    check_hit_trap(player, objects)
    check_collectible(player, objects)
    
    # Handle boss collision (only if boss is visible)
    handle_boss_collision(player, objects)
    
    # Check for win condition (only needed for standard levels)
    return check_checkpoint(player, objects)


# --- Game Over Function ---

def display_game_over(window, result_type, message):
    """
    Displays the game result screen (Win or Lose) with graphical buttons.
    Returns "restart" or "level_select".
    """
    BG_COLOR = (20, 20, 20)
    clock = pygame.time.Clock()
    
    # Increased scale_factor to 3 for larger buttons
    BUTTON_SCALE = 3
    
    # Load Button Images
    restart_img = load_image(join("assets", "Menu", "Buttons", "Restart.png"), scale_factor=BUTTON_SCALE)
    back_img = load_image(join("assets", "Menu", "Buttons", "Back.png"), scale_factor=BUTTON_SCALE)
    
    # Define Button Positions (centered vertically, spaced horizontally)
    BUTTON_SPACING = 220 # Adjusted spacing for larger buttons
    CENTER_Y = HEIGHT // 2 + 100
    
    BUTTONS = [
        {"id": "restart", "img": restart_img, "rect": restart_img.get_rect(center=(WIDTH // 2 - BUTTON_SPACING, CENTER_Y))},
        {"id": "level_select", "img": back_img, "rect": back_img.get_rect(center=(WIDTH // 2 + BUTTON_SPACING, CENTER_Y))},
    ]

    waiting = True
    while waiting:
        clock.tick(FPS)
        window.fill(BG_COLOR)
        
        # Display main message
        title_color = (255, 255, 0) if result_type == "win" else (255, 50, 50)
        draw_text(window, message, 60, WIDTH // 2, HEIGHT // 2 - 100, title_color)
        draw_text(window, "What would you like to do?", 30, WIDTH // 2, HEIGHT // 2, (255, 255, 255))
        
        # Draw and handle buttons
        for button in BUTTONS:
            window.blit(button["img"], button["rect"].topleft)
            
            # Highlight on hover
            if button["rect"].collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(window, (255, 255, 255), button["rect"], 3, 5)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "restart"
                if event.key == pygame.K_ESCAPE:
                    return "level_select"
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    for button in BUTTONS:
                        if button["rect"].collidepoint(event.pos):
                            return button["id"]
                            
    return "quit"

if __name__ == "__main__":
    main(window)