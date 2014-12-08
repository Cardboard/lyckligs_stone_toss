import os
import sys
import math
import random

import pygame

class Opossum:
    def __init__(self, x, y, img='lycklig.png'):
        self.image = pygame.image.load(os.path.join('graphics', img))
        self.rect = self.image.get_rect()
        # (def)ault unrotated arm image
        self.arm_def = pygame.image.load(os.path.join('graphics', 'arm.png'))
        self.arm = self.arm_def
        self.armrect = self.arm.get_rect()

        self.rect.x = x
        self.rect.y = y

        self.armrect.x = 136 - self.armrect.width/2
        self.armrect.y = 381 - self.armrect.height/2

        self.speed = 0.0
        self.randomize_speed()
        self.angle = 180.0

    # return position of the hand for the game to launch the stone from
    def get_hand_pos(self):
        r = self.armrect.width / 2
        w = r * math.sin(math.radians(self.angle + 90.0)) # 90.0 is a magic number, basically
        h = r * math.cos(math.radians(self.angle + 90.0))
        w -= 10
        h -= 10
        return (self.armrect.centerx + w, self.armrect.centery + h)

    # randomize the arm speed after each throw
    def randomize_speed(self):
        self.speed = random.uniform(30.0, 50.0)
    
    # spin the hand
    def update(self, dt, throws):
        if throws != 0 or not(self.angle >= 260 and self.angle <= 270):
            self.angle += dt * self.speed * -1
            self.angle = self.angle % 360.0
            self.arm = pygame.transform.rotate(self.arm_def, self.angle)

    def draw_arm(self, screen):
        dx = self.arm.get_rect().width - self.armrect.width
        dy = self.arm.get_rect().height - self.armrect.height
        fixed_rect = pygame.Rect(self.armrect)
        fixed_rect.x -= dx/2
        fixed_rect.y -= dy/2
        screen.blit(self.arm, fixed_rect)


class Stone:
    def __init__(self, img='stone.png'):
        self.image = pygame.image.load(os.path.join('graphics', img))
        self.rect = self.image.get_rect()
        self.vspeed = -1
        self.hspeed = -1
        self.gravity = 9.8 
        self.held = False
        self.thrown = False
        self.scored = False

    def update(self, dt, ground, bucket, game, player):
        if self.held:
            self.rect.x, self.rect.y = player.get_hand_pos()
        elif self.vspeed == 0.0 and self.hspeed == 0.0 and self.thrown and self.rect.bottom == ground and not(self.scored):
            self.dist = abs((bucket.rect.left - self.rect.right) / 10 + 1)
        else:
            if self.vspeed != -1:
                self.vspeed += (dt)
                self.rect.y += self.vspeed
            if self.hspeed != -1:
                self.rect.x += self.hspeed
            # hit ground
            if self.rect.bottom >= ground:
                self.rect.bottom = ground
                if self.vspeed <= 2.0:
                    self.vspeed = 0.0
                else:
                    self.vspeed = -1.0 * self.vspeed * 0.4
                self.hspeed -= 1.0
                self.hspeed = max(self.hspeed, 0.0)
            # hit bucket
            if self.rect.colliderect(bucket):
                game.sfx_hit.play()
                # hit left side of bucket
                if self.rect.left <= bucket.rect.left:
                    bucket.hit()
                    self.hspeed -= self.hspeed/2.0
                    self.hspeed = -1.0 * self.hspeed
                # land inside bucket
                else:
                    self.scored = True
                    self.vspeed = 0.0
                    self.hspeed = 0.0
                    self.rect.x = -50
                    self.dist = 0

class Bucket:
    def __init__(self):
        # 1:untouched, 2:hit once, 3:hit twice, gg handle
        self.image1 = pygame.image.load(os.path.join('graphics', 'bucket1.png'))
        self.rect1 = self.image1.get_rect()
        self.image2 = pygame.image.load(os.path.join('graphics', 'bucket2.png'))
        self.rect2 = self.image2.get_rect()
        self.image3 = pygame.image.load(os.path.join('graphics', 'bucket3.png'))
        self.rect3 = self.image3.get_rect()
        
        # set starting image/rect
        self.image = self.image1
        self.rect = self.rect1
        self.x = 650
        self.y = 450
        self.rect.center = (self.x, self.y)

        self.hits = 0

    def reset(self):
        self.hits = 0
        self.image = self.image1
        self.rect = self.rect1

    def hit(self):
        self.hits += 1
        x = self.rect.right
        y = self.rect.top

        if self.hits == 1:
            self.image = self.image2
            self.rect = self.rect2
            self.rect.right = x
            self.rect.top = y

        elif self.hits == 2:
            self.image = self.image3
            self.rect = self.rect3
            self.rect.right = x
            self.rect.top = y


