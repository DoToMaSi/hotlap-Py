"""
Hot LapY - A 2D Time Trial Racing Game

A thrilling 2D top-down racing game built with Pygame where players race 
against the clock to set the fastest lap times on various circuits.
"""

import pygame
import time
import math
from typing import Tuple, List, Optional


# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Car settings
CAR_WIDTH = 35
CAR_HEIGHT = 70

# Realistic car physics constants
MAX_SPEED = 8.0              # Maximum forward speed
MIN_SPEED = -4.0             # Maximum reverse speed
ACCELERATION = 0.04          # Base acceleration rate (reduced from 0.08 for much slower buildup)
DECELERATION = 0.4           # Natural deceleration (friction) - increased from 0.2
BRAKE_FORCE = 1.2            # Braking force - increased from 0.5
TURN_SPEED_BASE = 4.0        # Base turning speed
TURN_SPEED_FACTOR = 0.6      # Speed-dependent turning factor
TRACTION_LOSS_SPEED = 6.0    # Speed at which traction starts to decrease
FRICTION_COEFFICIENT = 0.95  # Overall friction multiplier

# Engine characteristics
ENGINE_TORQUE_MAX = 100      # Maximum torque (Nm)
ENGINE_POWER_MAX = 150       # Maximum power (HP)
OPTIMAL_RPM = 3500           # RPM for maximum power
MAX_RPM = 6000               # Redline RPM
IDLE_RPM = 800               # Idle RPM

# Realistic gear ratios (first gear = highest ratio, more torque multiplication)
GEAR_RATIOS = {
    -1: -3.5,    # Reverse gear
    0: 0.0,      # Neutral
    1: 3.5,      # First gear (high torque, low top speed)
    2: 2.1,      # Second gear
    3: 1.4,      # Third gear
    4: 1.0,      # Fourth gear (1:1 ratio)
    5: 0.8       # Fifth gear (overdrive, high top speed, low torque)
}

# Gear shift points (speed thresholds for automatic shifting)
SHIFT_UP_SPEEDS = {1: 1.5, 2: 2.8, 3: 4.2, 4: 5.8}  # Shift up at these speeds
SHIFT_DOWN_SPEEDS = {5: 5.0, 4: 3.5, 3: 2.2, 2: 1.0}  # Shift down below these speeds

# UI settings
FONT_SIZE = 28
UI_MARGIN = 10
UI_LINE_HEIGHT = 40


class GameAssets:
    """Handles loading and managing game assets."""
    
    def __init__(self):
        """Initialize and load all game assets."""
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)  # Higher quality for pitch shifting
        
        # Load images
        self.track_image = pygame.image.load('assets/images/track.png')
        # Load and vertically flip the car image to correct orientation
        car_image_raw = pygame.image.load('assets/images/car.png')
        self.car_image = pygame.transform.flip(car_image_raw, False, True)
        
        # Load sounds
        self.engine_sound = pygame.mixer.Sound('assets/sounds/car.wav')
        self.collision_sound = pygame.mixer.Sound('assets/sounds/collision.wav')
        
        # Store original engine sound data for pitch shifting
        self.original_engine_sound = pygame.mixer.Sound('assets/sounds/car.wav')


