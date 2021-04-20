import pygame, random
from pygame.math import Vector2 as vec

class ParticleSystem:

    def __init__(self, pos, vel, reduction_rate, size, num, color, spread=vec(5, 5)):
        self.pos = pos
        self.vel = vel
        self.radius = size
        self.reduction_rate = reduction_rate
        self.color = pygame.Color(*color)
        self.num = num
        self.particles = []
        self.spread = spread
        self.image = pygame.Surface((int(self.radius.x*2), int(self.radius.y*2))).convert_alpha()
        # self.image.set_colorkey((0, 0, 0))
        # format -> [pos, size, vel, ded or alive]

    def spawn(self):
        # format -> [pos, size, vel, ded or alive]
        for i in range(self.num):
            p = vec(self.pos.x + random.randint(-self.spread.x, self.spread.x), self.pos.y + random.randint(-self.spread.x, self.spread.y))
            # do = vec(self.pos.x - p.x, self.pos.y - p.y)
            s = vec(random.randint(2, self.radius.x), random.randint(2, self.radius.y))
            self.particles.append([p, s, 'alive'])

    def update(self):
        # surf_rect = surf.get_rect()
        for particle in self.particles:
            # if surf_rect.collidepoint(particle[0].x - scroll.x, particle[0].y - scroll.y):
            if particle[2] == "alive":  ## only update if the particle is alive
                particle[0] += self.vel * random.random()  ## updating position
                particle[1].x -= self.reduction_rate  ## updating(actually reducing) radius
                particle[1].y -= self.reduction_rate  ## updating(actually reducing) radius
                if particle[1].x <= 0 or particle[1].y <= 0:
                    particle[2] = "ded"  ## declaring it ded once it's lifetime is over :P
            else:
                self.particles.remove(particle)  ## removing the particle from the list... RIP particle

    def draw(self, surf, scroll, lerp_color=(255, 255, 255), flags=pygame.BLEND_RGBA_ADD):
        surf_rect = surf.get_rect()
        surf_rect.inflate(100, 100)
        for particle in self.particles:
            # if surf_rect.collidepoint(particle[0].x - scroll.x, particle[0].y - scroll.y):
            if particle[2] == "alive":  ## only draw if it is alive
                self.image = pygame.Surface((int(particle[1].x*2), int(particle[1].x*2))).convert()
                pygame.draw.circle(self.image, self.color.lerp(lerp_color, random.random()), (particle[1].x, particle[1].x), particle[1].x)
                self.image.set_colorkey((0, 0, 0))
                surf.blit(self.image, (particle[0].x - scroll.x, particle[0].y - scroll.y), special_flags=flags)
            else:
                self.particles.remove(particle)  ## removing the particle from the list or do i say, RIP particle xD
