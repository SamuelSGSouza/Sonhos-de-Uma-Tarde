from settings import *
from Player.player import Player
from sprites import *
from groups import AllSprites
from pytmx import load_pygame
from Ecosystem.ecossistema import Map
from Utils.effects import *
from Utils.items import *
from Utils.actions import *
from Utils.classes_raiz import *
from Utils.villagers import *
from Utils.monsters import *
import threading

class Mundo:
    def __init__(self, LARGURA_MAPA, ALTURA_MAPA, GRID_SIZE, objetos_fixos):
        self.LARGURA_MAPA = LARGURA_MAPA
        self.ALTURA_MAPA = ALTURA_MAPA
        self.GRID_SIZE = GRID_SIZE
        self.objetos_fixos = objetos_fixos

        # matriz inicial
        self.matriz_mapa = gerar_matriz_mapa(
            self.LARGURA_MAPA,
            self.ALTURA_MAPA,
            self.GRID_SIZE,
            self.objetos_fixos
        )

        self._matriz_lock = threading.Lock()
        self._thread_ativa = True

        # inicia a thread
        self._thread = threading.Thread(target=self._loop_atualizacao, daemon=True)
        self._thread.start()

    def _loop_atualizacao(self):
        """
        Loop que recalcula a matriz do mapa em background.
        """
        while self._thread_ativa:
            nova_matriz = gerar_matriz_mapa(
                self.LARGURA_MAPA,
                self.ALTURA_MAPA,
                self.GRID_SIZE,
                self.objetos_fixos
            )

            # protege a escrita contra acessos simultâneos
            with self._matriz_lock:
                self.matriz_mapa = nova_matriz

            time.sleep(0.2)  # atualiza a cada 200ms (ajuste como quiser)

    def get_matriz(self):
        """
        Obtém a matriz de forma segura.
        """
        with self._matriz_lock:
            return [linha[:] for linha in self.matriz_mapa]  # retorna cópia

    def stop(self):
        """Para a thread quando o jogo fechar."""
        self._thread_ativa = False
        self._thread.join()

