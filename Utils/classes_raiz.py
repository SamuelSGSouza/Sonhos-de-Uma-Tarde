
from abc import ABC, abstractmethod
from sprites import *
from settings import *
from Utils.effects import FrozenEffect

class Arrow(pygame.sprite.Sprite):
    def __init__(self, *groups, initial_pos, direction, angulo, atirador):
        super().__init__(*groups)
        self.image = pygame.transform.rotate(arrow_surf, angulo)
        self.rect = self.image.get_rect(center = initial_pos)
        self.hitbox = self.rect.copy()
        self.hitbox.width = self.hitbox.width//4
        self.hitbox.height = self.hitbox.height//4
        self.direction = direction
        self.is_getable = False
        self.speed = 700
        self.collidiu = False
        self.damage = 25
        self.shooter = atirador
        self.attack_damage = 25
        self.position_vector = pygame.Vector2
        self.player_sprite = self.shooter.player_sprite

    def update(self,dt):
        self.position_vector = pygame.Vector2(self.rect.center)
        if self.collidiu:
            return
        play_noise(self,self.shooter.arrow_sounds)
        self.move(dt)

        if self.rect.x > 6000 or self.rect.x <0:
            self.kill()

        if self.rect.y > 6000 or self.rect.y < 0:
            self.kill()

        

    def move(self, dt):
        self.direction = self.direction.normalize() if self.direction else self.direction

        hitbox = self.hitbox.copy()
        hitbox.x += dt * self.direction.x * self.speed
        hitbox.y += dt * self.direction.y * self.speed
        
        self.x_move_ok, self.y_move_ok = self.collisions()

        if self.x_move_ok:
            self.hitbox.x += dt * self.direction.x * self.speed
        if self.y_move_ok:
            self.hitbox.y += dt * self.direction.y * self.speed
            
        self.rect.center = self.hitbox.center

    def collisions(self,):
        chars_attacking = [char for char in self.groups()[0] if isinstance(char, Character) and char.attack_hitbox]
        for char in chars_attacking:
            if char.attack_hitbox.colliderect(self.rect):
                self.kill()
                self.collidiu=True
                return False, False
        hits = pygame.sprite.spritecollide(self, self.groups()[0], dokill=False)
        if hits:
            for sprite in hits:
                if not hasattr(sprite, "hitbox"):
                    continue
                if self.shooter == sprite:
                    continue
                if sprite in self.shooter.team_members:
                    continue
                    
                if self.hitbox.colliderect(sprite.hitbox):
                    if hasattr(sprite, "fixed_object"): #é um colision_sprite
                        self.collidiu = True
                        return False, False
                    
                    if isinstance(sprite, Character, ):
                        if sprite.is_dead:
                            continue
                        sprite.handle_damage(self.attack_damage,attacking_character=self.shooter)
                        self.kill()
                        self.collidiu=True
                        return False, False

        return True, True

class Snow:
    def __init__(self, screen_rect: pygame.Rect, flake_images, max_flakes=120):
        self.screen_rect = screen_rect
        # garante que tudo já está optimizado para a tela
        self.flake_images = [img.convert_alpha() for img in flake_images]
        self.flakes = []
        for _ in range(max_flakes):
            self.flakes.append(self._create_flake(start_random_y=True))
        
    def _create_flake(self, start_random_y=False):
        img = choice(self.flake_images)
        w, h = self.screen_rect.size

        x = randint(0, w)
        # pode nascer lá em cima ou espalhado verticalmente
        if start_random_y:
            y = randint(-h, 0)
        else:
            y = -img.get_height()

        speed_y = uniform(40, 120)   # queda
        drift_amp = uniform(5, 20)   # quanto balança pros lados
        drift_speed = uniform(0.5, 1.5)

        return {
            "img": img,
            "x": float(x),
            "y": float(y),
            "speed_y": speed_y,
            "drift_amp": drift_amp,
            "drift_speed": drift_speed,
            "base_x": float(x),
            "phase": uniform(0, 2 * pi),
        }

    def update(self, dt):
        # dt em segundos (clock.tick()/1000)
        t = pygame.time.get_ticks() / 1000.0
        bottom = self.screen_rect.bottom

        for f in self.flakes:
            f["y"] += f["speed_y"] * dt

            # drift horizontal bem simples com seno
            f["x"] = f["base_x"] + sin(t * f["drift_speed"] + f["phase"]) * f["drift_amp"]

            # se passou da tela, reaproveita floco
            if f["y"] > bottom:
                new_flake = self._create_flake(start_random_y=False)
                # reaproveita o dict, evita alocação
                f.update(new_flake)

    def draw(self, surface):
        for f in self.flakes:
            surface.blit(f["img"], (int(f["x"]), int(f["y"])))

class Light:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class LightingSystem:
    def __init__(self, screen_size, game_clock, light_sprite, light_radius=160, max_dark_alpha=200):
        self.overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
        self.game_clock = game_clock
        self.light_sprite = light_sprite
        self.light_radius = light_radius
        self.max_dark_alpha = max_dark_alpha
        self.lights: list[Light] = []

    def add_light(self, light: Light):
        self.lights.append(light)

    def clear_lights(self):
        self.lights.clear()

    def draw(self, screen):
        # 0.0 (noite escura) → 1.0 (dia claro)
        lf = self.game_clock.get_light_factor()

        # de noite: alpha alto; de dia: alpha baixo
        dark_alpha = int(self.max_dark_alpha * (1.0 - lf))

        # preenche tudo de preto com alpha (escuridão global)
        self.overlay.fill((0, 0, 0, dark_alpha))

        # para cada luz, "come" um pouco dessa escuridão
        for light in self.lights:
            x = int(light.x - self.light_radius)
            y = int(light.y - self.light_radius)

            self.overlay.blit(
                self.light_sprite,
                (x, y),
                special_flags=pygame.BLEND_RGBA_SUB  # subtrai alpha → clareia
            )

        # joga a overlay em cima da tela
        screen.blit(self.overlay, (0, 0))


        

