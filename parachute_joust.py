import os
import pygame
import math
import random
import array

# Screen dimensions
WIDTH, HEIGHT = 800, 600
GROUND_Y = HEIGHT - 80

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
BLUE = (50, 100, 220)
GREEN = (50, 200, 50)
BROWN = (139, 69, 19)
SKY = (135, 206, 235)
YELLOW = (255, 255, 0)


def draw_gradient(surf, top_color, bottom_color):
    """Fill *surf* with a vertical gradient from *top_color* to *bottom_color*."""
    height = surf.get_height()
    for y in range(height):
        t = y / height
        color = [int(top_color[i] * (1 - t) + bottom_color[i] * t) for i in range(3)]
        pygame.draw.line(surf, color, (0, y), (surf.get_width(), y))

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Parachute Joust")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
bigfont = pygame.font.SysFont(None, 72)

assets_dir = os.path.join(os.path.dirname(__file__), "assets")
PLAYER_SHEET_PATH = os.path.join(assets_dir, "player.png")


def ensure_player_sheet():
    os.makedirs(assets_dir, exist_ok=True)
    if os.path.exists(PLAYER_SHEET_PATH):
        return
    frame_w, frame_h = 20, 35
    sheet = pygame.Surface((frame_w * 2, frame_h), pygame.SRCALPHA)

    def draw_frame(surf, arms_up):
        pygame.draw.rect(surf, WHITE, (8, 0, 4, 8))  # head
        pygame.draw.rect(surf, WHITE, (5, 8, 10, 15))  # body
        pygame.draw.rect(surf, WHITE, (7, 23, 2, 12))  # left leg
        pygame.draw.rect(surf, WHITE, (11, 23, 2, 12))  # right leg
        if arms_up:
            pygame.draw.rect(surf, WHITE, (3, 0, 2, 10))
            pygame.draw.rect(surf, WHITE, (15, 0, 2, 10))
        else:
            pygame.draw.rect(surf, WHITE, (3, 8, 2, 10))
            pygame.draw.rect(surf, WHITE, (15, 8, 2, 10))

    idle = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
    draw_frame(idle, False)
    sheet.blit(idle, (0, 0))
    flail = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
    draw_frame(flail, True)
    sheet.blit(flail, (frame_w, 0))
    pygame.image.save(sheet, PLAYER_SHEET_PATH)


ensure_player_sheet()


def make_sound(freq, duration=0.3, volume=0.5, waveform='sine'):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n_samples):
        t = i / sample_rate
        if waveform == 'sine':
            val = math.sin(2 * math.pi * freq * t)
        elif waveform == 'square':
            val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        elif waveform == 'noise':
            val = random.uniform(-1, 1)
        else:
            val = 0
        buf.append(int(volume * 32767 * val))
    return pygame.mixer.Sound(buffer=buf)


def make_baa_sound():
    sample_rate = 44100
    duration = 0.6
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n_samples):
        t = i / sample_rate
        freq = 700 if t < duration / 2 else 500
        val = math.sin(2 * math.pi * freq * t)
        buf.append(int(0.6 * 32767 * val))
    return pygame.mixer.Sound(buffer=buf)


# Sounds
plane_sound = make_sound(110, 0.5, 0.4, 'square')
wind_sound = make_sound(0, 1.0, 0.3, 'noise')
blip_sound = make_sound(800, 0.1, 0.4, 'square')
thud_sound = make_sound(0, 0.5, 0.6, 'noise')
sheep_sound = make_baa_sound()


