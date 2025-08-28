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


def make_sound(freq, duration=0.3, volume=0.5):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [
        int(volume * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
        for i in range(n_samples)
    ])
    return pygame.mixer.Sound(buffer=buf)


# Sounds (simple generated tones)
plane_sound = make_sound(110, 0.5, 0.4)
wind_sound = make_sound(300, 0.5, 0.4)
blip_sound = make_sound(800, 0.1, 0.4)
thud_sound = make_sound(60, 0.5, 0.6)
sheep_sound = make_sound(500, 0.3, 0.6)


class Player:
    def __init__(self, x, color, controls):
        self.pos = pygame.Vector2(x, 120)
        self.vel = pygame.Vector2(0, 0)
        self.color = color
        self.controls = controls
        self.rect = pygame.Rect(0, 0, 30, 30)
        self.cooldown = 0

    def update(self, dt):
        keys = pygame.key.get_pressed()
        acc = pygame.Vector2(0, 0)
        if keys[self.controls['left']]:
            acc.x -= 200
        if keys[self.controls['right']]:
            acc.x += 200
        # Soft force toward center
        if self.pos.x < 50:
            acc.x += (50 - self.pos.x) * 2
        if self.pos.x > WIDTH - 50:
            acc.x -= (self.pos.x - (WIDTH - 50)) * 2
        self.vel.x += acc.x * dt
        self.vel.x *= 0.98
        self.pos.x += self.vel.x * dt

        if keys[self.controls['faster']]:
            self.vel.y += 300 * dt
        if keys[self.controls['slower']]:
            self.vel.y -= 300 * dt
        self.vel.y += 500 * dt
        self.pos.y += self.vel.y * dt
        self.rect.topleft = (self.pos.x - 15, self.pos.y - 15)
        if self.cooldown > 0:
            self.cooldown -= dt

    def draw(self, surf, glow=False):
        pygame.draw.rect(surf, self.color, self.rect)
        if glow:
            pygame.draw.rect(surf, WHITE, self.rect.inflate(10, 10), 2)


class Parachute:
    def __init__(self, x):
        self.pos = pygame.Vector2(x, 100)
        self.vel = pygame.Vector2(0, 0)
        self.rect = pygame.Rect(0, 0, 20, 20)
        self.holder = None

    def update(self, dt):
        if self.holder:
            self.pos = self.holder.pos + pygame.Vector2(0, -40)
        else:
            self.vel.y += 500 * dt
            self.pos += self.vel * dt
        self.rect.center = self.pos

    def draw(self, surf):
        if not self.holder:
            pygame.draw.rect(surf, YELLOW, self.rect)


# Game variables
state = 'intro'
plane_x = -150
plane_pass = 0
plane_door_opened = False
altitude = 10000
winner = None
loser = None
loser_crashed = False


# Players and parachute placeholders
p_red = Player(300, RED, {'left': pygame.K_a, 'right': pygame.K_d,
                          'slower': pygame.K_w, 'faster': pygame.K_s})
p_blue = Player(500, BLUE, {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT,
                            'slower': pygame.K_UP, 'faster': pygame.K_DOWN})
chute = Parachute((p_red.pos.x + p_blue.pos.x) / 2)


def reset_game():
    global plane_x, plane_pass, plane_door_opened, altitude
    global winner, loser, loser_crashed, state
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
        plane_rect = pygame.Rect(plane_x, 80, 120, 40)
        pygame.draw.rect(screen, (200, 200, 200), plane_rect)
        if plane_pass == 0:
            pygame.draw.rect(screen, BLACK, (plane_x + 80, 90, 30, 20))
            if plane_x > WIDTH:
                plane_pass = 1
                plane_x = -150
        else:
            if plane_x < WIDTH / 2:
                pygame.draw.rect(screen, BLACK, (plane_x + 80, 90, 30, 20))
            else:
                pygame.draw.rect(screen, BLACK, (plane_x + 80, 90, 30, 20), 2)
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
        p_red.update(dt)
        p_blue.update(dt)
        chute.update(dt)

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

        screen.fill(SKY)
        p_red.draw(screen, glow=(chute.holder == p_red))
        p_blue.draw(screen, glow=(chute.holder == p_blue))
        chute.draw(screen)
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
                sy = barn.bottom - 20
                pygame.draw.circle(screen, WHITE, (sx, sy), 10)
        # Draw players
        p_red.draw(screen, glow=(winner == p_red))
        p_blue.draw(screen, glow=(winner == p_blue))
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
            sy = barn.bottom - 20
            pygame.draw.circle(screen, WHITE, (sx, sy), 10)
        p_red.draw(screen, glow=(winner == p_red))
        p_blue.draw(screen, glow=(winner == p_blue))
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