class Car:
    """Represents the player's car with realistic physics including acceleration, braking, and steering."""
    
    def __init__(self, x: float, y: float):
        """Initialize car at given position with physics properties."""
        # Position and orientation
        self.x = x
        self.y = y
        self.angle = 0  # Facing up initially (degrees)
        
        # Physics properties
        self.velocity = 0.0          # Current speed (forward/backward)
        self.angular_velocity = 0.0  # Current turning rate
        self.acceleration = 0.0      # Current acceleration
        
        # Engine state
        self.engine_rpm = IDLE_RPM
        self.throttle = 0.0         # 0.0 to 1.0 (actual applied throttle)
        self.brake = 0.0            # 0.0 to 1.0 (actual applied brake)
        self.steering = 0.0         # -1.0 to 1.0 (left to right)
        
        # Progressive input state
        self.target_throttle = 0.0  # Target throttle from input
        self.target_brake = 0.0     # Target brake from input
        self.throttle_rate = 1.0 / 0.6  # Rate to reach full throttle in 0.6 seconds
        self.brake_rate = 1.0 / 0.6     # Rate to reach full brake in 0.6 seconds
        
        # Transmission state
        self.current_gear = 1       # Start in first gear
        self.gear_shift_timer = 0.0 # Delay between shifts
        
        # Collision rectangle
        self.rect = pygame.Rect(x, y, CAR_WIDTH, CAR_HEIGHT)
        
        # Store initial position for reset
        self.initial_x = x
        self.initial_y = y
    
    def reset_to_initial_state(self):
        """Reset car to initial position and state."""
        self.x = self.initial_x
        self.y = self.initial_y
        self.angle = 0
        self.velocity = 0.0
        self.angular_velocity = 0.0
        self.acceleration = 0.0
        self.engine_rpm = IDLE_RPM
        self.throttle = 0.0
        self.brake = 0.0
        self.steering = 0.0
        self.target_throttle = 0.0
        self.target_brake = 0.0
        self.current_gear = 1
        self.gear_shift_timer = 0.0
        self.rect.topleft = (self.x, self.y)
    
    def update_progressive_inputs(self, dt: float):
        """Update throttle and brake progressively towards target values."""
        # Update throttle progressively (handles both forward and reverse)
        if self.target_throttle > self.throttle:
            # Accelerating towards target (forward or reverse)
            self.throttle = min(self.target_throttle, self.throttle + self.throttle_rate * dt)
        elif self.target_throttle < self.throttle:
            # Releasing throttle or moving towards reverse
            release_rate = self.throttle_rate * 2.0  # Release twice as fast
            self.throttle = max(self.target_throttle, self.throttle - release_rate * dt)
        
        # Update brake progressively
        if self.target_brake > self.brake:
            # Applying brake towards target
            self.brake = min(self.target_brake, self.brake + self.brake_rate * dt)
        elif self.target_brake < self.brake:
            # Releasing brake (faster release for more responsive feel)
            release_rate = self.brake_rate * 2.0  # Release twice as fast
            self.brake = max(self.target_brake, self.brake - release_rate * dt)
    
    def set_throttle_input(self, input_value: float):
        """Set target throttle from input (-1.0 to 1.0, negative for reverse)."""
        self.target_throttle = max(-1.0, min(1.0, input_value))
    
    def set_brake_input(self, input_value: float):
        """Set target brake from input (0.0 to 1.0)."""
        self.target_brake = max(0.0, min(1.0, input_value))
    
    def get_current_gear_ratio(self) -> float:
        """Get the current gear ratio."""
        return GEAR_RATIOS.get(self.current_gear, 1.0)
    
    def should_shift_up(self) -> bool:
        """Determine if car should shift to higher gear."""
        if self.current_gear >= 5 or self.current_gear <= 0:
            return False
        
        speed_threshold = SHIFT_UP_SPEEDS.get(self.current_gear, float('inf'))
        return abs(self.velocity) > speed_threshold and self.gear_shift_timer <= 0
    
    def should_shift_down(self) -> bool:
        """Determine if car should shift to lower gear."""
        if self.current_gear <= 1 or self.current_gear > 5:
            return False
        
        speed_threshold = SHIFT_DOWN_SPEEDS.get(self.current_gear, 0)
        return abs(self.velocity) < speed_threshold and self.gear_shift_timer <= 0
    
    def shift_gear(self, direction: int):
        """Shift gear up (+1) or down (-1)."""
        if direction > 0 and self.current_gear < 5:
            self.current_gear += 1
        elif direction < 0 and self.current_gear > 1:
            self.current_gear -= 1
        
        # Set shift delay to prevent rapid shifting
        self.gear_shift_timer = 0.5  # 0.5 seconds between shifts
    
    def update_transmission(self, dt: float = 1/60):
        """Update automatic transmission logic."""
        # Update shift timer
        if self.gear_shift_timer > 0:
            self.gear_shift_timer -= dt
        
        # Automatic shifting logic
        if self.should_shift_up():
            self.shift_gear(1)
        elif self.should_shift_down():
            self.shift_gear(-1)
        
    def calculate_engine_torque(self) -> float:
        """Calculate engine torque based on RPM and throttle, multiplied by gear ratio."""
        if self.engine_rpm < IDLE_RPM:
            return 0.0
            
        # Torque curve: peaks at low-mid RPM, drops at high RPM
        rpm_factor = 1.0 - ((self.engine_rpm - OPTIMAL_RPM) / MAX_RPM) ** 2
        rpm_factor = max(0.3, rpm_factor)  # Minimum torque factor
        
        # Base engine torque
        base_torque = ENGINE_TORQUE_MAX * rpm_factor * self.throttle
        
        # Apply gear ratio (higher ratio = more torque multiplication)
        gear_ratio = abs(self.get_current_gear_ratio())  # Use absolute value
        final_torque = base_torque * gear_ratio
        
        return final_torque
    
    def calculate_engine_power(self) -> float:
        """Calculate engine power based on RPM, torque, and gear ratio."""
        torque = self.calculate_engine_torque()
        
        # Power = Torque × RPM (simplified)
        power_factor = min(1.0, self.engine_rpm / OPTIMAL_RPM)
        base_power = (torque * power_factor * self.engine_rpm) / 1000  # Scaled for gameplay
        
        # Gear affects power delivery efficiency
        gear_ratio = self.get_current_gear_ratio()
        if gear_ratio != 0:
            # Higher gears are more efficient at high speeds, lower gears at low speeds
            efficiency = 0.8 + 0.2 / abs(gear_ratio)  # Higher efficiency for higher gears
            return base_power * efficiency
        
        return 0.0
    
    def update_engine_rpm(self):
        """Update engine RPM based on throttle and current speed."""
        # Base RPM calculation from wheel speed
        speed_rpm = IDLE_RPM + abs(self.velocity) * 200  # Scale factor for gameplay
        
        # Throttle affects RPM
        target_rpm = speed_rpm + (self.throttle * (MAX_RPM - speed_rpm))
        
        # Smooth RPM changes
        rpm_change_rate = 100  # How quickly RPM changes
        if target_rpm > self.engine_rpm:
            self.engine_rpm = min(target_rpm, self.engine_rpm + rpm_change_rate)
        else:
            self.engine_rpm = max(target_rpm, self.engine_rpm - rpm_change_rate * 2)
        
        # Clamp RPM
        self.engine_rpm = max(IDLE_RPM, min(MAX_RPM, self.engine_rpm))
    
    def calculate_traction_factor(self) -> float:
        """Calculate traction based on speed (simulates tire grip loss at high speeds)."""
        if abs(self.velocity) < TRACTION_LOSS_SPEED:
            return 1.0
        
        speed_excess = abs(self.velocity) - TRACTION_LOSS_SPEED
        traction_loss = speed_excess * 0.1
        return max(0.3, 1.0 - traction_loss)  # Minimum 30% traction
    
    def update_physics(self):
        """Update car physics for realistic movement with proper gearing."""
        # Update transmission first
        self.update_transmission()
        
        # Calculate forces with gear-adjusted power
        engine_force = self.calculate_engine_power() * 0.03  # Further reduced from 0.05 for slower acceleration
        
        # Handle reverse gear
        gear_ratio = self.get_current_gear_ratio()
        if gear_ratio < 0:  # Reverse gear
            engine_force = -engine_force * 0.7  # Reduced power in reverse
        
        # Speed-dependent power reduction (realistic aerodynamic drag effect)
        speed_drag_factor = 1.0 - (abs(self.velocity) / MAX_SPEED) * 0.4
        engine_force *= max(0.3, speed_drag_factor)  # Minimum 30% power at top speed
        
        # Gear-specific top speed limitation
        if abs(self.velocity) > 0:
            gear_max_speed = MAX_SPEED / max(1.0, abs(gear_ratio) * 0.8)  # Higher gears allow higher speeds
            if abs(self.velocity) > gear_max_speed:
                engine_force *= 0.1  # Severely limit power beyond gear's optimal range
        
        # Braking force
        brake_force = self.brake * BRAKE_FORCE
        if self.velocity > 0:
            brake_force = -brake_force
        elif self.velocity < 0:
            brake_force = abs(brake_force)
        
        # Natural friction/drag
        friction_force = -self.velocity * DECELERATION * FRICTION_COEFFICIENT
        
        # Engine braking (more prominent in lower gears when not accelerating)
        engine_brake_force = 0
        if self.throttle <= 0 and abs(self.velocity) > 0.1 and self.current_gear > 0:
            # Engine braking is stronger in lower gears
            gear_brake_factor = (6 - self.current_gear) / 5.0  # Ranges from 0.2 (5th gear) to 1.0 (1st gear)
            engine_brake_strength = 0.8 * gear_brake_factor
            engine_brake_force = -self.velocity * engine_brake_strength
        
        # Total acceleration
        traction = self.calculate_traction_factor()
        net_force = (engine_force + brake_force) * traction + friction_force + engine_brake_force
        self.acceleration = net_force * ACCELERATION  # Apply base acceleration multiplier
        
        # Update velocity
        self.velocity += self.acceleration
        
        # Clamp velocity to realistic limits
        self.velocity = max(MIN_SPEED, min(MAX_SPEED, self.velocity))
        
        # Speed-dependent steering
        speed_factor = 1.0 - min(0.7, abs(self.velocity) / MAX_SPEED * TURN_SPEED_FACTOR)
        turn_rate = TURN_SPEED_BASE * speed_factor * traction
        
        # Apply steering
        if abs(self.velocity) > 0.05:  # Lower threshold for steering (was 0.1)
            # Enhanced steering responsiveness at low speeds
            speed_multiplier = max(0.5, abs(self.velocity) / MAX_SPEED + 0.5)
            self.angular_velocity = self.steering * turn_rate * speed_multiplier
        else:
            self.angular_velocity = 0
        
        # Update angle
        self.angle += self.angular_velocity
        
        # Update position based on velocity and angle
        if abs(self.velocity) > 0.01:  # Minimum velocity threshold
            self.x += self.velocity * math.sin(math.radians(self.angle))
            self.y -= self.velocity * math.cos(math.radians(self.angle))
        
        # Update collision rectangle
        self.rect.topleft = (self.x, self.y)
    
    def update_position(self, keys: pygame.key.ScancodeWrapper) -> bool:
        """Update car position based on key input with realistic progressive physics."""
        # Calculate delta time (assuming 60 FPS)
        dt = 1.0 / 60.0
        
        # Reset target input states
        self.target_throttle = 0.0
        self.target_brake = 0.0
        self.steering = 0.0
        moving_forward = False
        
        # Throttle input (progressive) - Arrow keys and WASD
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.set_throttle_input(1.0)
            moving_forward = True
        else:
            self.set_throttle_input(0.0)
            
        # Brake/Reverse input (progressive) - Arrow keys and WASD
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            if self.velocity > 0.5:
                # Braking while moving forward
                self.set_brake_input(1.0)
                self.set_throttle_input(0.0)  # Can't throttle while braking
            else:
                # Reverse throttle - set negative target throttle for reverse
                self.target_throttle = -1.8  # Increased from -0.7 for faster reverse
                self.set_brake_input(0.0)
        else:
            self.set_brake_input(0.0)
            
        # Steering input (still immediate for responsiveness) - Arrow keys and WASD
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.steering = -1.0
            
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.steering = 1.0
        
        # Update progressive inputs
        self.update_progressive_inputs(dt)
        
        # Update engine RPM
        self.update_engine_rpm()
        
        # Update physics
        self.update_physics()
        
        return moving_forward or abs(self.velocity) > 0.5
    
    def handle_collision(self):
        """Handle collision with walls by reducing velocity and bouncing back."""
        # Reduce velocity significantly on collision
        self.velocity *= 0.3
        
        # Bounce back slightly
        bounce_distance = 2.0
        self.x -= bounce_distance * math.sin(math.radians(self.angle))
        self.y += bounce_distance * math.cos(math.radians(self.angle))
        self.rect.topleft = (self.x, self.y)
    
    def handle_screen_boundaries(self) -> bool:
        """Handle collision with screen boundaries. Returns True if collision occurred."""
        collision_occurred = False
        
        # Left boundary
        if self.x < 0:
            self.x = 0
            self.velocity *= 0.5  # Reduce speed on boundary hit
            collision_occurred = True
        
        # Right boundary (account for car width)
        if self.x + CAR_WIDTH > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - CAR_WIDTH
            self.velocity *= 0.5
            collision_occurred = True
        
        # Top boundary
        if self.y < 0:
            self.y = 0
            self.velocity *= 0.5
            collision_occurred = True
        
        # Bottom boundary (account for car height)
        if self.y + CAR_HEIGHT > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - CAR_HEIGHT
            self.velocity *= 0.5
            collision_occurred = True
        
        # Update collision rectangle if boundary collision occurred
        if collision_occurred:
            self.rect.topleft = (self.x, self.y)
        
        return collision_occurred
    
    def get_speed_kmh(self) -> float:
        """Get current speed in km/h for display purposes."""
        return abs(self.velocity) * 15  # Scale factor for realistic-feeling speeds
    
    def get_gear(self) -> int:
        """Get current gear (returns the actual transmission gear)."""
        return self.current_gear
    
    def draw(self, screen: pygame.Surface, car_image: pygame.Surface):
        """Draw the car on the screen with proper rotation."""
        rotated_car = pygame.transform.rotate(car_image, -self.angle)
        rotated_rect = rotated_car.get_rect(center=self.rect.center)
        screen.blit(rotated_car, rotated_rect.topleft)


