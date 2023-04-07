import pygame

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
SPAWN_ENEMY_EVENT = pygame.USEREVENT + 1
# Spawn an enemy every 1000 milliseconds (1 second)
pygame.time.set_timer(SPAWN_ENEMY_EVENT, 200)


# Colors
WHITE = (255, 255, 255)
ENEMY_COLOR = (200, 50, 50)
TOWER_COLOR = (50, 50, 200)
SHADOW_OFFSET = (2, 2)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, path, speed):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        pygame.draw.circle(self.image, ENEMY_COLOR, (10, 10), 10)
        self.rect = self.image.get_rect()
        self.path = path
        self.speed = speed
        self.current_point = 0
        self.rect.topleft = path[self.current_point]

    def update(self):
        if self.current_point + 1 < len(self.path):
            target_x, target_y = self.path[self.current_point + 1]
            current_x, current_y = self.rect.topleft

            dx, dy = target_x - current_x, target_y - current_y
            distance = max(abs(dx), abs(dy))

            if distance > 0:
                move_x = self.speed * dx / distance
                move_y = self.speed * dy / distance
                self.rect.x += move_x
                self.rect.y += move_y

                if dx * (self.rect.x - target_x) + dy * (self.rect.y - target_y) >= 0:
                    self.current_point += 1


class Tower(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        pygame.draw.rect(self.image, TOWER_COLOR, (0, 0, 40, 40))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.attack_delay = 480  # Attack once per second
        self.last_attack_frame = 0

    def update(self, enemies, projectiles):
        if pygame.time.get_ticks() - self.last_attack_frame > self.attack_delay:
            target = find_target(self, enemies, 200, projectiles)

            if target:
                projectile = Projectile(
                    self.rect.centerx, self.rect.centery, target, 5)
                projectiles.add(projectile)

                self.last_attack_frame = pygame.time.get_ticks()


def draw_shadow(screen, color, rect, offset, shape='rect'):
    shadow_rect = rect.copy()
    shadow_rect.x += offset[0]
    shadow_rect.y += offset[1]
    if shape == 'rect':
        pygame.draw.rect(screen, color, shadow_rect)
    elif shape == 'circle':
        pygame.draw.circle(screen, color, shadow_rect.center, rect.width // 2)


def spawn_enemies(path, speed, count, spawn_delay, enemies):
    for i in range(count):
        enemy = Enemy(path, speed)
        enemies.add(enemy)
        pygame.time.delay(spawn_delay)


def create_tower(x, y):
    tower = Tower(0, 0)  # Initialize with (0, 0)
    tower.rect.center = (x, y)  # Set the center to the mouse cursor position
    return tower


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tower Defense")
    clock = pygame.time.Clock()

    # Enemy path
    path = [(100, 100), (700, 100), (700, 500), (100, 500), (100, 100)]

    # Create tower
    tower = Tower(350, 250)

    # Create sprite groups
    enemies = pygame.sprite.Group()
    towers = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    towers.add(tower)

    # Set up enemy spawn timer
    spawn_delay = 100
    pygame.time.set_timer(SPAWN_ENEMY_EVENT, spawn_delay)

    # Main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == SPAWN_ENEMY_EVENT:
                enemy = Enemy(path, 2)
                enemies.add(enemy)
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos

                # Left mouse button adds a tower
                if event.button == 1:
                    new_tower = create_tower(x, y)
                    towers.add(new_tower)

                # Right mouse button removes a tower
                elif event.button == 3:
                    for tower in towers:
                        if tower.rect.collidepoint(x, y):
                            towers.remove(tower)
                            break

        enemies.update()

        for tower in towers:
            tower.update(enemies, projectiles)

        projectiles.update()

        screen.fill(WHITE)

        for tower in towers:
            draw_shadow(screen, (0, 0, 0), tower.rect, SHADOW_OFFSET)
            screen.blit(tower.image, tower.rect)

        for enemy in enemies:
            draw_shadow(screen, (0, 0, 0), enemy.rect,
                        SHADOW_OFFSET, shape='circle')
            screen.blit(enemy.image, enemy.rect)

        for projectile in projectiles:
            draw_shadow(screen, (0, 0, 0), projectile.rect,
                        SHADOW_OFFSET, shape='circle')
            screen.blit(projectile.image, projectile.rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

# New class for projectiles


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target, speed):
        super().__init__()
        self.image = pygame.Surface((6, 6))
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        pygame.draw.circle(self.image, (50, 200, 50), (3, 3), 3)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.target = target
        self.speed = speed

    def update(self):
        if self.target and self.target.alive():
            dx, dy = self.target.rect.centerx - \
                self.rect.centerx, self.target.rect.centery - self.rect.centery
            distance = max(abs(dx), abs(dy))

            if distance > 0:
                move_x = self.speed * dx / distance
                move_y = self.speed * dy / distance
                self.rect.x += move_x
                self.rect.y += move_y

                if self.rect.colliderect(self.target.rect):
                    self.target.kill()
                    self.kill()
        else:
            self.kill()


def find_target(tower, enemies, range, projectiles):
    closest_distance = range ** 2
    closest_enemy = None

    for enemy in enemies:
        dx, dy = tower.rect.centerx - \
            enemy.rect.centerx, tower.rect.centery - enemy.rect.centery
        distance_sq = dx ** 2 + dy ** 2

        if distance_sq < closest_distance:
            closest_distance = distance_sq
            closest_enemy = enemy

    return closest_enemy


# Update the main game loop
if __name__ == "__main__":
    main()
