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
ACCELERATION = 0.08          # Acceleration rate (reduced from 0.15 for slower buildup)
DECELERATION = 0.2           # Natural deceleration (friction)
BRAKE_FORCE = 0.5            # Braking force
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

# UI settings
FONT_SIZE = 36
UI_MARGIN = 10
UI_LINE_HEIGHT = 40


class GameAssets:
    """Handles loading and managing game assets."""
    
    def __init__(self):
        """Initialize and load all game assets."""
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)  # Higher quality for pitch shifting
        
        # Load images
        self.track_image = pygame.image.load('assets/track.png')
        self.car_image = pygame.image.load('assets/car.png')
        
        # Load sounds
        self.engine_sound = pygame.mixer.Sound('assets/car.wav')
        self.collision_sound = pygame.mixer.Sound('assets/collision.wav')
        
        # Store original engine sound data for pitch shifting
        self.original_engine_sound = pygame.mixer.Sound('assets/car.wav')


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
        self.throttle = 0.0         # 0.0 to 1.0
        self.brake = 0.0            # 0.0 to 1.0
        self.steering = 0.0         # -1.0 to 1.0 (left to right)
        
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
        self.rect.topleft = (self.x, self.y)
        
    def calculate_engine_torque(self) -> float:
        """Calculate engine torque based on RPM and throttle."""
        if self.engine_rpm < IDLE_RPM:
            return 0.0
            
        # Torque curve: peaks at low-mid RPM, drops at high RPM
        rpm_factor = 1.0 - ((self.engine_rpm - OPTIMAL_RPM) / MAX_RPM) ** 2
        rpm_factor = max(0.3, rpm_factor)  # Minimum torque factor
        
        return ENGINE_TORQUE_MAX * rpm_factor * self.throttle
    
    def calculate_engine_power(self) -> float:
        """Calculate engine power based on RPM and torque."""
        torque = self.calculate_engine_torque()
        # Power = Torque × RPM / 5252 (converted to relative units)
        power_factor = min(1.0, self.engine_rpm / OPTIMAL_RPM)
        return (torque * power_factor * self.engine_rpm) / 1000  # Scaled for gameplay
    
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
        """Update car physics for realistic movement."""
        # Calculate forces
        engine_force = self.calculate_engine_power() * 0.05  # Reduced from 0.1 for slower acceleration
        
        # Speed-dependent power reduction (realistic aerodynamic drag effect)
        speed_drag_factor = 1.0 - (abs(self.velocity) / MAX_SPEED) * 0.3
        engine_force *= max(0.4, speed_drag_factor)  # Minimum 40% power at top speed
        
        # Braking force
        brake_force = self.brake * BRAKE_FORCE
        if self.velocity > 0:
            brake_force = -brake_force
        elif self.velocity < 0:
            brake_force = abs(brake_force)
        
        # Natural friction/drag
        friction_force = -self.velocity * DECELERATION * FRICTION_COEFFICIENT
        
        # Total acceleration
        traction = self.calculate_traction_factor()
        net_force = (engine_force + brake_force) * traction + friction_force
        self.acceleration = net_force
        
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
        """Update car position based on key input with realistic physics."""
        # Reset input states
        self.throttle = 0.0
        self.brake = 0.0
        self.steering = 0.0
        moving_forward = False
        
        # Throttle input
        if keys[pygame.K_UP]:
            self.throttle = 1.0
            moving_forward = True
            
        # Brake/Reverse input
        if keys[pygame.K_DOWN]:
            if self.velocity > 0.5:
                # Braking while moving forward
                self.brake = 1.0
            else:
                # Reverse throttle
                self.throttle = -0.7  # Reduced reverse power
            
        # Steering input
        if keys[pygame.K_LEFT]:
            self.steering = -1.0
            
        if keys[pygame.K_RIGHT]:
            self.steering = 1.0
        
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
        """Get current gear based on speed (for display)."""
        speed = abs(self.velocity)
        if speed < 0.5:
            return 0  # Neutral/Park
        elif speed < 2.0:
            return 1
        elif speed < 4.0:
            return 2
        elif speed < 6.0:
            return 3
        else:
            return 4
    
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
        """Get current lap time."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time


class GameUI:
    """Handles user interface rendering with enhanced car information."""
    
    def __init__(self):
        """Initialize UI components."""
        self.font = pygame.font.Font(None, FONT_SIZE)
        self.small_font = pygame.font.Font(None, 24)
    
    def draw_timer_info(self, screen: pygame.Surface, timer: LapTimer):
        """Draw timing information on the left side."""
        if timer.start_time is not None:
            current_time = timer.get_current_time()
            time_text = self.font.render(f"Time: {current_time:.2f}s", True, WHITE)
            
            best_display = f"{timer.best_time:.2f}s" if timer.best_time != float('inf') else "--"
            best_text = self.font.render(f"Best: {best_display}", True, WHITE)
            
            last_display = f"{timer.last_lap_time:.2f}s" if timer.last_lap_time is not None else "--"
            last_text = self.font.render(f"Last: {last_display}", True, WHITE)
            
            screen.blit(time_text, (UI_MARGIN, UI_MARGIN))
            screen.blit(best_text, (UI_MARGIN, UI_MARGIN + UI_LINE_HEIGHT))
            screen.blit(last_text, (UI_MARGIN, UI_MARGIN + UI_LINE_HEIGHT * 2))
    
    def draw_lap_counter(self, screen: pygame.Surface, timer: LapTimer):
        """Draw lap counter on the right side."""
        lap_text = self.font.render(f"Lap: {timer.lap_count}", True, WHITE)
        screen.blit(lap_text, (SCREEN_WIDTH - 150, UI_MARGIN))
    
    def draw_car_info(self, screen: pygame.Surface, car: Car):
        """Draw car information (speed, RPM, gear) on the right side."""
        speed_kmh = car.get_speed_kmh()
        gear = car.get_gear()
        rpm = int(car.engine_rpm)
        
        # Speed display
        speed_text = self.font.render(f"{speed_kmh:.0f} km/h", True, WHITE)
        screen.blit(speed_text, (SCREEN_WIDTH - 150, UI_MARGIN + UI_LINE_HEIGHT))
        
        # Gear display
        gear_display = "N" if gear == 0 else f"Gear {gear}"
        if car.velocity < -0.1:
            gear_display = "R"
        gear_text = self.small_font.render(gear_display, True, WHITE)
        screen.blit(gear_text, (SCREEN_WIDTH - 150, UI_MARGIN + UI_LINE_HEIGHT * 2))
        
        # RPM display
        rpm_text = self.small_font.render(f"RPM: {rpm}", True, WHITE)
        screen.blit(rpm_text, (SCREEN_WIDTH - 150, UI_MARGIN + UI_LINE_HEIGHT * 2 + 25))
        
        # Throttle/Brake indicators
        if car.throttle > 0:
            throttle_text = self.small_font.render(f"Throttle: {car.throttle*100:.0f}%", True, GREEN)
            screen.blit(throttle_text, (SCREEN_WIDTH - 150, UI_MARGIN + UI_LINE_HEIGHT * 3))
        elif car.brake > 0:
            brake_text = self.small_font.render(f"Brake: {car.brake*100:.0f}%", True, RED)
            screen.blit(brake_text, (SCREEN_WIDTH - 150, UI_MARGIN + UI_LINE_HEIGHT * 3))
    
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
    
    def calculate_pitch_from_rpm(self, rpm: float) -> float:
        """Calculate pitch multiplier based on RPM."""
        # Normalize RPM to 0-1 range
        rpm_normalized = (rpm - IDLE_RPM) / (MAX_RPM - IDLE_RPM)
        rpm_normalized = max(0.0, min(1.0, rpm_normalized))
        
        # Calculate pitch using exponential curve for more realistic sound
        pitch = self.min_pitch + (self.max_pitch - self.min_pitch) * (rpm_normalized ** 0.7)
        return pitch
    
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
        """Update engine sound based on car's engine RPM with pitch shifting."""
        engine_active = car.engine_rpm > IDLE_RPM or abs(car.velocity) > 0.1
        
        if engine_active:
            # Calculate target pitch
            target_pitch = self.calculate_pitch_from_rpm(car.engine_rpm)
            
            # Only update if pitch changed significantly (to avoid constant recreating)
            if abs(target_pitch - self.current_pitch) > 0.1:
                self.current_pitch = target_pitch
                
                # Stop current sound
                if self.engine_channel and self.engine_channel.get_busy():
                    self.engine_channel.stop()
                
                # Create pitched sound (fallback to volume control if pitch shifting fails)
                try:
                    pitched_sound = self.create_pitched_sound(self.assets.original_engine_sound, self.current_pitch)
                    self.engine_channel = pitched_sound.play(-1)  # Loop
                except:
                    # Fallback: use original sound with volume modulation
                    self.engine_channel = self.assets.engine_sound.play(-1)
                
                self.engine_playing = True
            
            # Adjust volume based on RPM and throttle
            if self.engine_channel and self.engine_channel.get_busy():
                rpm_factor = (car.engine_rpm - IDLE_RPM) / (MAX_RPM - IDLE_RPM)
                throttle_factor = max(0.3, car.throttle + 0.3)  # Minimum volume even at idle
                volume = 0.2 + (rpm_factor * 0.6) * throttle_factor  # Volume between 0.2 and 0.8
                volume = max(0.2, min(0.8, volume))
                self.engine_channel.set_volume(volume)
        else:
            if self.engine_playing and self.engine_channel:
                self.engine_channel.stop()
                self.engine_playing = False
    
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
        
        # Handle wall collisions
        wall_collision = self.track.check_wall_collision(self.car)
        boundary_collision = self.car.handle_screen_boundaries()
        
        if wall_collision:
            self.car.handle_collision()
            self.audio.play_collision_sound()
        elif boundary_collision:
            # Play collision sound for screen boundary hits too
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