import math
import os
import sys
import pygame

pygame.init()

#기본 설정
S_WIDTH, S_HEIGHT = 600, 400
FPS = 60
GROUND = S_HEIGHT - 40
NET_X = S_WIDTH // 2
NET_W = 8
NET_H = 110
NET_TOP = GROUND - NET_H

GRAVITY = 0.10
Air_Resistance = 0.999
BALL_RADIUS = 14
BALL_MAX_SPEED = 9

PK_RADIUS = 30
PK_SPEED = 5
PK_JUMP = -11
PK_GRAVITY = 0.5

WIN_SCORE = 7

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

screen = pygame.display.set_mode((S_WIDTH, S_HEIGHT))
pygame.display.set_caption("피카츄배구")
clock = pygame.time.Clock()


def make_font(size):
    return pygame.font.SysFont("malgungothic", size)


font_big = make_font(40)
font_mid = make_font(24)
font_small = make_font(16)


def load_image(name, size):
    path = os.path.join(BASE_DIR, name)
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    except (pygame.error, FileNotFoundError):
        return None

d = PK_RADIUS * 2
Pikachu_1 = load_image("Pikachu_1.png", (d, d))
Pikachu_2 = load_image("Pikachu_2.png", (d, d))
Pk_move_1 = load_image("Pk_move_1.png", (d, d))
Pk_move_2 = load_image("Pk_move_2.png", (d, d))
Ball_img = load_image("Ball.png", (BALL_RADIUS * 2, BALL_RADIUS * 2))


#피카츄 설정
class Pikachu:
    def __init__(self, side, keys, color, img_idle, img_jump):
        self.side = side
        self.keys = keys
        self.color = color
        self.img_idle = img_idle
        self.img_jump = img_jump
        self.radius = PK_RADIUS
        self.reset()

    def reset(self):
        self.x = S_WIDTH * (0.25 if self.side == 0 else 0.75)
        self.y = GROUND - self.radius
        self.vx = 0
        self.vy = 0
        self.spiking = False

    @property
    def on_ground(self):
        return self.y >= GROUND - self.radius

    def update(self, pressed):
        left, right, jump, spike = self.keys
        self.vx = 0
        if pressed[left]:
            self.vx = -PK_SPEED
        if pressed[right]:
            self.vx = PK_SPEED
        if pressed[jump] and self.on_ground:
            self.vy = PK_JUMP
        self.spiking = bool(pressed[spike]) and not self.on_ground

        self.x += self.vx
        self.vy += PK_GRAVITY
        self.y += self.vy

        if self.y >= GROUND - self.radius:
            self.y = GROUND - self.radius
            self.vy = 0

        if self.side == 0:
            lo, hi = self.radius, NET_X - NET_W // 2 - self.radius
        else:
            lo, hi = NET_X + NET_W // 2 + self.radius, S_WIDTH - self.radius
        self.x = max(lo, min(hi, self.x))

    def draw(self, surf):
        img = self.img_idle if self.on_ground else (self.img_jump or self.img_idle)
        if img:
            surf.blit(img, img.get_rect(center=(self.x, self.y)))
        else:
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
            ex = 14 if self.side == 0 else -14
            pygame.draw.polygon(surf, self.color, [
                (self.x - 20, self.y - 22), (self.x - 12, self.y - 48), (self.x - 4, self.y - 26)])
            pygame.draw.polygon(surf, self.color, [
                (self.x + 20, self.y - 22), (self.x + 12, self.y - 48), (self.x + 4, self.y - 26)])
            pygame.draw.circle(surf, (0, 0, 0), (int(self.x - 10), int(self.y - 6)), 4)
            pygame.draw.circle(surf, (0, 0, 0), (int(self.x + 10), int(self.y - 6)), 4)
            pygame.draw.circle(surf, (230, 50, 50), (int(self.x - 20), int(self.y + 6)), 5)
            pygame.draw.circle(surf, (230, 50, 50), (int(self.x + 20), int(self.y + 6)), 5)
        if self.spiking:
            pygame.draw.circle(surf, (255, 255, 255), (int(self.x), int(self.y)), self.radius + 4, 2)