class Game:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Lycklig's Stone Toss")
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.ground = 500

        # background
        self.bg = pygame.image.load(os.path.join('graphics', 'bg.png'))

        # title
        self.title = pygame.image.load(os.path.join('graphics', 'lyckligsstonetoss.png'))

        # player
        self.player = Opossum(10, 250)

        # stones
        self.throws = 5
        self.stones = [Stone() for i in range(self.throws)]
        self.reset_stones()

        # bucket
        self.bucket = Bucket()

        # score
        self.score_closest = 'n/a'
        self.score_total = -1

        # font
        pygame.font.init()
        self.font_size = 14
        self.font = pygame.font.Font('Biko_Regular.otf', self.font_size)

        # audio
        pygame.mixer.init()
        pygame.mixer.music.load(os.path.join('audio', 'lyckligs_bucket_throw.ogg'))
        pygame.mixer.music.play(-1)

        self.sfx_hit = pygame.mixer.Sound(os.path.join('audio', 'hit.ogg'))
        self.sfx_hit.set_volume(0.6)
        self.sfx_throw = pygame.mixer.Sound(os.path.join('audio', 'throw2.ogg'))
        self.sfx_throw.set_volume(0.3)


    def reset(self):
        # reset scores
        self.score_closest = 'n/a'
        self.score_total = -1
        # reset stones
        self.throws = 5
        self.reset_stones()
        # reset bucket
        self.bucket.reset()

    def reset_stones(self):
        for stone in self.stones:
            stone.rect.x = self.player.rect.x + random.randint(-5, 200)
            stone.rect.y = self.player.rect.bottom + random.randint(10, 75)
            stone.vspeed = -1
            stone.hspeed = -1
            stone.dist = 0
            stone.held = False
            stone.thrown = False
            stone.scored = False

        self.stones[self.throws-1].held = True

    def throw(self):
        if self.throws > 0:
            self.sfx_throw.play()
            self.throws -= 1
            self.stones[self.throws].held = False
            
            angle = math.radians(self.player.angle - 45.0)
            speed = self.player.speed / 5.0
            self.stones[self.throws].vspeed = -1 * speed * math.sin(angle)
            self.stones[self.throws].hspeed = speed * math.cos(angle) 

            self.stones[self.throws].thrown = True

            if self.throws > 0:
                self.stones[self.throws-1].held = True

            self.player.randomize_speed()

            
    def draw(self):
        # draw bg
        self.screen.blit(self.bg, (0,0))

        # draw title 
        self.screen.blit(self.title, (20, 20))

        # draw player & arm
        self.screen.blit(self.player.image, self.player.rect)
        self.player.draw_arm(self.screen)

        # draw bucket
        self.screen.blit(self.bucket.image, self.bucket.rect)
        
        # draw stones
        for stone in self.stones:
            self.screen.blit(stone.image, stone.rect)

        # draw UI
        text_info = self.font.render('space: throw,   esc: quit,   r: restart', 1, (50, 50, 50))
        if self.score_closest == 'n/a':
            text_closest = self.font.render('closest: n/a', 1, (50, 50, 50))
        else:
            text_closest = self.font.render('closest: {}'.format(self.score_closest), 1, (50, 50, 50))
        text_total = self.font.render('total: {}'.format(self.score_total), 1, (50, 50, 50))
        self.screen.blit(text_info, (25, 125))
        self.screen.blit(text_closest, (25, 140))
        self.screen.blit(text_total, (25, 155))

        # update display
        pygame.display.update()

    def main(self):
        while True:
            dt = self.clock.tick(self.fps) / 100.0
            for event in pygame.event.get():
               # if event.type == pygame.MOUSEBUTTONDOWN:
               #     print(event.pos)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_SPACE:
                        self.throw()

                    if event.key == pygame.K_r:
                        self.reset()

            self.player.update(dt, self.throws)
            
            self.score_total = sum([stone.dist for stone in self.stones])
            
            #print([stone.scored for stone in self.stones])

            for stone in self.stones:
                stone.update(dt, self.ground, self.bucket, self, self.player)
                if stone.scored:
                    self.score_closest = 'inside!'
                if stone.dist != 0 and self.score_closest != 'inside!':
                    if (stone.dist < self.score_closest or self.score_closest == 'n/a'):
                        self.score_closest = stone.dist
            #print('closest\t{}\ntotal\t{}'.format(self.score_closest,self.score_total))

            self.draw()


if __name__ == '__main__':
    game = Game()
    game.main()
