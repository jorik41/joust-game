import os
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
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

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Parachute Joust")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
bigfont = pygame.font.SysFont(None, 72)


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
        # phase used to animate rag-doll limb flailing
        self.flail_phase = random.random() * math.tau

    def update(self, dt, slowed=False):
        keys = pygame.key.get_pressed()
        acc = pygame.Vector2(0, 0)
        speed = 0.7 if slowed else 1.0
        if keys[self.controls['left']]:
            acc.x -= 200 * speed
        if keys[self.controls['right']]:
            acc.x += 200 * speed
        # Soft force toward center
        if self.pos.x < 50:
            acc.x += (50 - self.pos.x) * 2
        if self.pos.x > WIDTH - 50:
            acc.x -= (self.pos.x - (WIDTH - 50)) * 2
        self.vel.x += acc.x * dt
        self.vel.x *= 0.98
        self.pos.x += self.vel.x * dt * speed

        if keys[self.controls['faster']]:
            self.vel.y += 300 * dt * speed
        if keys[self.controls['slower']]:
            self.vel.y -= 300 * dt * speed
        self.vel.y += 500 * dt * speed
        self.pos.y += self.vel.y * dt * speed
        self.rect.topleft = (self.pos.x - 10, self.pos.y - 20)
        if self.cooldown > 0:
            self.cooldown -= dt
        self.flail_phase += dt * 5

    def draw(self, surf, glow=False, offset_y=0, holding_chute=False):
        head_center = (int(self.pos.x), int(self.pos.y - 20 - offset_y))
        pygame.draw.circle(surf, (255, 224, 189), head_center, 8)
        # Torso
        body_start = (self.pos.x, self.pos.y - 12 - offset_y)
        body_end = (self.pos.x, self.pos.y + 8 - offset_y)
        pygame.draw.line(surf, self.color, body_start, body_end, 4)

        shoulder = pygame.Vector2(self.pos.x, self.pos.y - 8 - offset_y)
        hip = pygame.Vector2(self.pos.x, self.pos.y + 8 - offset_y)
        arm_len = 15
        leg_len = 18
        phase = self.flail_phase

        # Left arm
        ang = math.pi / 2 + math.sin(phase) * 0.5
        elbow = shoulder + pygame.Vector2(math.cos(ang), math.sin(ang)) * arm_len
        hand = elbow + pygame.Vector2(math.cos(ang), math.sin(ang)) * arm_len
        pygame.draw.line(surf, self.color, shoulder, elbow, 3)
        pygame.draw.line(surf, self.color, elbow, hand, 3)

        # Right arm (fixed if holding parachute)
        if holding_chute:
            ang = -math.pi / 4
            target = shoulder + pygame.Vector2(math.cos(ang), math.sin(ang)) * arm_len * 2
            pygame.draw.line(surf, self.color, shoulder, target, 3)
        else:
            ang = math.pi / 2 + math.sin(phase + math.pi) * 0.5
            elbow = shoulder + pygame.Vector2(math.cos(ang), math.sin(ang)) * arm_len
            hand = elbow + pygame.Vector2(math.cos(ang), math.sin(ang)) * arm_len
            pygame.draw.line(surf, self.color, shoulder, elbow, 3)
            pygame.draw.line(surf, self.color, elbow, hand, 3)

        # Legs
        ang = math.pi / 2 + math.sin(phase + math.pi / 2) * 0.3
        knee = hip + pygame.Vector2(math.cos(ang), math.sin(ang)) * leg_len
        foot = knee + pygame.Vector2(math.cos(ang), math.sin(ang)) * leg_len
        pygame.draw.line(surf, self.color, hip, knee, 3)
        pygame.draw.line(surf, self.color, knee, foot, 3)

        ang = math.pi / 2 + math.sin(phase + 3 * math.pi / 2) * 0.3
        knee = hip + pygame.Vector2(math.cos(ang), math.sin(ang)) * leg_len
        foot = knee + pygame.Vector2(math.cos(ang), math.sin(ang)) * leg_len
        pygame.draw.line(surf, self.color, hip, knee, 3)
        pygame.draw.line(surf, self.color, knee, foot, 3)

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
    pygame.draw.rect(surf, (200, 200, 200), body)
    wing = pygame.Rect(x + 10, 95 - offset_y, 100, 15)
    pygame.draw.rect(surf, (180, 180, 180), wing)
    tail = pygame.Rect(x - 20, 85 - offset_y, 40, 20)
    pygame.draw.rect(surf, (180, 180, 180), tail)
    for i in range(3):
        window = pygame.Rect(x + 20 + i * 30, 90 - offset_y, 15, 10)
        pygame.draw.rect(surf, SKY, window)
        pygame.draw.rect(surf, BLACK, window, 1)
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


# Game variables
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

    if state == 'intro':
        screen.fill((20, 20, 60))
        t = bigfont.render("Parachute Joust", True, WHITE)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 3)))
        c = font.render("Red: A/D W/S   Blue: ←/→ ↑/↓", True, WHITE)
        screen.blit(c, c.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        p = font.render("Press Enter to start", True, WHITE)
        screen.blit(p, p.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3)))

    elif state == 'plane':
        screen.fill(SKY)
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

        screen.fill(SKY)
        draw_plane(screen, plane_x, True, camera_y)
        p_red.draw(screen, glow=(chute.holder == p_red), offset_y=camera_y,
                   holding_chute=(chute.holder == p_red))
        p_blue.draw(screen, glow=(chute.holder == p_blue), offset_y=camera_y,
                    holding_chute=(chute.holder == p_blue))
        chute.draw(screen, offset_y=camera_y)
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
            chute.pos = winner.pos + pygame.Vector2(0, -80)
        if loser:
            loser.vel.y += 1000 * dt
            loser.pos.y += loser.vel.y * dt
            if not loser_crashed and loser.pos.y >= GROUND_Y:
                loser_crashed = True
                loser.pos.y = GROUND_Y
                thud_sound.play()
                sheep_sound.play()
        if winner and winner.pos.y >= GROUND_Y - 40:
            winner.pos.y = GROUND_Y - 40
            state = 'end'

        screen.fill(SKY)
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
        pygame.draw.circle(screen, YELLOW, (int(chute.pos.x), int(chute.pos.y)), 40)
        pygame.draw.line(screen, BLACK, (chute.pos.x - 40, chute.pos.y), (winner.pos.x, winner.pos.y), 2)
        pygame.draw.line(screen, BLACK, (chute.pos.x + 40, chute.pos.y), (winner.pos.x, winner.pos.y), 2)

    elif state == 'end':
        screen.fill(SKY)
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
        pygame.draw.circle(screen, YELLOW, (int(chute.pos.x), int(chute.pos.y)), 40)
        pygame.draw.line(screen, BLACK, (chute.pos.x - 40, chute.pos.y), (winner.pos.x, winner.pos.y), 2)
        pygame.draw.line(screen, BLACK, (chute.pos.x + 40, chute.pos.y), (winner.pos.x, winner.pos.y), 2)
        txt = "Red" if winner == p_red else "Blue"
        m = bigfont.render(f"{txt} Wins!", True, BLACK)
        screen.blit(m, m.get_rect(center=(WIDTH // 2, HEIGHT // 3)))
        p = font.render("Press Enter to play again", True, BLACK)
        screen.blit(p, p.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    pygame.display.flip()

pygame.quit()
