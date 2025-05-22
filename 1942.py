import pygame
import random
import requests
import sys
import math
from enum import Enum

# Initialisierung
pygame.init()
screen_width = 800
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("1942: Shadow Wing - Occult War")                                        
clock = pygame.time.Clock()

# --- ENUM für Level-Status ---
class LevelState(Enum):
    RUNNING = 1
    BOSS_FIGHT = 2
    COMPLETED = 3

# --- Grafiken laden ---
def load_image(path, scale=None, flip=False):
    img = pygame.image.load(path).convert_alpha()
    if flip:
        img = pygame.transform.flip(img, False, True)
    return pygame.transform.scale(img, scale) if scale else img

# Hintergründe
BG_LEVELS = {
    1: load_image("images/level1.png", (screen_width, screen_height)),
    2: load_image("images/level2.png", (screen_width, screen_height)),
    3: load_image("images/level3.png", (screen_width, screen_height)),
    4: load_image("images/level3.png", (screen_width, screen_height)),
    5: load_image("images/level3.png", (screen_width, screen_height))
}

# Sprites
PLAYER_IMG = load_image("images/player.png", (80, 80))
BULLET_IMG = load_image("images/bullet.png", (5, 15))
ENEMY_IMGS = {
    "normal": load_image("images/enemy.png", (50, 50), flip=True),
}
BOSS_IMGS = {
    1: load_image("images/enemy.png", (150, 150), flip=True),
    2: load_image("images/enemy.png", (180, 180), flip=True),
    3: load_image("images/enemy.png", (200, 100), flip=True),
    4: load_image("images/enemy.png", (120, 200), flip=True),
    5: load_image("images/enemy.png", (250, 250), flip=True)
}

# --- Story-Texte pro Level ---
LEVEL_STORIES = {
    1: "MISSION 1: ÄRMELKANAL\nGeisterjäger tauchen im Nebel auf!\nZerstöre die Nazi-Nebelgeneratoren.",
    2: "MISSION 2: STALINGRAD\nBlutmond-Ritual erwacht Tote!\nStoppe den Schwarzen Mönch.",
    3: "MISSION 3: TRUK-LAGUNE\nJapanische Seelensteine rufen Yōkai.\nVersenke das Geisterschiff!",
    4: "MISSION 4: PEENEMÜNDE\nV2-Raketen mit Seelenenergie.\nSpreng die Höllenmaschine!",
    5: "FINAL MISSION: ALPENFESTUNG\nGötterblitz aktiviert!\nVernichte den Dämonengeneral!"
}