class GameClock:
    def __init__(self, start_hour=9, start_min=0, start_sec=0,
                 game_hour_in_real_seconds=300):
        self.hour = start_hour
        self.min = start_min
        self.sec = start_sec
        self.factor = game_hour_in_real_seconds
        self.game_seconds_per_real_second = 3600 / self.factor

    def set_speed(self, game_hour_in_real_seconds):
        self.factor = game_hour_in_real_seconds
        self.game_seconds_per_real_second = 3600 / self.factor

    def update(self, dt):
        game_sec_passed = dt * self.game_seconds_per_real_second
        self.sec += game_sec_passed

        if self.sec >= 60:
            self.min += int(self.sec // 60)
            self.sec = self.sec % 60

        if self.min >= 60:
            self.hour += self.min // 60
            self.min = self.min % 60

        if self.hour >= 24:
            self.hour %= 24

    def get_time_str(self):
        return f"{int(self.hour):02d}:{int(self.min):02d}"

    def get_time_in_hours(self) -> float:
        """Hora em float, ex: 18.5 = 18h30."""
        return self.hour + self.min / 60 + self.sec / 3600

    def get_day_phase(self) -> str:
        """
        Retorna uma fase simples do dia:
          - 'night'
          - 'dawn'
          - 'day'
          - 'dusk'
        Ajuste os intervalos como quiser.
        """
        h = self.get_time_in_hours()
        if 4 <= h < 6:
            return "dawn"
        elif 6 <= h < 18:
            return "day"
        elif 18 <= h < 20:
            return "dusk"
        else:
            return "night"

    def get_light_factor(self) -> float:
        """
        Retorna um valor entre 0.0 (bem escuro) e 1.0 (bem claro),
        para você usar na iluminação.
        """
        h = self.get_time_in_hours()

        # Noite “profunda”
        if h < 4 or h >= 22:
            return 0.1

        # Amanhecer: 4h -> 0.1  até  6h -> 1.0
        if 4 <= h < 6:
            t = (h - 4) / 2  # 0 a 1
            return 0.1 + t * (1.0 - 0.1)

        # Dia “cheio”
        if 6 <= h < 18:
            return 1.0

        # Entardecer: 18h -> 1.0  até  22h -> 0.1
        if 18 <= h < 22:
            t = (h - 18) / 4  # 0 a 1
            return 1.0 + t * (0.1 - 1.0)

        # fallback
        return 1.0

class Game:
    def __init__(self):
        #setup
        pygame.init()

        # self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.screen = pygame.display.set_mode((1280, 720), )
        self.overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.display.set_caption("Dungeon Exploration")
        self.game_running = True
        self.clock = pygame.time.Clock()
        self.lights_on = False

        #groups
        self.creatures_to_add = []
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.creatures = pygame.sprite.Group()
        self.player_group = pygame.sprite.Group()
        self.winter_curse_group = pygame.sprite.Group()
        self.group_index = 0

        #SPECIE GROUPS
        self.slime_sprites = pygame.sprite.Group()
        self.orc_sprites = pygame.sprite.Group()
        self.goblin_sprites = pygame.sprite.Group()
        self.human_sprites = pygame.sprite.Group()


        self.music_vol = 0.0
        self.village_music = join(getcwd(), "Sounds", "village_background.mp3")
        self.florest_music = join(getcwd(), "Sounds", "blizzard.mp3")
        self.maze_music = join(getcwd(), "Sounds", "maze_background_2.mp3")
        self.ice_florest_music = join(getcwd(), "Sounds", "icy_wind_3.mp3")
        self.background_music = join(getcwd(), "Sounds", "florest_background.mp3")
        self.battle_music = join(getcwd(), "Sounds", "battle_sound_2.mp3")
        self.music_fading = "out"
        self.changing_music = False
        
        #sprites
        self.player = Player(self.all_sprites, self.player_group,self.creatures, collision_sprites=self.collision_sprites, creatures_sprites=self.creatures)
        self.player.is_human = True
        # if self.player.rect.centerx <= 6000 and self.player.rect.centerx >= 3800:
        # if self.player.rect.centery <= 1400 and self.player.rect.centerx >=3300
        
        #box 1 entrada floresta
        self.box_1 = pygame.Rect(5600, 3708, 10, 100)
        self.box_2 = pygame.Rect(5660, 3708, 10, 100)

        #box 3 e 4 entrada floresta de gelo
        self.box_3 = pygame.Rect(883,1820, 100, 10)
        self.box_4 = pygame.Rect(883,1900, 100, 10)

        #box 5 e 6 entrada caverna dos orcs
        self.box_5 = pygame.Rect(1980,5435, 10, 100)
        self.box_6 = pygame.Rect(2040,5435, 10, 100)
       
        
        self.decided_path = []
        self.char_monitored = None
        

        # Variável para ligar/desligar o debug
        self.mostrar_grid_debug = False
        self.mostrar_rects = False
        self.contou_loop = False

    def change_background_music(self, dt):
        changing_speed = 0.32 #TODO: turn on volume
        # changing_speed = 0.00#
        if self.changing_music == True:
            if self.music_fading == "out": #diminuindo
                self.music_vol -=  changing_speed*dt
                pygame.mixer.music.set_volume(self.music_vol)
                if self.music_vol <= 0:
                    self.music_fading = "in"
                    pygame.mixer.music.load(self.background_music)
                    pygame.mixer.music.play(-1)
            else:
                self.music_vol +=  changing_speed*dt
                pygame.mixer.music.set_volume(self.music_vol)
                if self.music_vol >= 0.8:
                    self.music_fading = "out"
                    self.changing_music=False


    def game_init(self,):
        while True:
            self.__init__()

            min_fps = 999
            
            snow_folder = join(getcwd(), "Ecosystem", "Winter", "animated_objects", "snow")
            snow_images = load_snow_images(snow_folder)  # pasta com teus flocos
            snow = Snow(self.screen.get_rect(), snow_images, max_flakes=120)

            title_font = pygame.font.Font(join(getcwd(), "fonts/sansita/SansitaSwashed-Bold.ttf"), 60)
            button_font =tutorial_font =  pygame.font.Font(join(getcwd(), "fonts/sansita/SansitaSwashed-Medium.ttf"), 24)
            opcao = main_menu(self.screen, title_font, button_font, snow)
            intensidade_congelamento = 0

            exibir_tutorial = False
            
            self.setup()
            if opcao == "NOVO JOGO" or opcao == "CONTINUAR":
                if opcao == "NOVO JOGO":
                    exibir_tutorial = True
                    dados = {
                        "loop": 1,
                    }

                    with open(join(getcwd(), "save.json"), "w", encoding="utf-8") as f:
                        dump(dados, f, ensure_ascii=False, indent=4)
                    self.player.loop=1
                    width = self.screen.get_rect().width
                    height = self.screen.get_rect().height

                    COLORS = {
                        'bg': (244, 230, 200),
                        'border': (92, 64, 36),
                        'text': (42, 28, 16),
                        'text_name': (138, 94, 42),
                        'option_bg': (222, 196, 150),
                        'option_hover': (206, 172, 112),
                        'accent': (176, 126, 48),
                        'white': (250, 248, 245)
                    }
                    
                    

                    tutorial_border = pygame.Surface((width+10, height+10), pygame.SRCALPHA)
                    tutorial_suface = pygame.Surface((width, height), pygame.SRCALPHA)
                    pygame.draw.rect(
                    tutorial_border,
                        COLORS["border"],
                        (0, 0, width * 0.8 + 10, height * 0.8 + 10),
                        border_radius=14
                    )

                        # Fundo interno (mais claro)
                    pygame.draw.rect(
                        tutorial_suface,
                        COLORS["bg"],
                        (0, 0, width * 0.8, height * 0.8),
                        border_radius=12
                    )
                
                    self.screen.blit(tutorial_border, (width*0.1-5,height*0.1-5))
                    self.screen.blit(tutorial_suface, (width*0.1,height*0.1))
                    

                    font_title = pygame.font.Font(None, 42)
                    font_text = pygame.font.Font(None, 28)

                    # Área do modal
                    modal_w = int(width * 0.8)
                    modal_h = int(height * 0.8)
                    modal_x = int(width * 0.1)
                    modal_y = int(height * 0.1)

                    # Instruções
                    instructions = [
                        ("Mover", "W  A  S  D", "Walk", ),
                        ("Atacar", "K", "Attack_2", ),
                        ("Correr", "SHIFT", "Run", ),
                        ("Interagir", "SPACE", "Hurt",  ),
                    ]

                    card_w = modal_w - 80
                    card_h = 90
                    card_x = modal_x + 40
                    start_y = modal_y + 80
                    spacing = 20

                    # Título
                    title_surf = font_title.render("CONTROLES", True, COLORS["accent"])
                    self.screen.blit(title_surf, (modal_x + modal_w // 2 - title_surf.get_width() // 2, modal_y + 20))

                    

                    # Dica para fechar
                    hint = font_text.render("Pressione qualquer tecla para fechar", True, COLORS["text"])
                    self.screen.blit(
                        hint,
                        (modal_x + modal_w // 2 - hint.get_width() // 2, modal_y + modal_h - 40)
                    )
                    indexes = {
                        "Walk": 0,
                        "Attack_2": 0,
                        "Run": 0,
                        "Hurt": 0,
                    }
                    
                    while exibir_tutorial:
                        dt = self.clock.tick(240) / 1000
                        
                        for i, (label, key, action) in enumerate(instructions):
                            images = self.player.frames[action]["Front"]

                            index = indexes[action]
                            animation_speed = len(images)

                            if index > len(images )-1:
                                indexes[action] = 0
                                index = 0
                            indexes[action] += animation_speed * dt

                            size = 120 if action == "Attack_2" else 60
                            y = start_y + i * (card_h + spacing)

                            # Card
                            card_rect = pygame.Rect(card_x, y, card_w, card_h)
                            pygame.draw.rect(self.screen, COLORS["option_bg"], card_rect, border_radius=10)

                            # Espaço da imagem (placeholder)
                            img_rect = pygame.Rect(card_x + 10, y + 10, 70, 70)
                            pygame.draw.rect(self.screen, COLORS["bg"], img_rect, border_radius=8)
                            pygame.draw.rect(self.screen, COLORS["border"], img_rect, 2, border_radius=8)
                            
                            label_surf = font_text.render(label, True, COLORS["text_name"])
                            key_surf = font_text.render(key, True, COLORS["border"])

                            self.screen.blit(label_surf, (img_rect.right + 15, y + 20))
                            self.screen.blit(key_surf, (img_rect.right + 15, y + 50))

                            icon = images[int(index)].convert_alpha()
                            icon = pygame.transform.scale(icon, (size, size))
                            if size == 60:
                                self.screen.blit(icon, (img_rect.x + 5, img_rect.y + 5))
                            else:
                                self.screen.blit(icon, (img_rect.x + 5-30, img_rect.y + 5-30))

                            

                            
                            

                        for event in pygame.event.get():
                            if event.type == pygame.KEYDOWN:
                                exibir_tutorial=False
                            if event.type == pygame.QUIT:
                                exibir_tutorial = False
                                self.game_running = False
                        pygame.display.flip()

                self.player.le_infos_loop()             
                light_sprites = [sp for sp in self.all_sprites if hasattr(sp, "has_light")]
                
                #NEVE
                

                game_defaul_font = pygame.font.Font(None, 30)
                name_font = pygame.font.SysFont('arial', 18, bold=True)
                last_hour = 0
                self.changing_music = True

                
                game_clock = GameClock(start_hour=10, game_hour_in_real_seconds=90)
            
                #LUZ
                LIGHT_RADIUS = 550
                LIGHT_SPRITE = create_light_sprite(LIGHT_RADIUS)
                lighting = self.light = lighting = LightingSystem(
                    screen_size=(WINDOW_WIDTH, WINDOW_HEIGHT),
                    game_clock=game_clock,
                    light_sprite=LIGHT_SPRITE,
                    light_radius=LIGHT_RADIUS,
                    max_dark_alpha=220,  # quão escuro é o máximo da noite
                )
                
                
                starter_time = pygame.time.get_ticks()
                intensity = 1
                while self.game_running:
                    
                    now = pygame.time.get_ticks()
                    if self.player.is_dead and self.player.death_time and now - self.player.death_time > 4000:
                        self.player.salva_infos_loop()
                        if self.player.loop == 1:
                            som_loop()
                        
                        self.contou_loop=False

                        credits_folder = "credits_txts"  # coloque seus arquivos .txt aqui

                        options = {
                            "font_size": 24,
                            "title_size": 56,
                            "scroll_speed": 50,
                            "music_path": "Sounds/village_background.mp3",
                            "bg_color": (6, 6, 20),
                            "text_color": (240, 240, 240),
                            "title_color": (255, 180, 60),
                        }
                        final = define_final(self.player)
                        ev = EndingEvent(self.screen,final["titulo"], final["texto"], credits_folder, options)
                        ev.run()
                        break
                    
                    lighting.clear_lights()
                    dt = self.clock.tick(240) / 1000
                    self.all_sprites.dt = dt
                    
                        

                    esta_vila = self.human_village_rect.colliderect(self.player.rect)
                    esta_labirinto = self.player.inside_maze
                    esta_floresta_gelo = self.player.inside_ice_florest
                    passou_18h = int(game_clock.get_time_str().split(":")[0]) > 18
                    

                    if esta_vila and passou_18h:
                        self.player.viu_vila_destruida == True

                    #CONQUISTAS DE LOOP
                    loop = self.player.loop
                    

                    if passou_18h and self.background_music != self.battle_music:
                        self.changing_music = True
                        self.background_music = self.battle_music

                    elif esta_vila and self.background_music != self.village_music:
                        self.changing_music = True
                        self.background_music = self.village_music

                    elif esta_labirinto and self.background_music != self.maze_music:
                        self.changing_music = True
                        self.background_music = self.maze_music

                    elif esta_floresta_gelo and self.background_music != self.ice_florest_music:
                        self.changing_music = True
                        self.background_music = self.ice_florest_music

                    elif not esta_labirinto and not esta_vila and not esta_floresta_gelo and self.background_music != self.florest_music and self.background_music != self.battle_music:
                        self.changing_music = True
                        self.background_music = self.florest_music

                    self.change_background_music(dt)

                    self.screen.fill("#3a2e3f")
                    # Relógio na tela
                    time_str = game_clock.get_time_str()
                    
                    hour = int(time_str.split(":")[0])
                    self.all_sprites.hour = hour
                    if hour > 19 and not self.lights_on:
                        self.lights_on = True
                        for sprite in self.all_sprites:
                            if hasattr(sprite, "has_light") and getattr( sprite, "has_light", False):
                                sprite.turn_on()
                    elif hour> 6 and hour < 19 and self.lights_on:
                        self.lights_on = False
                        for sprite in self.all_sprites:
                            if hasattr(sprite, "has_light") and getattr( sprite, "has_light", False):
                                sprite.turn_off()
                    text_surf = game_defaul_font.render(time_str, True, (255, 255, 255))
                    
                    

                    #atualizando coisas
                    

                    
                    mouse_click = False
                    #event loop
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.game_running = False
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_g:
                                self.mostrar_grid_debug = not self.mostrar_grid_debug
                            if event.key == pygame.K_h:
                                self.mostrar_rects = not self.mostrar_rects
                        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                            mouse_click = True
                    #updates
                    self.all_sprites.draw(self.player.rect.center)
                    # print(self.player.rect.center)   
                    # print(self.player.has_emblem)   
                        

                    
                    offset = self.all_sprites.offset 


                    # if self.player.rect:
                    #     orr = self.player.hitbox
                    #     new_hitbox = pygame.FRect(orr.left + offset.x, orr.top + offset.y, orr.width, orr.height)
                    #     pygame.draw.rect(self.screen, (255, 255, 0), new_hitbox, 1)
                        
                    # if self.player.attack_hitbox:
                    #     orr = self.player.attack_hitbox
                    #     new_hitbox = pygame.FRect(orr.left + offset.x, orr.top + offset.y, orr.width, orr.height)
                    #     # pygame.draw.rect(self.screen, (255, 0, 0), new_hitbox, 1)

                    

                    # bx = self.box_1
                    # box_rect = pygame.Rect(bx.left + offset.x, bx.top + offset.y, bx.width, bx.height)
                    # pygame.draw.rect(self.screen, (122, 122, 122), box_rect, 1)  
                    
                    # bx = self.box_2
                    # box_rect = pygame.Rect(bx.left + offset.x, bx.top + offset.y, bx.width, bx.height)
                    # pygame.draw.rect(self.screen, (122, 122, 122), box_rect, 1)  
                    
                    # bx = self.box_3
                    # box_rect = pygame.Rect(bx.left + offset.x, bx.top + offset.y, bx.width, bx.height)
                    # pygame.draw.rect(self.screen, (122, 122, 122), box_rect, 1)  
                    
                    # bx = self.box_4
                    # box_rect = pygame.Rect(bx.left + offset.x, bx.top + offset.y, bx.width, bx.height)
                    # pygame.draw.rect(self.screen, (122, 122, 122), box_rect, 1)  
                    
                    # bx = self.box_5
                    # box_rect = pygame.Rect(bx.left + offset.x, bx.top + offset.y, bx.width, bx.height)
                    # pygame.draw.rect(self.screen, (122, 122, 122), box_rect, 1)  
                    
                    # bx = self.box_6
                    # box_rect = pygame.Rect(bx.left + offset.x, bx.top + offset.y, bx.width, bx.height)
                    # pygame.draw.rect(self.screen, (122, 122, 122), box_rect, 1)  
                    

                    fps = int(self.clock.get_fps())
                    if fps < min_fps:
                        if fps <= 10:
                            fps = 100
                        min_fps = fps
                    fps_text = game_defaul_font.render(f"FPS: {fps}", True, (0, 255, 255))  # verde
                    min_fps_text = game_defaul_font.render(f"Min FPS: {min_fps}", True, (0, 144, 144))  # verde
                    creatures = game_defaul_font.render(f"Criaturas: {len(self.creatures)}", True, (12, 144, 12))  # verde
                    self.screen.blit(fps_text, (10, 30))
                    # self.screen.blit(min_fps_text, (10, 50))
                    self.screen.blit(text_surf, (10, 10))
                    # self.screen.blit(creatures, (10, 80))
                    
                    
                    # --- UPDATE ---
                    # desenhar mapa e objetos
                    lights_on = [sp for sp in light_sprites if sp.on]

                    for l in lights_on:
                        lighting.add_light(Light(l.rect.centerx+offset.x,l.rect.centery+offset.y))


                    


                    snow.update(dt, )
                    snow.draw(self.screen)

                    # --- ILUMINAÇÃO ---
                    lighting.draw(self.screen)

                    player_vect = pygame.Vector2(self.player.rect.center)
                    for creat in self.creatures:
                        creat.daytime = hour

                        # if creat.is_player:
                        #     continue
                        # if creat.is_combating == False:
                        #     continue
                        # new_hitbox = pygame.FRect(creat.rect.left + offset.x, creat.rect.top + offset.y, creat.rect.width, creat.rect.height)
                        # pygame.draw.rect(self.screen, (255, 244, 0), new_hitbox, 1)

                        # new_hitbox = pygame.FRect(creat.hitbox.left + offset.x, creat.hitbox.top + offset.y, creat.hitbox.width, creat.hitbox.height)
                        # pygame.draw.rect(self.screen, (0, 244, 0), new_hitbox, 1)
                        
                        # if creat.is_attacking and creat.attack_hitbox:
                        #     new_hitbox = pygame.FRect(creat.attack_hitbox.left + offset.x, creat.attack_hitbox.top + offset.y, creat.attack_hitbox.width, creat.attack_hitbox.height)
                        #     pygame.draw.rect(self.screen, (255, 0, 0), new_hitbox, 1)
                        # print("Desenhando: ", creat)

                        # if creat.is_player:
                        #     continue
                        if (creat.position_vector - player_vect).length() > WINDOW_WIDTH//2:
                            continue
                        if creat.is_invisible:
                            continue
                        if creat.is_dead:
                            continue
                        
                        if creat.personal_name == "Nash":
                            print(f"HP da NASH: {creat.max_hp}")
                        # Configurações da barra de vida
                        bar_width = 160 
                        bar_height = 14 
                        
                        # Posição acima do personagem
                        bar_x = creat.hitbox.centerx - bar_width // 2 + offset.x
                        bar_y = creat.hitbox.top - 15 + offset.y

                        # 2. Obtenha o texto do personagem
                        if creat.speech_text:
                            txt = str(creat.speech_text)
                            if creat.specie == "ORC" and self.player.has_emblem == False:
                                txt = embaralha_palavras(str(creat.speech_text))
                            draw_simple_speech_bubble(
                                screen=self.screen,
                                font=game_defaul_font,
                                text=txt,
                                x=bar_x + bar_width // 2,  # Posição base do personagem
                                y=bar_y+15,  # Posição base do personagem
                                max_width=bar_width,  # Ajuste conforme necessidade
                                padding=15,
                            )
                        # Calcula a porcentagem de vida
                        health_ratio = creat.hp / creat.max_hp
                        
                        # Define a cor baseada na vida (verde -> amarelo -> vermelho)
                        if health_ratio > 0.6:
                            health_color = (50, 200, 50)    # Verde
                        elif health_ratio > 0.3:
                            health_color = (255, 200, 50)   # Amarelo
                        else:
                            health_color = (220, 50, 50)    # Vermelho
                        
                        # Desenha a barra de vida
                        # Fundo da barra (vazia)
                        if creat.specie != "SAMMY" and creat.specie != "GHOST" and creat.hp < 9999:
                            draw_health_bar(
                                surf=self.screen,
                                x=creat.hitbox.centerx + offset.x, y=bar_y,
                                height=bar_height,
                                current=creat.hp, maximum=creat.max_hp,
                                health_color=health_color,   # vermelho
                                empty_color=(55,55,55),
                                bg_color=(30,30,30),
                                border_color=(15,15,15)
                            )

                        
                        # txt = str(creat.current_action)
                        # fps_text = game_defaul_font.render(txt, True, (12, 12, 12))  # verde
                        # self.screen.blit(fps_text, (bar_x, bar_y-20))
                        
                        # txt = str(creat.action) +": " + str(int(creat.frame_index))
                        # fps_text = game_defaul_font.render(txt, True, (12, 12, 12))  # verde
                        # self.screen.blit(fps_text, (bar_x, bar_y-40))

                        # txt = "Ação - " + str(creat.current_action)
                        # fps_text = game_defaul_font.render(txt, True, (153, 12, 13))  # verde
                        # self.screen.blit(fps_text, (bar_x, bar_y-70))

                    
                    

                    if self.mostrar_grid_debug:
                        offset_x = int(self.all_sprites.offset[0])
                        offset_y = int(self.all_sprites.offset[1])
                        self.screen.blit(self.debug_grid_surface, (offset_x, offset_y))

                    if self.mostrar_rects:
                        for spr in self.collision_sprites:
                        
                            new_hitbox = pygame.FRect(spr.hitbox.left + offset.x, spr.hitbox.top + offset.y, spr.hitbox.width, spr.hitbox.height)
                            new_rect= pygame.FRect(spr.rect.left + offset.x, spr.rect.top + offset.y, spr.rect.width, spr.rect.height)
                            pygame.draw.rect(self.screen, (255, 255, 0), new_hitbox, 1)
                            pygame.draw.rect(self.screen, (255, 0, 255), new_rect, 1)
                    
                    
                        for creat in self.creatures:
                            creat.daytime = hour

                            if creat.is_player:
                                continue
                            new_hitbox = pygame.FRect(creat.rect.left + offset.x, creat.rect.top + offset.y, creat.rect.width, creat.rect.height)
                            pygame.draw.rect(self.screen, (255, 244, 0), new_hitbox, 1)

                            new_hitbox = pygame.FRect(creat.hitbox.left + offset.x, creat.hitbox.top + offset.y, creat.hitbox.width, creat.hitbox.height)
                            pygame.draw.rect(self.screen, (0, 244, 0), new_hitbox, 1)
                            
                            if creat.is_attacking and creat.attack_hitbox:
                                new_hitbox = pygame.FRect(creat.attack_hitbox.left + offset.x, creat.attack_hitbox.top + offset.y, creat.attack_hitbox.width, creat.attack_hitbox.height)
                                pygame.draw.rect(self.screen, (255, 0, 0), new_hitbox, 1)
                    # desenhar_matriz_mapa(self.screen, self.matriz_mapa, GRID_SIZE, offset)

                    if not self.player.is_chatting and now - starter_time > 5000:
                        self.all_sprites.update(dt, )
                        game_clock.update(dt)
                    else:
                        now = pygame.time.get_ticks()
                        chat_end = False
                        if self.player.player_chatting_to:
                            fala, opcoes = self.player.player_chatting_to.escolhe_fala()
                            if opcoes == []:
                                chat_end = True
                                if not self.player.player_chatting_end:
                                    self.player.player_chatting_end = now

                                tempo_espera = 100 * len(str(fala))
                                if now - self.player.player_chatting_end > tempo_espera:
                                    self.player.is_chatting = False
                                    self.player.player_chatting_end = None
                                    self.player.player_chatting_to = None

                            if opcoes != [] or self.player.is_chatting == True :
                                if not self.player.has_emblem:
                                    if "(língua Orc)" in fala:
                                        fala = embaralha_palavras(fala.replace("(língua Orc)", ""))
                                    for i in range(len(opcoes)):
                                        if "(língua Orc)" in opcoes[i]:
                                            opcoes[i] = embaralha_palavras(opcoes[i].replace("(língua Orc)", ""))

                                opcao_escolhida = show_modal(self.screen,font=game_defaul_font, main_text=fala, options=opcoes, max_width=800, chat_end=chat_end, name=str(self.player.player_chatting_to.personal_name))
                                
                                self.player.player_chatting_to.processa_escolha(str(opcao_escolhida))  
                    
                    def efeito_resfriamento(tela: pygame.Surface, intensidade: int):                    
                        """
                        Aplica um efeito visual de congelamento na tela.
                        
                        Args:
                            tela: A surface principal do Pygame (geralmente a 'screen').
                            intensidade: Valor inteiro de 0 a 100 indicando a força do efeito.
                        """
                        if intensidade <= 0:
                            return
                        
                        # Limita a intensidade ao intervalo válido
                        intensidade = max(0, min(100, intensidade))
                        
                        largura, altura = tela.get_size()
                        
                        # Cria uma surface transparente para o overlay
                        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
                        
                        # Tom azul-gelo (quanto maior a intensidade, mais opaco)
                        alpha_azul = int(intensidade / 100 * 180)  # até ~180 de opacidade
                        overlay.fill((100, 180, 255, alpha_azul))
                        
                        # Adiciona cristais de gelo (pontos brancos semi-transparentes)
                        num_cristais = int(intensidade * 15)  # mais intensidade = mais cristais
                        for _ in range(num_cristais):
                            x = randint(0, largura - 1)
                            y = randint(0, altura - 1)
                            raio = randint(1, 4)
                            alpha_cristal = randint(80, 180)
                            pygame.draw.circle(overlay, (255, 255, 255, alpha_cristal), (x, y), raio)
                        
                        # Aplica o overlay na tela
                        tela.blit(overlay, (0, 0))

                    resf_value = 0.02
                    if self.player.aplicar_resfriamento == True:
                        efeito_resfriamento(self.screen,int(intensidade_congelamento))
                        intensidade_congelamento += resf_value
                    else:
                        intensidade_congelamento -= resf_value * 4
                        intensidade_congelamento = 0 if intensidade_congelamento < 0 else intensidade_congelamento
                    self.player.intensidade_resfriamento = intensidade_congelamento
                    
                    
                    mouse_pos = pygame.mouse.get_pos()

                    if self.player.transformations:
                        desenhar_menu_transformacoes(
                            screen=self.screen,
                            sprites=self.player.transformations,
                            mouse_pos=mouse_pos,
                            mouse_click=mouse_click,
                            estado_info={"aberto": True},
                            player=self.player
                        )
                    if self.decided_path != self.char_monitored.rota:
                        self.decided_path = self.char_monitored.rota
                        caminhos = []
                        for c in self.decided_path:
                            x,y = int(c[0]//GRID_SIZE), int(c[1]//GRID_SIZE)
                            caminhos.append((x,y))

                        finais = []
                        for c in self.char_monitored.locais_patrulha:
                            x,y = int(c[0]//GRID_SIZE), int(c[1]//GRID_SIZE)
                            finais.append((x,y))

                        # print(self.char_monitored.locais_patrulha)
                        # self.debug_grid_surface = criar_surface_debug_matriz(
                        #     self.matriz_mapa, 
                        #     tilesize=GRID_SIZE,
                        #     cor_obstaculo=(255, 0, 0, 80),     # Vermelho semi-transparente
                        #     cor_caminho=(00, 0, 255, 80),     # Vermelho semi-transparente
                        #     cor_fundo=(0, 0, 0, 0),
                        #     caminho=caminhos,
                        #     finais=finais
                        # )

                    DURATION = 7000  # ms

                    elapsed = now - starter_time
                    if elapsed < DURATION:
                        alpha = 255 * (1 - elapsed / DURATION)

                        fade = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                        fade.fill((255, 255, 255, int(alpha)))

                        self.screen.blit(fade, (0, 0))
                        # opcao_escolhida = show_modal(self.screen,font=game_defaul_font, main_text=self.player.frases_loops[self.player.loop], options=[], max_width=800, chat_end=elapsed < DURATION, )

                    

                    pygame.display.flip()

                
                

                pygame.quit()

    def setup(self,):
        inicio_setup = perf_counter()
        self.mapa = Map(self.all_sprites, self.collision_sprites, self.creatures, player_group=self.player_group, winter_curse_group = self.winter_curse_group)

        inicio = perf_counter()
        objetos_fixos =[sprite for sprite in self.collision_sprites if isinstance(sprite, CollisionSprites) and sprite.is_getable ==False]
        
        
        matriz_pura = gerar_matriz_mapa(LARGURA_MAPA, ALTURA_MAPA, GRID_SIZE, [])
        self.matriz_mapa = gerar_matriz_mapa(LARGURA_MAPA, ALTURA_MAPA, GRID_SIZE, objetos_fixos)
        matriz = {
            "matriz": self.matriz_mapa,
            "matriz_pura": matriz_pura
        }

        with open("matriz_mapa.json", "w", encoding="utf-8") as f:
            dump(matriz, f, ensure_ascii=False, indent=4)

        inicio = perf_counter()
        with open("matriz_mapa.json", "r", encoding="utf-8") as f:
            dados = load(f)
            matriz = dados["matriz"]
            matriz_pura = dados["matriz_pura"]


        self.matriz_mapa = matriz
        self.all_sprites.world_matriz = self.matriz_mapa
        self.all_sprites.matriz_pura = matriz_pura
        self.all_sprites.winter_curse_group = self.winter_curse_group

        # Cria a surface de debug UMA ÚNICA VEZ
        self.debug_grid_surface = criar_surface_debug_matriz(
            self.matriz_mapa, 
            tilesize=GRID_SIZE,
            cor_obstaculo=(255, 0, 0, 80),     # Vermelho semi-transparente
            cor_caminho=(00, 0, 255, 80),     # Vermelho semi-transparente
            cor_fundo=(0, 0, 0, 0),
            caminho=[],
            finais=[]
            
        )



        #village infos
        self.human_village_rect = pygame.Rect(3800,1400,2200, 2000)
        self.orcs_village_rect = pygame.Rect(360,4358,1500, 1500)
        self.human_pits = [(5528, 2200), (4618, 2836), (4481, 2000) ]
        nina = Nina(self.all_sprites, self.player_group,self.creatures, collision_sprites=self.collision_sprites, creatures_sprites=self.creatures, default_size=DCS-HHDCS - HHHDCS, player=self.player)
        self.player.nina = nina
        alav = PessoaAlavanca(self.all_sprites, self.player_group,self.creatures, collision_sprites=self.collision_sprites, creatures_sprites=self.creatures, default_size=DCS-HHDCS - HHHDCS, player=self.player)
        alav.player = self.player
        # Obi
        obi = Obi(self.all_sprites, self.player_group,self.creatures, collision_sprites=self.collision_sprites, creatures_sprites=self.creatures, npc_name="Obi")
        self.char_monitored = obi
        dash = Dash(self.all_sprites, self.player_group,self.creatures, collision_sprites=self.collision_sprites, creatures_sprites=self.creatures, npc_name="Dash", is_ranged=True, attack_hitbox_list={"Front": (0,0), "Back": (0,0), "Left": (0,0), "Right": (0,0)}, range_distance=550, player=self.player)
        nash = Nash(self.all_sprites, self.player_group,self.creatures, collision_sprites=self.collision_sprites, creatures_sprites=self.creatures, npc_name="Nash", is_ranged=False, default_size=HDCS +HHDCS - 5, team_members=[dash,], attack_hitbox_list={"Front": (150,70), "Back": (150,70), "Left": (130,70), "Right": (130,70),})
        dash.team_members = [nash,]

        rose = Rose(self.all_sprites, self.player_group,self.creatures, collision_sprites=self.collision_sprites, creatures_sprites=self.creatures, npc_name="Rose", is_ranged=False, default_size=HDCS +HHDCS - 7, original_speed=120, actions_to_add=["SpellCast",])
        holz = Holz(self.all_sprites, self.player_group,self.creatures, collision_sprites=self.collision_sprites, creatures_sprites=self.creatures, npc_name="Holz", is_ranged=False, default_size=HDCS +HHDCS + 7, player=self.player)
        holz.NINA = nina
        Fischerin = Villager(self.all_sprites, self.player_group,self.creatures, collision_sprites=self.collision_sprites, creatures_sprites=self.creatures, npc_name="Fischerin", is_ranged=False, default_size=HDCS +HHDCS -3,actions_to_add=["Fishing",] )
        verant = Verant(self.all_sprites, self.player_group,self.creatures, collision_sprites=self.collision_sprites, creatures_sprites=self.creatures, npc_name="Verant", is_ranged=False, default_size=HDCS +HHDCS -3,player=self.player, )
        verloren = Verloren(self.all_sprites, self.player_group,self.creatures, collision_sprites=self.collision_sprites, creatures_sprites=self.creatures, npc_name="Verloren", is_ranged=False, default_size=HDCS +HHDCS,player=self.player, )
        
        initial_position = (5866, 5918)
        explorer_orc = ExplorerOrc(self.all_sprites, collision_sprites=self.collision_sprites, initial_position=initial_position, creatures_sprites=self.creatures, )
        self.creatures.add(explorer_orc)
        explorer_orc.player = self.player
        explorer_orc.hp = 0 
        explorer_orc.is_dying = True

        map_width = self.mapa.map.width * 16 * SCALE
        map_height = self.mapa.map.height * 16 * SCALE


        spawn_points = [
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


        inicio = perf_counter()
        monster_path = join(getcwd(), "Ecosystem","Winter","Monsters", "Winter Slime",)
        slime_images = load_character_images(monster_path, False)
        for i in range(0,10):
            initial_position = choice(spawn_points)
            slime = Slime(self.all_sprites, collision_sprites=self.collision_sprites, initial_position=initial_position, creatures_sprites=self.creatures, creature_images=slime_images)
            self.creatures.add(slime)

        monster_path = join(getcwd(), "Ecosystem","Winter","Monsters", "Chefe dos Goblins",)
        creature_images = load_character_images(monster_path, False)
        for i in range(0,10):
            initial_position = choice(spawn_points)
            goblin = Goblin(self.all_sprites, collision_sprites=self.collision_sprites, initial_position=initial_position, creatures_sprites=self.creatures,creature_images=[])
            self.creatures.add(goblin)

        monster_path = join(getcwd(), "Ecosystem","Winter","Monsters", "Orc do Gelo",)
        creature_images = load_character_images(monster_path, False)
        for i in range(0,5):
            initial_position = choice(spawn_points)
            orc_cacador = OrcCacador(self.all_sprites, collision_sprites=self.collision_sprites, initial_position=initial_position, creatures_sprites=self.creatures,creature_images=[] )
            self.creatures.add(orc_cacador)

        monster_path = join(getcwd(), "Ecosystem","Winter","Monsters", "Winter Ghost",)
        creature_images = load_character_images(monster_path, False)
        for i in range(0,5):
            initial_position = (5660,4928)
            orc_cacador = Ghost(self.all_sprites, collision_sprites=self.collision_sprites, initial_position=initial_position, creatures_sprites=self.creatures,creature_images=[] )
            self.creatures.add(orc_cacador)
        
        monster_path = join(getcwd(), "Ecosystem","Winter","Monsters", "Orc",)
        creature_images = load_character_images(monster_path, False)
        for i in range(0,10):
            initial_position = (1222,4820)
            orc_cacador = Orc(self.all_sprites, collision_sprites=self.collision_sprites, initial_position=initial_position, creatures_sprites=self.creatures, creature_images=[])
            self.creatures.add(orc_cacador)
        

        initial_position = (1271,5368)
        orc = OrcMensageiro(self.all_sprites, collision_sprites=self.collision_sprites, initial_position=initial_position, creatures_sprites=self.creatures, )
        self.creatures.add(orc)

        orc = OrcGuarda(self.all_sprites, collision_sprites=self.collision_sprites, initial_position=initial_position, creatures_sprites=self.creatures, guard_pos=0)
        self.creatures.add(orc)
        orc = OrcGuarda(self.all_sprites, collision_sprites=self.collision_sprites, initial_position=initial_position, creatures_sprites=self.creatures, guard_pos=1)
        self.creatures.add(orc)

        initial_position = (1371,5368)
        orc = ChiefOrc(self.all_sprites, collision_sprites=self.collision_sprites, initial_position=initial_position, creatures_sprites=self.creatures, )
        orc.player = self.player
        self.creatures.add(orc)


        creats_groups = {
            "HUMAN": self.human_sprites,
            "SLIME": self.slime_sprites,
            "GOBLIN": self.goblin_sprites,
            "ORC": self.goblin_sprites,
        }
        inicio = perf_counter()
        for creat in self.creatures:
            if creat.specie in list(creats_groups.keys()):
                creat.specie_group = creats_groups[creat.specie]
                creats_groups[creat.specie].add(creat)
        golem = CrystalGolem(self.all_sprites, collision_sprites=self.collision_sprites, initial_position=(959,1912), creatures_sprites=self.creatures, )
        golem.player = self.player
        self.creatures.add(golem)


        # self.player.human_0 = obi
        # self.player.goblin_0 = goblin
        # self.player.slime_0 = slime
        self.player.orc_0 = explorer_orc
        
        original_player =Player(collision_sprites=[], creatures_sprites=[])
        original_player.hp = 0
        original_player.is_dying = True

        self.player.original_form = original_player
        


        

        

        #LENDO SONS
        pygame.mixer.pre_init(
            frequency=44100,
            size=-16,
            channels=2,
            buffer=512
        )
        pygame.init()
        pygame.mixer.set_num_channels(32)

        som_ataque_espada_1 = pygame.mixer.Sound("Sounds/sword_sound_1.mp3")
        som_ataque_espada_2 = pygame.mixer.Sound("Sounds/sword_sound_2.mp3")
        som_arco_atirando = pygame.mixer.Sound("Sounds/arrow_start.mp3")
        som_flecha_voando = pygame.mixer.Sound("Sounds/arrow_fly.mp3")
        som_slime_andando_1 = pygame.mixer.Sound("Sounds/slime-step-1.mp3")
        som_slime_andando_2 = pygame.mixer.Sound("Sounds/slime-step-2.mp3")
        som_slime_atacando = pygame.mixer.Sound("Sounds/iced_magic.mp3")
        som_golem_atacando = pygame.mixer.Sound("Sounds/golem_attack.mp3")

        som_ghost_andando = pygame.mixer.Sound("Sounds/ghost_step_2.mp3")
        som_ghost_atacando = pygame.mixer.Sound("Sounds/ghost_attack.mp3")

        for creat in self.creatures:
            creat.player_sprite = self.player
                
            if creat.specie == "GOLEM":
                creat.attack_sounds = [som_golem_atacando,]
            else:
                creat.attack_sounds = [som_ataque_espada_1, som_ataque_espada_2]
            creat.arrow_sounds = [som_flecha_voando, ]
            if creat.is_ranged:
                creat.attack_sounds = [som_arco_atirando,]

            if creat.specie == "SLIME":
                creat.walk_sounds = [som_slime_andando_1, som_slime_andando_2]
                creat.attack_sounds = [som_slime_atacando,]
            
            if creat.specie == "GHOST":
                creat.walk_sounds = [som_ghost_andando,]
                creat.attack_sounds = [som_ghost_atacando,]
        
        fim_setup = perf_counter()


if __name__ == "__main__":
    game = Game()

    game.game_init()
