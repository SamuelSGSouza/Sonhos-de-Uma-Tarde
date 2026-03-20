from Utils.classes_raiz import *
from Utils.actions import *


class Villager(Character):
    
    def __init__(self, *groups, collision_sprites:pygame.sprite.Group,creatures_sprites:pygame.sprite.Group, npc_name="Nina", house_point=(0,0), is_ranged=False, attack_hitbox_list={"Front": (150,70), "Back": (150,70), "Left": (70,150), "Right": (70,150),}, range_distance=36, default_size = HDCS + HHDCS, team_members = [], original_speed:int=200, actions_to_add=[], forma_character:str="", initial_position=None):
        scale_attacks = {
            "Obi": 3,
            "Dash": 1,
            "Nash": 3,
            "Rose": 1,
            "Holz": 2,
            "Fischerin": 2,
            "Sammy": 3,
            "Nina": 1,
            "Verant":1,
            "Verloren": 1
        }
        super().__init__(*groups, collision_sprites=collision_sprites,creatures_sprites=creatures_sprites, personal_name=npc_name, scale_on_attack_value=scale_attacks[npc_name], is_ranged=is_ranged, range_distance=range_distance, team_members=team_members)
        self.all_groups= groups
        self.is_player = False
        self.is_human = True
        self.npc_name = npc_name

        self.village_rect = pygame.Rect(3800,1400,2200, 2000)
        self.water_sources = [(5528, 2200), (4618, 2836), (4481, 2000) ]
        self.house_point = house_point

        self.forma = forma_character
        self.armor_type = ""
        self.default_folder_path = join(getcwd(), "NPCs", npc_name, self.forma)
        self.scripts = load_scripts(self.default_folder_path)
        self.default_size = default_size
        self.waking_up_hour = randint(4,7)

        self.action = "Walk"
        self.state, self.frame_index = "Front", 0
        self.actions = ["Walk", "Idle", "Hurt", "Run","Attack_1", "Attack_2", "Dying", "Dead"] + actions_to_add
        self.actions = ["Walk", "Idle", "Hurt", "Run","Attack_1", "Attack_2", "Dying", "Dead", "Beg", "Begging", "WakeUp"] + actions_to_add
        self.load_character_images()
        
        
        self.image = pygame.transform.scale(self.frames[self.action][self.state][0], (self.default_size, self.default_size))
        self.rect = self.image.get_frect(center = (5010, 3010))
        self.hitbox = pygame.FRect(
            self.rect.left + self.rect.width/2,
            self.rect.top + self.rect.height/3+50,
            self.rect.width/2,
            self.rect.height * 2/3
            )
        
        self.hitbox.center = self.rect.center

        self.original_speed = original_speed
        self.direction = pygame.Vector2()

        #ATTACK
        self.animation_speed = 5
        self.attack_hitbox_list = attack_hitbox_list
        self.last_attack_time = pygame.time.get_ticks()
        
        #brain
        self.brains = {
            "Obi": ObiBrain(self,can_attack=True),
            "Dash": LaRochBrothers(self,can_attack=True),
            "Nash": LaRochBrothers(self,can_attack=True),
            "Rose": RoseBrain(self, ),
            "Holz": HolzBrain(self, can_attack=True),
            "Fischerin": FischerinBrain(self, ),
            "Sammy": SammyBrain(self, ),
            "Nina": NinaBrain(self,),
            "Verant": VerantBrain(self,),
            "Verloren": VerlorenBrain(self,)
        }
        self.brain = self.brains[npc_name]
        
        
        
        # === SENSES===
        self.last_called_senses_time = pygame.time.get_ticks()
        self.call_senses_delay = 200


        # === VISÃO: lista de hitboxes à frente ===
        self.vision_max_dist = 150

        # Abordagem simples: “cone” aproximado com N retângulos AABB
        self.vision_segments = 4                               # quantos retângulos formam o cone
        self.vision_step = self.vision_max_dist / self.vision_segments
        self.vision_base_width = self.hitbox.width     # largura inicial
        self.vision_spread_per_seg = max(2, int(self.hitbox.width * 0.12))  # cresce a cada segmento
        self.vision_hitboxes: list[pygame.FRect] = []
        self.update_vision_hitboxes()  # gerar já na criação


        self.max_hp = 100
        self.hp = 100
        self.attack_damage = 10
        self.attacked_by_character = None

        self.attack_1,self.attack_2 = False,False
        self.specie = "HUMAN"

        self.current_id = "1"
        self.pontuacao = 0.0
        self.confiabilidades["ORC"] = 0.3

        self.can_talk =True

        if initial_position:
            self.rect = self.image.get_frect(center = initial_position)
    # ---------------------------------------------------------
    # Direção “para onde está olhando”. Se tiver direction != 0,
    # usa ela; senão usa self.state.
    # ---------------------------------------------------------
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

        hits = pygame.sprite.spritecollide(self, self.creatures_sprites, dokill=False)        
        for hit in hits:
            if hit.personal_name == self.personal_name:
                continue
            if hit == self:
                continue
            if hit.is_human == True:
                continue
            if hit.is_dead == True:
                continue
            return hit
        return None
        for creature in self.creatures_sprites:
            
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

    def update(self, dt: float,):
        self.now = pygame.time.get_ticks()
        self.position_vector = pygame.Vector2(self.rect.center)
        
        if not self.handle_states(dt):
            return
        
        
        

        self.dt = dt
        self.regen_life(self.now)
        # if not self.current_action or self.current_action.is_finished():
            # 1) Fugir de um alvo (por ~1.5s ou até ficar longe 220px):
            # move_action = Move(player, mode="flee", threat=orc, duration_ms=1500, flee_until=220)

            # 2) Ir até um ponto:
            # move_action = Move(npc, mode="to", dest=(1200, 640), duration_ms=3000, arrival_radius=10)

            # 3) Passear (wander) por ~2s:
            # self.current_action = Move(self, mode="wander", duration_ms=2000)

        # 2) Ir até um ponto (encerra ao chegar)
        # creat.current_action = Move(creat, mode='to', target_pos=(1200, 640), arrive_radius=24)

        # # 3) Fugir de um ponto (por 1.2s)
        # creat.current_action = Move(creat, mode='from', from_pos=self.player.hitbox.center, duration_ms=1200, speed_multiplier=1.15)

        # self.current_action.update(dt)
        if self.now - self.last_called_senses_time > self.call_senses_delay:
            percepted_monster =self.sensed_creature()
            self.update_vision_hitboxes()
            self.last_called_senses_time = self.now

            important_infos = {
                "percepted_enemy": None
            }
            if self.brain != None:
                try:
                    choosen_action = self.brain.choose_action(**important_infos)
                except Exception as e:
                    raise Exception(f"Erro ao escolher ação com cérebro {self.brain} do usuário {self}: \n {e}")
                self.current_action = choosen_action
        self.handle_effects()
        
        
        # if now - self.last_called_senses_time >= self.call_senses_delay:
        #     self.last_called_senses_time = now
        # self.move(dt)
        if self.current_action and not self.is_handling_damage:
            self.current_action.update(dt)
        if self.is_running:
            if not self.running_speed_applied:
                self.speed_multipliers.append(self.running_speed_multiplier)
                self.running_speed_applied = True
        else:
            if self.running_speed_applied:
                self.speed_multipliers.remove(self.running_speed_multiplier)
                self.running_speed_applied = False
        
        self.animate(dt)
        self.attack(self.attack_1,self.attack_2)


    def escolhe_fala(self, ):
        fala_data = self.talks.get(self.current_id)
        if not fala_data:
            return "", []
        
        # Verifica se é fim (sem respostas) e aplica reputação
        if not fala_data["respostas"]:
            delta_rep = self.pontuacao * 20  # Exemplo: pontuação alta -> +rep, baixa -> -rep
            return fala_data["fala"], []  # Mostra fala final e encerra
        
        return fala_data["fala"], list(fala_data["respostas"].keys())

    def processa_escolha(self, escolha: str):
        if escolha == "None":
            return
        respostas = self.talks[self.current_id]["respostas"]
        keys = list(respostas.keys())
        escolha = keys[int(escolha)]
        info = respostas[escolha]
        self.current_id = info["next_id"]
        return True

    def __str__(self):
        return self.npc_name
    