class Player:
    def __init__(self, x, color, controls):
        self.pos = pygame.Vector2(x, 120)
        self.vel = pygame.Vector2(0, 0)
        self.color = color
        self.controls = controls
        self.rect = pygame.Rect(0, 0, 20, 35)
        self.cooldown = 0
        # load generated sprite sheet and prepare animation frames
        sheet = pygame.image.load(PLAYER_SHEET_PATH).convert_alpha()
        frame_w, frame_h = 20, 35
        self.frames = []
        for i in range(sheet.get_width() // frame_w):
            frame = sheet.subsurface(pygame.Rect(i * frame_w, 0, frame_w, frame_h)).copy()
            frame.fill(self.color, special_flags=pygame.BLEND_MULT)
            self.frames.append(frame)
        self.frame_index = 0
        self.anim_time = 0.0

    def update(self, dt, slowed=False):
        keys = pygame.key.get_pressed()
        acc = pygame.Vector2(0, 0)
        # Slow horizontally when near screen edges so players cannot leave view
        left_dist = self.pos.x
        right_dist = WIDTH - self.pos.x
        edge_dist = min(left_dist, right_dist)
        edge_factor = max(0.2, min(1.0, edge_dist / 100))
        speed_x = (0.7 if slowed else 1.0) * edge_factor
        if keys[self.controls['left']]:
            acc.x -= 200 * edge_factor
        if keys[self.controls['right']]:
            acc.x += 200 * edge_factor
        self.vel.x += acc.x * dt
        self.vel.x *= 0.98
        self.pos.x += self.vel.x * dt * speed_x
        self.pos.x = max(10, min(WIDTH - 10, self.pos.x))

        if keys[self.controls['faster']]:
            self.vel.y += 300 * dt
        if keys[self.controls['slower']]:
            self.vel.y -= 300 * dt
        self.vel.y += 500 * dt
        self.pos.y += self.vel.y * dt
        # Keep player within vertical screen bounds
        self.pos.y = max(10, min(HEIGHT - 10, self.pos.y))
        self.rect.topleft = (self.pos.x - 10, self.pos.y - 20)
        if self.cooldown > 0:
            self.cooldown -= dt
        self.anim_time += dt * 10
        self.frame_index = int(self.anim_time) % len(self.frames)

    def draw(self, surf, glow=False, offset_y=0, holding_chute=False):
        frame = self.frames[self.frame_index]
        surf.blit(frame, (self.rect.x, self.rect.y - offset_y))
        if glow:
            pygame.draw.rect(surf, WHITE, self.rect.move(0, -offset_y).inflate(10, 10), 2)


class Parachute:
    def __init__(self, x):
        self.pos = pygame.Vector2(x, 100)
        self.vel = pygame.Vector2(0, 0)
        self.rect = pygame.Rect(0, 0, 20, 20)
        self.holder = None

    def update(self, dt):
        if self.holder:
            # Position near holder's right hand
            self.pos = self.holder.pos + pygame.Vector2(15, -10)
        else:
            self.vel.y += 500 * dt
            self.pos += self.vel * dt
        self.rect.center = self.pos

    def draw(self, surf, offset_y=0):
        pygame.draw.rect(surf, YELLOW, self.rect.move(0, -offset_y))


def draw_plane(surf, x, door_open, offset_y=0):
    body = pygame.Rect(x, 80 - offset_y, 120, 40)
    pygame.draw.rect(surf, (210, 210, 210), body, border_radius=10)

    # Nose cone
    nose = [(x + 120, 100 - offset_y), (x + 140, 90 - offset_y),
            (x + 140, 110 - offset_y)]
    pygame.draw.polygon(surf, (210, 210, 210), nose)

    # Wing
    wing = [(x + 30, 95 - offset_y), (x + 110, 80 - offset_y),
            (x + 90, 110 - offset_y), (x + 30, 110 - offset_y)]
    pygame.draw.polygon(surf, (180, 180, 180), wing)

    # Tail fin
    tail = [(x, 80 - offset_y), (x - 30, 70 - offset_y),
            (x - 30, 110 - offset_y), (x, 100 - offset_y)]
    pygame.draw.polygon(surf, (180, 180, 180), tail)

    for i in range(3):
        window = pygame.Rect(x + 20 + i * 30, 90 - offset_y, 15, 10)
        pygame.draw.rect(surf, SKY, window, border_radius=3)
        pygame.draw.rect(surf, BLACK, window, 1, border_radius=3)

    door = pygame.Rect(x + 80, 90 - offset_y, 30, 20)
    if door_open:
        pygame.draw.rect(surf, BLACK, door, 2)
    else:
        pygame.draw.rect(surf, BLACK, door)


def draw_sheep(surf, x, y):
    body = pygame.Rect(x - 20, y - 10, 40, 20)
    pygame.draw.ellipse(surf, WHITE, body)
    head = pygame.Rect(x + 10, y - 8, 16, 16)
    pygame.draw.ellipse(surf, WHITE, head)
    pygame.draw.circle(surf, BLACK, (x + 18, y - 2), 2)
    pygame.draw.circle(surf, BLACK, (x + 24, y - 2), 2)
    for dx in (-10, -5, 5, 10):
        pygame.draw.rect(surf, BLACK, (x + dx, y + 8, 3, 8))


class WindStreak:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = HEIGHT + random.uniform(0, HEIGHT)
        self.speed = random.uniform(300, 500)
        self.length = random.randint(10, 30)

    def update(self, dt):
        self.y -= self.speed * dt

    def draw(self, surf):
        start = (self.x, self.y)
        end = (self.x, self.y + self.length)
        pygame.draw.line(surf, WHITE, start, end, 1)


class Cloud:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.speed = random.uniform(20, 60)
        self.size = random.randint(60, 120)

    def update(self, dt):
        """Drift the cloud sideways across the sky."""
        self.pos.x -= self.speed * dt

    def draw(self, surf, offset_y=0):
        rect = pygame.Rect(0, 0, self.size, int(self.size * 0.6))
        rect.center = (self.pos.x, self.pos.y - offset_y)
        pygame.draw.ellipse(surf, WHITE, rect)


# Game variables
wind_streaks = []
clouds = []
intro_clouds = []
state = 'intro'
plane_x = -150
plane_pass = 0
plane_door_opened = False
altitude = 10000
winner = None
loser = None
loser_crashed = False
camera_y = 0


# Players and parachute placeholders
p_red = Player(300, RED, {'left': pygame.K_a, 'right': pygame.K_d,
                          'slower': pygame.K_w, 'faster': pygame.K_s})
p_blue = Player(500, BLUE, {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT,
                            'slower': pygame.K_UP, 'faster': pygame.K_DOWN})
chute = Parachute((p_red.pos.x + p_blue.pos.x) / 2)


def reset_game():
    global plane_x, plane_pass, plane_door_opened, altitude
    global winner, loser, loser_crashed, state, camera_y
    global wind_streaks, clouds
    p_red.pos = pygame.Vector2(300, 120)
    p_red.vel = pygame.Vector2(0, 0)
    p_red.cooldown = 0
    p_blue.pos = pygame.Vector2(500, 120)
    p_blue.vel = pygame.Vector2(0, 0)
    p_blue.cooldown = 0
    chute.pos = pygame.Vector2((p_red.pos.x + p_blue.pos.x) / 2, 100)
    chute.vel = pygame.Vector2(0, 0)
    chute.holder = None
    plane_x = -150
    plane_pass = 0
    plane_door_opened = False
    altitude = 10000
    winner = None
    loser = None
    loser_crashed = False
    camera_y = 0
    wind_streaks.clear()
    clouds.clear()
    state = 'plane'
    plane_sound.play(-1)


running = True
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if state == 'intro':
                reset_game()
            elif state == 'end':
                state = 'intro'
                intro_clouds.clear()

    if state == 'intro':
        draw_gradient(screen, (20, 20, 60), (0, 0, 0))
        if random.random() < 0.02:
            y = random.uniform(50, HEIGHT // 2)
            intro_clouds.append(Cloud(WIDTH + 60, y))
        for cl in intro_clouds[:]:
            cl.update(dt)
            cl.draw(screen)
            if cl.pos.x + cl.size < 0:
                intro_clouds.remove(cl)
        t = bigfont.render("Parachute Joust", True, WHITE)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 3)))
        c = font.render("Red: A/D W/S   Blue: ←/→ ↑/↓", True, WHITE)
        screen.blit(c, c.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        if pygame.time.get_ticks() // 500 % 2:
            p = font.render("Press Enter to start", True, WHITE)
            screen.blit(p, p.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3)))

    elif state == 'plane':
        draw_gradient(screen, SKY, WHITE)
        plane_x += 200 * dt
        if plane_pass == 0:
            draw_plane(screen, plane_x, False)
            if plane_x > WIDTH:
                plane_pass = 1
                plane_x = -150
        else:
            if plane_x < WIDTH / 2:
                draw_plane(screen, plane_x, False)
            else:
                draw_plane(screen, plane_x, True)
                if not plane_door_opened:
                    # Drop players and parachute
                    p_red.pos = pygame.Vector2(plane_x + 80, 110)
                    p_blue.pos = pygame.Vector2(plane_x + 110, 110)
                    chute.pos = pygame.Vector2(plane_x + 95, 110)
                    plane_door_opened = True
                    state = 'fall'
                    plane_sound.stop()
                    wind_sound.play(-1)

    elif state == 'fall':
        altitude -= 450 * dt
        plane_x += 200 * dt
        p_red.update(dt, slowed=(chute.holder == p_red))
        p_blue.update(dt, slowed=(chute.holder == p_blue))
        chute.update(dt)

        min_y = min(p_red.pos.y, p_blue.pos.y)
        camera_y = max(0, min_y - 200)

        if random.random() < 0.3:
            wind_streaks.append(WindStreak())
        for w in wind_streaks[:]:
            w.update(dt)
            if w.y + w.length < 0:
                wind_streaks.remove(w)

        if random.random() < 0.02:
            cloud_y = camera_y + random.uniform(-100, HEIGHT)
            clouds.append(Cloud(WIDTH + 60, cloud_y))
        for c in clouds[:]:
            c.update(dt)
            if c.pos.x + c.size < 0:
                clouds.remove(c)

        if chute.holder is None:
            if chute.rect.colliderect(p_red.rect):
                chute.holder = p_red
                p_red.cooldown = 0.5
                blip_sound.play()
            elif chute.rect.colliderect(p_blue.rect):
                chute.holder = p_blue
                p_blue.cooldown = 0.5
                blip_sound.play()
        else:
            if p_red.rect.colliderect(p_blue.rect):
                if chute.holder == p_red and p_red.cooldown <= 0:
                    chute.holder = p_blue
                    p_red.cooldown = p_blue.cooldown = 0.5
                    blip_sound.play()
                elif chute.holder == p_blue and p_blue.cooldown <= 0:
                    chute.holder = p_red
                    p_red.cooldown = p_blue.cooldown = 0.5
                    blip_sound.play()

        if altitude <= 1000:
            winner = chute.holder
            loser = p_blue if winner == p_red else p_red
            state = 'resolution'
            wind_sound.stop()
            camera_y = 0

        draw_gradient(screen, SKY, WHITE)
        for w in wind_streaks:
            w.draw(screen)
        draw_plane(screen, plane_x, True, camera_y)
        p_red.draw(screen, glow=(chute.holder == p_red), offset_y=camera_y,
                   holding_chute=(chute.holder == p_red))
        p_blue.draw(screen, glow=(chute.holder == p_blue), offset_y=camera_y,
                    holding_chute=(chute.holder == p_blue))
        chute.draw(screen, offset_y=camera_y)
        for c in clouds:
            c.draw(screen, offset_y=camera_y)
        alt_txt = font.render(f"Altitude: {int(altitude)} m", True, BLACK)
        screen.blit(alt_txt, (10, 10))
        holder_txt = "None"
        if chute.holder == p_red:
            holder_txt = "Red"
        elif chute.holder == p_blue:
            holder_txt = "Blue"
        hold = font.render(f"Parachute: {holder_txt}", True, BLACK)
        screen.blit(hold, (10, 40))

    elif state == 'resolution':
        # Winner floats, loser plummets
        if winner:
            winner.vel.y = max(winner.vel.y, 0)
            winner.vel.y += 40 * dt
            winner.pos.y += winner.vel.y * dt
            winner.pos.y = max(10, min(HEIGHT - 10, winner.pos.y))
            chute.pos = winner.pos + pygame.Vector2(0, -80)
        if loser:
            loser.vel.y += 1000 * dt
            loser.pos.y += loser.vel.y * dt
            loser.pos.y = max(10, min(HEIGHT - 10, loser.pos.y))
            if not loser_crashed and loser.pos.y >= GROUND_Y:
                loser_crashed = True
                loser.pos.y = GROUND_Y
                thud_sound.play()
                sheep_sound.play()
        if winner and winner.pos.y >= GROUND_Y - 40:
            winner.pos.y = GROUND_Y - 40
            state = 'end'

        draw_gradient(screen, SKY, WHITE)
        # Draw barn and ground
        pygame.draw.rect(screen, GREEN, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        barn = pygame.Rect(WIDTH // 2 - 60, GROUND_Y - 80, 120, 80)
        pygame.draw.rect(screen, BROWN, barn)
        pygame.draw.polygon(screen, (170, 0, 0),
                            [(barn.left, barn.top), (barn.right, barn.top),
                             (barn.centerx, barn.top - 30)])
        if loser_crashed:
            hole = pygame.Rect(barn.centerx - 20, barn.top - 20, 40, 40)
            pygame.draw.rect(screen, BLACK, hole)
        for i in range(3):
            sx = barn.left + 30 + i * 30
            sy = barn.bottom - 10
            draw_sheep(screen, sx, sy)
        # Draw players
        p_red.draw(screen, glow=(winner == p_red), holding_chute=False)
        p_blue.draw(screen, glow=(winner == p_blue), holding_chute=False)
        # Draw parachute canopy
        bob = math.sin(pygame.time.get_ticks() / 200) * 5
        pygame.draw.circle(screen, YELLOW, (int(chute.pos.x), int(chute.pos.y + bob)), 40)
        pygame.draw.line(screen, BLACK, (chute.pos.x - 40, chute.pos.y + bob), (winner.pos.x, winner.pos.y), 2)
        pygame.draw.line(screen, BLACK, (chute.pos.x + 40, chute.pos.y + bob), (winner.pos.x, winner.pos.y), 2)

    elif state == 'end':
        draw_gradient(screen, SKY, WHITE)
        pygame.draw.rect(screen, GREEN, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        barn = pygame.Rect(WIDTH // 2 - 60, GROUND_Y - 80, 120, 80)
        pygame.draw.rect(screen, BROWN, barn)
        pygame.draw.polygon(screen, (170, 0, 0),
                            [(barn.left, barn.top), (barn.right, barn.top),
                             (barn.centerx, barn.top - 30)])
        hole = pygame.Rect(barn.centerx - 20, barn.top - 20, 40, 40)
        pygame.draw.rect(screen, BLACK, hole)
        for i in range(3):
            sx = barn.left + 30 + i * 30
            sy = barn.bottom - 10
            draw_sheep(screen, sx, sy)
        p_red.draw(screen, glow=(winner == p_red), holding_chute=False)
        p_blue.draw(screen, glow=(winner == p_blue), holding_chute=False)
        bob = math.sin(pygame.time.get_ticks() / 200) * 5
        pygame.draw.circle(screen, YELLOW, (int(chute.pos.x), int(chute.pos.y + bob)), 40)
        pygame.draw.line(screen, BLACK, (chute.pos.x - 40, chute.pos.y + bob), (winner.pos.x, winner.pos.y), 2)
        pygame.draw.line(screen, BLACK, (chute.pos.x + 40, chute.pos.y + bob), (winner.pos.x, winner.pos.y), 2)
        txt = "Red" if winner == p_red else "Blue"
        m = bigfont.render(f"{txt} Wins!", True, BLACK)
        screen.blit(m, m.get_rect(center=(WIDTH // 2, HEIGHT // 3)))
        if pygame.time.get_ticks() // 500 % 2:
            p = font.render("Press Enter to play again", True, BLACK)
            screen.blit(p, p.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    pygame.display.flip()

pygame.quit()