class Character(pygame.sprite.Sprite):
    
    def __init__(self, *groups,collision_sprites:pygame.sprite.Group,creatures_sprites:pygame.sprite.Group, noise_intensity_on_walk:int=50, noise_intensity_on_attack:int=80, noise_intensity_on_run:int=70,
                personal_name = "Player", instinct_intensity_percent=12,
                max_hp:int = 100,life_regen_percent=1, attack_damage:int=10, 
                attack_delay:int= 1750, attack_duration:int = 2000,
                is_ranged=False, range_distance = 36,
                scale_on_attack_value=2, team_members=[], is_player=False):
        super().__init__(*groups, )
        self.specie = ""
        self.being_healed = False
        self.healing_character = None
        self.default_size = HDCS + HHDCS
        self.scale_on_attack = scale_on_attack_value
        #ACTIONS STATUS
        self.is_human = False
        self.is_running = False
        self.is_interacting = False
        self.is_chatting = False
        self.is_talking = False
        self.is_player = is_player
        self.is_blind = False
        self.is_invisible = False
        self.is_sleeping = False
        self.is_attacking = False
        self.is_handling_damage = False
        self.is_character = True
        self.is_dodging = False
        self.is_combating = False
        self.is_dying = False
        self.is_dead = False
        self.is_drinking = False
        self.is_frozen = False
        self.is_begging = False
        self.healing = False
        self.is_ranged = is_ranged
        self.range_distance = range_distance
        
        self.can_talk = False
        self.talk_options = ["respondendo","iniciando"]

        #kill_humans
        self.kill_humans = False
        self.kill_monsters = False
        self.kills = []

        self.water_sources = []
        self.position_vector = pygame.Vector2(0,0)
        # Delays
        self.call_senses_delay = 500
        self.drinking_delay = 5000
        self.interact_delay = 500
        self.attack_delay = attack_delay
        self.collision_delay = 0
        self.talk_delay = randint(25000, 50000)
        self.change_pov_delay = randint(1000, 2000)

        #init times
        init_time = pygame.time.get_ticks()
        self.last_called_senses_time = init_time
        self.last_interact_time = init_time
        self.last_attack_time = init_time
        self.last_collision  = init_time
        self.last_drink_time = init_time
        self.last_talk_time = init_time
        self.last_changed_pov = init_time
        self.last_regenered_hp = init_time
        self.last_mimetization = init_time
        self.last_step_time = init_time
        self.start_begging_time = init_time
        
        self.mimetization_delay = 15000
        self.begging_delay = 8000

        
        self.has_vision = True
        # self.vision_max_dist = vision_max_dist
        # self.vision_deg = vision_deg  # mantido para futura checagem angular (se quiser)
        self.has_hearing = True
        self.instinct_intensity = instinct_intensity_percent


        self.fixed_decided = False
        self.dodge_direction = pygame.Vector2()
        self.daytime = 0
        
        

        self.attack_hitbox = None
        
        self.attack_duration_ms = attack_duration
        
        self.attacking_character = None
        self.attack_hitbox_list = None

        self.speech_text = ""
        self.effects: list = []
        self.speed_multipliers: list[float] = []
        
        self.actions = ["Walk", "Idle", "Attack_1","Attack_2", "Run", "Dead", "Beg", "Sleep", "Hurt", "Beg", "Begging", "WakeUp"]
        self.action = "Walk"
        self.personal_name = personal_name

        # Atributos básicos
        self.original_speed = getattr(self, "original_speed", 100.0)
        self.max_hp = max_hp
        self.hp = self.max_hp
        self.life_regen_percent = life_regen_percent
        self.attack_damage = attack_damage
        self.direction = getattr(self, "direction", pygame.Vector2())
        self.running_speed_applied = False
        self.running_speed_multiplier = 1.2
        self.collision_sprites = collision_sprites
        self.creatures_sprites = creatures_sprites
        self.fixed_sprites = [sprite for sprite in collision_sprites if isinstance(sprite, CollisionSprites) and sprite.is_getable ==False]
        
        
        self.x_move_ok, self.y_move_ok = True, True

        # Knockback: posição do atacante no último hit (defina externamente)
        self.last_hit_from = None

        # Shake de tela (config simples)
        self.shake_duration_ms = 120
        self._shake_end_time = 0
        self._shake_intensity = 0.0

        #EFFECTS
        self.spacial_skill_blocked= False

        ##noises
        self.noise_intensities ={
            "Walk": noise_intensity_on_walk,
            "Run": noise_intensity_on_run,
            "Attack_1": noise_intensity_on_attack,
            "Attack_2": noise_intensity_on_attack,
        }
        

        #inventory
        self.inventory:list[Item] = []
        

        self.current_action = None
        self.dt = None
        self.seeing=""
        self.hearing=""
        self.percepting=""

        self.matriz_mapa = [[]]

        self.hurt_animation_duration = 200

        #basic needs
        self.thirst_percent = 50
        self.thirst_increase_rate = uniform(0.1,0.2)

        self.effects_on_damage = []

        self.team_members = team_members
        self.death_time = None
        self.delete_sprites_on_death = False
        self.respawnable = False
        self.encerrou_conversa = False
        self.talks = {
            "1": {  # Introdução
                "fala": "Não posso falar agora.",
                "respostas": {}
            },
        }
        self.current_id = "1"
        self.pontuacao = 0.0
        self.confiabilidades = { #Sendo 1 totalmente confiável e 0 totalmente odiado
            "HUMAN": 0,
            "SLIME": 0,
            "GHOST": 0,
            "ORC": 0,
            "GOLEM": 0,
            "GOBLIN": 0,
            "SAMMY": 100
        }
        self.player_sprite:pygame.sprite.Sprite = None

        self.attack_sounds = []
        self.arrow_sounds = []
        self.walk_sounds = []
        self.has_steps = False
        root_path = join(getcwd(), "Ecosystem", "Winter", "Steps")
        step_images = listdir(root_path)
        self.step_images = []
        for file in step_images:
            filepath = join(root_path, file)
            
            img = pygame.transform.rotozoom(pygame.image.load(filepath).convert_alpha(), 0, 2)
            self.step_images.append(img)

        self.use_center_on_attack = False

        self.specie_group = pygame.sprite.Group()

        self.last_step_sound = pygame.time.get_ticks()
        self.step_sound_delay = 0


        self.rota = []
        self.has_emblem = False
        self.spawn_points = [
            (5429,4233),
            (4748,4465),
            (3502,4505),
            (2911, 3922),
            (1780, 2610),
            (534, 3515),
            (765, 2650),
            (4197, 3582),
            (3229, 2667),
            (2266, 1742),
            (3107, 517),
        ]


        if not self.is_player:
            grupo = self.groups()[0]
            if hasattr(grupo, "world_matriz"):
                matriz_mundo = grupo.world_matriz
                self.locais_favoritos = []
                for _ in range(0,200):
                    x, y = randint(0, LARGURA_MAPA-200), randint(0, ALTURA_MAPA-200)
                    if matriz_mundo[x//GRID_SIZE][y//GRID_SIZE] != 1 and (x,y) not in self.locais_favoritos:
                        self.locais_favoritos.append((x,y))


    def _get_facing_dir(self) -> pygame.Vector2:
        d = self.direction
        if d.x != 0 or d.y != 0:
            try:
                return d.normalize()
            except ValueError:
                pass
        if self.state == "Front":
            return pygame.Vector2(0, 1)
        if self.state == "Back":
            return pygame.Vector2(0, -1)
        if self.state == "Left":
            return pygame.Vector2(-1, 0)
        return pygame.Vector2(1, 0)  # "Right" ou default

    def get_hour(self) -> int:
        hour = self.groups()[0].hour
        return hour

    # ---------------------------------------------------------
    # Constrói a lista de retângulos (FRect) à frente do monstro.
    # Retângulos AABB, baratos de checar, bons p/ broad-phase.
    # ---------------------------------------------------------
    def update_vision_hitboxes(self):
        if self.fixed_decided == False:
            if len(self.collision_sprites) > 0:
                self.fixed_decided = True
                self.fixed_sprites =[sprite for sprite in self.collision_sprites if isinstance(sprite, CollisionSprites) and sprite.is_getable ==False]
        facing = self._get_facing_dir()
        origin = pygame.Vector2(self.hitbox.center)

        self.vision_hitboxes.clear()
        step = self.vision_step
        base_w = self.vision_base_width
        spread = self.vision_spread_per_seg

        # Para manter AABB barato:
        # - Se olhando horizontalmente, cada segmento é um retângulo mais comprido no eixo X
        #   e vai “engordando” no eixo Y (largura).
        # - Se olhando verticalmente, análogo ao eixo Y.
        for i in range(1, self.vision_segments + 1):
            center = origin + facing * (i * step)
            widen = base_w + (i - 1) * spread

            if abs(facing.x) > 0:   # olhando p/ esquerda/direita
                rect_w = step       # comprimento do segmento
                rect_h = widen      # “abertura” (altura)
            else:                   # olhando p/ cima/baixo
                rect_w = widen
                rect_h = step

            r = pygame.FRect(0, 0, rect_w, rect_h)
            r.center = (center.x, center.y)

            for colission_box in self.fixed_sprites:
                if colission_box.rect.colliderect(r):
                    return
            self.vision_hitboxes.append(r)

    #SENSES
    def sensed_creature(self,):
        self.seeing = ""
        self.hearing = ""

        
        for creature in self.creatures_sprites:
            if creature.personal_name == self.personal_name:
                continue
            if creature == self:
                continue
            if creature.is_human == True:
                continue
            if creature.is_dead == True:
                continue
                
            if self.rect.colliderect(creature.rect):
                return creature

            if self.has_vision:
                    
                # Para manter a "leveza", a condição mais simples é a criatura estar visível
                # e dentro do alcance de visão.
                is_visible = getattr(creature, 'is_visible', True) # Assumindo True se não definido
                
                if is_visible:
                    for vh in self.vision_hitboxes:
                        if vh.colliderect(creature.hitbox):
                            self.seeing = f"seeing {creature.personal_name}"
                            return creature

            if self.has_hearing:
                if creature.is_making_noise:
                    creature_center = pygame.Vector2(creature.rect.center)
                    self_center = pygame.Vector2(self.rect.center)
                    dist = ( creature_center- self_center).length()
                    if dist <= creature.noise_intensity:
                        self.hearing = f"hearing {creature}"
                        return creature      

        return None

    ##Vision
    def can_see_target(monster, target, blockers: pygame.sprite.Group,
                   radius: float = 250.0,
                   fov_deg: float = 90.0,
                   step: float = 8.0,
                   rays: int = 3) -> bool:
        """
        Retorna True se o 'monster' puder ver o 'target'.
        Combina checagem de cone de visão (ângulo + raio)
        e raycast leve (obstáculos).

        Parâmetros:
            monster, target: Sprites com hitbox
            blockers: grupo de colisão (paredes, árvores, etc.)
            radius: distância máxima de visão
            fov_deg: abertura do cone (em graus)
            step: tamanho de passo do raycast
            rays: número de raios testados (centro + laterais)
        """
        origin = pygame.Vector2(monster.hitbox.center)
        to_target = pygame.Vector2(target.hitbox.center) - origin
        dist = to_target.length()
        if dist > radius:
            return False
        if dist == 0:
            return True

        # Vetor de direção do monstro (usando ângulo ou estado)
        angle = atan2(monster.direction.y, monster.direction.x)

        facing = pygame.Vector2(cos(angle), sin(angle))
        to_target_norm = to_target.normalize()
        dot = facing.dot(to_target_norm)
        if dot < cos(radians(fov_deg / 2)):
            return False  # fora do cone de visão

        # Pré-carrega retângulos para desempenho
        blocker_rects = [b.hitbox for b in blockers]

        # Gera raios central + laterais dentro do cone
        base_angle = atan2(facing.y, facing.x)
        half_spread = radians(fov_deg / 6)  # leve variação angular
        offsets = [0.0]
        if rays >= 3:
            offsets += [-half_spread, half_spread]
        elif rays == 5:
            offsets += [-half_spread, half_spread, -2*half_spread, 2*half_spread]

        for off in offsets:
            dir_vec = pygame.Vector2(cos(base_angle + off), sin(base_angle + off))
            pos = origin.copy()
            traveled = 0.0
            while traveled < dist:
                pos += dir_vec * step
                traveled += step
                if any(r.collidepoint(pos) for r in blocker_rects):
                    break  # bloqueado
                if (target.hitbox.collidepoint(pos)):
                    return True  # visão confirmada
        return False


    def escolhe_fala(self, ):
        fala_data = self.talks.get(self.current_id)
        if not fala_data:
            return "", []
        
        # Verifica se é fim (sem respostas) e aplica reputação
        if not fala_data["respostas"]:
            if not self.encerrou_conversa:
                player = [c for c in self.creatures_sprites if c.is_player == True][0]
                player.confiabilidades[self.specie] += self.pontuacao
                self.encerrou_conversa = True
                self.pontuacao = 0
                
            delta_rep = self.pontuacao * 20  # Exemplo: pontuação alta -> +rep, baixa -> -rep
            # self.reputacao_orcs = max(0, min(100, self.reputacao_orcs + delta_rep))
            return fala_data["fala"], []  # Mostra fala final e encerra
        
        self.encerrou_conversa = False
        return fala_data["fala"], list(fala_data["respostas"].keys())
        
    def processa_escolha(self, escolha: str):
        pass

    @property
    def speed(self):
        return self.original_speed
    
    @property
    def is_making_noise(self):
        if self.action in ["Stealth", "Idle"]:
            return False
        else:
            return True
        
    @property
    def noise_intensity(self) -> int:
        if self.is_making_noise:
            ni = 100
            if self.action in self.noise_intensities.keys():
                ni = self.noise_intensities[self.action]
            return ni
        return 0
    
    def regen_life(self,now, multiply_regen=1):
        #regenera um percentual a cada segundo
        if now - self.last_regenered_hp > 1000 and self.hp < self.max_hp:
            self.last_regenered_hp = now
            self.hp += self.max_hp*self.life_regen_percent*multiply_regen/100

    def load_character_images(self,):
        self.frames = {}
        actions = self.actions
        for act in actions:
            povs = ["Front", "Back", "Left", "Right", ]

            self.frames[act] = {}
            for pov in povs:
                full_dir_path = join(self.default_folder_path,self.armor_type, pov,  act)
                dir_images = []
                for image in sorted(listdir(full_dir_path), key=lambda name: int(name.split(".")[0])):
                    pov_image = pygame.image.load(join(full_dir_path, image)).convert_alpha()
                    if act in ["Attack_1", "Attack_2", "Fishing"]:
                        scale = self.scale_on_attack
                        dir_images.append(pygame.transform.scale(pov_image, (self.default_size*scale, self.default_size*scale)))
                    else:
                        dir_images.append(pygame.transform.scale(pov_image, (self.default_size, self.default_size)))
                self.frames[act][pov] = dir_images

    def handle_states(self,dt):
        if self.is_dead:
            if not self.death_time:
                self.death_time = pygame.time.get_ticks()

            if self.respawnable:
                self.hp = self.max_hp
                self.is_dead = False
                self.is_dying = False
                center = choice(self.spawn_points)
                self.rect.center = center
                self.hitbox.center = center
                self.action="Idle"
                self.attacking_character = None


            elif self.delete_sprites_on_death:
                

                self.kill()
                del self
            
            return
        
        if self.is_dying:
            self.action = "Dying"
            if self.frame_index >= len(self.frames[self.action][self.state]):
                self.action="Dead"
                self.is_dead = True
            self.animate(dt)
            return 
        
        if self.is_frozen:
            self.handle_effects()
            if self.action == "Hurt":
                if self.frame_index >= len(self.frames[self.action][self.state]):
                    self.action="Dead"
                    self.is_handling_damage = False
                self.animate(dt)

            return
        
        if self.is_handling_damage:
            self.action = "Hurt"
            if self.frame_index >= len(self.frames[self.action][self.state]):
                self.action="Idle"
                self.is_handling_damage = False
            self.animate(dt)
            return 
        
        if self.being_healed:
            self.dt = dt
            self.regen_life(self.now, multiply_regen=3)
            return
        if self.healing:
            
            if self.healing_character.hp >= self.healing_character.max_hp or (self.healing_character.position_vector - self.position_vector).length() > self.rect.width:
                self.healing_character.hp = self.healing_character.max_hp
                self.healing_character.being_healed=False
                self.healing = False
            self.animate(dt)
            return
        
        if self.is_chatting:
            self.action = "Idle"
            self.animate(dt)
            if self.current_action:
                self.current_action.update(dt)
            return
    
        if self.is_begging:
            if self.action == "Begging" or self.action=="Beg":
                self.action = "Beg"
                if not self.speech_text:
                    self.speech_text = choice(
                        [
                            "Por favor, eu faço qualquer coisa… só me deixe viver.",
                            "Não me mate, ainda há tempo de parar.",
                            "Eu não quero morrer, eu imploro.",
                            "Tenha piedade… minha vida ainda importa."
                        ])
                self.animate(dt)
                if pygame.time.get_ticks() - self.start_begging_time > self.begging_delay:
                    self.is_begging = False
                    self.action = "WakeUp"
                    parar_ataque = choice([True, False])
                    if parar_ataque:
                        self.attacking_character = None
                        self.is_combating = False

                return
            else:
                self.action="Begging"
                self.start_begging_time = pygame.time.get_ticks()
            self.animate(dt)
            return
        return True

    def handle_effects(self, *args, **kwargs):
        
        for e in self.effects[:]:
            e.update(self)

    def move(self, dt):

        self.direction = self.direction.normalize() if self.direction else self.direction

        if not self.is_attacking:
            hitbox = self.hitbox.copy()
            hitbox.x += dt * self.direction.x * self.speed
            hitbox.y += dt * self.direction.y * self.speed
            
            self.x_move_ok, self.y_move_ok = self.collision(hitbox)

            self.hitbox.x += dt * self.direction.x * self.speed
            self.hitbox.y += dt * self.direction.y * self.speed

            

        self.rect.center = self.hitbox.center

    def collision(self, hitbox):
        now = pygame.time.get_ticks()
        FEEDBACK_MS = 120      # tempo que fica "torto" após soltar o toque
        FEEDBACK_DEG = 6       # giro leve
        x_move_ok = True
        y_move_ok = True
        winter_curse_group = self.groups()[0].winter_curse_group
        if self.is_player:
            colissiors = self.collision_sprites
        else:
            colissiors = [winter_tree for winter_tree in winter_curse_group]

        # 1) Recupera apenas os sprites que realmente colidem (loop em C, bem mais rápido)
        hits = pygame.sprite.spritecollide(self, colissiors, False)
        if not hits:
            return x_move_ok, y_move_ok

        for sprite in hits:
            
            # 1) Restaura automaticamente quando passar o tempo
            if getattr(sprite, "_rot_reset_at", 0) and now >= sprite._rot_reset_at:
                if getattr(sprite, "_original_image", None) is not None:
                    center = sprite.rect.center
                    sprite.image = sprite._original_image
                    sprite.rect = sprite.image.get_frect(center=center)
                sprite._rotated_once = False
                sprite._rot_reset_at = 0

            

            if sprite.hitbox.colliderect(hitbox):
                if hasattr(sprite, "is_ground"):
                    continue

                if getattr(sprite, "is_winter_curse", False):
                    if (self.position_vector - pygame.Vector2(sprite.rect.center)).length() < self.rect.width*1.3:
                        if not self.is_frozen:
                            freeze = FrozenEffect(20000, curse_groups=[self.groups()[0], self.collision_sprites, winter_curse_group])
                            self.effects.append(freeze)

                if isinstance(sprite, EffectSprite):
                    
                    effect_class = sprite.effect
                    
                    effect_classes = [isinstance(effect, effect_class) for effect in self.effects]
                    if not any(effect_classes):
                        self.effects.append(effect_class())                       
                        
                    continue

                if isinstance(sprite, AnimatedSprite):
                    if self.is_interacting and sprite.on==False:
                        sprite.turn_on()                    
                    elif self.is_interacting and sprite.on==True:
                        sprite.turn_off()                    
                        
                    continue

                if sprite.is_getable:
                    
                    if self.is_interacting:
                        self.inventory.append(sprite.item)
                        self.collision_sprites.remove(sprite)
                        sprite.is_invisible = True
                    
                    

                # 2) Se NÃO for CollisionSprites: só feedback visual (giro) e segue
                if isinstance(sprite, MoveableSprites):
                    # guarda a original 1x
                    if not hasattr(sprite, "_original_image"):
                        sprite._original_image = sprite.image  # pode usar .copy() se preferir
                    # gira só na 1ª vez
                    if not getattr(sprite, "_rotated_once", False):
                        sprite._rotated_once = True
                        mid_bottom = sprite.hitbox.midbottom
                        center = sprite.rect.center
                        sprite.image = pygame.transform.rotate(sprite.image, FEEDBACK_DEG)
                        sprite.rect = sprite.image.get_frect(center=center)
                        sprite.hitbox.midbottom = mid_bottom
                    # empurra o prazo de restauração enquanto continuar encostando
                    sprite._rot_reset_at = now + FEEDBACK_MS
                    continue  # não bloqueia

                if hasattr(sprite, "is_inventory"):
                    if sprite.is_inventory and self.is_interacting:
                        for item in sprite.inventory:
                            #TODO: Criar interação com inventário do objeto
                            pass

                
                
                

                # 3) Fluxo atual (bloqueio) para CollisionSprites
                if hitbox.right > sprite.hitbox.left and hitbox.right > self.hitbox.right :
                    x_move_ok = False

                if hitbox.left < sprite.hitbox.right and hitbox.left < self.hitbox.left :
                    x_move_ok = False

                if hitbox.bottom > sprite.hitbox.top and hitbox.bottom > self.hitbox.bottom :
                    y_move_ok = False

                if hitbox.top < sprite.hitbox.bottom and hitbox.top < self.hitbox.top :
                    y_move_ok = False

                # self.rect.center = self.hitbox.center
        return x_move_ok, y_move_ok


    def handle_damage(
        self,
        damage: float,
        impact_slide: bool = False,
        impact_slide_strength: float = 50.0,
        attacking_character = None
    ) -> None:
        
         #zerando a direção para ele não ser arremessado
        self.direction = pygame.Vector2()

        if attacking_character:
            
            self.last_interacted_character = attacking_character
            attacking_character.last_interacted_character = self
            if self.specie == attacking_character.specie:
                return 
            
            # Fantasmas só podem ser feridos por slimes
            if self.specie == "GHOST" and attacking_character.specie != "SLIME":
                return
            
            #Mecânica de se desculpar
            if self.can_talk == True and attacking_character.can_talk == True: #se ambos podem falar
                if self.hp < self.max_hp *0.5: #se está com menos da metade da vida
                    if self.hp < attacking_character.hp: #se o atacante tem mais vida
                        self.is_begging = True

            
            for char in self.specie_group:
                
                if (char.position_vector - self.position_vector).length() < WINDOW_WIDTH//2:
                    attacking_character.confiabilidades[self.specie] -= 0.2
                    char.attacking_character = attacking_character
                    char.is_combating = True
                    break

             
                

            
        
        #se já está tomando dano, não toma mais
        if self.is_handling_damage == True:
            return

       

        # 1) Dano
        self.hp = max(0, self.hp - float(damage))
        # 2) Tremor de tela
        if self.is_player:
            self.on_shake_screen(damage)

        self.is_handling_damage = True
        self.is_combating = True
        self.frame_index = 0
        self.attacking_character = attacking_character
        if self.hp <= 0 and attacking_character:
            self.is_dying = True
            
            attacking_character.kills.append(self)
            

            for char in self.creatures_sprites:
                if char.specie == self.specie:
                    if (char.position_vector - self.position_vector).length() < WINDOW_HEIGHT//2:
                        attacking_character.confiabilidades[self.specie] -= 0.5
                        break
        
        # 3) Knockback simples (instântaneo)
        if impact_slide:
            # Pega centro correto (hitbox > rect)
            center = pygame.Vector2(
                self.hitbox.center if hasattr(self, "hitbox") else self.rect.center
            )

            # Calcula a direção do knockback
            if isinstance(self.last_hit_from, (tuple, list, pygame.Vector2)):
                src = pygame.Vector2(self.last_hit_from)
                dir_vec = center - src
            else:
                dir_vec = -self.direction if self.direction.length_squared() > 0 else pygame.Vector2()

            # Aplica knockback
            if dir_vec.length_squared() > 0:
                dir_vec = dir_vec.normalize() * float(impact_slide_strength)

                # Move a hitbox se existir
                if hasattr(self, "hitbox"):
                    self.hitbox.center += dir_vec

                    # Mantém rect sincronizado
                    if hasattr(self, "rect"):
                        self.rect.center = self.hitbox.center

                # Se não tiver hitbox, move só o rect
                elif hasattr(self, "rect"):
                    self.rect.center += dir_vec

    def attack(self,attack_1_button, attack_2_button):
        now = pygame.time.get_ticks()
        attack_passed_time = now - self.last_attack_time
        width, height = self.attack_hitbox_list[self.state]
        attack_hitbox_rect = pygame.rect.FRect(0, 0, width, height)
        if self.use_center_on_attack == False:
            if self.state == "Right":
                attack_hitbox_rect.midleft = self.hitbox.center
            if self.state == "Left":
                attack_hitbox_rect.midright = self.hitbox.center
            if self.state == "Front":
                attack_hitbox_rect.midtop = self.hitbox.center
            if self.state == "Back":
                attack_hitbox_rect.midbottom = self.hitbox.center
        else:
            attack_hitbox_rect.center = self.hitbox.center
        self.attack_hitbox = attack_hitbox_rect
       
        #se não está atacando & tecla de ataque acabou de ser pressionada & passou do tempo de delay de ataque
        if not self.is_attacking and any([attack_1_button,attack_2_button]) and attack_passed_time > self.attack_delay:
            
            
            self.action = "Attack_2" 
            self.is_attacking = True
            self.last_attack_time = now
            self.frame_index = 0
            self.animation_speed=len(self.frames[self.action][self.state])
            play_noise(self, self.attack_sounds)
           
           
           
       
        if self.is_attacking:#encerra ataque

            self.action = "Attack_2"
            #Os alvos sempre vão estar dentro da rect do atacante, então filtro os que se chocam
            on_range_creatures = pygame.sprite.spritecollide(self, self.creatures_sprites, False)
            if on_range_creatures:
                chars = [c for c in on_range_creatures if isinstance(c,Character) and c!= self and c not in self.team_members]
                for char in chars:
                    if self.attack_hitbox.colliderect(char.hitbox) and char.is_handling_damage == False:
                        char.handle_damage(self.attack_damage, impact_slide=True, impact_slide_strength=self.attack_damage*5, attacking_character=self)
                   
            if self.frame_index >= len(self.frames[self.action][self.state]):
                self.is_attacking=False
                self.action="Idle"
                self.attack_hitbox=None
                self.animation_speed=5
                self.attack_1,self.attack_2 = False,False

                #criando imagem de flecha
                if self.is_ranged:
                    origem = self.position_vector

                    if self.attacking_character:
                        alvo = self.attacking_character.position_vector
                        direcao = alvo - origem

                        direcao.x *= -1
                        angulo = pygame.math.Vector2(0, -1).angle_to(direcao)
                        direcao.x *= -1

                    else:
                        # Direção que o player está olhando
                        directions = {
                            "Front": pygame.Vector2(0,1),
                            "Back": pygame.Vector2(0,-1),
                            "Left": pygame.Vector2(-1,0),
                            "Right": pygame.Vector2(1,0),
                        }
                        direcao = directions[self.state].normalize()

                        # Ângulo baseado no "norte" da tela
                        direcao.x *= -1
                        angulo = pygame.math.Vector2(0, -1).angle_to(direcao)
                        direcao.x *= -1

                    Arrow(
                        self.groups()[0],
                        self.collision_sprites,
                        initial_pos=origem,
                        direction=direcao,
                        angulo=angulo,
                        atirador=self
                    )
                    #cria sprite de flecha e posiciona no centro do personagem
        else:
            self.attack_hitbox=None

    # ===== Tremor de tela =====
    def on_shake_screen(self, intensity: float = 2.0) -> None:
        """Ativa o tremor por um tempo curto (shake_duration_ms)."""
        self._shake_intensity = float(intensity)
        self._shake_end_time = pygame.time.get_ticks() + int(self.shake_duration_ms)

    def sample_shake_offset(self) -> pygame.Vector2:
        """
        Retorna um pequeno offset aleatório enquanto o shake estiver ativo.
        Use somando isso ao offset da câmera/posicionamento do draw.
        """
        now = pygame.time.get_ticks()
        if now < self._shake_end_time and self._shake_intensity > 0.0:
            ox = uniform(-self._shake_intensity, self._shake_intensity)
            oy = uniform(-self._shake_intensity, self._shake_intensity)
            return pygame.Vector2(ox, oy)
        return pygame.Vector2()

    def facing_pov(self) -> pygame.Vector2:
        if self.direction.x**2 > self.direction.y**2:
            return "Right" if self.direction.x >= 0 else "Left" if self.direction.x <= 0 else None 
        else:
            return "Front" if self.direction.y >= 0 else "Back" if self.direction.y <= 0 else None

    def make_steps(self,):
        img = choice(self.step_images)
        step = Steps(self.groups()[0], surface=img, pos=self.hitbox.midbottom)
        step.rect.center = self.hitbox.midbottom

    def animate(self,dt, ):
        

        now = pygame.time.get_ticks()
        if self.is_running:
            movement_action = "Run"
            if not self.running_speed_applied:
                self.speed_multipliers.append(self.running_speed_multiplier)
                self.running_speed_applied = True
        else:
            movement_action = "Walk"
            if self.running_speed_applied:
                self.speed_multipliers.remove(self.running_speed_multiplier)
                self.running_speed_applied = False

        if self.direction.x != 0 and self.direction.y != 0:
            if now - self.last_changed_pov > self.change_pov_delay:
                self.last_changed_pov = now
                self.state = self.facing_pov()
            self.action = movement_action if self.action in ["Walk","Idle"] else self.action

        elif self.direction.x != 0:
            self.state = "Right" if self.direction.x >= 0 else "Left"
            self.action = movement_action if self.action in ["Walk","Idle"] else self.action

        elif self.direction.y != 0:
            self.state = "Front" if self.direction.y >= 0 else "Back"
            self.action = movement_action if self.action in ["Walk","Idle"] else self.action

        if not self.direction and self.action in ["Walk", "Run",]:
            self.action="Idle"

       
        self.frame_index += self.animation_speed * dt
        original_centerx = self.rect.centerx
        original_centery = self.rect.centery
        try:
            frame_idx = int(self.frame_index) % len(self.frames[self.action][self.state])
            if frame_idx > len(self.frames[self.action][self.state])-1:
                frame_idx = 0
            self.image = self.frames[self.action][self.state][frame_idx]

            if frame_idx == 0 and self.direction and now - self.last_step_sound > self.step_sound_delay:
                self.last_step_sound = now
                play_noise(self, self.walk_sounds,)
        except:
            print(f"Erro ao tentar acessar a imagem número {int(self.frame_index)} da ação {self.action} olhando para {self.state} no personagem {self.personal_name}")
            raise Exception(f"Erro ao tentar acessar a imagem número {int(self.frame_index)} da ação {self.action} olhando para {self.state} no personagem {self.personal_name}")
        self.rect = self.image.get_frect(center = (original_centerx, original_centery))

        if self.action in ["Walk", "Run"] and self.has_steps ==True and now - self.last_step_time > self.speed:
            self.last_step_time = now
            self.make_steps()
    
    def __str__(self,):
        return self.personal_name

class Mimetizacao:
    def __init__(self, character:Character, to_mimetize:Character):
        self.character = character
        self.to_mimetize = to_mimetize

    def mimetize(self,):
        now = pygame.time.get_ticks()
        self.character.last_mimetization  = now

        self.character.rect.width = self.to_mimetize.rect.width
        self.character.hitbox.width = self.to_mimetize.hitbox.width

        self.character.rect.height = self.to_mimetize.rect.height
        self.character.hitbox.height = self.to_mimetize.hitbox.height
        
        self.character.frames = self.to_mimetize.frames
        self.character.max_hp = self.to_mimetize.max_hp
        self.character.attack_damage = self.to_mimetize.attack_damage
        self.character.original_speed = self.to_mimetize.original_speed
        self.character.attack_hitbox_list = self.to_mimetize.attack_hitbox_list
        self.character.actions = self.to_mimetize.actions
        self.character.specie = self.to_mimetize.specie
        self.character.is_ranged = self.to_mimetize.is_ranged
        self.character.attack_sounds = self.to_mimetize.attack_sounds
        self.character.can_talk = self.to_mimetize.can_talk
        self.character.use_center_on_attack = self.to_mimetize.use_center_on_attack
        self.character.walk_sounds = self.to_mimetize.walk_sounds


class Item(ABC):
    """
    Base de item do jogo.
    """

    def __init__(self, name: str, all_sprites, collision_sprites, image_surface: pygame.Surface=None,image_path:str="", ) -> None:
        self.name = name
        self.original_image = image_surface if image_surface else pygame.image.load(image_path).convert_alpha()
        self.inventory_image = pygame.transform.scale(self.original_image, (16,16))
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites

    
    def use(self,character:Character, using_type="consume"):
        if using_type == "consume":
            self.on_consume(character)
        elif using_type == "drop":
            self.on_drop(position = character.hitbox.center)
        elif using_type == "throw":
            self.on_throw(center_position = character.hitbox.center)

        character.inventory.remove(self)
    
    def on_drop(self, position,):
        CollisionSprites(self.all_sprites, self.collision_sprites, pos=position, surface=pygame.transform.scale(self.original_image, (self.original_image.width, self.original_image.height)), item=self, use_center=True, is_getable=True)
        
    # -------- hooks (sobrescreva em subclasses) --------
    def on_consume(self, user, world, **kwargs) -> bool:
        pass
    
    def on_throw(self,*args,**kwargs) -> bool:
        pass

class Spell:
    """
    #verify the kind of spell
    #1. Magia de alvo travado - Magia que causa algum efeito no alvo, mas sem efeito visual se movendo do lançador ao alvo
    #2. Magia de projétil - Dispara algo no alvo
    #3. Magia de área - afetam todos os seres numa determinada área
    #4. Magia global - Magias que afetam a própria mecânica do jogo como tempo e espaço
    """
    def __init__(self, *, mana_cost: float = 0.0,
             spelling_difficult_level: int = 1,
             spell_type: str = "AT",#AT. Magia de alvo travado, MP. Magia de projétil, MA. Magia de área, MG.Magia global
             spell_subtype: str = "Spacial",
             spell_range:float = 0,
             ):
        self.mana_cost = mana_cost
        self.spelling_difficult_level = max(1, min(10, spelling_difficult_level))
        self.spell_type = spell_type
        self.spell_subtype = spell_subtype
        self.spell_range = spell_range
   
    def generate_possible_targets_list(self,user:Character, all_creatures:list[Character],):
        possibles = []
        if self.spell_range <=0: #is a global spell
            return [creat for creat in all_creatures]

        for creat in all_creatures:
            if (pygame.Vector2(user.hitbox.center) - pygame.Vector2(creat.hitbox.center)).length() <= self.spell_range:
                    possibles.append(creat)
        
        return possibles

    def can_use(self, user: Character, target: Character, *args, **kwargs) -> bool:
        #verify if cost was taken

        #TODO: verify if there are any blockers to this type or subtype
        return True
    
    def try_use(self, user: Character, all_creatures:list[Character]=[],target:Character=None, *args, **kwargs):
        possible_creatures = self.generate_possible_targets_list(user, all_creatures)
        if not possible_creatures:
            return False
        if not self.can_use(user, target, *args, **kwargs):
            return False
        if not self.take_cost(user, *args, **kwargs):
            return False
        if self.spell_type == "AT":
            targ = choice([creat for creat in possible_creatures])
            self.use(user,targ, *args, **kwargs)
        #TODO: Continue creating the other kind os spells
        return True

    def take_cost(self,*args, **kwargs) -> bool:
        """
            Spells can take different costs. Most generaly it will be mana, but
            it can also cost life or somekind of item

            If cost is not attended then the spell fails
        """
        return True

    def use(self, user:Character, target:Character,*args,**kwargs ):
        pass
        

class Objeto:
    def __init__(self, nome):
        self.nome = nome
   

class Habilidade:
    def __init__(self, nome:str):
        self.nome = nome
        
class Status:
    def __init__(self, nome):
        self.nome = nome

    @classmethod
    @abstractmethod
    def efeito(*args, **kwargs):
        """
        Cada status aplica um bônus ou desvantagem no usuário.
        Vários status podem ser aplicados simultânemanete

        Ex de status:
        Faminto - O usuário se torna mais agressivo e perde características como velocidade e força
        Envenenado - O usuário perde constantemente uma parte da sua vida máxima
        Congelando - O usuário perde velocidade e precisão 
        """