# --- Klassen ---
class Explosion(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        self.image = load_image("images/explosion.png", (50, 50))
        self.rect = self.image.get_rect(center=center)
        self.lifetime = 200
        self.created = pygame.time.get_ticks()

    def update(self):
        if pygame.time.get_ticks() - self.created > self.lifetime:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = PLAYER_IMG
        self.rect = self.image.get_rect(center=(screen_width//2, screen_height - 60))
        self.hitbox = self.rect.inflate(-30, -30)  # Hitbox 30px kleiner
        self.speed = 5
        self.health = 3
        self.max_health = 5
        self.shoot_delay = 150  # Schnellere Feuerrate
        self.last_shot = 0
        self.shooting = False  # Für Dauerfeuer


    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0: 
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < screen_width: 
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0: 
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < screen_height: 
            self.rect.y += self.speed
        self.hitbox.center = self.rect.center
        

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)
        bullet_size = (20, 30)  # Größere Schüsse

        offsets = [-20, -8, 8, 20]  # Positionen relativ zur Mitte
        for offset in offsets:
            bullet = Bullet(self.rect.centerx + offset, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = BULLET_IMG
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = -6
        self.hitbox = self.rect.inflate(-3, -3)


    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0: self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, player, formation=None):
        super().__init__()
        self.type = "normal"
        self.image = ENEMY_IMGS[self.type]
        self.rect = self.image.get_rect()
        
        self.hitbox = self.rect.inflate(-10, -10)
        self.player = player
        self.speed = random.uniform(0.5, 1.5)
        self.shoot_delay = random.randint(5000, 8000)  # Langsamere Schussfrequenz
        self.angle = 0
        self.health = 1
        
        # Initialisierungsposition
        spawn_side = random.choice(["top", "left", "right", "bottom"])
        if spawn_side == "top":
            self.rect.center = (random.randint(0, screen_width), random.randint(-100, -50))
        elif spawn_side == "bottom":
            self.rect.center = (random.randint(0, screen_width), random.randint(screen_height+50, screen_height+100))
        elif spawn_side == "left":
            self.rect.center = (random.randint(-100, -50), random.randint(0, screen_height))
        else:
            self.rect.center = (random.randint(screen_width+50, screen_width+100), random.randint(0, screen_height))
            
        # Bewegungsmuster
        self.movement_pattern = random.choice(["dive", "strafe", "circle"])
        self.last_shot = pygame.time.get_ticks()
        self.shoot_delay = random.randint(1500, 3000)

    def update(self):
        # Bewegungsmuster
        if self.movement_pattern == "dive":
            self.dive_attack()
        elif self.movement_pattern == "strafe":
            self.strafe_movement()
        else:
            self.circle_movement()
            
        # Schießen
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now

        # Hitbox aktualisieren
        self.hitbox.center = self.rect.center

        self.rect.y += self.speed

        # Entferne Gegner, wenn sie weit außerhalb des Bildschirms sind
        if (self.rect.top > screen_height + 100 or 
            self.rect.bottom < -100 or 
            self.rect.left > screen_width + 100 or 
            self.rect.right < -100):
            self.kill()

    def dive_attack(self):
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)
        if distance != 0:
            dx /= distance
            dy /= distance
        self.rect.x += dx * self.speed * 1.5
        self.rect.y += dy * self.speed * 1.5

    def strafe_movement(self):
        self.rect.x += math.sin(self.angle) * 3
        self.rect.y += self.speed
        self.angle += 0.1

    def circle_movement(self):
        self.rect.x += math.cos(self.angle) * 3
        self.rect.y += math.sin(self.angle) * 2
        self.angle += 0.05

    def shoot(self):
        bullet = EnemyBullet(self.rect.centerx, self.rect.bottom)
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((4, 15))  # Kleinere Schüsse
        self.image.fill((255, 50, 50))
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = self.rect.inflate(-2, -2)
        self.speed = 4
        

    def update(self):
        self.rect.y += self.speed
        self.hitbox.center = self.rect.center
        if self.rect.top > screen_height:
            self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.level = level
        self.image = BOSS_IMGS[level]
        self.rect = self.image.get_rect(center=(screen_width//2, 100))
        self.hitbox = self.rect.inflate(-50, -50)
        self.health = 30 + (level * 10)
        self.direction = 1
        self.shoot_delay = 1000
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        self.rect.x += self.direction * (3 + self.level // 2)
        if self.rect.left <= 0 or self.rect.right >= screen_width:
            self.direction *= -1
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now

    def shoot(self):
        for angle in range(-30, 31, 15):
            bullet = BossBullet(self.rect.centerx, self.rect.bottom, angle)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

class BossBullet(EnemyBullet):
    def __init__(self, x, y, angle):
        super().__init__(x, y)
        self.image = pygame.Surface((6, 20))
        self.image.fill((255, 0, 100))
        self.angle = math.radians(angle)
        self.speed = 5

    def update(self):
        self.rect.x += math.cos(self.angle) * self.speed
        self.rect.y += math.sin(self.angle) * self.speed
        self.hitbox.center = self.rect.center
        if self.rect.top > screen_height:
            self.kill()

# --- Level-Logik ---
class LevelManager:
    def __init__(self, player):
        self.current_level = 1
        self.state = LevelState.RUNNING
        self.boss = None
        self.kills_required = 15
        self.enemy_spawn_timer = 0
        self.spawn_delay = 2500  # 2.5 Sekunden zwischen Wellen
        self.player = player
        self.wave_count = 0
        self.max_enemies = 6 # Maximale Gegner auf dem Screen
        self.current_enemies = 0

    def spawn_enemies(self):
        now = pygame.time.get_ticks()
        if len(enemies) >= 6:
            return
        if now - self.enemy_spawn_timer > self.spawn_delay:
            # Verschiedene Formationen
            formation = random.choice(["line", "triangle", "random_cluster"])
            enemies_to_spawn = []
            
            if formation == "line":
                for i in range(5):
                    enemy = Enemy(self.player)
                    enemy.rect.center = (200 + i*100, -50 - i*50)
                    enemies_to_spawn.append(enemy)
            elif formation == "triangle":
                positions = [(400, -50), (300, -100), (500, -100), (200, -150), (600, -150)]
                for pos in positions:
                    enemy = Enemy(self.player)
                    enemy.rect.center = pos
                    enemies_to_spawn.append(enemy)
            else:
                for _ in range(random.randint(3, 6)):
                    enemy = Enemy(self.player)
                    enemies_to_spawn.append(enemy)
            
            for enemy in enemies_to_spawn:
                all_sprites.add(enemy)
                enemies.add(enemy)
            
            self.wave_count += 1
            if self.wave_count % 3 == 0:
                self.spawn_delay = max(500, self.spawn_delay - 100)
            
            self.enemy_spawn_timer = now

    def start_boss_fight(self):
        self.boss = Boss(self.current_level)
        all_sprites.add(self.boss)
        enemies.add(self.boss)
        self.state = LevelState.BOSS_FIGHT

    def next_level(self):
        self.current_level += 1
        self.state = LevelState.RUNNING
        self.kills_required = 15 + (self.current_level * 3)
        self.spawn_delay = 1000 - (self.current_level * 50)
        self.wave_count = 0
    
    def spawn_wave(self):
        now = pygame.time.get_ticks()
        if now - self.last_spawn > self.spawn_delay and self.current_enemies < self.max_enemies:
            spawn_count = min(2, self.max_enemies - self.current_enemies)  # Max 2 neue Gegner
            for _ in range(spawn_count):
                enemy = Enemy(self.player)
                all_sprites.add(enemy)
                enemies.add(enemy)
                self.current_enemies += 1
            self.last_spawn = now

# --- Spielzustände ---
def show_story_screen(level):
    screen.blit(BG_LEVELS[level], (0, 0))
    font_large = pygame.font.SysFont("arial", 48, bold=True)
    font_small = pygame.font.SysFont("arial", 24)
    
    title = font_large.render(LEVEL_STORIES[level].split("\n")[0], True, (255, 255, 255))
    line1 = font_small.render(LEVEL_STORIES[level].split("\n")[1], True, (255, 255, 255))
    line2 = font_small.render(LEVEL_STORIES[level].split("\n")[2], True, (255, 255, 255))
    
    screen.blit(title, title.get_rect(center=(screen_width//2, 200)))
    screen.blit(line1, line1.get_rect(center=(screen_width//2, 300)))
    screen.blit(line2, line2.get_rect(center=(screen_width//2, 350)))
    
    pygame.display.flip()
    pygame.time.wait(3000)

# --- Hauptspiel ---
def main_game():
    global all_sprites, enemies, bullets, enemy_bullets
    
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    
    player = Player()
    all_sprites.add(player)
    
    level_manager = LevelManager(player)
    
    score = 0
    kills = 0
    font = pygame.font.SysFont("arial", 24)
    
    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: 
                    running = False
                if event.key == pygame.K_SPACE: 
                    player.shoot()

        screen.blit(BG_LEVELS[level_manager.current_level], (0, 0))
        
        if level_manager.state == LevelState.RUNNING:
            level_manager.spawn_enemies()
            all_sprites.update()
            
            # Kollisionen
            for hit in pygame.sprite.groupcollide(enemies, bullets, False, True,
                                                collided=lambda x,y: x.hitbox.colliderect(y.rect)):
                hit.health -= 1
                if hit.health <= 0:
                    explosion = Explosion(hit.rect.center)
                    all_sprites.add(explosion)
                    hit.kill()
                    kills += 1
                    score += 10
            
            if kills >= level_manager.kills_required:
                level_manager.start_boss_fight()
                kills = 0
            
        elif level_manager.state == LevelState.BOSS_FIGHT:
            all_sprites.update()
            
              
            if level_manager.boss:
                boss_hits = pygame.sprite.spritecollide(
                    level_manager.boss, bullets, True,
                    collided=lambda x,y: x.hitbox.colliderect(y.rect)
                )
                for _ in boss_hits:
                    level_manager.boss.health -= 1
                    score += 5
                    if level_manager.boss.health <= 0:
                        level_manager.boss.kill()
                        level_manager.boss = None
                        if level_manager.current_level < 5:
                            show_story_screen(level_manager.current_level + 1)
                            level_manager.next_level()
                        else:
                            running = False
                for hit in pygame.sprite.groupcollide(enemies, bullets, False, True,
                                          collided=lambda x,y: x.hitbox.colliderect(y.rect)):
                    if isinstance(hit, Boss):
                        continue  # Boss wird separat behandelt
                hit.health -= 1
                if hit.health <= 0:
                    explosion = Explosion(hit.rect.center)
                    all_sprites.add(explosion)
                    hit.kill()
                    score += 10
        
        # Spieler-Kollisionen
        player_hit = pygame.sprite.spritecollide(
            player, enemies, True,
            collided=lambda x,y: x.hitbox.colliderect(y.hitbox)
        ) or pygame.sprite.spritecollide(
            player, enemy_bullets, True,
            collided=lambda x,y: x.hitbox.colliderect(y.hitbox)
        )
        
        if player_hit:
            player.health -= 1
            if player.health <= 0:
                running = False
        
        # Zeichnen
         
        all_sprites.draw(screen)
        
        # UI
        screen.blit(font.render(f"Level: {level_manager.current_level}/5", True, (255, 255, 255)), (10, 10))
        screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (10, 40))
        screen.blit(font.render(f"Leben: {player.health}/{player.max_health}", True, (255, 255, 255)), (10, 70))
        
        if level_manager.state == LevelState.RUNNING:
            screen.blit(font.render(f"Gegner: {kills}/{level_manager.kills_required}", True, (255, 255, 255)), (10, 100))
        elif level_manager.state == LevelState.BOSS_FIGHT and level_manager.boss:
            screen.blit(font.render(f"BOSS: {level_manager.boss.health} HP", True, (255, 0, 0)), (10, 100))
        
        pygame.display.flip()
    
    show_game_over(score)
    submit_score_to_server(score)

def show_game_over(score):
    screen.fill((0, 0, 0))
    font = pygame.font.SysFont("arial", 48)
    text = font.render(f"GAME OVER - Score: {score}", True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=(screen_width//2, screen_height//2)))
    pygame.display.flip()
    pygame.time.wait(3000)



def submit_score_to_server(score):
    name = input("Name für Highscore: ")  # Im Terminal eingeben
    try:
        response = requests.post("http://localhost:5000/submit_score", json={
            "name": name,
            "score": score
        })
        if response.status_code == 200:
            print("Score erfolgreich gesendet.")
        else:
            print("Fehler beim Senden:", response.text)
    except Exception as e:
        print("Verbindung zum Server fehlgeschlagen:", e)


if __name__ == "__main__":
    show_story_screen(1)
    main_game()
    pygame.quit()
    sys.exit()