from settings import *
from Utils.classes_raiz import Character,Mimetizacao
from Utils.villagers import Dash
from Utils.speels import *
from Utils.effects import Blind
import re

class Player(Character):
    def __init__(self, *groups, collision_sprites:pygame.sprite.Group,creatures_sprites:pygame.sprite.Group):
        super().__init__(*groups, collision_sprites=collision_sprites, creatures_sprites=creatures_sprites, is_player=True)
        self.all_groups= groups
        self.is_player = True
        self.is_human = True
        self.all_creatures_group = []
        

        self.armor_type = ""
        self.default_folder_path = join(getcwd(), "Player", "graphics","Warrior_animations", "Default")
        # self.default_folder_path = join(getcwd(), "NPCs", "Obi",)
        self.default_size = HDCS + HHDCS
        


        self.action = "Walk"
        self.state, self.frame_index = "Front", 0
        self.actions = ["Walk", "Idle", "Attack_2", "Attack_1", "Run", "Hurt", "Dying", "Dead", "Begging", "Beg", "WakeUp"]
        self.load_character_images()
        
        
        self.image = pygame.transform.scale(self.frames[self.action][self.state][0], (self.default_size, self.default_size))
        self.rect = self.image.get_frect(center = (5000, 3000))
        # self.rect = self.image.get_frect(center = (2369.525390625, 750.13313293457031))
        # self.rect = self.image.get_frect(center = (5866, 5918))
        # self.rect = self.image.get_frect(center = (3239, 5888))
        self.hitbox = pygame.FRect(
            self.rect.left + self.rect.width/2,
            self.rect.top + self.rect.height/3+50,
            self.rect.width/2,
            self.rect.height * 2/3
            )
        self.hitbox.center = self.rect.center

        self.original_speed = 200
        self.direction = pygame.Vector2()
        self.collision_sprites = collision_sprites

        #ATTACK
        self.animation_speed = 5
        self.attack_hitbox_list = {
            "Front": (75,35),#width, height
            "Back": (75,35),#width, height
            "Left": (35,75),#width, height
            "Right": (35,75),#width, height
        }
        self.attack_hitbox = None
        self.is_attacking =False
        self.attack_delay = 750
        self.last_attack_time = pygame.time.get_ticks()
        self.attack_duration_ms = 2000
        #spell_casting
        
        self.death_time = None


        self.box_1 = pygame.Rect(5600, 3708, 10, 100)
        self.box_2 = pygame.Rect(5660, 3708, 10, 100)
        self.box_3 = pygame.Rect(883,1820, 100, 10)
        self.box_4 = pygame.Rect(883,1900, 100, 10)
        self.box_5 = pygame.Rect(1980,5435, 10, 100)
        self.box_6 = pygame.Rect(2040,5435, 10, 100)
        self.inside_maze = True
        self.inside_ice_florest = False
        self.max_hp = 50
        self.attack_damage = randint(12,20)
        self.hp=self.max_hp

        self.player_chatting_to: Character=None
        self.player_chatting_end =  None
        self.specie = "HUMAN"


        self.confiabilidades = { #Sendo acima de 1 totalmente confiável e abaixo de 0 totalmente odiado
            "HUMAN": 0.5,
            "SLIME": 0.5,
            "GHOST": 0.5,
            "ORC": 0.5,
            "GOLEM": 0.5,
            "GOBLIN": 0.5
        }
        self.slime_0 = None
        self.orc_0 = None
        self.orc_chefe_0 = None
        self.human_0 = None
        self.goblin_0 = None
        self.original_form = None
        self.has_emblem = False
        

        self.aplicar_resfriamento = False
        self.intensidade_resfriamento = 0

        self.transformations = []

        self.attack_sounds = []
        self.step_sounds = [
        #    pygame.mixer.Sound("Sounds/step_sound.mp3"),
        #    pygame.mixer.Sound("Sounds/step_sound_2.mp3"),
           pygame.mixer.Sound("Sounds/step_sound_3.mp3")
        ]

        self.loop = self.le_infos_loop()

        self.falou_chefe_vila = False
        self.falou_chefe_orcs = False
        self.convenceu_chefe_orcs = False
        self.convenceu_chefe_vila = False
        self.viu_vila_destruida = False
        self.falou_orc_caido = False
        self.has_steps = True
        self.puxou_alavanca = False


        self.frases_loops = {
            1: "Quem eu sou, que eu fui e o que eu fiz... Isso não importa.\n\nTodo mundo tem arrependimentos na vida, e eu estou aqui pra tentar consertar os meus.",
            2: "Espera. Esse lugar... Esse momento.... \n\n Eu já ouvi história sobre magias do tempo. Será que estou preso em algum tipo de feitiço temporal?",
            3: "Eu vim Aqui pelo Cristal, mas parece que tem mais coisas acontecendo no momento.",
            4: "Eu entendo que essas pessoas estão com problemas, mas esse problema não é meu."
        }

        #DIALOGOS DESBLOQUEAVEIS
        self.nina = None
        self.viu_corpo_nina = False #1
        self.sabe_movimentacao_orcs = False #2
        self.sabe_nome_nina = False #3
        self.tem_apoio_holz = False #4
        self.salvou_nina = False
        self.falou_nina = False
        self.falou_holz = False

    @property
    def speed(self):
        mult = min(1, 1.0 - (1 - self.hp/self.max_hp))
        for f in self.speed_multipliers:
            mult *= f
        return self.original_speed * mult

    def move(self, dt):
        self.direction = self.direction.normalize() if self.direction else self.direction

        if not self.is_attacking:
            hitbox = self.hitbox.copy()
            hitbox.x += dt * self.direction.x * self.speed
            hitbox.y += dt * self.direction.y * self.speed
            
            self.x_move_ok, self.y_move_ok = self.collision(hitbox)

            if self.x_move_ok:
                self.hitbox.x += dt * self.direction.x * self.speed
            if self.y_move_ok:
                self.hitbox.y += dt * self.direction.y * self.speed
            
            if (self.x_move_ok or self.y_move_ok) and self.direction:
                play_noise(self, self.step_sounds, cooldown=1000, volume=0.2)
        self.rect.center = self.hitbox.center
    
    def list_transformations(self,):
        transformations = [self.original_form,]
        species = []

        transformations_confiabilidades = {
            "HUMAN": self.human_0,
            "SLIME": self.slime_0,
            "ORC": self.orc_0,
            "GOBLIN": self.goblin_0
        }
        for kill in self.kills:
            if kill.specie not in species:
                if kill.specie == "HUMAN":
                    transformations.append(kill)
                else:
                    species.append(kill.specie)
                    transformations.append(kill)
        for conf, val in self.confiabilidades.items():
            if val > 1:
                transformations.append(transformations_confiabilidades[conf])
        self.transformations = transformations


    def salva_infos_loop(self,):
        self.loop += 1 
        dados = {
            "loop": self.loop,
            "viu_corpo_nina": self.viu_corpo_nina,
            "sabe_movimentacao_orcs": self.sabe_movimentacao_orcs,
            "sabe_nome_nina": self.sabe_nome_nina,
            "tem_apoio_holz": self.tem_apoio_holz,
            "salvou_nina": self.salvou_nina,
            "falou_nina": self.falou_nina,
            "falou_holz": self.falou_holz,
        }

        with open(join(getcwd(), "save.json"), "w", encoding="utf-8") as f:
            dump(dados, f, ensure_ascii=False, indent=4)


    def le_infos_loop(self):
        with open(join(getcwd(), "save.json"), "r", encoding="utf-8") as f:
            dados = load(f)

        for chave, valor in dados.items():
            setattr(self, chave, valor)

        return self.loop

    def handle_conditions(self,):
        if not self.viu_corpo_nina and self.nina.is_dead and (pygame.Vector2(self.nina.rect.center) - pygame.Vector2(self.rect.center)).length() < WINDOW_WIDTH//2:
            self.viu_corpo_nina = True

    def verifica_respostas(self, respostas:list):
        respostas_permitidas = []
        for resposta in respostas:
            match = re.match(r"^#(\d+)", resposta)

            if match:
                
                numero = int(match.group(1))
                if numero == 1 and self.viu_corpo_nina:
                    respostas_permitidas.append(re.sub(r"^#(\d+)", "", resposta))
                if numero == 2 and self.sabe_movimentacao_orcs:
                    respostas_permitidas.append(re.sub(r"^#(\d+)", "", resposta))
                if numero == 3 and self.sabe_nome_nina:
                    respostas_permitidas.append(re.sub(r"^#(\d+)", "", resposta))
                if numero == 4 and self.sabe_nome_nina:
                    respostas_permitidas.append(re.sub(r"^#(\d+)", "", resposta))
                if numero == 5 and self.sabe_nome_nina:
                    respostas_permitidas.append(re.sub(r"^#(\d+)", "", resposta))
                if numero == 7 and self.falou_nina or self.falou_holz:
                    respostas_permitidas.append(re.sub(r"^#(\d+)", "", resposta))
            else:
                respostas_permitidas.append(resposta)
        return respostas_permitidas
    def update(self, dt):
        if not self.handle_states(dt):
            return
        
        self.handle_conditions()
        
        self.now = pygame.time.get_ticks()
        self.list_transformations()
        collision_box_1 = self.hitbox.colliderect(self.box_1)
        collision_box_2 = self.hitbox.colliderect(self.box_2)
        collision_box_3 = self.hitbox.colliderect(self.box_3)
        collision_box_4 = self.hitbox.colliderect(self.box_4)
        collision_box_5 = self.hitbox.colliderect(self.box_5)
        collision_box_6 = self.hitbox.colliderect(self.box_6)
        if collision_box_1 or collision_box_2:

            #saindo da floresta
            if collision_box_1:
                for idx,e in enumerate(self.effects):
                    if isinstance(e, Blind):
                        e.on_remove(self)
                        self.effects.pop(idx)
                        self.inside_maze = False
            else: #entrando na floresta
                if not any([isinstance(e,Blind) for e in self.effects]):
                    self.effects.append(Blind(duration_ms=-1))
                    self.inside_maze = True

        if collision_box_3 or collision_box_4:
            if collision_box_3:
                self.aplicar_resfriamento = True
                self.inside_ice_florest = True
            else:
                self.aplicar_resfriamento = False
                self.inside_ice_florest = False

        # print(f"Está na floresta = {self.inside_ice_florest}")
        frozen_speed = 0.9999
        if self.aplicar_resfriamento == True:
            self.speed_multipliers.append(frozen_speed)
        else:
            speeds = [s for s in self.speed_multipliers if s != frozen_speed]
            self.speed_multipliers = speeds
        
        if collision_box_5 or collision_box_6:
            if collision_box_5:
                for sprite in self.all_groups[0]:
                    if hasattr(sprite, "is_roof") and sprite.is_roof == True:
                        sprite.is_invisible = True
            else:
                for sprite in self.all_groups[0]:
                    if hasattr(sprite, "is_roof") and sprite.is_roof == True:
                        sprite.is_invisible = False
                

        self.position_vector = pygame.Vector2(self.rect.center)


        
        self.handle_effects()

        keys = pygame.key.get_pressed()
        self.direction.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        

        attack_1_button = keys[pygame.K_k]
        attack_2_button = keys[pygame.K_l]
        self.is_running = keys[pygame.K_LSHIFT]


        transformation_keys = [
            pygame.K_1, 
            pygame.K_2,
            pygame.K_3, 
            pygame.K_4, 
            pygame.K_5, 
            pygame.K_6,
            pygame.K_7,
            pygame.K_8,
            ]
        transformation_iterator = 0
        for tk in transformation_keys:
            transforming_button = keys[tk]
            if transforming_button and transformation_iterator <= len(self.transformations) -1:
                mimic = Mimetizacao(character=self, to_mimetize=self.transformations[transformation_iterator])
                mimic.mimetize()
                break
            transformation_iterator +=1
            
        item_button = keys[pygame.K_p]
        if item_button:
            if len(self.inventory)>=1:
                self.inventory[0].use(self, "drop")


        now = pygame.time.get_ticks()

        interact_button = keys[pygame.K_SPACE] and now - self.last_interact_time > self.interact_delay
        if interact_button:
            self.last_interact_time = now
        self.is_interacting = interact_button

        if self.is_interacting:
            hits =  pygame.sprite.spritecollide(self, self.creatures_sprites, dokill=False)
            if hits:
                for creat in hits:
                    if (not creat.is_player and creat.is_dead==False and creat.specie not in ["GHOST", "SLIME", "GOBLIN", "GOLEM"]) or creat.personal_name == "Orc Explorer":
                        self.is_chatting = True
                        self.player_chatting_to = creat

                        break

        self.move(dt)
        self.animate(dt,)
        self.attack(attack_1_button, attack_2_button)
        # self.choose_image(dt)
 

