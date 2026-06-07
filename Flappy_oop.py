import pygame
import random
import sys
import math

# --- Constants ---
WIDTH, HEIGHT = 400, 600
GROUND_Y = 520
FPS = 60
TEXT_COLOR = (255, 255, 255)

# --- Helper Functions ---
def scale_pipe_3slice(img, target_height):
    """Scales the pipe vertically while keeping the top and bottom 12 pixels unchanged."""
    width = img.get_width()
    orig_height = img.get_height()
    
    # Fallback if the image is too small to slice
    if orig_height <= 24:
        return pygame.transform.scale(img, (width, target_height))
        
    new_img = pygame.Surface((width, target_height), pygame.SRCALPHA)
    
    # 1. Extract the unchanged top and bottom caps
    top_part = img.subsurface((0, 0, width, 12))
    bottom_part = img.subsurface((0, orig_height - 12, width, 12))
    
    # 2. Extract and stretch the middle
    middle_part = img.subsurface((0, 12, width, orig_height - 24))
    middle_scaled = pygame.transform.scale(middle_part, (width, target_height - 24))
    
    # 3. Glue them back together
    new_img.blit(top_part, (0, 0))
    new_img.blit(middle_scaled, (0, 12))
    new_img.blit(bottom_part, (0, target_height - 12))
    
    return new_img

# --- Classes ---
class Bird(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.images = [
            pygame.image.load('Sprites/bird1.png').convert_alpha(),
            pygame.image.load('Sprites/bird2.png').convert_alpha(),
            pygame.image.load('Sprites/bird3.png').convert_alpha()
        ]
        self.index = 1
        self.counter = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect(center=(80, HEIGHT // 2))

        self.velocity = 0
        self.gravity = 0.45
        self.flap_strength = -8
        self.is_flapping = False

    def update(self):
        self.velocity += self.gravity
        self.rect.y += int(self.velocity)

        if self.is_flapping:
            self.counter += 1
            flap_cooldown = 5 

            if self.counter > flap_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images):
                    self.index = 0
                    self.is_flapping = False 
        else:
            self.index = 1 

        self.image = pygame.transform.rotate(self.images[self.index], self.velocity * -2)

    def flap(self):
        self.velocity = self.flap_strength
        self.is_flapping = True
        self.index = 0 

    def check_bounds(self):
        if self.rect.top <= 0 or self.rect.bottom >= GROUND_Y:
            if self.rect.top <= 0:
                return "Sky"
            else:
                return "Ground"
        return False


class PipePair:
    def __init__(self, x):
        self.x = x
        self.gap = 160
        self.speed = 3
        self.passed = False  

        # 3-slice scaling for the pipes
        self.top_image = pygame.image.load('Sprites/pipe_down.png').convert_alpha()
        self.top_image = scale_pipe_3slice(self.top_image, HEIGHT)
        
        self.bottom_image = pygame.image.load('Sprites/pipe_up.png').convert_alpha()
        self.bottom_image = scale_pipe_3slice(self.bottom_image, HEIGHT)

        self.width = self.bottom_image.get_width()

        gap_y = random.randint(140, 380)

        self.top_rect = self.top_image.get_rect(bottomleft=(self.x, gap_y - self.gap // 2))
        self.bottom_rect = self.bottom_image.get_rect(topleft=(self.x, gap_y + self.gap // 2))

    def update(self):
        self.top_rect.x -= self.speed
        self.bottom_rect.x -= self.speed

    def draw(self, surface):
        surface.blit(self.top_image, self.top_rect)
        surface.blit(self.bottom_image, self.bottom_rect)

    def collides_with(self, bird_rect):
        bird_mask = pygame.mask.from_surface(pygame.transform.rotate(pygame.image.load('Sprites/bird2.png').convert_alpha(), game.bird.velocity * -2)) 
        top_mask = pygame.mask.from_surface(self.top_image)
        bottom_mask = pygame.mask.from_surface(self.bottom_image)

        top_offset = (self.top_rect.x - bird_rect.x, self.top_rect.y - bird_rect.y)
        bottom_offset = (self.bottom_rect.x - bird_rect.x, self.bottom_rect.y - bird_rect.y)

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or t_point:
            return True
        return False

    def is_off_screen(self):
        return self.top_rect.right < 0


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("OOP Flappy Clone")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 40)

        bg_original = pygame.image.load('Sprites/bg.png').convert_alpha()
        bg_height = HEIGHT
        bg_width = int(bg_original.get_width() * (bg_height / bg_original.get_height()))
        self.bg_img = pygame.transform.scale(bg_original, (bg_width, bg_height))

        ground_original = pygame.image.load('Sprites/ground.png').convert_alpha()
        ground_height = HEIGHT - GROUND_Y
        ground_width = int(ground_original.get_width() * (ground_height / ground_original.get_height()))
        self.ground_img = pygame.transform.scale(ground_original, (ground_width, ground_height))

        self.ground_width = self.ground_img.get_width()
        self.bg_width = self.bg_img.get_width()

        # Dynamically calculate how many copies needed to draw to cover the screen entirely
        self.bg_copies = math.ceil(WIDTH / self.bg_width) + 1
        self.ground_copies = math.ceil(WIDTH / self.ground_width) + 1

        self.pipe_spawn_delay = 1400  
        self.reset_game()

    def reset_game(self):
        self.bird = Bird()
        self.pipes = []
        self.score = 0
        self.game_over = False
        self.last_pipe_time = pygame.time.get_ticks()
        self.ground_scroll = 0
        self.bg_scroll = 0
        self.scroll_speed = 3
        self.bg_scroll_speed = 1

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.game_over:
                        self.reset_game()
                    else:
                        self.bird.flap()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    def update(self):
        if self.game_over:
            return

        self.bird.update()

        self.ground_scroll -= self.scroll_speed
        if self.ground_scroll <= -self.ground_width:
             self.ground_scroll += self.ground_width

        self.bg_scroll -= self.bg_scroll_speed
        if self.bg_scroll <= -self.bg_width:
             self.bg_scroll += self.bg_width

        bounds_check = self.bird.check_bounds()
        if bounds_check:
            if bounds_check == "Sky":
                self.game_over = True
            else:
                self.bird.flap() 

        now = pygame.time.get_ticks()
        if now - self.last_pipe_time > self.pipe_spawn_delay:
            self.pipes.append(PipePair(WIDTH))
            self.last_pipe_time = now

        for pipe in self.pipes:
            pipe.update()

            if pipe.collides_with(self.bird.rect):
                self.game_over = True

            if not pipe.passed and pipe.top_rect.right < self.bird.rect.left:
                pipe.passed = True
                self.score += 1

        self.pipes = [p for p in self.pipes if not p.is_off_screen()]

    def draw(self):
        self.screen.fill((135, 206, 235))

        # Draw enough copies to completely cover the screen regardless of width
        for i in range(self.bg_copies):
            self.screen.blit(self.bg_img, (self.bg_scroll + i * self.bg_width, 0))

        for pipe in self.pipes:
            pipe.draw(self.screen)

        for i in range(self.ground_copies):
            self.screen.blit(self.ground_img, (self.ground_scroll + i * self.ground_width, GROUND_Y))

        self.screen.blit(self.bird.image, self.bird.rect)

        score_text = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_text, (10, 10))

        if self.game_over:
            msg = self.font.render("Game Over! Space to restart", True, TEXT_COLOR)
            self.screen.blit(msg, (15, HEIGHT // 2 - 20))

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS + self.score)

if __name__ == "__main__":
    game = Game()
    game.run()