class Track:
    """Represents the racing track with walls, checkpoints, and start/finish line."""
    
    def __init__(self):
        """Initialize track elements."""
        self.walls = [
            pygame.Rect(200, 150, 400, 10),  # Top wall
            pygame.Rect(200, 440, 400, 10),  # Bottom wall
            pygame.Rect(200, 150, 10, 300),  # Left wall
            pygame.Rect(590, 150, 10, 300)   # Right wall
        ]
        
        self.start_line = pygame.Rect(0, 400, 200, 10)
        
        self.checkpoints = [
            pygame.Rect(SCREEN_WIDTH // 2, 0, 10, 150),      # Top checkpoint
            pygame.Rect(SCREEN_WIDTH - 200, SCREEN_HEIGHT // 2, 200, 10),  # Right checkpoint
            pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150, 10, 150)   # Bottom checkpoint
        ]
    
    def check_wall_collision(self, car: Car) -> bool:
        """Check if car collides with any wall."""
        for wall in self.walls:
            if car.rect.colliderect(wall):
                return True
        return False
    
    def handle_wall_collisions(self, car: Car) -> bool:
        """Handle wall collisions with proper positioning and velocity reduction. Returns True if collision occurred."""
        collision_occurred = False
        
        for wall in self.walls:
            if car.rect.colliderect(wall):
                collision_occurred = True
                
                # Determine which side of the wall was hit and reposition accordingly
                car_center_x = car.x + CAR_WIDTH // 2
                car_center_y = car.y + CAR_HEIGHT // 2
                wall_center_x = wall.x + wall.width // 2
                wall_center_y = wall.y + wall.height // 2
                
                # Calculate overlap distances
                overlap_x = min(car.x + CAR_WIDTH - wall.x, wall.x + wall.width - car.x)
                overlap_y = min(car.y + CAR_HEIGHT - wall.y, wall.y + wall.height - car.y)
                
                # Resolve collision by moving car to the side with smaller overlap
                if overlap_x < overlap_y:
                    # Horizontal collision - move car left or right
                    if car_center_x < wall_center_x:
                        # Car is to the left of wall, push it left
                        car.x = wall.x - CAR_WIDTH
                    else:
                        # Car is to the right of wall, push it right
                        car.x = wall.x + wall.width
                else:
                    # Vertical collision - move car up or down
                    if car_center_y < wall_center_y:
                        # Car is above wall, push it up
                        car.y = wall.y - CAR_HEIGHT
                    else:
                        # Car is below wall, push it down
                        car.y = wall.y + wall.height
                
                # Reduce velocity on collision (same as screen boundaries)
                car.velocity *= 0.5
                
                # Update collision rectangle
                car.rect.topleft = (car.x, car.y)
                
                # Only handle one collision per frame for stability
                break
        
        return collision_occurred
    
    def check_checkpoint_collision(self, car: Car, checkpoints_crossed: List[bool]) -> List[bool]:
        """Check and update checkpoint crossings."""
        for i, checkpoint in enumerate(self.checkpoints):
            if car.rect.colliderect(checkpoint) and not checkpoints_crossed[i]:
                checkpoints_crossed[i] = True
        return checkpoints_crossed
    
    def check_start_line_collision(self, car: Car) -> bool:
        """Check if car crosses start/finish line."""
        return car.rect.colliderect(self.start_line)
    
    def draw(self, screen: pygame.Surface):
        """Draw all track elements."""
        # Draw walls
        for wall in self.walls:
            pygame.draw.rect(screen, WHITE, wall)
        
        # Draw start/finish line
        pygame.draw.rect(screen, GREEN, self.start_line)
        
        # Draw checkpoints
        for checkpoint in self.checkpoints:
            pygame.draw.rect(screen, WHITE, checkpoint)


class LapTimer:
    """Manages lap timing and lap counting."""
    
    def __init__(self):
        """Initialize timer variables."""
        self.start_time: Optional[float] = None
        self.best_time = float('inf')
        self.last_lap_time: Optional[float] = None
        self.lap_count = 1
        self.lap_completed = False
    
    def reset(self):
        """Reset timer to initial state."""
        self.start_time = None
        self.best_time = float('inf')
        self.last_lap_time = None
        self.lap_count = 1
        self.lap_completed = False
    
    def start_timing(self):
        """Start the lap timer."""
        if self.start_time is None:
            self.start_time = time.time()
    
    def complete_lap(self, checkpoints_crossed: List[bool]) -> bool:
        """Complete a lap if all checkpoints were crossed. Returns True if lap was valid."""
        if not all(checkpoints_crossed) or self.start_time is None:
            return False
        
        elapsed_time = time.time() - self.start_time
        self.last_lap_time = elapsed_time
        
        if elapsed_time < self.best_time:
            self.best_time = elapsed_time
        
        self.lap_count += 1
        self.start_time = time.time()
        return True
    
    def get_current_time(self) -> float:
        """Get current lap time, clamped to maximum of 60 seconds."""
        if self.start_time is None:
            return 0.0
        current_time = time.time() - self.start_time
        return min(current_time, 60.0)  # Clamp to maximum 60 seconds


class GameUI:
    """Handles user interface rendering with enhanced styled rectangles."""
    
    def __init__(self):
        """Initialize UI components."""
        self.font = pygame.font.Font('assets/fonts/SmoochSans-Bold.ttf', FONT_SIZE)
        self.small_font = pygame.font.Font('assets/fonts/SmoochSans-Bold.ttf', 18)
        
        # UI styling constants
        self.box_padding = 12
        self.box_margin = 8
        self.border_width = 2
        self.border_radius = 8
        
        # Colors with transparency
        self.box_bg_color = (0, 0, 0, 180)  # Semi-transparent black
        self.border_color = WHITE
    
    def format_time(self, seconds: float) -> str:
        """Format time in M:SS.ss format without leading zeros for minutes, or as seconds if at maximum."""
        if seconds == float('inf'):
            return "--:--"
        
        # If at maximum time (60 seconds), show as seconds format
        if seconds >= 60.0:
            return f"{seconds:.2f}s"
        
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        
        if minutes > 0:
            return f"{minutes}:{remaining_seconds:05.2f}"
        else:
            return f"{remaining_seconds:.2f}s"
    
    def draw_rounded_rect_with_border(self, surface: pygame.Surface, rect: pygame.Rect, 
                                    bg_color: tuple, border_color: tuple, border_width: int, border_radius: int):
        """Draw a rounded rectangle with border and semi-transparent background."""
        # Create a temporary surface for the rounded rectangle with transparency
        temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Draw the background rectangle
        pygame.draw.rect(temp_surface, bg_color, (0, 0, rect.width, rect.height), border_radius=border_radius)
        
        # Draw the border
        pygame.draw.rect(temp_surface, border_color, (0, 0, rect.width, rect.height), 
                        width=border_width, border_radius=border_radius)
        
        # Blit to main surface
        surface.blit(temp_surface, rect.topleft)
    
    def draw_timer_info(self, screen: pygame.Surface, timer: LapTimer):
        """Draw timing information with styled rounded rectangle background."""
        if timer.start_time is not None:
            current_time = timer.get_current_time()
            current_display = self.format_time(current_time)
            best_display = self.format_time(timer.best_time) if timer.best_time != float('inf') else "--:--"
            last_display = self.format_time(timer.last_lap_time) if timer.last_lap_time is not None else "--:--"
            
            # Render text
            time_text = self.font.render(f"Time: {current_display}", True, WHITE)
            best_text = self.font.render(f"Best: {best_display}", True, WHITE)
            last_text = self.font.render(f"Last: {last_display}", True, WHITE)
            
            # Use fixed width to prevent wobbling (wide enough for longest possible time format)
            fixed_width = 200  # Fixed width that accommodates "Time: 60.00s" and similar
            total_height = time_text.get_height() * 3 + self.box_margin * 2
            
            # Create rectangle for background with fixed width
            rect_width = fixed_width + self.box_padding * 2
            rect_height = total_height + self.box_padding * 2
            timer_rect = pygame.Rect(UI_MARGIN, UI_MARGIN, rect_width, rect_height)
            
            # Draw styled background
            self.draw_rounded_rect_with_border(screen, timer_rect, self.box_bg_color, 
                                             self.border_color, self.border_width, self.border_radius)
            
            # Draw text inside the rectangle
            text_x = UI_MARGIN + self.box_padding
            text_y = UI_MARGIN + self.box_padding
            
            screen.blit(time_text, (text_x, text_y))
            screen.blit(best_text, (text_x, text_y + time_text.get_height() + self.box_margin))
            screen.blit(last_text, (text_x, text_y + (time_text.get_height() + self.box_margin) * 2))
    
    def draw_lap_counter(self, screen: pygame.Surface, timer: LapTimer):
        """Draw lap counter with styled rounded rectangle background."""
        lap_text = self.font.render(f"Lap: {timer.lap_count}", True, WHITE)
        
        # Calculate rectangle size
        rect_width = lap_text.get_width() + self.box_padding * 2
        rect_height = lap_text.get_height() + self.box_padding * 2
        
        # Position on the right side
        rect_x = SCREEN_WIDTH - rect_width - UI_MARGIN
        lap_rect = pygame.Rect(rect_x, UI_MARGIN, rect_width, rect_height)
        
        # Draw styled background
        self.draw_rounded_rect_with_border(screen, lap_rect, self.box_bg_color, 
                                         self.border_color, self.border_width, self.border_radius)
        
        # Draw text inside the rectangle
        text_x = rect_x + self.box_padding
        text_y = UI_MARGIN + self.box_padding
        screen.blit(lap_text, (text_x, text_y))
    
    def draw_car_info(self, screen: pygame.Surface, car: Car):
        """Draw car information on the right side."""
        # Throttle/Brake indicators removed for cleaner UI
        pass
    
    def draw_controls_help(self, screen: pygame.Surface):
        """Draw control instructions at the bottom of the screen."""
        controls_text = self.small_font.render("Press R to Reset", True, WHITE)
        text_rect = controls_text.get_rect()
        screen.blit(controls_text, (SCREEN_WIDTH // 2 - text_rect.width // 2, SCREEN_HEIGHT - 30))


class AudioManager:
    """Manages game audio with realistic engine sound based on RPM with pitch shifting."""
    
    def __init__(self, assets: GameAssets):
        """Initialize audio manager with game assets."""
        self.assets = assets
        self.engine_playing = False
        self.current_pitch = 1.0
        self.engine_channel = None
        
        # RPM to pitch mapping constants
        self.base_rpm = IDLE_RPM      # RPM that corresponds to original pitch
        self.min_pitch = 0.6          # Minimum pitch multiplier (low RPM)
        self.max_pitch = 2.0          # Maximum pitch multiplier (high RPM)
    
    def calculate_pitch_from_speed(self, velocity: float) -> float:
        """Calculate pitch multiplier based on car speed for smoother audio."""
        # Normalize velocity to 0-1 range based on max speed
        speed_normalized = abs(velocity) / MAX_SPEED
        speed_normalized = max(0.0, min(1.0, speed_normalized))
        
        # Calculate pitch using smooth curve for natural sound progression
        pitch = self.min_pitch + (self.max_pitch - self.min_pitch) * (speed_normalized ** 0.5)
        return max(0.7, min(2.5, pitch))  # Clamp to reasonable bounds
    
    def create_pitched_sound(self, original_sound: pygame.mixer.Sound, pitch: float) -> pygame.mixer.Sound:
        """Create a new sound with modified pitch (simplified approach)."""
        # Note: This is a simplified pitch shifting approach
        # For production games, you'd want to use more sophisticated audio libraries
        
        # Get the raw sound data
        try:
            # Convert sound to array for manipulation
            sound_array = pygame.sndarray.array(original_sound)
            
            # Simple pitch shifting by resampling (basic approach)
            if pitch != 1.0:
                # Calculate new length based on pitch
                new_length = int(len(sound_array) / pitch)
                if new_length > 0:
                    # Resample the audio (basic linear interpolation)
                    import numpy as np
                    indices = np.linspace(0, len(sound_array) - 1, new_length)
                    
                    # Handle both mono and stereo
                    if len(sound_array.shape) == 1:  # Mono
                        resampled = np.interp(indices, np.arange(len(sound_array)), sound_array)
                    else:  # Stereo
                        resampled = np.zeros((new_length, sound_array.shape[1]))
                        for channel in range(sound_array.shape[1]):
                            resampled[:, channel] = np.interp(indices, np.arange(len(sound_array)), sound_array[:, channel])
                    
                    # Convert back to sound
                    resampled = resampled.astype(sound_array.dtype)
                    return pygame.sndarray.make_sound(resampled)
        except (ImportError, Exception):
            # Fallback: return original sound if numpy not available or error occurs
            pass
        
        return original_sound
    
    def reset(self):
        """Reset audio state."""
        if self.engine_playing and self.engine_channel:
            self.engine_channel.stop()
            self.engine_playing = False
        self.current_pitch = 1.0
        self.engine_channel = None
    
    def update_engine_sound(self, car: Car):
        """Update engine sound based on car's speed with pitch shifting. Engine always rumbles at idle."""
        # Engine is always active - always rumbling
        
        # Calculate target pitch based on speed, with minimum idle pitch
        base_pitch = self.calculate_pitch_from_speed(car.velocity)
        idle_pitch = 0.8  # Minimum pitch for idle rumble
        target_pitch = max(idle_pitch, base_pitch)
        
        # Start engine sound if not already playing
        if not self.engine_playing or not (self.engine_channel and self.engine_channel.get_busy()):
            try:
                pitched_sound = self.create_pitched_sound(self.assets.original_engine_sound, target_pitch)
                self.engine_channel = pitched_sound.play(-1)  # Loop
            except:
                # Fallback: use original sound
                self.engine_channel = self.assets.engine_sound.play(-1)
            
            self.engine_playing = True
            self.current_pitch = target_pitch
        
        # Only update pitch if it changed significantly (to avoid constant recreating)
        elif abs(target_pitch - self.current_pitch) > 0.05:
            self.current_pitch = target_pitch
            
            # Stop current sound
            if self.engine_channel and self.engine_channel.get_busy():
                self.engine_channel.stop()
            
            # Create new pitched sound
            try:
                pitched_sound = self.create_pitched_sound(self.assets.original_engine_sound, self.current_pitch)
                self.engine_channel = pitched_sound.play(-1)  # Loop
            except:
                # Fallback: use original sound
                self.engine_channel = self.assets.engine_sound.play(-1)
        
        # Adjust volume - always has minimum idle volume
        if self.engine_channel and self.engine_channel.get_busy():
            speed_factor = abs(car.velocity) / MAX_SPEED
            throttle_factor = max(0.2, car.throttle + 0.2)  # Base idle volume
            
            # Calculate volume with minimum idle level
            idle_volume = 0.25  # Minimum idle rumble volume
            active_volume = 0.4 + (speed_factor * 0.4) * throttle_factor
            volume = max(idle_volume, active_volume)
            volume = min(0.8, volume)  # Cap maximum volume
            
            self.engine_channel.set_volume(volume)
    
    def play_collision_sound(self):
        """Play collision sound effect."""
        self.assets.collision_sound.play()


class Game:
    """Main game class that orchestrates all components."""
    
    def __init__(self):
        """Initialize the game."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Hot LapY")
        self.clock = pygame.time.Clock()
        
        # Initialize game components
        self.assets = GameAssets()
        self.car = Car(50, 280)  # Start position
        self.track = Track()
        self.timer = LapTimer()
        self.ui = GameUI()
        self.audio = AudioManager(self.assets)
        
        # Game state
        self.running = True
        self.checkpoints_crossed = [False, False, False]
    
    def reset_game(self):
        """Reset the entire game to initial state."""
        # Reset car
        self.car.reset_to_initial_state()
        
        # Reset timer
        self.timer.reset()
        
        # Reset checkpoints
        self.checkpoints_crossed = [False, False, False]
        
        # Reset audio
        self.audio.reset()
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
    def update_game_logic(self):
        """Update game logic for one frame."""
        keys = pygame.key.get_pressed()
        
        # Check for reset key
        if keys[pygame.K_r]:
            self.reset_game()
            return  # Skip other updates this frame
        
        # Update car movement with realistic physics
        engine_active = self.car.update_position(keys)
        
        # Start timer on first movement
        if engine_active and abs(self.car.velocity) > 0.1:
            self.timer.start_timing()
        
        # Handle wall collisions with improved positioning
        wall_collision = self.track.handle_wall_collisions(self.car)
        boundary_collision = self.car.handle_screen_boundaries()
        
        if wall_collision or boundary_collision:
            # Play collision sound for both wall and boundary hits
            self.audio.play_collision_sound()
        
        # Update engine sound based on car state
        self.audio.update_engine_sound(self.car)
        
        # Check checkpoint crossings
        self.checkpoints_crossed = self.track.check_checkpoint_collision(
            self.car, self.checkpoints_crossed
        )
        
        # Handle start/finish line crossing
        if self.track.check_start_line_collision(self.car) and self.timer.start_time is not None:
            if not self.timer.lap_completed:
                self.timer.lap_completed = True
            else:
                if self.timer.complete_lap(self.checkpoints_crossed):
                    self.checkpoints_crossed = [False, False, False]
                self.timer.lap_completed = False
    
    def render(self):
        """Render the game for one frame."""
        self.screen.fill(BLACK)
        
        # Draw track background
        self.screen.blit(self.assets.track_image, (0, 0))
        
        # Draw track elements
        self.track.draw(self.screen)
        
        # Draw car
        self.car.draw(self.screen, self.assets.car_image)
        
        # Draw UI
        self.ui.draw_timer_info(self.screen, self.timer)
        self.ui.draw_lap_counter(self.screen, self.timer)
        self.ui.draw_car_info(self.screen, self.car)
        self.ui.draw_controls_help(self.screen)
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update_game_logic()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()


def main():
    """Main function to start the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()