class Verloren( Villager):
    def __init__(self, *groups, collision_sprites, creatures_sprites, npc_name="Verloren", house_point=(0, 0), is_ranged=False, attack_hitbox_list={ "Front": (150, 70),"Back": (150, 70),"Left": (70, 150),"Right": (70, 150) }, range_distance=36, default_size=HDCS + HHDCS, team_members=[], original_speed = 80, actions_to_add=[], player=None):
        super().__init__(*groups, collision_sprites=collision_sprites, creatures_sprites=creatures_sprites, npc_name=npc_name, house_point=house_point, is_ranged=is_ranged, attack_hitbox_list=attack_hitbox_list, range_distance=range_distance, default_size=default_size, team_members=team_members, original_speed=original_speed, actions_to_add=actions_to_add)

        self.max_hp = randint(20,30)
        self.hp=self.max_hp
        self.attack_damage = randint(12,20)

        self.encontrou_player = False
        self.player = player
        
        #Falas loop 1 - primeiro encontro
        self.talks_anter_fugir = {
            "1": {
                "fala": "O que? Você conseguiu cruzar essa floresta de fantasmas??? Isso é impressionante!\n Eu me chamo Verloren, sou um estudioso viajante. Vim para esse vale para estudar- bem, não importa. O que acha de fazermos um acordo?",
                "respostas": {
                    "Um acordo?": {"next_id": "2"},
                }
            },
            "2": {
                "fala": "Isso mesmo! Eu sei quase tudo que há para saber sobre o vale. Se conseguir me tirar vivo dessa floresta, eu irei responder uma pergunta sua, o que acha?",
                "respostas": {
                    "Nada feito. Primeiro me conte o que quero saber e depois eu te ajudo a sair daqui.": {"next_id": "end_negativo"},
                    "Fechado! Vou fazer o possível para te tirar daqui.": {"next_id": "end_acordo"}
                }
            },
            "end_acordo": {
                "fala": "Temos um acordo então!",
                "respostas": {}
            },
            "end_negativo": {
                "fala": "Nem pensar! Eu te conto o que você quer saber e você me mata aqui mesmo. Eu prefiro apodrecer aqui do que me vender a tipos como você!",
                "respostas": {}
            }
        }

        self.talks_depois_fugir = {
            "1": {
                "fala": "Impressionante! Você realmente conseguiu! Como prometido, o que você gostaria de perguntar?",
                "respostas": {
                    "Quero saber sobre o Golem": {"next_id": "2_golem"},
                    "Quero saber sobre os Orcs": {"next_id": "2_orcs"},
                    "Quero saber sobre o Coração do Inverno": {"next_id": "2_inverno"},
                }
            },

            #Rota do Golem
            "2_golem": {
                "fala": "Muito bem. Falemos sobre o Golem na entrada da floresta de gelo.\n Minhas pesquisas me mostraram que aquele golem foi criado por algum tipo de elfo do gelo que vivia naquela floresta muito tempo atrás. \n Não consegui determinar exatamente qual foi o fim desse elfo, mas descobri que ele se preocupava com o descontrole da própria criação, então criou uma forma de pará-lo caso as coisas saíssem do controle. \n Próximo à árvore mais alta da floresta de gelo, ele deixou algum tipo de mecanismo que permite deixá-lo inoperante. \n E isso é tudo que eu sei, pois eu mesmo não consegui ir até lá para conferir.",
                "respostas": {
                    "Entendi. Isso ajuda bastante! E o que você vai fazer agora?": {"next_id": "end_fora"},
                }
            },

            #Rota dos Orcs
            "2_orcs": {
                "fala": "Muito bem. Falemos sobre os Orcs.\n\n Os humanos e os orcs dividem espaço nesse vale a muito tempo, por isso conflitos sempre ocorreram. Mas não entenda errado, não estou dizendo que eles vivem sempre em guerra. \n\nHá períodos que o chefe de uma das raças consegue entrar em acordo com a outra e eles vivem um momento de prosperidade, mas isso dura poucas gerações e em seguida o conflito reinicia. \n\n Minha conclusão é que nunca vai haver algo como 'Paz Duradoura' entre as duas espécies.",
                "respostas": {
                    "Entendo... Isso é um pouco triste. Mas e você, o que vai fazer agora?": {"next_id": "end_fora"},
                }
            },

            #Rota do Coração do Inverno
            "2_inverno": {
                "fala": "Oh meu amigo... Somos dois tolos. \n\nTambém ouvi as histórias de como um cristal mágico de poder imensurável estava selado em algum lugar desse vale.\nOuvi também as lendas que dizem que 'Aquele que possuir o poder do cristal, poderá desfazer qualquer erro cometido em sua vida!'. \n\n ... \n\n A verdade, é que não há nenhum cristal.\n\n Procurei por todo esse vale, analisei todos os registros e no fim, parece que isso se mostrou ser apenas uma lenda... feita para atrair idiotas como nós até lugares como esse.",
                "respostas": {
                    "...": {"next_id": "end_fora"},
                }
            },



            "end_fora": {
                "fala": "Vou ficar na vila por alguns dias até descansar e me recuperar, depois vou voltar para a capital. Boa sorte para você meu amigo!",
                "respostas": {}
            },
        }

        self.rect.center = (4368.84765625, 5950.86865234375)
        self.hitbox.center = (4368.84765625, 5950.86865234375)
        self.fechou_acordo = False
        self.resetou_fala = False
        self.saiu_labirinto = False


        vr = self.village_rect #village rect
        matriz_mundo = self.groups()[0].world_matriz

        self.locais_patrulha = []
        for _ in range(0,200):
            x, y = randint(vr.left, vr.right), randint(vr.top, vr.bottom)
            if matriz_mundo[x//GRID_SIZE][y//GRID_SIZE] != 1 and (x,y) not in self.locais_patrulha:
                self.locais_patrulha.append((x,y))
        
        

    def escolhe_fala(self, ):
        #falas 1 a 4 dependem do loop de morte do jogador. 
        #falas 5 só são desbloqueadas depois de falar com o chefe dos orcs e conseguir convencer ele a suspender o ataque.
    
        loop = self.player.loop

        if self.player.inside_maze:
            falas = self.talks_anter_fugir
        else:
            if not self.resetou_fala:
                self.resetou_fala = True
                self.current_id="1"
            falas = self.talks_depois_fugir
            

        
        self.talks = falas
        if self.current_id == "end_acordo":
            self.fechou_acordo = True

        if self.current_id == "end_fora":
            self.saiu_labirinto = True

        fala_data = self.talks.get(self.current_id)
        if not fala_data:
            return "", []
        
        # Verifica se é fim (sem respostas) e aplica reputação
        if not fala_data["respostas"]:
            delta_rep = self.pontuacao * 20  # Exemplo: pontuação alta -> +rep, baixa -> -rep
            return fala_data["fala"], []  # Mostra fala final e encerra
        
        return fala_data["fala"], list(fala_data["respostas"].keys())

class Verant(Villager):
    def __init__(self, *groups, collision_sprites, creatures_sprites, npc_name="Verant", house_point=(0, 0), is_ranged=False, attack_hitbox_list={ "Front": (150, 70),"Back": (150, 70),"Left": (70, 150),"Right": (70, 150) }, range_distance=36, default_size=HDCS + HHDCS, team_members=[], original_speed = 80, actions_to_add=[], player=None):
        super().__init__(*groups, collision_sprites=collision_sprites, creatures_sprites=creatures_sprites, npc_name=npc_name, house_point=house_point, is_ranged=is_ranged, attack_hitbox_list=attack_hitbox_list, range_distance=range_distance, default_size=default_size, team_members=team_members, original_speed=original_speed, actions_to_add=actions_to_add)

        self.max_hp = randint(20,30)
        self.hp=self.max_hp
        self.attack_damage = randint(12,20)

        self.encontrou_player = False
        self.player = player
        
        #Falas loop 1 - primeiro encontro
        self.talks_loop_1 = {
            "1": {
                "fala": "Olha só o que os ventos do sul trouxeram. Bem-vindo viajante, à vila de Tod. A vila mais ao norte do continente!",
                "respostas": {
                    "Obrigado. É um lugar bonito.": {"next_id": "2"},
                    "Vocês parecem isolados aqui.": {"next_id": "2_clima"}
                }
            },
            "2": {
                "fala": "Bonito e resistente, como meu povo. Sou o Chefe, responsável por manter todos alimentados e seguros.",
                "respostas": {
                    "Parece uma tarefa difícil.": {"next_id": "end"}
                }
            },
            "2_clima": {
                "fala": "Isolados, mas autossuficientes. O frio é rigoroso, mas nossos estoques são o orgulho deste vale.",
                "respostas": {
                    "Entendo.": {"next_id": "end"}
                }
            },
            "end": {
                "fala": "Aproveite a estadia. Só não se perca no labirinto ao entardecer.",
                "respostas": {}
            }
        }

        self.talks_loop_2 = {
            "1": {
                "fala": "Olha só o que os ventos do sul trouxeram. Bem-vindo viajante, à vila de Tod. A vila mais ao norte do continente!",
                "respostas": {
                    "Obrigado. Não pude deixar de notar que a vila está bem agitada.": {"next_id": "2_tensao"},
                    "Obrigado pela hospitalidade, mas sabe, pela minha experiência um sorriso sempre esconde algo por trás. E você chefe, o que você está escondendo?": {"next_id": "2_direto"}
                }
            },
            "2_tensao": {
                "fala": "Olhos aguçados. O inverno está chegando e os estoques precisam estar trancados. Segurança é nossa prioridade.",
                "respostas": {
                    "Segurança contra o frio ou contra o que está lá fora?": {"next_id": "end"}
                }
            },
            "2_direto": {
                "fala": "Cuidado com as palavras. Um convidado não deve questionar a hospitalidade de quem o protege.",
                "respostas": {
                    "Entendo.": {"next_id": "end"}
                }
            },
            "end": {
                "fala": "Apenas aproveite o dia. Ele costuma ser curto por aqui.",
                "respostas": {}
            }
        }

        self.talks_loop_3 = {
            "1": {
                "fala": "Olha só o que os ventos do sul trouxeram. Bem-vindo viajante, à vila de Tod. A vila mais ao norte do continente!",
                "respostas": {
                    "Obrigado, chefe. Eu vi uma movimentação estranha dos Orcs enquanto vinha para cá. Sabe o que está acontecendo?": {"next_id": "2_tensao"},
                }
            },
            "2_tensao": {
                "fala": "Foi um ano difícil de caça e as tempestades de inverno estão chegando. Mas não precisa se preocupar, nós somos muito melhores nisso então nossos estoques estão cheios!",
                "respostas": {
                    "Uns morrem de sede enquanto outros se afogam...": {"next_id": "end"}
                }
            },
            "end": {
                "fala": "Não é problema meu! Meus deveres acabam nos limites dessa vila. Aproveite sua estada aqui.",
                "respostas": {}
            }
        }
        
        self.talks_loop_4 = {
            "1": {
                "fala": "Olha só o que os ventos do sul trouxeram. Bem-vindo viajante, à vila de Tod. A vila mais ao norte do continente!",
                "respostas": {
                    "Obrigado, chefe, mas eu trago más notícias: essa vila vai ser atacada pelos Orcs essa noite.": {"next_id": "2_alerta"},
                    "Chefe, eu preciso falar com você com urgência. É sobre os Orcs.": {"next_id": "2_alerta_sutil"}
                }
            },

            "2_alerta": {
                "fala": "Atacada? Orcs não marcham até aqui por acaso. São criaturas selvagens demais para tamanha organização.",
                "respostas": {
                    "Eles estão famintos. Não é um ataque por ódio.": {"next_id": "3_fome"},
                    "Você está subestimando o desespero deles.": {"next_id": "3_desespero"}
                }
            },

            "2_alerta_sutil": {
                "fala": "Se isso for mais uma história para assustar meu povo, poupe seu fôlego. Já temos medo suficiente.",
                "respostas": {
                    "Não é história. Eu vi um Orc cair na floresta.": {"next_id": "3_orc"},
                }
            },

            "3_fome": {
                "fala": "Fome? Todos passam fome no inverno. A diferença é que nós nos preparamos.",
                "respostas": {
                    "Vocês se prepararam… eles não.": {"next_id": "4_frio"}
                }
            },

            "3_desespero": {
                "fala": "Desespero não justifica atravessar minhas muralhas com machados.",
                "respostas": {
                    "Então prepare suas muralhas. Eles virão de qualquer forma.": {"next_id": "4_preparo"}
                }
            },

            "3_orc": {
                "fala": "Um Orc morto não é novidade. A floresta sempre cobra seu preço.",
                "respostas": {
                    "Esse não morreu lutando.": {"next_id": "4_frio"}
                }
            },

            "4_frio": {
                "fala": "Mesmo que fosse verdade… o que espera que eu faça? Abrir meus celeiros para monstros?",
                "respostas": {
                    "Espero que você sobreviva à noite.": {"next_id": "end"},
                }
            },

            "4_preparo": {
                "fala": "Se eles ousarem chegar até aqui, encontrarão lanças e fogo.",
                "respostas": {
                    "Então essa noite vai ser longa.": {"next_id": "end"}
                }
            },

            "end": {
                "fala": "A vila de Tod já enfrentou coisas piores do que boatos. Agora, se me der licença, tenho um povo para proteger.",
                "respostas": {}
            }
        }

        self.talks_loop_5 = {
            "1": {
                "fala": "Olha só o que os ventos do sul trouxeram. Bem-vindo viajante, à vila de Tod. A vila mais ao norte do continente!",
                "respostas": {
                    "Obrigado, chefe, mas eu trago más notícias: essa vila vai ser atacada pelos Orcs essa noite.": {"next_id": "2_alerta"},
                    "Chefe, eu preciso falar com você com urgência. É sobre os Orcs.": {"next_id": "2_alerta_sutil"}
                }
            },

            "2_alerta": {
                "fala": "Atacada? Orcs não marcham até aqui por acaso. São criaturas selvagens demais para tamanha organização.",
                "respostas": {
                    "Eles estão famintos. Não é um ataque por ódio.": {"next_id": "3_fome"},
                    "Você está subestimando o desespero deles.": {"next_id": "3_desespero"}
                }
            },

            "2_alerta_sutil": {
                "fala": "Se isso for mais uma história para assustar meu povo, poupe seu fôlego. Já temos medo suficiente.",
                "respostas": {
                    "Não é história. Eu vi um Orc cair na floresta.": {"next_id": "3_orc"},
                }
            },

            "3_fome": {
                "fala": "Fome? Todos passam fome no inverno. A diferença é que nós nos preparamos.",
                "respostas": {
                    "Vocês se prepararam… eles não.": {"next_id": "4_frio"}
                }
            },

            "3_desespero": {
                "fala": "Desespero não justifica atravessar minhas muralhas com machados.",
                "respostas": {
                    "Então prepare suas muralhas. Eles virão de qualquer forma.": {"next_id": "4_preparo"}
                }
            },

            "3_orc": {
                "fala": "Um Orc morto não é novidade. A floresta sempre cobra seu preço.",
                "respostas": {
                    "Esse não morreu lutando.": {"next_id": "4_frio"}
                }
            },

            "4_frio": {
                "fala": "Mesmo que fosse verdade… o que espera que eu faça? Abrir meus celeiros para monstros?",
                "respostas": {
                    "Espero que você sobreviva à noite.": {"next_id": "end"},
                }
            },

            "4_preparo": {
                "fala": "Se eles ousarem chegar até aqui, encontrarão lanças e fogo.",
                "respostas": {
                    "Então essa noite vai ser longa.": {"next_id": "end"}
                }
            },

            "end": {
                "fala": "A vila de Tod já enfrentou coisas piores do que boatos. Agora, se me der licença, tenho um povo para proteger.",
                "respostas": {}
            }
        }

        self.talks_loop_5_sucesso = {
            "1": {
                "fala": (
                    "Vejo pelo seu rosto que algo mudou. \n"
                    "Ou você traz boas notícias… ou veio me dizer que eu estava certo desde o início."
                ),
                "respostas": {
                    "O ataque foi suspenso.": {"next_id": "2_suspenso"},
                    "Eu falei com o chefe dos orcs.": {"next_id": "2_suspenso"}
                }
            },

            "2_suspenso": {
                "fala": (
                    "Suspenso? \n"
                    "Orcs não suspendem ataques. Eles vencem ou morrem tentando."
                ),
                "respostas": {
                    "Eles estão famintos, não sedentos por guerra.": {"next_id": "3_fome"},
                    "Eles recuaram porque ainda há uma saída sem sangue.": {"next_id": "3_saida"}
                }
            },

            "3_fome": {
                "fala": (
                    "Fome… \n"
                    "Meu povo também passa fome no inverno. A diferença é que eu os preparei."
                ),
                "respostas": {
                    "Preparou alguns, enquanto outros morrem do lado de fora.": {"next_id": "4_confronto"},
                }
            },

            "3_saida": {
                "fala": (
                    "E essa saída exige o quê? \n"
                    "Que eu abra meus celeiros para monstros?"
                ),
                "respostas": {
                    "Exige racionamento. Para todos.": {"next_id": "4_racionamento"},
                    "Exige que você governe, não acumule.": {"next_id": "4_confronto"}
                }
            },

            "4_confronto": {
                "fala": (
                    "Cuidado. \n"
                    "Você fala como se entendesse o peso de manter uma vila inteira viva."
                ),
                "respostas": {
                    "Eu entendo o peso de enterrar vilas inteiras.": {"next_id": "5_verdade"},
                    "Você não está protegendo seu povo. Está protegendo seu controle.": {"next_id": "5_verdade"}
                }
            },

            "4_racionamento": {
                "fala": (
                    "Racionamento causa pânico. \n"
                    "Pânico vira revolta. Revolta derruba chefes."
                ),
                "respostas": {
                    "A guerra derruba tudo.": {"next_id": "5_verdade"},
                    "Dividir comida custa menos do que reconstruir cinzas.": {"next_id": "5_verdade"}
                }
            },

            "5_verdade": {
                "fala": (
                    "… \n"
                    "Se meu povo souber que eu escondi comida enquanto outros morriam…"
                ),
                "respostas": {
                    "Então seja lembrado como quem mudou o curso da história.": {"next_id": "end_positivo"},
                    "Ou seja lembrado como o último chefe de Tod.": {"next_id": "end_positivo"}
                }
            },

            "end_positivo": {
                "fala": (
                    "Você me colocou diante de uma escolha que evitei por tempo demais. \n"
                    "Se os Orcs ficarem… haverá regras. Vigilância. Troca justa."
                    "\n\nMas se houver paz esta noite… será porque alguém teve coragem de dividir."
                ),
                "respostas": {}
            }
        }

        self.talks_loop_5_fracasso = {
            "1": {
                "fala": (
                    "Vejo pelo seu rosto que algo mudou. \n"
                    "Aquelas criaturas não aceitaram um acordo, não é?."
                ),
                "respostas": {
                    "Eu falhei em convencê-lo.": {"next_id": "2_suspenso"},
                    "Você é um tolo se está mais preocupado em estar certo do que com o futuro da vila.": {"next_id": "2_suspenso"}
                }
            },

            "2_suspenso": {
                "fala": (
                    "Nem por um segundo eu acreditei que seria possível dialogar com aquelas criaturas."
                ),
                "respostas": {
                    "Então agora só resta o derramamento de sangue...": {"next_id": "3_fome"},
                }
            },

            "3_fome": {
                "fala": "Exato! E Tod irá impedir esses selvagens!",
                "respostas": {}
            },


        }

        vr = self.village_rect #village rect
        matriz_mundo = self.groups()[0].world_matriz

        self.locais_patrulha = []
        for _ in range(0,200):
            x, y = randint(vr.left, vr.right), randint(vr.top, vr.bottom)
            if matriz_mundo[x//GRID_SIZE][y//GRID_SIZE] != 1 and (x,y) not in self.locais_patrulha:
                self.locais_patrulha.append((x,y))
        
    def escolhe_fala(self, ):
        #falas 1 a 4 dependem do loop de morte do jogador. 
        #falas 5 só são desbloqueadas depois de falar com o chefe dos orcs e conseguir convencer ele a suspender o ataque.
    
        loop = self.player.loop

        if self.player.falou_chefe_orcs:
            if self.player.convenceu_chefe_orcs:
                falas = {
                    1: self.talks_loop_5_sucesso,
                }
            else:
                falas = {
                    1: self.talks_loop_5_fracasso,
                }
        else:
            falas = {
                1: self.talks_loop_1,
                2: self.talks_loop_2,
                3: self.talks_loop_3,
                4: self.talks_loop_4,
                5: self.talks_loop_5,
            }
        if loop not in falas.keys():
            loop = choice(list(falas.keys()))

        
        self.talks = falas[loop]

        fala_data = falas[loop].get(self.current_id)
        if not fala_data:
            return "", []
        
        # Verifica se é fim (sem respostas) e aplica reputação
        if not fala_data["respostas"]:
            self.player.falou_chefe_vila = True
            delta_rep = self.pontuacao * 20  # Exemplo: pontuação alta -> +rep, baixa -> -rep
            return fala_data["fala"], []  # Mostra fala final e encerra
        
        return fala_data["fala"], list(fala_data["respostas"].keys())

class PessoaAlavanca(Villager):
    def __init__(self, *groups, collision_sprites, creatures_sprites, npc_name="Nina", house_point=(0, 0), is_ranged=False, attack_hitbox_list={ "Front": (150, 70),"Back": (150, 70),"Left": (70, 150),"Right": (70, 150) }, range_distance=36, default_size=HDCS - HHDCS, team_members=[], original_speed = 200, actions_to_add=[], player):
        super().__init__(*groups, collision_sprites=collision_sprites, creatures_sprites=creatures_sprites, npc_name=npc_name, house_point=house_point, is_ranged=is_ranged, attack_hitbox_list=attack_hitbox_list, range_distance=range_distance, default_size=default_size, team_members=team_members, original_speed=original_speed, actions_to_add=actions_to_add, )
        self.brain = PessoaAlavancaBrain(self,)
        self.encontrou_player = False
        self.player = player
        self.rect.center = (2398.87744140625, 120.6853256225586)
        self.hitbox.center = (2398.87744140625, 120.6853256225586)

        self.sons_alavanca = [pygame.mixer.Sound("Sounds/lever_sound.mp3"), ]
        self.sound_ok = False
        self.talks = {
            "1": {  # Introdução
                "fala": "(Parece que tem uma alavanca aqui)",
                "respostas": {
                    "Puxar": {"pontuacao": 0.8, "next_id": "end_puxou"},
                    "Não Puxar": {"pontuacao": 0.8, "next_id": "end_nao_puxou"},
                }
            },
            "end_nao_puxou": { 
                "fala": "Eu não sei o que isso faz, então é melhor não mexer.",
                "respostas": {}
            },
            "end_puxou": { 
                "fala": "Alguma coisa aconteceu, mas o que?...",
                "respostas": {}
            },
        }
        self.hp = 99999
        self.personal_name = ""
        
    def escolhe_fala(self, ):
        
        if self.current_id == "end_puxou" and not self.sound_ok:
            play_noise(self, self.sons_alavanca, cooldown=1000, volume=0.2)
            self.sound_ok = True
            self.player.puxou_alavanca = True

        fala_data = self.talks.get(self.current_id)
        if not fala_data:
            return "", []
        
        # Verifica se é fim (sem respostas) e aplica reputação
        if not fala_data["respostas"]:
            delta_rep = self.pontuacao * 20  # Exemplo: pontuação alta -> +rep, baixa -> -rep
            return fala_data["fala"], []  # Mostra fala final e encerra
        
        return fala_data["fala"], list(fala_data["respostas"].keys())

class Nina(Villager):
    def __init__(self, *groups, collision_sprites, creatures_sprites, npc_name="Nina", house_point=(0, 0), is_ranged=False, attack_hitbox_list={ "Front": (150, 70),"Back": (150, 70),"Left": (70, 150),"Right": (70, 150) }, range_distance=36, default_size=HDCS - HHDCS, team_members=[], original_speed = 200, actions_to_add=[], player):
        super().__init__(*groups, collision_sprites=collision_sprites, creatures_sprites=creatures_sprites, npc_name=npc_name, house_point=house_point, is_ranged=is_ranged, attack_hitbox_list=attack_hitbox_list, range_distance=range_distance, default_size=default_size, team_members=team_members, original_speed=original_speed, actions_to_add=actions_to_add, )
        self.encontrou_player = False
        self.player = player
        self.max_hp=20
        self.hp= 20
        #Falas loop 1
        self.talks = {
            "1": {  # Encontro inicial com Nina
                "fala": "Está perdido, viajante?",
                "respostas": {
                    "Talvez um pouco. ": {"pontuacao": 0, "next_id": "rota_1_1"},
                    "Acho que estou exatamente onde eu deveria estar.": {"pontuacao": 0, "next_id": "rota_2_1"},
                    "#1 Na verdade, estou aqui pra te tirar dessa montanha": {"pontuacao": 0, "next_id": "rota_secreta_1"},
                }
            },
            "rota_secreta_1": { 
                "fala": "O que? Do que está falando?",
                "respostas": {
                    "Se ficar aqui, você vai morrer. ": {"pontuacao": 0, "next_id": "rota_secreta_1_1"},
                    "#2 Está acontecendo uma movimentação estranha dos Orcs no vale. Isso está assustando os monstros e todos eles estão fugindo para cá": {"pontuacao": 0, "next_id": "end_acompanhar"},
                }
            },
            "rota_secreta_1_1": { 
                "fala": "Isso é algum tipo de ameaça?",
                "respostas": {
                    "Escuta, não dá tempo de explicar. Eu preciso que você venha comigo agora mesmo. ": {"pontuacao": 0, "next_id": "end_ficar"},
                    "#3 Nina, eu estou aqui para te ajudar. Precisamos ir agora!": {"pontuacao": 0, "next_id": "end_acompanhar"},
                }
            },
            "rota_1_1": {  
                "fala": "Bom, pra começar, você está no Vale do Retorno, o vale mais ao norte do continente! Você veio aqui pelo Coração do Inverno, certo?",
                "respostas": {
                    "Isso mesmo! Você sabe algo sobre ele?": {"pontuacao": 0, "next_id": "rota_1_2"},
                    "Esse 'Coração do Inverno', o que é?": {"pontuacao": 0, "next_id": "rota_1_2"},
                }
            },
            "rota_1_2": {  
                "fala": "'O Coração do Inverno' é uma jóia com poderes lendários, que dizem ser a fonte das grandes nevascas que acontecem em todo o norte do continente. A lenda conta que aquele que o possuir pode não apenas governas todas as terras de gelo, mas também realizar um único desejo de proporções ilimitadas.",
                "respostas": {
                    "Entendo... Mas não é por isso que estou aqui.": {"pontuacao": 0, "next_id": "end_1"},
                    "Fale mais, por favor.": {"pontuacao": 0, "next_id": "rota_1_3"},
                }
            },
            "rota_1_3": {  
                "fala": "Os viajantes que vem sempre dizem que o Coração deve estar por aqui, mas já procuraram em todo o vale e nunca encontraram. Nos últimos anos tem aparecido cada vez menos gente procurando",
                "respostas": {
                    "E quanto a você? Acha que ele existe e está escondido nesse vale?": {"pontuacao": 0, "next_id": "rota_1_4"},
                    "Eu não sou como eles, pode apostar que eu vou encontrar o Coração!": {"pontuacao": 0, "next_id": "end_1"},
                }
            },
            "rota_1_4": {  
                "fala": "Sendo bem honesta, viajante, acho que são só histórias que alguém espalhou por aí e todos passaram a acreditar. Vivi minha vida inteira nesse vale, vi inúmeros caçadores de recompensa e viajantes vagarem por aqui tentando encontrar esse Coração e todos eles sempre iam embora com decepção e cansaço em seu olhar... Então não, acredito que essa jóia não existe. E se ela existe, ela não está aqui.",
                "respostas": {
                    "Entendo...Agradeço pelas informações! Mesmo assim, pretendo gastar um pouco de tempo procurando por ela.": {"pontuacao": 0, "next_id": "end_1"},
                    "Agradeço pelas informações! Só mais uma coisa, pode me dizer seu nome?": {"pontuacao": 0, "next_id": "end_2"},
                }
            },
            "rota_2_1": {  
                "fala": "Você é algum tipo de estudioso ou pesquisador? O último viajante que passou por aqui falando assim foi um elfo junto com um bando de guarda-costas.",
                "respostas": {
                    "O que aconteceu com esse elfo?": {"pontuacao": 0, "next_id": "rota_2_2"},
                    "Esse estudioso viajante descobriu alguma coisa?": {"pontuacao": 0, "next_id": "rota_1_3"},
                }
            },
            "rota_2_2": {  
                "fala": "Ele e os ajudantes foram para a floresta dos fantasmas, falando que o Coração TINHA que estar lá. Isso já faz alguns dias e ele ainda não retornou, então acho que deve ter morrido por lá.",
                "respostas": {
                    "Esse 'Coração', o que ele é?": {"pontuacao": 0, "next_id": "rota_1_2"},
                    "Me pergunto se ele realmente existe...": {"pontuacao": 0, "next_id": "rota_1_3"},
                }
            },


            "end_1": {  
                "fala": "Bom, seja como for, se passar pela vila não se esqueça de contratar os serviços do lenhador. Ele é o melhor no que faz.",
                "respostas": {}
            },
            "end_2": {  
                "fala": "Meu nome? He he...  Eu sou a Nina, muito prazer viajante! Quando passar pela vila não se esqueça de contratar os serviços do meu pai. Ele é o Holz, lenhador da vila.",
                "respostas": {}
            },
            "end_acompanhar": {  
                "fala": "Com você sa- Não, tudo bem. Eu vou com você!",
                "respostas": {}
            },
            "end_ficar": {  
                "fala": "Eu não sei quem, ou o que você é, então não vou a lugar nenhum com você!",
                "respostas": {}
            },

        }

        self.locais_patrulha = []
        vr_left = 3972 #village rect
        vr_right = 6000
        vr_top = 0
        vr_bottom = 1075
        vr = self.village_rect #village rect
        matriz_mundo = self.groups()[0].world_matriz
        self.acompanhar_player = False
        self.locais_patrulha = []
        self.locais_montanha = [(3299, 518), (3400, 135)]
        self.ficar_vila = False
        for _ in range(0,200):
            x, y = randint(vr.left, vr.right), randint(vr.top, vr.bottom)
            if matriz_mundo[x//GRID_SIZE][y//GRID_SIZE] != 1 and (x,y) not in self.locais_patrulha:
                self.locais_patrulha.append((x,y))

    def escolhe_fala(self, ):
        self.player.falou_nina = True

        fala_data = self.talks.get(self.current_id)
        if not fala_data:
            return "", []
        
        if self.current_id == "end_acompanhar":
            self.acompanhar_player = True
        
        if self.current_id == "end_2":
            self.player.sabe_nome_nina=True

        # Verifica se é fim (sem respostas) e aplica reputação
        if not fala_data["respostas"]:
            delta_rep = self.pontuacao * 20  # Exemplo: pontuação alta -> +rep, baixa -> -rep
            return fala_data["fala"], []  # Mostra fala final e encerra
        
        respostas = self.player.verifica_respostas(list(fala_data["respostas"].keys()))
        return fala_data["fala"], respostas

class Dash(Villager):
    def __init__(self, *groups, collision_sprites, creatures_sprites, npc_name="Nina", house_point=(0, 0), is_ranged=False, attack_hitbox_list={ "Front": (150, 70),"Back": (150, 70),"Left": (70, 150),"Right": (70, 150) }, range_distance=36, default_size=HDCS + HHDCS, team_members=[], original_speed = 200, actions_to_add=[], player=None):
        super().__init__(*groups, collision_sprites=collision_sprites, creatures_sprites=creatures_sprites, npc_name=npc_name, house_point=house_point, is_ranged=is_ranged, attack_hitbox_list=attack_hitbox_list, range_distance=range_distance, default_size=default_size, team_members=team_members, original_speed=original_speed, actions_to_add=actions_to_add)
        self.player = player
        self.talks = {
        "1": {  # Introdução
            "fala": "Salve viajante, está perdido?",
            "respostas": {
                "Olá amigo, estou apenas de passagem.  E vocês?": {"pontuacao": 0.8, "next_id": "rota_1"},
                "Só estou procurando uma coisa, não se preocupem comigo.": {"pontuacao": -0.6, "next_id": "rota_2"},
                "#7 É... As pessoas me perguntam muito isso por aqui": {"pontuacao": 0.2, "next_id": "rota_secreta"},
            }
        },
        "rota_1": { 
            "fala": "Eu sou o Dash e Essa é a Nash, somos os caçadores da vila. Você disse que está só de passagem, certo? Então é melhor ir embora logo, senão você pode se arrepender.",
            "respostas": {
                "Por que diz isso?": {"pontuacao": 0.8, "next_id": "end_conselho"},
                "#9 Fala isso por causa das nevascas?": {"pontuacao": -0.6, "next_id": "rota_secreta_2"},
            }
        },
        "rota_secreta_1_1": { 
            "fala": "Para ser sincero com você, também estamos tentando descobrir. Notamos uma movimentação estranha dos monstros e dos Orcs, mas ainda não temos certeza do que está acontecendo.",
            "respostas": {
                "#8 Eu notei que a quantidade de monstros aqui no vale está diminuindo.": {"pontuacao": 0.8, "next_id": "end_explicacao"},
                "Espero que esteja tudo bem": {"pontuacao": -0.6, "next_id": "end_esperanca"},
            }
        },
        
        "rota_secreta_1_2_2": { 
            "fala": "Muitos anos antes disso acontecer, parece que os Orcs também tiveram um período de fartura e cresceram em número e força.\n\nEles precisavam de recursos para poder alimentar tantas bocas, então atacaram a vila humana.\n\nOs humanos receberam ajuda da capital então os Orcs foram recharçados e quase entraram em extinsão por aqui.",
            "respostas": {
                "Você odeia os Orcs?": {"pontuacao": 0.8, "next_id": "rota_secreta_1_2_3"},
                "Parece um ciclo sem fim de morte e sangue": {"pontuacao": 0.8, "next_id": "rota_secreta_1_2_3"},
            }
        },
        "rota_secreta_1_2_1": { 
            "fala": "Alguns vão dizer que foi um sucesso e que conseguimos reduzir a população de Orcs, mas a verdade é que muito sangue foi derramado dos dois lados.\n\nNão Houve vencedores.",
            "respostas": {
                "Isso parece uma atitude radical e cruel": {"pontuacao": 0.8, "next_id": "rota_secreta_1_2_2"},
                "Os Orcs realmente eram uma ameaça tão grande assim?": {"pontuacao": 0.8, "next_id": "rota_secreta_1_2_2"},
            }
        },
        "rota_secreta_1_2": { 
            "fala": "Fico feliz que diga isso, amigo. Se fosse a alguns anos atrás você não iria querer passar nem um dia por aqui. \n\nOs Orcs estavam se reproduzindo muito rápido, então o chefe da vila na época organizou uma expedição de extermínio, por medo que eles pudessem dominar o vale.",
            "respostas": {
                "E o que aconteceu?": {"pontuacao": 0.8, "next_id": "rota_secreta_1_2_1"},
            }
        },
        "rota_secreta": { 
            "fala": "Não se preocupe, amigo. Isso são apenas as pessoas daqui sendo simpáticas... ou pelo menos tentando.",
            "respostas": {
                "Eu agradeço por isso. Aqui parece um bom lugar para se viver.": {"pontuacao": 0.8, "next_id": "rota_secreta_1_1"},
                "Eu agradeço por isso. Aproveitando que estamos aqui, como estão as coisas aqui no vale?": {"pontuacao": -0.6, "next_id": "rota_secreta_1_2"},
            }
        },
        "rota_secreta_2": { 
            "fala": "Ah então você já  sabe das nevascas? Claro, tem elas também, mas alguma coisa estranha está acontecendo aqui no vale. Eu e a Nash estamos tentando descobrir o que é. Estamos agora indo nos infiltrar no lar dos Orcs para ver se descobrimos alguma coisa",
            "respostas": {
                "Se descobrirem algo eu gostaria de saber também. Talvez eu possa ajudar com algo": {"pontuacao": 0.8, "next_id": "end_ajuda"},
                "#10 Na verdade, eu já sei o que está acontecendo. Os Orcs estão se preparando para atacar a vila....": {"pontuacao": -0.6, "next_id": "rota_secreta_2"},
            }
        },
        "rota_secreta_3": { 
            "fala": "O que?! Como você sabe disso???",
            "respostas": {
                "Eu não posso te contar": {"pontuacao": 0.8, "next_id": "end_nao_confiavel"},
                "(Falar sobre o loop)": {"pontuacao": -0.6, "next_id": "end_nao_confiavel"},
                "Também estava preocupado com a movimentação estranha, então me infiltrei no covil deles e descobri tudo.": {"pontuacao": -0.6, "next_id": "end_confiavel"},
            }
        },
        "rota_2": { 
            "fala": "Tenha cuidado então. Esse vale é mais perigoso e traiçoeiro do que parece.",
            "respostas": {
                "Por que diz isso?": {"pontuacao": 0.8, "next_id": "end_conselho"},
            }
        },

        
        "end_conselho": {
            "fala": "É apenas um pequeno conselho. Seguir ou não, é escolha sua.",
            "respostas": {}
        },
        "end_ajuda": {
            "fala": "Obrigado amigo! Se descobrirmos algo, vamos te avisar também.",
            "respostas": {}
        },
        "end_nao_confiavel": {
            "fala": "Eu e a Nash já devíamos ter imaginado que os Orcs poderiam atacar depois de tudo que aconteceu, mas parece que você não vai falar a verdade sobre o que sabe, então parece que não dá pra confiar em você.",
            "respostas": {}
        },
        "end_confiavel": {
            "fala": "Droga! depois do que aconteceu esse ano nós devíamos ter imaginado. Obrigado pelas informações amigo! Vamos voltar para a vila e fazer todos se prepararem.",
            "respostas": {}
        },
        "end_esperanca": {
            "fala": "É o que todos esperamos.",
            "respostas": {}
        },
        "end_explicacao": {
            "fala": "Oh... Você tem olhos de caçador, viajante. Parece que os Orcs estão se movendo de forma estranha e isso está afugentando os monstros, que estão correndo para a montanha. \n\nA intuição da Nash está dizendo que os Orcs tem alguma coisa a ver com isso, então vamos nos infiltrar na aldeia deles pra ver o que descobrimos. se descobrirmos alguma coisa a gente te avisa.",
            "respostas": {}
        },
        "rota_secreta_1_2_3": { 
            "fala": "Vivi minha vida inteira como caçador junto da minha irmã e tivemos que aprender quase tudo sozinhos.\n\nA maior lição que aprendemos foi que na natureza não existe lado certo ou errado, bom ou mal, são apenas seres lutando pela própria sobrevivência.\n\nMas admito que eu, particulamente, gostaria de poder viver em paz com os Orcs.",
            "respostas": {}
        },
    }
        
        self.hp = 30
        self.max_hp = 30
        self.attack_damage = randint(12,20)
        self.soube_ataque = False
    
    def escolhe_fala(self, ):
        fala_data = self.talks.get(self.current_id)
        if not fala_data:
            return "", []
        

        # Verifica se é fim (sem respostas) e aplica reputação
        if not fala_data["respostas"]:
            delta_rep = self.pontuacao * 20  # Exemplo: pontuação alta -> +rep, baixa -> -rep
            return fala_data["fala"], []  # Mostra fala final e encerra
        
        respostas = self.player.verifica_respostas(list(fala_data["respostas"].keys()))
        return fala_data["fala"], respostas


class Nash(Villager):
    def __init__(self, *groups, collision_sprites, creatures_sprites, npc_name="Nina", house_point=(0, 0), is_ranged=False, attack_hitbox_list={ "Front": (150, 70),"Back": (150, 70),"Left": (70, 150),"Right": (70, 150) }, range_distance=36, default_size=HDCS + HHDCS, team_members=[], original_speed = 200, actions_to_add=[]):
        super().__init__(*groups, collision_sprites=collision_sprites, creatures_sprites=creatures_sprites, npc_name=npc_name, house_point=house_point, is_ranged=is_ranged, attack_hitbox_list=attack_hitbox_list, range_distance=range_distance, default_size=default_size, team_members=team_members, original_speed=original_speed, actions_to_add=actions_to_add)
        
        self.max_hp = 120
        self.hp = self.max_hp

        self.talks = {
            "1": {  # Introdução
                "fala": "O que você quer? Nós já nos conhecemos?",
                "respostas": {
                    "Só estou de passagem.": {"pontuacao": 0.6, "next_id": "rota_1"},
                    "#11 Você é uma caçadora? Os monstros da região parecem": {"pontuacao": 0.6, "next_id": "rota_secreta"},
                }
            },
            
        }
        
        self.attack_damage = randint(12,20)
        self.soube_ataque = False

class Obi(Villager):
    def __init__(self, *groups, collision_sprites, creatures_sprites, npc_name="Nina", house_point=(0, 0), is_ranged=False, attack_hitbox_list={ "Front": (150, 70),"Back": (150, 70),"Left": (70, 150),"Right": (70, 150) }, range_distance=36, default_size=HDCS + HHDCS, team_members=[], original_speed = 200, actions_to_add=[]):
        super().__init__(*groups, collision_sprites=collision_sprites, creatures_sprites=creatures_sprites, npc_name=npc_name, house_point=house_point, is_ranged=is_ranged, attack_hitbox_list=attack_hitbox_list, range_distance=range_distance, default_size=default_size, team_members=team_members, original_speed=original_speed, actions_to_add=actions_to_add)
        self.locais_patrulha = []
        vr = self.village_rect #village rect
        matriz_mundo = self.groups()[0].world_matriz

        self.locais_patrulha = []
        for _ in range(0,200):
            x, y = randint(vr.left, vr.right), randint(vr.top, vr.bottom)
            if matriz_mundo[x//GRID_SIZE][y//GRID_SIZE] != 1 and (x,y) not in self.locais_patrulha:
                self.locais_patrulha.append((x,y))
        
        self.talks = {
        "1": {  # Introdução
            "fala": "Pare aí. A vila anda tensa, e eu não deixo qualquer um circular livremente. Sou Obi, guarda da vila. Diga por que está aqui.",
            "respostas": {
                "Só estou de passagem. Não quero problemas.": {"pontuacao": 0.3, "next_id": "2_neutra"},
                "Posso ajudar na patrulha se precisar.": {"pontuacao": 0.6, "next_id": "2_positiva"},
                "Isso é um interrogatório ou você sempre trata assim?": {"pontuacao": -0.5, "next_id": "2_negativa"},
                "Saia da minha frente ou vai se arrepender.": {"pontuacao": -1.0, "next_id": "end_negativo"}
            }
        },
        "2_positiva": {
            "fala": "Ajuda é bem-vinda… desde que siga ordens. Temos relatos de movimentação estranha perto do portão norte.",
            "respostas": {
                "Posso vigiar enquanto você faz a ronda interna.": {"pontuacao": 0.7, "next_id": "end_positivo"},
                "Prefiro investigar sozinho e te reportar depois.": {"pontuacao": 0.4, "next_id": "3_positiva"},
                "Só se tiver alguma recompensa envolvida.": {"pontuacao": -0.3, "next_id": "2_neutra"}
            }
        },
        "2_negativa": {
            "fala": "Atitude suspeita. Não me obrigue a te retirar da vila à força.",
            "respostas": {
                "Calma, só estava testando. Vamos conversar.": {"pontuacao": 0.2, "next_id": "3_neutra"},
                "Tente a sorte.": {"pontuacao": -0.8, "next_id": "end_negativo"},
                "O que está acontecendo exatamente?": {"pontuacao": 0.1, "next_id": "2_neutra"}
            }
        },
        "2_neutra": {
            "fala": "Se ficar, siga as regras. Patrulha reforçada rende 15 moedas por turno.",
            "respostas": {
                "Aceito. Ordem é ordem.": {"pontuacao": 0.4, "next_id": "end_positivo"},
                "Quinze é pouco. Quero 30.": {"pontuacao": -0.2, "next_id": "3_neutra"},
                "Prefiro não me envolver.": {"pontuacao": -0.5, "next_id": "end_negativo"}
            }
        },
        "3_positiva": {
            "fala": "Você se move bem e não chama atenção. Isso é útil pra um guarda.",
            "respostas": {
                "Fico feliz em ajudar a manter a vila segura.": {"pontuacao": 0.4, "next_id": "end_positivo"}
            }
        },
        "3_neutra": {
            "fala": "Não gosto de negociar, mas a vila precisa de braços. Só não cause problemas.",
            "respostas": {
                "Sem confusão. Só trabalho.": {"pontuacao": 0.0, "next_id": "end_neutro"}
            }
        },
        "end_positivo": {
            "fala": "Bom trabalho. Enquanto eu estiver de guarda, você é bem-vindo na vila.",
            "respostas": {}
        },
        "end_negativo": {
            "fala": "Chega. Fora da vila. Agora.",
            "respostas": {}
        },
        "end_neutro": {
            "fala": "Faça seu serviço e siga seu caminho. Nada além disso.",
            "respostas": {}
        }
    }
    
        self.max_hp = randint(40,60)
        self.attack_damage = randint(24,40)

class Rose(Villager):
    def __init__(self, *groups, collision_sprites, creatures_sprites, npc_name="Nina", house_point=(0, 0), is_ranged=False, attack_hitbox_list={ "Front": (150, 70),"Back": (150, 70),"Left": (70, 150),"Right": (70, 150) }, range_distance=36, default_size=HDCS + HHDCS, team_members=[], original_speed = 200, actions_to_add=[]):
        super().__init__(*groups, collision_sprites=collision_sprites, creatures_sprites=creatures_sprites, npc_name=npc_name, house_point=house_point, is_ranged=is_ranged, attack_hitbox_list=attack_hitbox_list, range_distance=range_distance, default_size=default_size, team_members=team_members, original_speed=original_speed, actions_to_add=actions_to_add)

        self.talks = {
            "1": {  # Introdução
                "fala": "Ah… passos cansados. Eu reconheço esse som. Sou Rose, cuido dos feridos e dos que ainda fingem estar bem. O que te traz até mim, filho?",
                "respostas": {
                    "Preciso de ajuda. Estou machucado.": {"pontuacao": 0.6, "next_id": "2_positiva"},
                    "Só queria conversar um pouco.": {"pontuacao": 0.4, "next_id": "2_neutra"},
                    "Curandeira, faça seu trabalho rápido.": {"pontuacao": -0.6, "next_id": "2_negativa"},
                    "Não confio em remédios e superstições.": {"pontuacao": -1.0, "next_id": "end_negativo"}
                }
            },
            "2_positiva": {
                "fala": "Machucados no corpo são fáceis. Difícil é tratar o que sangra por dentro. Sente-se, vou cuidar de você.",
                "respostas": {
                    "Obrigado, Rose. A vila tem sorte de ter você.": {"pontuacao": 0.7, "next_id": "end_positivo"},
                    "Não se preocupe, já aguentei coisa pior.": {"pontuacao": 0.3, "next_id": "3_positiva"},
                    "Isso vai me custar quanto?": {"pontuacao": -0.2, "next_id": "2_neutra"}
                }
            },
            "2_neutra": {
                "fala": "Conversas também curam, às vezes mais que ervas. Mas o tempo não espera. O que deseja saber?",
                "respostas": {
                    "O que anda acontecendo com a vila?": {"pontuacao": 0.5, "next_id": "3_positiva"},
                    "Preciso só de algo para seguir viagem.": {"pontuacao": 0.1, "next_id": "3_neutra"},
                    "Nada. Foi perda de tempo.": {"pontuacao": -0.5, "next_id": "end_negativo"}
                }
            },
            "2_negativa": {
                "fala": "Cuidado com as palavras. Já vi muita gente forte cair por menos.",
                "respostas": {
                    "Perdão, estou exausto.": {"pontuacao": 0.3, "next_id": "3_neutra"},
                    "Não preciso de sermões.": {"pontuacao": -0.7, "next_id": "end_negativo"},
                    "Só diga se pode ajudar ou não.": {"pontuacao": 0.0, "next_id": "2_neutra"}
                }
            },
            "3_positiva": {
                "fala": "A vila sente medo. Dash luta com o coração, Nash com a cabeça… e Obi carrega o peso de todos. Você pode ser o equilíbrio.",
                "respostas": {
                    "Vou fazer o possível para ajudar.": {"pontuacao": 0.6, "next_id": "end_positivo"},
                    "Não prometo nada, mas ouvirei.": {"pontuacao": 0.2, "next_id": "end_neutro"}
                }
            },
            "3_neutra": {
                "fala": "Leve estas ervas. Não curam tudo, mas ajudam a seguir em frente.",
                "respostas": {
                    "Agradeço. Já é mais do que esperava.": {"pontuacao": 0.3, "next_id": "end_neutro"}
                }
            },
            "end_positivo": {
                "fala": "Vá com cuidado, meu filho. A vila precisa de mais gente que escute antes de agir.",
                "respostas": {}
            },
            "end_negativo": {
                "fala": "Quando a dor apertar, talvez lembre das minhas palavras… ou talvez seja tarde.",
                "respostas": {}
            },
            "end_neutro": {
                "fala": "O caminho continua. Cabe a você como trilhá-lo.",
                "respostas": {}
            }
        }

class Holz(Villager):
    def __init__(self, *groups, collision_sprites, creatures_sprites, npc_name="Nina", house_point=(0, 0), is_ranged=False, attack_hitbox_list={ "Front": (150, 70),"Back": (150, 70),"Left": (70, 150),"Right": (70, 150) }, range_distance=36, default_size=HDCS + HHDCS, team_members=[], original_speed = 200, actions_to_add=[], player=None):
        arvore_1 = (5217,2837)
        arvore_2 = (5533,1566)
        arvore_3 = (4564, 1294)
        arvore_4 = (5158, 1084)
        self.arvores = [arvore_1, arvore_2, arvore_3, arvore_4]
        self.arvore_escolhida = None

        super().__init__(*groups, collision_sprites=collision_sprites, creatures_sprites=creatures_sprites, npc_name=npc_name, house_point=house_point, is_ranged=is_ranged, attack_hitbox_list=attack_hitbox_list, range_distance=range_distance, default_size=default_size, team_members=team_members, original_speed=original_speed, actions_to_add=actions_to_add)

        self.player = player
        self.hp = 30
        self.max_hp=30
        self.talks = {
            "1": {  # Introdução
                "fala": "Você com certeza está perdido viajante! Ho ho ho... É raro ver andarilhos por aqui tão perto do início das nevascas. Se não for embora logo vai ser obrigado a passar o resto do inverno aqui no vale.",
                "respostas": {
                    "Passar o inverno aqui na vila não parece tão ruim. Isso seria um problema?": {"pontuacao": 0.4, "next_id": "rota_1"},
                    "Não estava sabendo disso. Pode me dizer quando as nevascas devem começar?": {"pontuacao": 0.6, "next_id": "rota_2"},
                    "#4 Você deve ser o Holz, certo?": {"pontuacao": -0.4, "next_id": "rota_secreta"},
                }
            },
            "rota_secreta": {  
                "fala": "Olha só... Se sabe meu nome então talvez não esteja tão perdido assim. Como me conhece?",
                "respostas": {
                    "Encontrei sua filha nas montanhas. Ela ia ser atacada por alguns monstros e eu dei uma força.": {"pontuacao": 0.4, "next_id": "end_secreto"},
                }
            },
            "rota_2": {  
                "fala": "Cada osso do meu corpo me diz que amanhã mesmo as primeiras neves já devem começar a cair",
                "respostas": {
                    "Se as nevascas estão tão próximas assim, talvez tenha alguma trabalho com o qual eu possa ajudar para ganhar alguns favores em troca.": {"pontuacao": 0.4, "next_id": "end_5"},
                    "Entendo. Melhor eu resolver logo minhas questões então! Muito obrigado amigo!": {"pontuacao": 0.6, "next_id": "end_4"},
                }
            },
            "rota_1": {  
                "fala": "Isso você deve perguntar ao chefe da vila. Mas cá entre nós, tivemos uma excelente temporada de caça e os celeiros estão cheios! Não deve ser problema ho ho ho...",
                "respostas": {
                    "Posso usar seu nome como referência quando eu falar com o chefe?": {"pontuacao": 0.4, "next_id": "end_1"},
                    "É normal os celeiros estarem tão cheios assim?": {"pontuacao": 0.6, "next_id": "rota_1_2"},
                }
            },
            "rota_1_2": {  
                "fala": "Uma praga se espalhou pela tribo dos orcs durante a temporada de coleta. Não foi nada tão letal, mas poucos deles estavam em condições de  juntar recursos então conseguimos coletar mais que o normal.",
                "respostas": {
                    "Mas isso quer dizer que os Orcs não tem recursos pra passar essa temporada de nevascas, certo?": {"pontuacao": 0.4, "next_id": "rota_1_3"},
                    "Pelo que você está falando, parece que o destino decidiu qual raça deve viver ou morrer": {"pontuacao": 0.6, "next_id": "end_2"},
                }
            },
            "rota_1_2": {  
                "fala": "Só podemos nos preocupar com a presa que estamos caçando. Lamento por eles, mas isso não é problema nosso.",
                "respostas": {
                    "Tem razão. Talvez eles mereçam o que está acontecendo.": {"pontuacao": 0.4, "next_id": "end_2"},
                    "Eu entendo o que você quer dizer amigo,  mas quando uma criatura está encurralada é quando ela é mais perigosa, pois não tem nada a perder.": {"pontuacao": 0.6, "next_id": "rota_1_4"},
                }
            },
            "rota_1_4": {  
                "fala": "Está dizendo pra darmos as mãos com os monstros e abraçarmos uma árvore?",
                "respostas": {
                    "Não exatamente...": {"pontuacao": 0.4, "next_id": "end_3"},
                    "É quase isso": {"pontuacao": 0.6, "next_id": "end_3"},
                }
            },
            "end_1": {  
                "fala": "O que? Nunca! Que tipo de pessoa pede favores a um desconhecido sem oferecer algo em troca? Eu não confio em pessoas que agem assim.",
                "respostas": {}
            },
            "end_2": {  
                "fala": "Cuidado viajante, a natureza pode ter sido gentil conosco essa temporada, mas na próxima podemos ser nós os que estarão passando fome.",
                "respostas": {}
            },
            "end_3": {  
                "fala": "Olha garoto, não vou dizer que não entendo o que você está falando, mas não tem como falar com essas coisas. E é melhor você nem tentar, senão vai só morrer por nada.",
                "respostas": {}
            },
            "end_4": {  
                "fala": "Boa sorte, Viajante! Fale com o chefe da vila se precisar de algo.",
                "respostas": {}
            },
            "end_5": {  
                "fala": "Muito bem! Gosto de pessoas que não tem medo de trabalhar pesado! Os Monstros hoje estão bem agitados. Me proteja enquanto eu corto a próxima árvore e fico te devendo uma.",
                "respostas": {}
            },
            "end_secreto": {  
                "fala": "O que? Se está falando a verdade eu tenho uma dívida eterna com você, rapaz. Se precisar de qualquer coisa é só me falar.",
                "respostas": {}
            },




            "end_6": {  
                "fala": "Olha só! Você realmente me protegeu! Fico te devendo muito com isso, meu amigo. Se precisar de qualquer coisa na vila, pode contar comigo.",
                "respostas": {}
            },
            "end_7": {  
                "fala": "Você realmente não é confiável Vá embora daqui!",
                "respostas": {}
            },




        }

        self.talks_tarde = {
            "1": { 
                "fala": "Viajante, você viu minha filha? Ela sempre vai para as montanhas durante a manhã, mas até agora ela não voltou.",
                "respostas": {
                    "Não a vi senhor. Sinto muito.": {"pontuacao": 0.6, "next_id": "end_secreto_naovi"},
                    "#5 É uma jovem ruiva, não é? Já a encontrei nas montanhas. Parecia estar tudo bem com ela.": {"pontuacao": 0.4, "next_id": "end_secreto_ok"},
                }
            },
            "end_secreto_ok": { 
                "fala": "É mesmo? Se está tudo bem com ela então acho que não preciso me preocupar",
                "respostas": {}
            },
            "end_secreto_naovi": {  # Introdução
                "fala": "Entendo... Talvez seja melhor eu ir dar uma olhada",
                "respostas": {}
            },
        }

        self.talks_viu_nina_morta = {
            "1_morta": {  # Introdução
                "fala": "Minha pequena...",
                "respostas": {}
            },
        }
        self.max_hp = randint(20,30)
        self.attack_damage = randint(12,20)
        self.espera_ajuda_player = False
        self.tree_group = pygame.sprite.Group()
        self.foi_atingido = False
        self.cortou_uma_arvore = False
        self.ir_procurar_nina = False
        self.NINA = None
        for sp in self.collision_sprites:
            if hasattr(sp, "is_tree") and sp.is_tree:
                sp.add(self.tree_group)
       
    def handle_damage(self, damage, impact_slide = False, impact_slide_strength = 50, attacking_character=None):
        initial_hp = self.hp
        damaged =  super().handle_damage(damage, impact_slide, impact_slide_strength, attacking_character)
        actual_hp = self.hp
        if actual_hp < initial_hp and self.espera_ajuda_player:
            self.foi_atingido = True

        return damaged
    def escolhe_fala(self, ):
        hora = self.get_hour()
        self.player.falou_holz = True

        if hora > 12 and not self.player.salvou_nina:
            if self.NINA.is_dead and (self.position_vector - self.NINA.position_vector).length() < WINDOW_WIDTH//4:
                self.talks = self.talks_viu_nina_morta
            else:
                self.talks = self.talks_tarde
            
            if self.current_id not in list(self.talks.keys()):
                self.current_id = list(self.talks.keys())[0]
            fala_data = self.talks.get(self.current_id)
            if not fala_data:
                return "", []
            
            if self.current_id == "end_secreto_naovi":
                self.ir_procurar_nina = True
            
            fala_data = self.talks.get(self.current_id)
            # Verifica se é fim (sem respostas) e aplica reputação
            if not fala_data["respostas"]:
                delta_rep = self.pontuacao * 20  # Exemplo: pontuação alta -> +rep, baixa -> -rep
                return fala_data["fala"], []  # Mostra fala final e encerra

            respostas = self.player.verifica_respostas(list(fala_data["respostas"].keys()))
            print(f"Respostas: {respostas}")
            return fala_data["fala"], respostas

        else:

            fala_data = self.talks.get(self.current_id)
            if not fala_data:
                return "", []
            
            if self.current_id == "end_5":
                self.espera_ajuda_player = True
                if self.cortou_uma_arvore:
                    self.espera_ajuda_player = False
                    self.current_id = "end_6"
                    self.player.tem_apoio_holz = True
                elif self.foi_atingido:
                    self.espera_ajuda_player = False
                    self.current_id = "end_7"

            
            if self.current_id == "end_secreto":
                self.player.tem_apoio_holz = True

            fala_data = self.talks.get(self.current_id)
            # Verifica se é fim (sem respostas) e aplica reputação
            if not fala_data["respostas"]:
                delta_rep = self.pontuacao * 20  # Exemplo: pontuação alta -> +rep, baixa -> -rep
                return fala_data["fala"], []  # Mostra fala final e encerra
            
            respostas = self.player.verifica_respostas(list(fala_data["respostas"].keys()))
            return fala_data["fala"], respostas
    

class Sammy(Villager):
    def __init__(self, *groups, collision_sprites, creatures_sprites, npc_name="Sammy", house_point=(0, 0), is_ranged=False, attack_hitbox_list={ "Front": (150, 70),"Back": (150, 70),"Left": (70, 150),"Right": (70, 150) }, range_distance=36, default_size=HDCS + HHDCS, team_members=[], original_speed = 200, actions_to_add=[], initial_position:set=()):

        
        self.talks = {
        "1": {  # Introdução
            "fala": "Pare aí. A vila anda tensa, e eu não deixo qualquer um circular livremente. Sou Obi, guarda da vila. Diga por que está aqui.",
            "respostas": {
                "Só estou de passagem. Não quero problemas.": {"pontuacao": 0.3, "next_id": "2_neutra"},
                "Posso ajudar na patrulha se precisar.": {"pontuacao": 0.6, "next_id": "2_positiva"},
                "Isso é um interrogatório ou você sempre trata assim?": {"pontuacao": -0.5, "next_id": "2_negativa"},
                "Saia da minha frente ou vai se arrepender.": {"pontuacao": -1.0, "next_id": "end_negativo"}
            }
        },
        "2_positiva": {
            "fala": "Ajuda é bem-vinda… desde que siga ordens. Temos relatos de movimentação estranha perto do portão norte.",
            "respostas": {
                "Posso vigiar enquanto você faz a ronda interna.": {"pontuacao": 0.7, "next_id": "end_positivo"},
                "Prefiro investigar sozinho e te reportar depois.": {"pontuacao": 0.4, "next_id": "3_positiva"},
                "Só se tiver alguma recompensa envolvida.": {"pontuacao": -0.3, "next_id": "2_neutra"}
            }
        },
        "2_negativa": {
            "fala": "Atitude suspeita. Não me obrigue a te retirar da vila à força.",
            "respostas": {
                "Calma, só estava testando. Vamos conversar.": {"pontuacao": 0.2, "next_id": "3_neutra"},
                "Tente a sorte.": {"pontuacao": -0.8, "next_id": "end_negativo"},
                "O que está acontecendo exatamente?": {"pontuacao": 0.1, "next_id": "2_neutra"}
            }
        },
        "2_neutra": {
            "fala": "Se ficar, siga as regras. Patrulha reforçada rende 15 moedas por turno.",
            "respostas": {
                "Aceito. Ordem é ordem.": {"pontuacao": 0.4, "next_id": "end_positivo"},
                "Quinze é pouco. Quero 30.": {"pontuacao": -0.2, "next_id": "3_neutra"},
                "Prefiro não me envolver.": {"pontuacao": -0.5, "next_id": "end_negativo"}
            }
        },
        "3_positiva": {
            "fala": "Você se move bem e não chama atenção. Isso é útil pra um guarda.",
            "respostas": {
                "Fico feliz em ajudar a manter a vila segura.": {"pontuacao": 0.4, "next_id": "end_positivo"}
            }
        },
        "3_neutra": {
            "fala": "Não gosto de negociar, mas a vila precisa de braços. Só não cause problemas.",
            "respostas": {
                "Sem confusão. Só trabalho.": {"pontuacao": 0.0, "next_id": "end_neutro"}
            }
        },
        "end_positivo": {
            "fala": "Bom trabalho. Enquanto eu estiver de guarda, você é bem-vindo na vila.",
            "respostas": {}
        },
        "end_negativo": {
            "fala": "Chega. Fora da vila. Agora.",
            "respostas": {}
        },
        "end_neutro": {
            "fala": "Faça seu serviço e siga seu caminho. Nada além disso.",
            "respostas": {}
        }
    }
    
        super().__init__(*groups, collision_sprites=collision_sprites, creatures_sprites=creatures_sprites, npc_name=npc_name, house_point=house_point, is_ranged=is_ranged, attack_hitbox_list=attack_hitbox_list, range_distance=range_distance, default_size=default_size, team_members=team_members, original_speed=original_speed, actions_to_add=actions_to_add)
        self.all_groups= groups
        self.is_player = False
        self.is_human = True


        self.village_rect = pygame.Rect(3800,1400,2200, 2000)
        self.water_sources = [(5528, 2200), (4618, 2836), (4481, 2000) ]
        self.house_point = house_point

        self.armor_type = ""
        self.default_folder_path = join(getcwd(), "NPCs", npc_name,)
        self.scripts = load_scripts(self.default_folder_path)
        self.default_size = default_size
        self.waking_up_hour = randint(4,7)

        self.action = "Walk"
        self.state, self.frame_index = "Front", 0
        self.actions = ["Walk", "Idle", "Hurt", "Run","Attack_1", "Attack_2", "Dying", "Dead", "Run"]
        self.load_character_images()
        
        
        self.image = pygame.transform.scale(self.frames[self.action][self.state][0], (self.default_size, self.default_size))
        
        if initial_position:
            self.rect = self.image.get_frect(center = initial_position)
        else:
            self.rect = self.image.get_frect(center = (5010, 3010))
        self.hitbox = pygame.FRect(
            self.rect.left + self.rect.width/2,
            self.rect.top + self.rect.height/3+50,
            self.rect.width/2,
            self.rect.height * 2/3
            )
        
        self.hitbox.center = self.rect.center

        self.original_speed = original_speed
        self.direction = pygame.Vector2()

        #ATTACK
        self.animation_speed = 5
        self.attack_hitbox_list = attack_hitbox_list
        self.last_attack_time = pygame.time.get_ticks()
                
        
        
        # === SENSES===
        self.last_called_senses_time = pygame.time.get_ticks()
        self.call_senses_delay = 200


        # === VISÃO: lista de hitboxes à frente ===
        self.vision_max_dist = 150

        # Abordagem simples: “cone” aproximado com N retângulos AABB
        self.vision_segments = 4                               # quantos retângulos formam o cone
        self.vision_step = self.vision_max_dist / self.vision_segments
        self.vision_base_width = self.hitbox.width     # largura inicial
        self.vision_spread_per_seg = max(2, int(self.hitbox.width * 0.12))  # cresce a cada segmento
        self.vision_hitboxes: list[pygame.FRect] = []
        self.update_vision_hitboxes()  # gerar já na criação


        self.max_hp = 9999
        self.hp = 9999
        self.attack_damage = 9999
        self.attacked_by_character = None

        self.attack_1,self.attack_2 = False,False
        self.specie = "SAMMY"

        self.current_id = "1"
        self.pontuacao = 0.0
        self.confiabilidades["ORC"] = 10
        self.confiabilidades["GOBLIN"] = 10
        self.confiabilidades["HUMAN"] = 10
        self.confiabilidades["SLIME"] = 10
        self.confiabilidades["GOLEM"] = 10
        self.confiabilidades["GHOST"] = 10

        self.can_talk =True







    


    




