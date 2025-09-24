import pygame;
import time;
import math;

pygame.init()



WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hot Lap")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Load images
track_image = pygame.image.load('assets/track.png')
car_image = pygame.image.load('assets/car.png')
car_rect = car_image.get_rect(center=(WIDTH // 2, HEIGHT - 100))  # Start position, using center for rotation
car_x, car_y = car_rect.center  # Update initial positions

# Initialize mixer and load sounds
pygame.mixer.init()
engine_sound = pygame.mixer.Sound('assets/car.wav')
collision_sound = pygame.mixer.Sound('assets/collision.wav')

# Car properties
car_width, car_height = 35, 70  # Made smaller: was 53x102, now 35x70
car_x = 50  # Start slightly to the right of the start line
car_y = 320  # Start slightly below the start line center
car_speed = 5
car_angle = 0  # Facing up initially (0 degrees)

# We'll use a rect for collision and drawing
car_rect = pygame.Rect(car_x, car_y, car_width, car_height)

# Track boundaries (simple oval-like track using rects for walls)
track_walls = [
    pygame.Rect(200, 150, 400, 10),  # Top wall - smaller track area
    pygame.Rect(200, 440, 400, 10),  # Bottom wall - smaller track area
    pygame.Rect(200, 150, 10, 300),  # Left wall - smaller track area
    pygame.Rect(590, 150, 10, 300)   # Right wall - smaller track area
]

# Start/Finish line (vertical line on the left-center)
start_line = pygame.Rect(0, 250, 100, 10)  # Left-center position, shorter line

# Timer variables
start_time = None
elapsed_time = 0
best_time = float('inf')  # Initially infinite

# Game state
running = True
clock = pygame.time.Clock()
lap_completed = False

while running:
    screen.fill(BLACK)  # Clear screen

    # Draw track background
    screen.blit(track_image, (0, 0))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get keys pressed
    keys = pygame.key.get_pressed()

    # Movement controls
    moving_forward = False
    if keys[pygame.K_UP]:
        if start_time is None:
            start_time = time.time()  # Start timer on first move
        car_x += car_speed * math.sin(math.radians(car_angle))
        car_y -= car_speed * math.cos(math.radians(car_angle))
        moving_forward = True
    if keys[pygame.K_DOWN]:
        car_x -= car_speed * math.sin(math.radians(car_angle)) / 2  # Slower reverse
        car_y += car_speed * math.cos(math.radians(car_angle)) / 2
    if keys[pygame.K_LEFT]:
        car_angle -= 3  # Turn left
    if keys[pygame.K_RIGHT]:
        car_angle += 3  # Turn right

    # Update car rect position
    car_rect.topleft = (car_x, car_y)

    # Collision with walls
    collided = False
    # Collision with walls
    for wall in track_walls:
        if car_rect.colliderect(wall):
            # Simple bounce back
            car_x -= car_speed * math.sin(math.radians(car_angle))
            car_y += car_speed * math.cos(math.radians(car_angle))
            collided = True

    if collided:
        collision_sound.play()

    # Sound for engine
    if moving_forward:
        if engine_sound.get_num_channels() == 0:  # Play only if not already playing
            engine_sound.play(-1)  # Loop
    else:
        engine_sound.stop()

    # Check if crossed start/finish line
    if car_rect.colliderect(start_line) and start_time is not None:
        if not lap_completed:
            # First cross is start, ignore
            lap_completed = True
        else:
            # Completed a lap
            elapsed_time = time.time() - start_time
            if elapsed_time < best_time:
                best_time = elapsed_time
            start_time = time.time()  # Reset for next lap
            lap_completed = False  # Reset flag

    # Draw track walls
    for wall in track_walls:
        pygame.draw.rect(screen, WHITE, wall)

    # Draw start/finish line
    pygame.draw.rect(screen, GREEN, start_line)

    # Draw car (rotated)
    rotated_car = pygame.transform.rotate(car_image, -car_angle)  # Negative angle for correct visual
    rotated_rect = rotated_car.get_rect(center=car_rect.center)
    screen.blit(rotated_car, rotated_rect.topleft)

    # Display timer
    if start_time is not None:
        current_time = time.time() - start_time
        font = pygame.font.Font(None, 36)
        time_text = font.render(f"Time: {current_time:.2f}s", True, WHITE)
        best_display = f"{best_time:.2f}s" if best_time != float('inf') else "--"
        best_text = font.render(f"Best: {best_display}", True, WHITE)
        screen.blit(time_text, (10, 10))
        screen.blit(best_text, (10, 50))

    # Update display and limit FPS
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()