class Ball:
    def __init__(self):
        self.serve(0)

    def serve(self, side):
        self.x = S_WIDTH * (0.25 if side == 0 else 0.75)
        self.y = 120
        self.vx = 0
        self.vy = 0
        self.radius = BALL_RADIUS

    def limit_speed(self):
        sp = math.hypot(self.vx, self.vy)
        if sp > BALL_MAX_SPEED:
            self.vx *= BALL_MAX_SPEED / sp
            self.vy *= BALL_MAX_SPEED / sp

    def update(self):
        self.vy += GRAVITY
        self.vx *= Air_Resistance
        self.x += self.vx
        self.y += self.vy
        r = self.radius

        if self.x - r <= 0:
            self.x = r
            self.vx = abs(self.vx)
        elif self.x + r >= S_WIDTH:
            self.x = S_WIDTH - r
            self.vx = -abs(self.vx)
        if self.y - r <= 0:
            self.y = r
            self.vy = abs(self.vy)

        half = NET_W / 2
        if self.y > NET_TOP:

            if abs(self.x - NET_X) < half + r:
                if self.x < NET_X:
                    self.x = NET_X - half - r
                    self.vx = -abs(self.vx) * 0.8
                else:
                    self.x = NET_X + half + r
                    self.vx = abs(self.vx) * 0.8
        else:
            dx, dy = self.x - NET_X, self.y - NET_TOP
            dist = math.hypot(dx, dy)
            if dist < r + half:
                if dist == 0:
                    dx, dy, dist = 0, -1, 1
                nx, ny = dx / dist, dy / dist
                self.x = NET_X + nx * (r + half)
                self.y = NET_TOP + ny * (r + half)
                dot = self.vx * nx + self.vy * ny
                if dot < 0:
                    self.vx -= 2 * dot * nx
                    self.vy -= 2 * dot * ny

    def hit_by(self, p):
        dx, dy = self.x - p.x, self.y - p.y
        dist = math.hypot(dx, dy)
        min_dist = self.radius + p.radius
        if dist >= min_dist:
            return
        if dist == 0:
            dx, dy, dist = 0, -1, 1
        nx, ny = dx / dist, dy / dist

        # 겹침 해소
        self.x = p.x + nx * min_dist
        self.y = p.y + ny * min_dist

        if p.spiking:
            # 스파이크: 상대 진영 아래쪽으로 강하게
            direction = 1 if p.side == 0 else -1
            self.vx = direction * 10
            self.vy = 8
        else:
            # 상대속도 기준 반사 + 피카츄 속도 더하기
            rvx, rvy = self.vx - p.vx, self.vy - p.vy
            dot = rvx * nx + rvy * ny
            if dot < 0:
                self.vx -= 2 * dot * nx
                self.vy -= 2 * dot * ny
            self.vx += p.vx * 0.5
            self.vy += p.vy * 0.5
            # 너무 약하게 맞으면 최소한 띄워주기
            if self.vy > -4 and ny < -0.3:
                self.vy = -7
        self.limit_speed()

    def draw(self, surf):
        # 그림자
        sh = max(4, int(self.radius * (1 - (GROUND - self.y) / GROUND * 0.7)))
        pygame.draw.ellipse(surf, (60, 120, 60), (self.x - sh, GROUND - 3, sh * 2, 6))
        if Ball_img:
            surf.blit(Ball_img, Ball_img.get_rect(center=(self.x, self.y)))
        else:
            pygame.draw.circle(surf, (255, 255, 255), (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surf, (200, 40, 40), (int(self.x), int(self.y)), self.radius, 3)


# ---------------------------------------------------------------- 그리기
def draw_text(text, font, color, center):
    img = font.render(text, True, color)
    screen.blit(img, img.get_rect(center=center))


def draw_court():
    screen.fill((120, 190, 255))
    pygame.draw.rect(screen, (90, 170, 80), (0, GROUND, S_WIDTH, S_HEIGHT - GROUND))
    pygame.draw.rect(screen, (240, 240, 240), (NET_X - NET_W // 2, NET_TOP, NET_W, NET_H))
    pygame.draw.circle(screen, (240, 240, 240), (NET_X, NET_TOP), NET_W // 2)


def draw_score(score):
    draw_text(str(score[0]), font_big, (255, 255, 255), (S_WIDTH // 4, 40))
    draw_text(str(score[1]), font_big, (255, 255, 255), (S_WIDTH * 3 // 4, 40))


# ---------------------------------------------------------------- 메인
def title_screen():
    """ENTER: 시작, ESC: 종료"""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        draw_court()
        draw_text("피카츄 배구", font_big, (255, 230, 0), (S_WIDTH // 2, 100))
        draw_text("ENTER : 시작   ESC : 종료", font_mid, (255, 255, 255), (S_WIDTH // 2, 190))
        draw_text("1P: W(점프) A D(이동) S(공중에서 스파이크)", font_small, (30, 30, 30), (S_WIDTH // 2, 250))
        draw_text("2P: ↑(점프) ← →(이동) ↓(공중에서 스파이크)", font_small, (30, 30, 30), (S_WIDTH // 2, 275))
        pygame.display.flip()
        clock.tick(FPS)


def main():
    p1 = Pikachu(0, (pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_k),
                 (255, 215, 0), Pikachu_1, Pk_move_1)
    p2 = Pikachu(1, (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_LSHIFT),
                 (255, 190, 0), Pikachu_2, Pk_move_2)
    ball = Ball()
    score = [0, 0]
    state = "serve"        # serve -> play -> point -> over
    timer = 60             # 서브 전 잠깐 대기
    server = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return                       # 타이틀로 돌아가기
                if state == "over" and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return

        pressed = pygame.key.get_pressed()
        p1.update(pressed)
        p2.update(pressed)

        if state == "serve":
            timer -= 1
            if timer <= 0:
                state = "play"
        elif state == "play":
            ball.update()
            ball.hit_by(p1)
            ball.hit_by(p2)
            # 바닥에 닿으면 득점
            if ball.y + ball.radius >= GROUND:
                ball.y = GROUND - ball.radius
                landed_left = ball.x < NET_X
                winner = 1 if landed_left else 0
                score[winner] += 1
                server = winner
                state = "over" if max(score) >= WIN_SCORE else "point"
                timer = 90
        elif state == "point":
            timer -= 1
            if timer <= 0:
                p1.reset()
                p2.reset()
                ball.serve(server)
                state = "serve"
                timer = 45

        draw_court()
        draw_score(score)
        p1.draw(screen)
        p2.draw(screen)
        ball.draw(screen)

        if state == "point":
            draw_text("득점!", font_big, (255, 255, 0), (S_WIDTH // 2, 150))
        elif state == "over":
            w = "1P" if score[0] > score[1] else "2P"
            draw_text(f"{w} 승리!", font_big, (255, 255, 0), (S_WIDTH // 2, 140))
            draw_text("ENTER: 타이틀로", font_mid, (255, 255, 255), (S_WIDTH // 2, 200))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    while True:
        title_screen()
        main()
