from settings import *
from Utils.classes_raiz import Character
from Utils.effects import *
import time
class Action:
    def __init__(self, character:Character,):
        self.character = character
        pass


class Brain:
    

    def __init__(self, character:Character, crying_time=3000, mental_type:str="calmo"):
        self.character = character
        self.rota = []
        self.rota_index = 0
        self.last_dest = []
        self.can_attack = True
        self.final_dest = None
        self.crying_time = crying_time
        self.crying_start = None
        self.mental_type=mental_type

        self.can_attack = False
        self.target = None
        self.final_dest = ()
    

    def have_mercy(self,to_mercy:Character ) -> bool:
        is_begging = to_mercy.is_begging
        if not is_begging:
            return False
        conf =  to_mercy.confiabilidades[self.character.specie]
        if conf >= 1:
            choices = [True, False, True, True, True]
        elif conf >=0.5:
            choices = [True, False, False, True, True]
        elif conf >=0:
            choices = [True, False, False, False, True]
        elif conf >=-0.5:
            choices = [True, False, False, False, False]
        else:
            choices = [True, False, False, False, False]
        have_mercy = choice(choices)
        return have_mercy
        
    def esta_em_combate(self,):
        if self.character.is_combating:
            if self.can_attack:
                if self.character.attacking_character:
                    if self.character.is_attacking or self.have_mercy(self.character.attacking_character):
                        return None
                    return Combat(self.character, self.character.attacking_character,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
            if not self.esbarrar_em_character():
                self.character.is_combating = False
            return KeepDistance(self.character, self.character.attacking_character)
        return None
    
    def percepeu_inimigo(self,percepted_enemy: Character):
        if percepted_enemy:
            if self.can_attack and percepted_enemy.specie != self.character.specie and self.have_mercy(percepted_enemy) == False:
                self.character.attacking_character = percepted_enemy
                return Combat(self.character, percepted_enemy,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
            elif self.character.specie == percepted_enemy.specie:
                return None
            else:
                return KeepDistance(self.character, percepted_enemy)
        return None
    
    def tem_alvo_para_atacar(self):
        if self.target:
            
            self.character.attacking_character = self.target
            if self.target.is_dead:
                self.target=None
                return None
         
            if self.character.team_members != None:
                for team_member in self.character.team_members:
                    if not team_member.brain.target:
                        team_member.brain.target = self.target
            return Combat(self.character, self.target,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
        
        #verifica se algum membro da equipe está em combate
        for team_member in self.character.team_members:
            if team_member.brain.target:
                self.character.attacking_character = team_member.brain
                return Combat(self.character, team_member.brain.target,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
            if team_member.attacking_character and self.have_mercy(team_member.attacking_character) == False:
                self.character.attacking_character = team_member.attacking_character
                return Combat(self.character, team_member.attacking_character,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
        
        return None
    
    def esbarrar_em_character(self,):
        if self.character.is_chatting == True or self.character.is_begging==True:
            return None
        proximos = pygame.sprite.spritecollide(self.character, self.character.creatures_sprites, False)
        if proximos:
            for creature in proximos: 
                if creature != self.character:
                    if creature.specie == self.character.specie:
                        if creature.is_player or creature.is_dead:
                            return None
                        if self.character.now - self.character.last_talk_time > self.character.talk_delay and self.character.can_talk == True and self.character.scripts:
                            self.character.last_talk_time = self.character.now
                            self.character.is_chatting = True
                            creature.is_chatting = True
                            tipo_conversa = choice(self.character.talk_options)
                            try:
                                script = [t.replace(r"{nome_character}", creature.personal_name) for t in choice(self.character.scripts[tipo_conversa]) ]
                            except:
                                raise Exception(f"Falha ao iniciar conversa entre: {self.character} X {creature}")
                            if tipo_conversa == "respondendo":
                                action_a,action_b,conv = start_chat(creature, self.character,script=script)
                                creature.current_action = action_a
                                self.character.current_action = action_b
                            else:
                                action_a,action_b,conv = start_chat(self.character,creature,script=script)
                                creature.current_action = action_b
                                self.character.current_action = action_a
                            self.conversation = conv
                            return self.character.current_action
                    elif not creature.is_dead and self.have_mercy(creature)==False:# se a criatura não está morta
                        if self.character.confiabilidades[self.character.specie] <= MARGEM_DE_ATAQUE and self.can_attack:# se a confiabilidade para com a espécie for menor que a margem, ataca
                            self.character.attacking_character = creature
                            return Combat(self.character, creature,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
                        return None

        return None
    
    def membro_equipe_morreu(self,):
        for tm in self.character.team_members:
            if tm.is_dead:
                if not self.crying_start:
                    self.crying_start = pygame.time.get_ticks()

                enemy_team_members = self.character.attacking_character.team_members if self.character.attacking_character else []

                if not self.character.speech_text:                
                    self.character.speech_text = define_text_on_dead_ally(self.character.team_members, self.mental_type,enemy_team_members )
                self.character.handle_damage(0, attacking_character=self.character.attacking_character)
                if pygame.time.get_ticks() - self.crying_start > self.crying_time:
                    self.character.speech_text = ""
                    self.crying_start = None
                    self.character.team_members.remove(tm)

                    return None
                return Move(self.character, "wander")
        return None


    def rotina_diaria(self,):
        return None

    def choose_action(self, percepted_enemy):
        tg = self.character.attacking_character or self.target
        if tg:
            if tg.is_begging and self.have_mercy(tg):
                self.character.attacking_character = None
                self.target = None
                self.character.is_combating = False
        #sobrevivencia:
        acao_esta_em_combate = self.esta_em_combate()
        if acao_esta_em_combate:
            return acao_esta_em_combate
        
        acao_morte_membro_equipe = self.membro_equipe_morreu()
        if acao_morte_membro_equipe:
            return acao_morte_membro_equipe

        
        acao_percepeu_inimigo = self.percepeu_inimigo(percepted_enemy)
        if acao_percepeu_inimigo:
            return acao_percepeu_inimigo
        
        acao_tem_alvo_para_atacar = self.tem_alvo_para_atacar()
        if acao_tem_alvo_para_atacar:
            return acao_tem_alvo_para_atacar

        acao_esbarrar_character = self.esbarrar_em_character()
        if acao_esbarrar_character:
            return acao_esbarrar_character
        
        acao_rotina = self.rotina_diaria()
        if acao_rotina:
            return acao_rotina
        self.character.action="Idle"
        self.character.state="Front"
        return None
        
    
        
    def move_to(self, final_dest:set, tolerance = 2, use_manhattam=False):
        char_center = self.character.rect.center
        char_point = pygame.Vector2(char_center[0],char_center[1])

        if self.character.specie == "GHOST":
            matriz = self.character.groups()[0].matriz_pura
        else:
            matriz = self.character.groups()[0].world_matriz

        try:
            final_dest_point = pygame.Vector2(final_dest[0],final_dest[1])
        except:
            raise Exception(f"Erro ao tentar pegar o ponto final do personagem {self.character}")
        if not self.rota or self.last_dest != final_dest:
            self.rota = calcula_rota_correta(matriz, char_center, final_dest) or []
            self.character.rota = self.rota
            if not self.rota:
                self.final_dest = None
                return None
        #se acabou a rota ou chegou no destino, reseta tudo
        if self.rota_index >= len(self.rota) or (final_dest_point - char_point).length() <= self.character.default_size//tolerance:
            self.rota_index = 0
            self.rota = []
            self.final_dest = None
            return None
        
        
        dest = self.rota[self.rota_index] if self.rota else final_dest
        dest_point = pygame.Vector2(dest[0],dest[1])


        if (dest_point - char_point).length() <= GRID_SIZE//2:
            self.rota_index +=1

        
        move = Move(self.character, "to", dest=dest)
        return move



class OrcRootBrain(Brain):
    def __init__(self, character, crying_time=3000, mental_type = "calmo"):
        super().__init__(character, crying_time, mental_type)

    def percepeu_inimigo(self,percepted_enemy: Character):
        if percepted_enemy:
            if self.can_attack and percepted_enemy.specie != self.character.specie and self.have_mercy(percepted_enemy) == False and percepted_enemy.has_emblem == False:
                self.character.attacking_character = percepted_enemy
                return Combat(self.character, percepted_enemy,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
            elif self.character.specie == percepted_enemy.specie:
                return None
            else:
                return KeepDistance(self.character, percepted_enemy)
        return None
    
    def tem_alvo_para_atacar(self):
        if self.target:
            
            self.character.attacking_character = self.target
            if self.target.is_dead or self.target.has_emblem == True:
                self.target=None
                return None
         
            if self.character.team_members != None:
                for team_member in self.character.team_members:
                    if not team_member.brain.target:
                        team_member.brain.target = self.target
            return Combat(self.character, self.target,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
        
        #verifica se algum membro da equipe está em combate
        for team_member in self.character.team_members:
            if team_member.brain.target:
                self.character.attacking_character = team_member.brain
                return Combat(self.character, team_member.brain.target,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
            if team_member.attacking_character and self.have_mercy(team_member.attacking_character) == False:
                self.character.attacking_character = team_member.attacking_character
                return Combat(self.character, team_member.attacking_character,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
        
        return None
    
    def esbarrar_em_character(self,):
        if self.character.is_chatting == True or self.character.is_begging==True:
            return None
        proximos = pygame.sprite.spritecollide(self.character, self.character.creatures_sprites, False)
        if proximos:
            for creature in proximos: 
                if creature != self.character:
                    if creature.specie == self.character.specie or creature.has_emblem == True:
                        if creature.is_player :
                            return None
                        if self.character.now - self.character.last_talk_time > self.character.talk_delay and self.character.can_talk == True and self.character.scripts:
                            self.character.last_talk_time = self.character.now
                            self.character.is_chatting = True
                            creature.is_chatting = True
                            tipo_conversa = choice(self.character.talk_options)
                            try:
                                script = [t.replace(r"{nome_character}", creature.personal_name) for t in choice(self.character.scripts[tipo_conversa]) ]
                            except:
                                raise Exception(f"Falha ao iniciar conversa entre: {self.character} X {creature}")
                            if tipo_conversa == "respondendo":
                                action_a,action_b,conv = start_chat(creature, self.character,script=script)
                                creature.current_action = action_a
                                self.character.current_action = action_b
                            else:
                                action_a,action_b,conv = start_chat(self.character,creature,script=script)
                                creature.current_action = action_b
                                self.character.current_action = action_a
                            self.conversation = conv
                            return self.character.current_action
                    elif not creature.is_dead and self.have_mercy(creature)==False:# se a criatura não está morta
                        if self.character.confiabilidades[self.character.specie] <= MARGEM_DE_ATAQUE:# se a confiabilidade para com a espécie for menor que a margem, ataca
                            self.character.attacking_character = creature
                            return Combat(self.character, creature,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
                        return None

        return None
    
    

class MonsterBrain(Brain):
    def __init__(self, character):
        super().__init__(character)
        self.can_attack =True

    def rotina_diaria(self):
        if self.character.get_hour() >10:
            points = [(3299, 518), (3400, 135)]
            if not self.final_dest:
                self.final_dest = choice(points)
        return super().rotina_diaria()

class SlimeBrain(MonsterBrain):
    def __init__(self, character):
        super().__init__(character)

    
    def rotina_diaria(self):
        super().rotina_diaria()
        if not self.final_dest:
            self.final_dest = choice(self.character.locais_favoritos)

        move = self.move_to(self.final_dest)
        return move


class GolemBrain(MonsterBrain):
    def __init__(self, character):
        super().__init__(character)

    def rotina_diaria(self):
        if self.character.player.puxou_alavanca:
            return None
        return self.move_to((862,1810), )

    def esbarrar_em_character(self):
        if self.character.player.puxou_alavanca:
            return None
        return super().esbarrar_em_character()
    
    def esta_em_combate(self):
        if self.character.player.puxou_alavanca:
            return None
        return super().esta_em_combate()
    
    def tem_alvo_para_atacar(self):
        if self.character.player.puxou_alavanca:
            return None
        return super().tem_alvo_para_atacar()

    def percepeu_inimigo(self, percepted_enemy):
        if self.character.player.puxou_alavanca:
            return None
        return super().percepeu_inimigo(percepted_enemy)

class GhostBrain(MonsterBrain):
    def __init__(self, character):
        super().__init__(character)

    def rotina_diaria(self,):
        locais = {
            "local_1":{
                "x_min": 4654,
                "x_max": 6101,
                "y_min":4892,
                "y_max":6000
            },
            "local_2": {
                "x_min": 5592,
                "x_max": 6000,
                "y_min":3809,
                "y_max":6109
            },
        }
        if not self.final_dest:
            local = choice(["local_1", "local_2"])
            local_rect = locais[local]

            self.final_dest = (randint(local_rect["x_min"], local_rect["x_max"]), randint(local_rect["y_min"], local_rect["y_max"]))
        move = self.move_to(self.final_dest)
        return move

class NinaBrain(Brain):
    def __init__(self, character, can_attack=False):
        super().__init__(character,mental_type="raivoso")
        self.can_attack = can_attack
        self.target = None
        self.final_dest = ()
        self.primeiro_acompanhamento = True

    def rotina_diaria(self):

        if self.character.acompanhar_player:
            if self.primeiro_acompanhamento:
                self.final_dest = None
                self.primeiro_acompanhamento = False
            if not self.final_dest:
                self.final_dest = self.character.player.rect.center
            move = self.move_to(self.final_dest)
            if self.character.player.rect.colliderect(self.character.village_rect):
                self.character.acompanhar_player = False
                self.character.ficar_vila = True
                self.character.player.salvou_nina = True
        else:
            hora = self.character.get_hour()
            if hora < 12 and not self.character.ficar_vila:
                if not self.final_dest:
                    self.final_dest = choice(self.character.locais_montanha)
            else:
                if not self.final_dest:
                    self.final_dest = choice(self.character.locais_patrulha)
            move = self.move_to(self.final_dest)
        return move

class PessoaAlavancaBrain(Brain):
    def __init__(self, character, can_attack=False):
        super().__init__(character,mental_type="raivoso")
        self.can_attack = can_attack
        self.target = None
        self.final_dest = ()

    def rotina_diaria(self):
        return None

class VerantBrain(Brain):
    def __init__(self, character, can_attack=False):
        super().__init__(character,mental_type="raivoso")
        self.can_attack = can_attack
        self.target = None
        self.final_dest = ()

    def rotina_diaria(self):
        
        if not self.final_dest:
            self.final_dest = choice(self.character.locais_patrulha)
        move = self.move_to(self.final_dest)
        return move

class VerlorenBrain(Brain):
    def __init__(self, character, can_attack=False):
        super().__init__(character,mental_type="raivoso")
        self.can_attack = False
        self.target = None
        self.final_dest = ()

    def rotina_diaria(self):
        self.character.original_speed = self.character.player.original_speed
        if self.character.fechou_acordo:
            if not self.final_dest:
                if self.character.saiu_labirinto:
                    self.final_dest = choice(self.character.locais_patrulha)
                else:
                    self.final_dest = self.character.player.rect.center
            return self.move_to(self.final_dest)
        return None

class ObiBrain(Brain):
    def __init__(self, character, can_attack=False):
        super().__init__(character,mental_type="raivoso")
        self.can_attack = can_attack
        self.target = None
        self.final_dest = ()
    
    def rotina_diaria(self):
        
        if not self.final_dest:
            self.final_dest = choice(self.character.locais_patrulha)

        move = self.move_to(self.final_dest)
        return move
    
class LaRochBrothers(Brain):
    """
    La Roch são os irmãos caçadores. Durante o dia eles caçam criaturas e monstros.
    """
    def __init__(self, character, can_attack=False):
        super().__init__(character,)
        self.can_attack = can_attack
        self.final_dest = ()
        self.target = None
    
    def rotina_diaria(self):
        hora = self.character.get_hour()
        if self.character.soube_ataque:
            pass
        else:
            if hora < 11:
            
                vr = self.character.village_rect #village rect
                if not self.final_dest:
                    hora = self.character.get_hour()
                    if hora >19:
                        self.final_dest = (vr.right, vr.top)
                    else:
                        self.final_dest = ()
                        for _ in range(20):
                            self.final_dest = (randint(0, vr.right), randint(vr.top, 6000))

                            if not (self.final_dest[0] < 460+1500 and self.final_dest[1] > 4358+1500):
                                break

                        if self.character.team_members != None:
                            for team_member in self.character.team_members:
                                team_member.brain.final_dest = self.final_dest
            else:
                if not self.final_dest:
                    self.final_dest = (1201, 5311)

        move = self.move_to(self.final_dest)
        return move
    
class RoseBrain(Brain):
    def __init__(self, character, crying_time=8000, mental_type = "calmo"):
        super().__init__(character, crying_time, mental_type)
        self.can_attack = False
        self.target = None
        self.final_dest = ()


    def rotina_diaria(self):
        vr = self.character.village_rect #village rect
        if not self.final_dest:
            self.final_dest = (randint(vr.left, vr.right), randint(vr.top, vr.bottom))
        move = self.move_to(self.final_dest)
        return move
    
    def esbarrar_em_character(self,):
        if self.character.is_chatting == True:
            return None
        proximos = pygame.sprite.spritecollide(self.character, self.character.creatures_sprites, False)
        if proximos:
            for creature in proximos: 
                if creature != self.character:
                    if creature.is_human == True and creature.is_player == False:

                        if creature.hp < creature.max_hp:
                            frases_vovo = [
                                r"Mas veja só você {nome_character}, todo estrupiado! Deixe eu curar isso antes que a Morte tenha ideias.",
                                r"Meu deus {nome_character}! Já disse mil vezes: esquivar não dói! Agora sente e deixe a vovó arrumar essa bagunça.",
                                r"Ai, ai {nome_character}… Se eu ganhasse uma moeda a cada vez que te remendo, já teria aposentado essa bengala."
                            ]
                            self.character.speech_text = choice(frases_vovo).replace(r"{nome_character}", creature.personal_name)
                            self.character.healing=True
                            self.character.healing_character=creature
                            self.character.action="SpellCast"
                            creature.being_healed = True
                            return

                        if self.character.now - self.character.last_talk_time > self.character.talk_delay:
                            self.character.last_talk_time = self.character.now
                            self.character.is_chatting = True
                            creature.is_chatting = True
                            tipo_conversa = choice(["respondendo","iniciando"])
                            script = [t.replace(r"{nome_character}", creature.personal_name) for t in choice(self.character.scripts[tipo_conversa]) ]
                            if tipo_conversa == "respondendo":
                                action_a,action_b,conv = start_chat(creature, self.character,script=script)
                                creature.current_action = action_a
                                self.character.current_action = action_b
                            else:
                                action_a,action_b,conv = start_chat(self.character,creature,script=script)
                                creature.current_action = action_b
                                self.character.current_action = action_a
                            self.conversation = conv
                            return self.character.current_action

        return None

class HolzBrain(Brain):
    def __init__(self, character, can_attack=False):
        super().__init__(character,mental_type="raivoso")
        self.can_attack = can_attack
        self.target = None
        self.final_dest = ()
        self.iniciar_corte = False
        self.momento_inicio_corte = None
        self.arvore_destino = None
    
    def rotina_diaria(self):
        if self.character.ir_procurar_nina:
            if not self.final_dest:
                self.final_dest = self.character.NINA.rect.center
            return self.move_to(self.final_dest)
        
        if self.iniciar_corte == True:
            self.character.action = "Attack_1"
            dist = (self.character.position_vector - pygame.Vector2(self.final_dest)).length()
            if dist >= self.character.rect.width // 2 or not self.arvore_destino:
                self.iniciar_corte = False
                self.momento_inicio_corte = None
                return Idle(self.character)
            

            if pygame.time.get_ticks() - self.momento_inicio_corte >= 40*1000:
                
                pygame.sprite.spritecollide(self.character, self.character.tree_group, dokill=True)

                
                self.character.arvores.pop(self.character.arvores.index(self.arvore_destino))
                self.arvore_destino = None
                self.momento_inicio_corte = None
                self.iniciar_corte = False
                self.final_dest = None
                if self.character.espera_ajuda_player:
                    self.character.cortou_uma_arvore = True
                return Idle(self.character)
            return Idle(self.character)
        

        if not self.final_dest:
            arvore = choice(self.character.arvores)
            self.arvore_destino = arvore
            self.final_dest = arvore
        
        dist = (self.character.position_vector - pygame.Vector2(self.final_dest)).length()
        if dist <= self.character.rect.width //2:
            self.iniciar_corte = True
            self.momento_inicio_corte = pygame.time.get_ticks()
            return Idle(self.character)
        #     self.iniciar_corte = True
        return self.move_to(self.final_dest)

class FischerinBrain(Brain):
    def __init__(self, character, can_attack=False):
        super().__init__(character,mental_type="calmo")
        self.can_attack = can_attack
        self.target = None
        self.final_dest = ()
        self.iniciar_corte = False
        self.momento_inicio_pesca = None
        self.arvore_destino = None
        self.forced_state = ""
        self.tempo_de_pescaria = 60000
        self.locais_de_pesca = [((4632, 2857), "Front"), ((5161, 4370), "Left"), ((4022,4763), "Back")]
    
    def rotina_diaria(self):
        #se não tem um rota de pesca definida, define uma.
        if not self.final_dest:
            self.final_dest, self.forced_state = choice(self.locais_de_pesca)

        #se tem uma rota de pesca definida,e ainda não está no local, vai até o local
        dist = (self.character.position_vector - pygame.Vector2(self.final_dest)).length()
        if dist >= self.character.rect.width //2:
            return self.move_to(self.final_dest)
        

        #se está num local de pesca:
            #define o state de acordo com a posição do local.

        self.character.state = self.forced_state
        self.character.action = "Fishing"
        if not self.momento_inicio_pesca:
            self.momento_inicio_pesca = pygame.time.get_ticks()
        
        if pygame.time.get_ticks() - self.momento_inicio_pesca > self.tempo_de_pescaria:
            self.momento_inicio_pesca = None
            self.final_dest = None
            self.forced_state = ""
            

        return
        if self.iniciar_corte == True:
            self.character.action = "Attack_1"
            dist = (self.character.position_vector - pygame.Vector2(self.final_dest)).length()
            if dist >= self.character.rect.width // 2 or not self.arvore_destino:
                self.iniciar_corte = False
                self.momento_inicio_corte = None
                return Idle(self.character)
            

            if pygame.time.get_ticks() - self.momento_inicio_corte >= self.arvore_destino.rect.width*1000:
                self.arvore_destino.kill()
                self.arvore_destino = None
                self.momento_inicio_corte = None
                self.iniciar_corte = False
                self.final_dest = None
                return Idle(self.character)
            return Idle(self.character)
        
        arvores = [sp for sp in self.character.collision_sprites if hasattr(sp, "is_tree") and sp.is_tree]
        menor_dist = 9999
        arvore_prox = None
        for arvore in arvores[:100]:
            arvore_vector = pygame.Vector2(arvore.rect.center)
            dist = (self.character.position_vector - arvore_vector).length()
            if dist < menor_dist:
                menor_dist = dist
                arvore_prox = arvore

        if not self.final_dest:
            self.arvore_destino = arvore_prox
            self.final_dest = arvore_prox.rect.center
        
        dist = (self.character.position_vector - pygame.Vector2(self.final_dest)).length()
        if dist <= self.character.rect.width //2:
            self.iniciar_corte = True
            self.momento_inicio_corte = pygame.time.get_ticks()
            return Idle(self.character)
        #     self.iniciar_corte = True
        return self.move_to(self.final_dest)

class SammyBrain(Brain):
    def __init__(self, character):
        super().__init__(character)

    def rotina_diaria(self,):
    
        return None

class Conversation:
    """
    Estado compartilhado de uma conversa:
      - lines: lista de falas alternadas (A, B, A, B, ...)
      - turn: 0 = A fala, 1 = B fala
    O tempo de cada fala é estimado por tamanho do texto.
    """
    def __init__(self, lines:list[str], chars_per_sec:int=10, min_ms:int=300, pad_ms:int=250):
        self.lines = lines
        self.chars_per_sec = chars_per_sec
        self.min_ms = min_ms
        self.pad_ms = pad_ms

        self.i = -1                  # índice da fala atual
        self.turn = 0                # 0=A (iniciador), 1=B (respondente)
        self.current_text = ""
        self.line_ends_at = 0
        self.finished = False

    def _start_line(self, now_ms:int):
        self.i += 1
        if self.i >= len(self.lines):
            self.current_text = ""
            self.finished = True
            return
        self.current_text = self.lines[self.i]
        dur = max(self.min_ms, int(len(self.current_text)/self.chars_per_sec*1000)) + self.pad_ms
        self.line_ends_at = now_ms + dur
        self.turn = self.i % 2  # alterna: 0,1,0,1,...

    def update(self, now_ms:int):
        if self.finished:
            return
        if self.i == -1:
            self._start_line(now_ms)
        elif now_ms >= self.line_ends_at:
            self._start_line(now_ms)

class Chatting(Action):
    """
    Action de conversa simples:
      - 'role' define quem fala nos índices pares(0) ou ímpares(1) da conversa.
      - Enquanto o outro fala: fica escutando (não faz nada).
      - Quando terminar: encerra para ambos (estado compartilhado marca finished).
    """
    def __init__(self, character, chatting_to:Character, conversation:Conversation, role:int, max_dist_px:int=80):
        super().__init__(character)
        self.other = chatting_to
        self.conv = conversation
        self.role = role           # 0 = iniciador (A), 1 = respondente (B)
        self.max_dist = max_dist_px
        self.done = False          # ajuste para seu nome de flag (is_done, finished, etc.)

        # Campos “best-effort” para balão de fala (seu draw pode usar se existir)
        setattr(self.character, "speech_text", getattr(self.character, "speech_text", ""))
        setattr(self.other, "speech_text", getattr(self.other, "speech_text", ""))

    def _clear_bubbles(self):
        if hasattr(self.character, "speech_text"):
            self.character.speech_text = ""
        if hasattr(self.other, "speech_text"):
            self.other.speech_text = ""
        if hasattr(self.character, "is_talking"):
            self.character.is_talking = False
        if hasattr(self.other, "is_talking"):
            self.other.is_talking = False

    def _end_chat(self):
        self._clear_bubbles()
        self.done = True  # ou self.is_done = True
        self.character.current_action = None
        self.character.is_chatting = False
        self.other.current_action = None
        self.other.is_chatting = False

    def update(self, dt):
        if self.done:
            self._end_chat()
            return

        # Falha rápida se o outro sumiu ou afastou
        try:
            my_pos = pygame.Vector2(self.character.rect.center)
            ot_pos = pygame.Vector2(self.other.rect.center)
            if (my_pos - ot_pos).length() > self.max_dist or not self.other.alive():
                self.conv.finished = True
        except Exception:
            self.conv.finished = True

        now = pygame.time.get_ticks()
        self.conv.update(now)

        if self.conv.finished:
            self._end_chat()
            return

        # Se é meu turno: eu falo; senão, escuto (não faço nada)
        my_turn = (self.conv.turn == self.role)
        if my_turn:
            if hasattr(self.character, "is_talking"):
                self.character.is_talking = True
            self.character.speech_text = self.conv.current_text
            # garante que o outro esteja "escutando"
            if hasattr(self.other, "is_talking"):
                self.other.is_talking = False
            self.other.speech_text = ""
        else:
            if hasattr(self.character, "is_talking"):
                self.character.is_talking = False
            self.character.speech_text = ""

    def __str__(self):
        return f"Chatting to {self.other.personal_name}"

def start_chat(a:Character, b:Character, script:list[str]) -> tuple[Chatting, Chatting, Conversation]:
    """
    Helper: cria as duas actions com a mesma Conversation.
    O script é uma lista de falas alternadas: [fala_A, fala_B, fala_A, fala_B, ...]
    """
    a.is_chatting = True
    b.is_chatting = True
    conv = Conversation(script)
    return Chatting(a, b, conv, role=0), Chatting(b, a, conv, role=1), conv


#ORCS
class ExplorerOrcBrain(OrcRootBrain):
    def __init__(self, character):
        super().__init__(character)

    def rotina_diaria(self,):
        self.final_dest = (5852, 5842)
        move = self.move_to(self.final_dest)
        return move
    
class ChiefOrcBrain(OrcRootBrain):
    def __init__(self, character):
        super().__init__(character)

    def rotina_diaria(self,):
        hora = self.character.get_hour()
        if hora < 19:
            return None
        else:
            self.character.confiabilidades["HUMAN"] = -20
            # vaga pela vila humana matando todos que encontrar
            if not self.final_dest:
                self.final_dest = choice(self.character.locais_vila_humana)

            move = self.move_to(self.final_dest)
            return move

    def esbarrar_em_character(self):
        hora = self.character.get_hour()
        if hora < 20:
            return None
        return super().esbarrar_em_character()
    
class OrcBrain(OrcRootBrain):
    def __init__(self, character, ):
        super().__init__(character,mental_type="raivoso")
        self.can_attack = True
        self.target = None
        self.final_dest = ()
        self.indo_reuniao = False
        self.ouvindo_reuniao = False
        
    def esbarrar_em_character(self):
        if self.character.is_chatting == True or self.character.is_begging==True:
            return None
        proximos = pygame.sprite.spritecollide(self.character, self.character.creatures_sprites, False)
        if proximos:
            for creature in proximos: 
                if creature != self.character:
                    if creature.specie == self.character.specie or creature.has_emblem:
                        if creature.is_player :
                            return None
                        if self.character.now - self.character.last_talk_time > self.character.talk_delay and self.character.can_talk == True and self.character.scripts and creature.personal_name=="Ghorak":
                            self.character.last_talk_time = self.character.now
                            self.character.is_chatting = True
                            creature.is_chatting = True
                            tipo_conversa = choice(self.character.talk_options)
                            try:
                                script = [t.replace(r"{nome_character}", creature.personal_name) for t in choice(self.character.scripts[tipo_conversa]) ]
                            except:
                                raise Exception(f"Falha ao iniciar conversa entre: {self.character} X {creature}")
                            if tipo_conversa == "respondendo":
                                action_a,action_b,conv = start_chat(creature, self.character,script=script)
                                creature.current_action = action_a
                                self.character.current_action = action_b
                            else:
                                action_a,action_b,conv = start_chat(self.character,creature,script=script)
                                creature.current_action = action_b
                                self.character.current_action = action_a
                            self.conversation = conv
                            return self.character.current_action
                    elif not creature.is_dead and self.have_mercy(creature)==False:# se a criatura não está morta
                        if self.character.confiabilidades[self.character.specie] <= MARGEM_DE_ATAQUE:# se a confiabilidade para com a espécie for menor que a margem, ataca
                            self.character.attacking_character = creature
                            return Combat(self.character, creature,ranged=self.character.is_ranged, attack_range=self.character.range_distance)
                        return None

        return None

    def rotina_diaria(self):
        hora = self.character.get_hour()
        if hora < 19:
            if not self.final_dest:
                self.final_dest = choice(self.character.locais_patrulha)

            move = self.move_to(self.final_dest)
            return move
        else:
            
            self.character.confiabilidades["HUMAN"] = -20
            # vaga pela vila humana matando todos que encontrar
            if not self.final_dest:
                self.final_dest = choice(self.character.locais_vila_humana)

            move = self.move_to(self.final_dest)
            return move

        return None
    
class OrcCacadorBrain(OrcRootBrain):
    def __init__(self, character, ):
        super().__init__(character,mental_type="raivoso")
        self.can_attack = True
        self.target = None
        self.final_dest = ()
        self.indo_reuniao = False
        self.ouvindo_reuniao = False
    def rotina_diaria(self):
        hora = self.character.get_hour()
        falou_mensageiro = self.character.falou_mensageiro
        locais_reuniao = [(1271,5268), (1302, 5084), (1121,4898), (859, 5109)]
        if  hora < 17 or not falou_mensageiro:
            #anda pelo mapa matando o que encontrar
            if not self.final_dest:
                self.final_dest = choice(self.character.locais_patrulha)

            move = self.move_to(self.final_dest)
            return move
        
        elif hora >= 17 and hora < 19 and falou_mensageiro:
            if not self.final_dest and not self.indo_reuniao and not self.ouvindo_reuniao:
                self.final_dest = choice(locais_reuniao)
                self.indo_reuniao=True
            if self.final_dest:
                move = self.move_to(self.final_dest)
                return move
            return None
        else:
            self.character.confiabilidades["HUMAN"] = -20
            # vaga pela vila humana matando todos que encontrar
            if not self.final_dest:
                self.final_dest = choice(self.character.locais_vila_humana)

            move = self.move_to(self.final_dest)
            return move

        return None

class OrcMensageiroBrain(OrcRootBrain):
    def __init__(self, character, ):
        super().__init__(character,mental_type="raivoso")
        self.can_attack = False
        self.target = None
        self.final_dest = ()
        self.indo_reuniao = False
        self.ouvindo_reuniao = False
    
    def esbarrar_em_character(self,):
        if self.character.is_chatting == True or self.character.is_begging==True:
            return None
        proximos = pygame.sprite.spritecollide(self.character, self.character.creatures_sprites, False)
        if proximos:
            for creature in proximos: 
                if creature != self.character:
                    if creature.specie == self.character.specie:
                        if self.character.now - self.character.last_talk_time > 10000 and self.character.can_talk == True and self.character.scripts and creature not in self.character.orcs_falados:
                            self.character.last_talk_time = self.character.now
                            self.character.is_chatting = True
                            creature.is_chatting = True
                            tipo_conversa = choice(self.character.talk_options)
                            try:
                                script = [t.replace(r"{nome_character}", creature.personal_name) for t in choice(self.character.scripts[tipo_conversa]) ]
                            except:
                                raise Exception(f"Falha ao iniciar conversa entre: {self.character} X {creature}")
                            if tipo_conversa == "respondendo":
                                action_a,action_b,conv = start_chat(creature, self.character,script=script)
                                creature.current_action = action_a
                                self.character.current_action = action_b
                            else:
                                action_a,action_b,conv = start_chat(self.character,creature,script=script)
                                creature.current_action = action_b
                                self.character.current_action = action_a
                            self.conversation = conv
                            creature.falou_mensageiro = True
                            self.character.orcs_falados.append(creature)
                            return self.character.current_action
                    

        return None
    

    def rotina_diaria(self):
        hora = self.character.get_hour()

        locais_reuniao = [(1271,5268), (1302, 5084), (1121,4898), (859, 5109)]

        if hora < 10:
            return None
        if  hora < 17  or len(self.character.orcs_falados) < 10:
            #anda pelo mapa matando o que encontrar
            if not self.final_dest:
                #escolhe um dos orcs e vai até ele
                orc_dest = choice(self.character.orcs_para_falar)
                self.final_dest = orc_dest.rect.center

            move = self.move_to(self.final_dest)
            return move
        
        elif hora >= 17 and hora < 19:
            if not self.final_dest and not self.indo_reuniao and not self.ouvindo_reuniao:
                self.final_dest = choice(locais_reuniao)
                self.indo_reuniao=True
            if self.final_dest:
                move = self.move_to(self.final_dest)
                return move
            return None
        else:
            self.character.confiabilidades["HUMAN"] = -20
            # vaga pela vila humana matando todos que encontrar
            if not self.final_dest:
                self.final_dest = choice(self.character.locais_vila_humana)

            move = self.move_to(self.final_dest)
            return move

        return None

class OrcGuardaBrain(OrcRootBrain):
    def __init__(self, character, guard_pos=0):
        super().__init__(character,mental_type="raivoso")
        self.can_attack = True
        self.target = None
        self.final_dest = ()
        self.guard_pos = guard_pos

    def rotina_diaria(self):
        if self.guard_pos == 0:
            return self.move_to((2168,5579), )
        else:
            return self.move_to((2161,5414), )

class KeepDistance(Action):
    """
    Mantém distância ideal do target (kiting). Usa Move('to') para navegação.
    Retorna True enquanto ativo; False se perder o alvo por muito tempo ou sair do leash.
    """
    def __init__(
        self,
        character: Character,
        target: Character,
        *,
        ideal_radius: float = 180.0,     # distância desejada
        inner_radius: float = 140.0,     # muito perto → recua
        outer_radius: float = 220.0,     # muito longe → aproxima
        orbit_enabled: bool = True,      # orbitar quando dentro da banda [inner, outer]
        orbit_dps: float = 70.0,         # graus por segundo ao orbitar
        orbit_dir: int = 1,              # 1 horário, -1 anti-horário
        leash_px: float = 600.0,         # distância máxima até o alvo
        loss_timeout_ms: int = 900,      # tempo sem perceber até abortar
        replan_cooldown_ms: int = 200,
        is_running: bool = False         # ranged geralmente anda, não corre
    ):
        super().__init__(character=character)
        self.target = target
        self.ideal_radius = float(ideal_radius)
        self.inner_radius = float(inner_radius)
        self.outer_radius = float(outer_radius)
        self.orbit_enabled = orbit_enabled
        self.orbit_dps = float(orbit_dps)
        self.orbit_dir = 1 if orbit_dir >= 0 else -1
        self.leash_px = float(leash_px)
        self.loss_timeout_ms = int(loss_timeout_ms)
        self._last_seen_ms = pygame.time.get_ticks()

        # Reuso total do seu mover
        self._move = Move(
            character=character,
            mode="to",
            dest=None,
            is_running=is_running
        )

    def _now(self) -> int:
        return pygame.time.get_ticks()

    def _dist_to_target(self) -> float:
        me = pygame.Vector2(self.character.hitbox.center)
        tgt = pygame.Vector2(self.target.hitbox.center)
        return (tgt - me).length()

    def update(self, dt: float) -> bool:
        # Alvo válido?
        if not hasattr(self.target, "hitbox"):
            return False

        me = pygame.Vector2(self.character.hitbox.center)
        tgt = pygame.Vector2(self.target.hitbox.center)
        r = me - tgt
        if r.length_squared() == 0:
            r = pygame.Vector2(1, 0)  # evita zero exato
        dist = r.length()

        # Leash geral
        if dist > self.leash_px:
            return False

        # Percepção (integre com seu sistema de sentidos)
        percep = getattr(self.character, "percepted_creatures", None)
        now = self._now()
        if percep is not None and (self.target in percep):
            self._last_seen_ms = now
        elif (now - self._last_seen_ms) > self.loss_timeout_ms:
            return False

        # Janela de ataque útil para ranged
        self.in_attack_window = (self.inner_radius <= dist <= self.outer_radius)

        # Controle por faixas
        if dist < self.inner_radius:
            # Muito perto → recua para um ponto na circunferência ideal
            dest = tgt + r.normalize() * self.ideal_radius
        elif dist > self.outer_radius:
            # Muito longe → aproxima para a circunferência ideal
            dest = tgt + r.normalize() * self.ideal_radius
        else:
            # Dentro da banda → orbita (movimento tangencial ao redor do alvo)
            if self.orbit_enabled:
                angle_step = self.orbit_dps * dt * self.orbit_dir
                # Mantém módulo ideal e aplica rotação incremental
                dest = tgt + pygame.Vector2(self.ideal_radius, 0).rotate(r.as_polar()[1] + angle_step)
            else:
                # Sem órbita: permaneça mirando um ponto estável na banda
                dest = tgt + r.normalize() * self.ideal_radius
        
        grupo = self.character.groups()[0]
        if hasattr(grupo, "world_matriz"):
            matriz_mundo = grupo.world_matriz
            if matriz_mundo[int(dest[0])//GRID_SIZE][int(dest[1])//GRID_SIZE] == 1:
                return False
        
        self._move.dest = dest
        self._move.update(dt)
        return True

    def __str__(self):
        return f"KeepDistance from {self.target}"

class Guard(Action):
    """
    Guarda uma posição: vigia um raio, intercepta intrusos e retorna ao posto.
    Usa Move('to') para navegação/evitar obstáculo.
    Sempre retorna True (ação contínua); o FSM interrompe quando necessário.
    """
    def __init__(
        self,
        character: Character,
        *,
        home_pos: tuple | pygame.Vector2 | None = None,  # posto; default = posição atual
        aggro_radius: float = 240.0,                     # raio para detectar intruso
        leash_from_home: float = 520.0,                  # limite de perseguição medido do posto
        stop_radius: float = 28.0,                       # alcance para "contato"
        scan_cooldown_ms: int = 220,                     # frequência de varredura de alvos
        loss_timeout_ms: int = 900,                      # tempo sem ver alvo para desistir
        lead_ms: int = 180,                              # antecipação (lead) da posição do alvo
        is_running: bool = True,                         # sentinelas correm ao interceptar
        idle_mode: str = "look_around"                   # comportamento parado no posto
    ):
        super().__init__(character=character)
        me = pygame.Vector2(self.character.hitbox.center)
        self.home = pygame.Vector2(home_pos) if home_pos is not None else me
        self.aggro_radius = float(aggro_radius)
        self.leash_from_home = float(leash_from_home)
        self.stop_radius = float(stop_radius)
        self.scan_cooldown_ms = int(scan_cooldown_ms)
        self.loss_timeout_ms = int(loss_timeout_ms)
        self.lead_ms = int(lead_ms)
        self.idle_mode = idle_mode

        self._move = Move(
            character=character,
            mode="to",
            dest=self.home,
            is_running=is_running
        )

        self.target: Character | None = None
        self._last_seen_ms = pygame.time.get_ticks()
        self._last_scan_ms = 0
        self._last_tgt_pos = None
        self.in_intercept_window = False  # True quando perto o bastante p/ atacar

    def _now(self) -> int:
        return pygame.time.get_ticks()

    def _dist(self, a: pygame.Vector2, b: pygame.Vector2) -> float:
        return (a - b).length()

    def _predict_target_pos(self, dt: float) -> pygame.Vector2:
        cur = pygame.Vector2(self.target.hitbox.center)
        if self._last_tgt_pos is None:
            self._last_tgt_pos = cur
            return cur
        v = (cur - self._last_tgt_pos) / max(dt, 1e-3)
        self._last_tgt_pos = cur
        return cur + v * (self.lead_ms / 1000.0)

    def _pick_intruder(self) -> Character | None:
        """
        Escolhe intruso mais próximo do posto dentro do aggro_radius.
        Usa 'percepted_creatures' se disponível para ser barato.
        """
        home = self.home
        candidates = []

        percep = getattr(self.character, "percepted_creatures", None)
        if percep:
            pool = percep
        else:
            # Se quiser, use um grupo global de criaturas.
            pool = getattr(self.character, "all_creatures_group", []) or []

        # Filtro simples: ignora a si próprio e, se existir, aliados (por 'team')
        my_team = getattr(self.character, "team", None)
        for c in pool:
            if c is self.character:
                continue
            if not hasattr(c, "hitbox"):
                continue
            if my_team is not None and getattr(c, "team", None) == my_team:
                continue
            if self._dist(home, pygame.Vector2(c.hitbox.center)) <= self.aggro_radius:
                candidates.append(c)

        if not candidates:
            return None

        # Mais próximo do posto
        candidates.sort(key=lambda c: self._dist(home, pygame.Vector2(c.hitbox.center)))
        return candidates[0]

    def _within_leash(self) -> bool:
        pos = pygame.Vector2(self.character.hitbox.center)
        return self._dist(pos, self.home) <= self.leash_from_home

    def update(self, dt: float) -> bool:
        now = self._now()
        me = pygame.Vector2(self.character.hitbox.center)

        # 1) Se há um alvo atual, manter/validar; senão, procurar (com cooldown)
        if self.target is not None:
            # Percepção mantém vivo o alvo
            percep = getattr(self.character, "percepted_creatures", None)
            if percep is not None and (self.target in percep):
                self._last_seen_ms = now
            # Perdeu o alvo?
            lost_by_time = (now - self._last_seen_ms) > self.loss_timeout_ms
            invalid = not hasattr(self.target, "hitbox")
            if lost_by_time or invalid:
                self.target = None
                self._last_tgt_pos = None
        else:
            if now - self._last_scan_ms >= self.scan_cooldown_ms:
                self.target = self._pick_intruder()
                self._last_scan_ms = now
                self._last_tgt_pos = None
                if self.target is not None:
                    self._last_seen_ms = now

        # 2) Se tenho alvo e ainda dentro do leash do posto → intercepto
        if self.target is not None and self._within_leash():
            tgt_pos = pygame.Vector2(self.target.hitbox.center)
            dist_to_tgt = self._dist(me, tgt_pos)
            self.in_intercept_window = (dist_to_tgt <= self.stop_radius)

            if self.in_intercept_window:
                # Paro e deixo o FSM decidir (Attack, por ex.)
                self.character.direction.update(0, 0)
                return True

            # Segue com antecipação barata
            dest = self._predict_target_pos(dt)
            self._move.dest = dest
            self._move.update(dt)
            return True

        # 3) Caso contrário, retornar ao posto
        self.target = None
        self._last_tgt_pos = None
        self.in_intercept_window = False

        # Se já está no posto (tolerância), ficar Idle/olhar ao redor
        if self._dist(me, self.home) <= max(8.0, self.stop_radius):
            # comportamento ocioso no posto
            if getattr(self.character, "action", None) != "Idle":
                # opcional: alinhar estado visual
                self.character.action = "Idle"
            # pode adicionar micro-wander de 1~2px se quiser “respirar”
            return True

        # Não está exatamente no posto → mover de volta
        self._move.dest = self.home
        self._move.update(dt)
        return True

    def __str__(self):
        return "Guard"

class Move(Action):
    """
    Ação de movimentação com 3 modos (flee / to / wander) + desvio simples:
      - 3 probes ("whiskers"): frente, frente-esq, frente-dir (retângulos minúsculos)
      - Ao bloquear, entra em modo "hug" (contornar) por alguns ms seguindo a parede.
      - Sai do "hug" quando a linha de visão (amostrada) até o destino estiver limpa.

    Mantido leve: usa spritecollide com um Sprite "probe" reutilizável (sem laços pesados).
    """
    def __init__(
        self,
        character: Character,
        mode: str = "wander",
        threat=None,
        dest: tuple | None = None,
        arrival_radius: float = 12.0,
        flee_until: float = 220.0,
        is_running: bool = False,        # empurrão para frente no "hug"
    ):
        super().__init__(character=character)
        self.mode = mode
        self.threat = threat
        self.dest = pygame.Vector2(dest) if dest else None

        self.arrival_radius = float(arrival_radius)
        self.flee_until = float(flee_until)

        # animação
        character.action = "Run" if is_running else "Walk"

        #WANDER
        self._wander_target = None

    def _me(self) -> pygame.Vector2:
        return pygame.Vector2(self.character.hitbox.center)

    def _dist_to(self,to:pygame.Vector2):
        return (self.character.position_vector - to).length()

    def _desired_dir(self) -> pygame.Vector2:
        direction = pygame.Vector2()
        me = self._me()

        if self.mode == "flee" and self.threat:
            # fugir: vetor do inimigo para mim
            v = me - pygame.Vector2(self.threat.hitbox.center)
            return v.normalize() if v.length_squared() else pygame.Vector2()

        if self.mode == "to" and self.dest is not None:
            v = self.dest - me
            if v.length() <= self.arrival_radius:
                return pygame.Vector2()
            return v.normalize() if v.length_squared() else pygame.Vector2()

        # wander (alvo local aleatório)
        if self._wander_target is None or self._dist_to(self._wander_target) <= self.arrival_radius:
            jitter = pygame.Vector2(randint(-80, 80), randint(-80, 80))
            self._wander_target = me + jitter

        v = self._wander_target - me
        if v.length_squared() == 0:
            v = pygame.Vector2(uniform(-1, 1), uniform(-1, 1))
        return v.normalize()

    
    # ----------------- ciclo de atualização -----------------

    def update(self, dt: float) -> bool:
        desired = self._desired_dir()

        # aplica e move (o Character resolve colisão por eixo)
        self.character.direction = desired if desired.length_squared() else pygame.Vector2()
        self.character.move(dt)
        

        return True
    
    def __str__(self):
        if self.mode == "to":
            act = "Running" if self.character.action == "Run" else "Walking"
            return act + " to " + f"{self.dest}"
        return "Running" if self.character.action == "Run" else "Walking"

class Investigate(Action):
    """
    Vai até a posição do estímulo e realiza uma busca simples em anel.
    Termina se:
      - o 'source' voltar a ser percebido (found=True), ou
      - esgotar os pontos/tempo (found=False).
    """
    def __init__(
        self,
        character: Character,
        stimulus_pos: tuple[int | float, int | float],
        source=None,                    # Character opcional (quem gerou o estímulo)
        ring_radius: float = 96.0,      # raio do anel de busca
        ring_points: int = 6,           # quantos pontos no anel
        arrival_radius: float = 14.0,   # raio de chegada por ponto
        timeout_ms: int = 5000,         # tempo máximo de busca
        dwell_ms: int = 250             # pequena “olhada” ao chegar num ponto
    ):
        super().__init__(character=character)
        self.source = source
        self.arrival_radius = float(arrival_radius)
        self.timeout_ms = int(timeout_ms)
        self.dwell_ms = int(dwell_ms)

        self._started_ms = pygame.time.get_ticks()
        self._dwell_until = 0
        self._idx = 0
        self.found = False

        center = pygame.Vector2(stimulus_pos)

        # Pré-computa os waypoints: centro + anel simples
        self._waypoints: list[pygame.Vector2] = [center]
        if ring_points > 0 and ring_radius > 0:
            step = 2 * pi / ring_points
            for i in range(ring_points):
                ang = i * step
                # leve ruído para não ficar hexágono perfeito
                jitter = pygame.Vector2(uniform(-6, 6), uniform(-6, 6))
                p = center + pygame.Vector2(cos(ang), sin(ang)) * ring_radius + jitter
                self._waypoints.append(p)

        # sub-ação de movimento até o primeiro waypoint
        self._move = None
        if self._waypoints:
            self._move = Move(
                character=self.character,
                mode="to",
                dest=self._waypoints[0],
                arrival_radius=self.arrival_radius,
            )

    def _now(self) -> int:
        return pygame.time.get_ticks()

    def _arrived(self, dest: pygame.Vector2) -> bool:
        me = pygame.Vector2(self.character.hitbox.center)
        return me.distance_to(dest) <= self.arrival_radius

    def _reacquired_source(self) -> bool:
        if not self.source:
            return False
        # Se você já usa self.character.percepted_creatures
        pcs = getattr(self.character, "percepted_creatures", [])
        return self.source in pcs

    def update(self, dt: float) -> bool:
        now = self._now()

        # 1) Achou de novo o alvo? termina com sucesso
        if self._reacquired_source():
            self.found = True
            return False  # action concluída

        # 2) Timeout da investigação
        if now - self._started_ms >= self.timeout_ms:
            return False

        # 3) Sem waypoints ou terminou todos
        if not self._waypoints or self._idx >= len(self._waypoints):
            return False

        dest = self._waypoints[self._idx]

        # 4) Se estamos “observando” o entorno, espera um pouco parado
        if self._dwell_until > now:
            self.character.direction = pygame.Vector2()
            return True

        # 5) Caminha usando a própria Move(to)
        if self._move is None:
            self._move = Move(
                character=self.character,
                mode="to",
                dest=dest,
                arrival_radius=self.arrival_radius,
            )

        self._move.dest = pygame.Vector2(dest)  # garante dest atualizado
        self._move.update(dt)

        # 6) Ao chegar, agenda um dwell e avança para o próximo ponto
        if self._arrived(dest):
            self._idx += 1
            self._dwell_until = now + self.dwell_ms
            self._move = None  # será recriada para o próximo waypoint

        return True
    
    def __str__(self):
        return "Investigating"

class Pursue(Action):
    """
    Persegue um alvo com antecipação (lead) e regras de perda de alvo.
    Usa internamente Move(mode='to') para navegar com colisão simples.
    Termina (return False) se perder o alvo por muito tempo ou sair do leash.
    Mantém (return True) enquanto perseguindo; se estiver em alcance (stop_radius),
    o FSM pode trocar para Attack, por exemplo.
    """
    def __init__(
        self,
        character: Character,
        target: Character,
        *,
        stop_radius: float = 28.0,        # quando <= isso, considera "em alcance"
        leash_px: float = 420.0,          # distância máxima antes de abortar
        loss_timeout_ms: int = 1200,      # tempo sem perceber o alvo até abortar
        lead_ms: int = 220,               # antecipação da posição do alvo
        replan_cooldown_ms: int = 200,
        is_running: bool = True
    ):
        super().__init__(character=character)
        self.target = target
        self.stop_radius = float(stop_radius)
        self.leash_px = float(leash_px)
        self.loss_timeout_ms = int(loss_timeout_ms)
        self.lead_ms = int(lead_ms)

        # Reaproveita sua Move 'to' para toda a locomoção/evitar obstáculo
        self._move = Move(
            character=character,
            mode="to",
            dest=None,
            replan_cooldown_ms=replan_cooldown_ms,
            is_running=is_running
        )

        self._last_seen_ms = pygame.time.get_ticks()
        self._last_target_pos = pygame.Vector2(self.target.hitbox.center)

    def _now(self) -> int:
        return pygame.time.get_ticks()

    def _dist_to_target(self) -> float:
        me = pygame.Vector2(self.character.hitbox.center)
        tgt = pygame.Vector2(self.target.hitbox.center)
        return (tgt - me).length()

    def _predict_target_pos(self, dt: float) -> pygame.Vector2:
        """Lead por velocidade recente do alvo (barato)."""
        cur = pygame.Vector2(self.target.hitbox.center)
        # evita dt 0 e ruído
        v = (cur - self._last_target_pos) / max(dt, 1e-3)
        predicted = cur + v * (self.lead_ms / 1000.0)
        self._last_target_pos = cur
        return predicted

    def update(self, dt: float) -> bool:
        # Alvo inválido?
        if not hasattr(self.target, "hitbox"):
            return False

        # Leash/abort
        if self._dist_to_target() > self.leash_px:
            return False

        # Checagem de percepção simples (integra com seu sistema de sentidos)
        percep = getattr(self.character, "percepted_creatures", None)
        now = self._now()
        if percep is not None and (self.target in percep):
            self._last_seen_ms = now
        elif (now - self._last_seen_ms) > self.loss_timeout_ms:
            # perdeu o alvo tempo demais → termina; FSM pode acionar Investigate
            return False

        # Em alcance? Pare, mantenha direção zero e deixe o FSM trocar pra Attack.
        if self._dist_to_target() <= self.stop_radius:
            self.character.direction.update(0, 0)
            return True

        # Perseguir com antecedência de posição
        dest = self._predict_target_pos(dt)
        self._move.dest = dest
        self._move.update(dt)
        return True

    def __str__(self):
        return "Pursuing"

class Combat(Action):
    """
    Ação de combate contra um alvo: persegue e ataca até que eu ou o alvo estejam 'dead'.
    Retorna True enquanto o combate estiver em curso; retorna False quando o combate termina
    (um dos dois morreu), permitindo que o FSM troque de ação.

    Novos parâmetros (opcionais):
      - ranged: bool = False         -> modo à distância (usa distância ótima / min_range)
      - optimal_range: float | None  -> distância que o atacante tenta manter (se None usa attack_range)
      - min_range: float | None      -> distância mínima tolerada (se o alvo estiver mais perto, recua)
      - attack_cooldown_ms: int      -> intervalo mínimo entre ataques (ms)
    """
    def __init__(
        self,
        character: Character,
        target: Character,
        *,
        attack_range: float = 36.0,
        move_running: bool = True,
        stop_on_kill: bool = True,  # se True, para mover/atacar após matar
        retreat_on_low_hp: float | None = None,  # se definido, distância para recuar quando hp baixo (0..1 fraction)
        ranged: bool = False,
        optimal_range: float | None = None,
        min_range: float | None = None,
        attack_cooldown_ms: int = 500,  # cooldown mínimo entre ataques (ms)
    ):
        super().__init__(character=character)
        self.target = target
        self.attack_range = float(attack_range)
        self.stop_on_kill = bool(stop_on_kill)
        self.retreat_on_low_hp = float(retreat_on_low_hp) if retreat_on_low_hp is not None else None

        # Ranged settings
        self.ranged = bool(ranged)
        # distância desejada para combate ranged; se None usamos attack_range
        self.optimal_range = float(optimal_range) if optimal_range is not None else float(attack_range)
        # distância mínima aceitável (se o alvo vier para muito perto, recuar). Se None, usa metade do attack_range.
        self.min_range = float(min_range) if min_range is not None else max(0.0, float(attack_range) * 0.5)

        # timing de ataque
        self.attack_cooldown_ms = int(attack_cooldown_ms)
        self._last_attack_time = -99999

        # Move helper (assumo que exista uma classe Move compatível)
        self._move = Move(character=character, mode="to", dest=pygame.Vector2(target.hitbox.center), is_running=move_running)

    def _now(self) -> int:
        return pygame.time.get_ticks()

    def _dist(self, a: pygame.Vector2, b: pygame.Vector2) -> float:
        return (a - b).length()

    def _is_dead(self, ent) -> bool:
        # Várias formas de checar morte: prioridade para atributo 'status'
        if ent is None:
            return True
        if getattr(ent, "status", None) == "dead":
            return True
        if getattr(ent, "is_dead", None):
            return True
        hp = getattr(ent, "hp", None)
        if hp is not None:
            try:
                return float(hp) <= 0.0
            except Exception:
                pass
        return False

    def _can_attack(self) -> bool:
        """Verifica se o cooldown de ataque já passou."""
        delay_passed = (self._now() - self._last_attack_time) >= self.attack_cooldown_ms
        is_attacking = self.character.is_attacking
        return delay_passed and not is_attacking
    
    def _do_ranged_attack(self):
        """
        Tenta executar um ataque à distância.
        Preferimos chamar métodos do character (ranged_attack/fire_projectile) se existirem,
        senão definimos flags compatíveis (attack_1/attack_2/attack_ranged) para o sistema atual.
        """
        self._last_attack_time = self._now()
        # prioridade para chamadas dedicadas
        try:
            if hasattr(self.character, "ranged_attack") and callable(getattr(self.character, "ranged_attack")):
                self.character.ranged_attack(self.target)
                return
            if hasattr(self.character, "fire_projectile") and callable(getattr(self.character, "fire_projectile")):
                # fire_projectile pode aceitar target ou posição
                try:
                    self.character.fire_projectile(self.target)
                except TypeError:
                    self.character.fire_projectile(pygame.Vector2(self.target.hitbox.center))
                return
        except Exception:
            # falhou ao chamar métodos dedicados; fallback para flags abaixo
            pass

        # fallback: usar as flags de ataque já utilizadas para animações/efeitos
        if randint(0, 10) >= 5:
            self.character.attack_1 = True
            self.character.attack_2 = False
        else:
            self.character.attack_2 = True
            self.character.attack_1 = False

        # marca também uma flag genérica para ataques ranged, se o character usar isso
        try:
            self.character.attack_ranged = True
        except Exception:
            pass

    def _do_melee_attack(self):
        """Executa ataque corpo-a-corpo (mesma compatibilidade do código original)."""
        self._last_attack_time = self._now()
        if randint(0, 10) >= 5:
            self.character.attack_1 = True
            self.character.attack_2 = False
        else:
            self.character.attack_2 = True
            self.character.attack_1 = False

    def end_combat(self,):
        # limpar estados/flags de combate no character
        try:
            self.character.is_combating = False
        except Exception:
            pass
        try:
            self.character.attacking_character = None
        except Exception:
            pass
        # limpar flags de ataque também (por segurança)
        try:
            self.character.attack_1 = False
            self.character.attack_2 = False
            self.character.attack_ranged = False
        except Exception:
            pass
        return 

    def update(self, dt: float) -> bool:
        now = self._now()

        # checar se eu já morri
        if self._is_dead(self.character):
            # meu personagem morreu — combate acaba
            self.end_combat()
            return False

        # cheque target válido e não-morto
        if self.target is None or self._is_dead(self.target):
            # não há alvo vivo — término do combate
            self.end_combat()
            return False

        me_pos = pygame.Vector2(self.character.hitbox.center)
        tgt_pos = pygame.Vector2(self.target.hitbox.center)
        dist = self._dist(me_pos, tgt_pos)
        

        # se especificado retreat_on_low_hp, avaliar
        if self.retreat_on_low_hp is not None:
            my_hp = getattr(self.character, "hp", None)
            if my_hp is not None:
                try:
                    frac = float(my_hp) / max(1.0, float(getattr(self.character, "max_hp", my_hp)))
                    if frac <= self.retreat_on_low_hp:
                        # recuar: andar um pouco para trás em relação ao alvo (dest = direção oposta)
                        dir_vec = (me_pos - tgt_pos)
                        if dir_vec.length_squared() < 1e-6:
                            # empurra pra uma direção arbitrária
                            dir_vec = pygame.Vector2(1, 0)
                        dir_vec = dir_vec.normalize()
                        retreat_dest = me_pos + dir_vec * max(self.attack_range * 1.5, 80.0)
                        self._move.dest = retreat_dest
                        self._move.update(dt)
                        return True
                except Exception:
                    pass

        # --- LÓGICA PARA RANGED VS MELEE ---
        if self.ranged:
            # COMBATE À DISTÂNCIA: queremos manter distância entre min_range e optimal_range.
            # Se estamos fora do optimal_range (muito longe) -> aproximar.
            # Se estamos mais perto que min_range -> recuar.
            # Se estamos dentro da faixa aceitável -> parar e atirar (respeitando cooldown).
            if dist > self.optimal_range:
                # aproximar para a distância ótima (parando em optimal_range)
                # definimos dest como a posição do alvo (move se necessário), mas Move deve parar quando alcançado.
                self._move.dest = tgt_pos
                self._move.update(dt)
                return True

            if dist < self.min_range:
                # recuar um pouco para ganhar espaço
                dir_vec = (me_pos - tgt_pos)
                if dir_vec.length_squared() < 1e-6:
                    dir_vec = pygame.Vector2(1, 0)
                dir_vec = dir_vec.normalize()
                retreat_dest = me_pos + dir_vec * max(self.optimal_range, 80.0)
                self._move.dest = retreat_dest
                self._move.update(dt)
                return True

            # estamos entre min_range e optimal_range -> ficar parado e atacar à distância
            # alinhar visual / direção (se aplicável)
            try:
                self.character.direction.update(tgt_pos.x - me_pos.x, tgt_pos.y - me_pos.y)
            except Exception:
                pass

            # atacar se cooldown permitir
            if self._can_attack():
                self._do_ranged_attack()

            # depois do ataque, checar se o alvo morreu
            if self._is_dead(self.target):
                if self.stop_on_kill:
                    try:
                        self.character.direction.update(0, 0)
                        # parar movimento
                        try:
                            self.character.velocity = pygame.Vector2(0, 0)
                        except Exception:
                            pass
                    except Exception:
                        pass
                self.end_combat()
                return False

            # continuar combate ranged
            return True

        else:
            # MELEE / comportamento original:
            # se estamos fora de alcance → mover para o alvo (com alguma tolerância)
            if dist > self.attack_range:
                # mover prevendo posição simples (sem lead)
                self._move.dest = tgt_pos
                self._move.update(dt)
                return True

            # estamos dentro do alcance → parar e atacar se puder
            # alignar visual / direção
            try:
                self.character.direction.update(tgt_pos.x - me_pos.x, tgt_pos.y - me_pos.y)
            except Exception:
                pass

            # tempo de ataque?
            if self._can_attack():
                self._do_melee_attack()

            # depois do ataque, checar se o alvo morreu
            if self._is_dead(self.target):
                if self.stop_on_kill:
                    # opcional: zerar velocidade e ficar Idle
                    try:
                        self.character.direction.update(0, 0)
                    except Exception:
                        pass
                # combate acabou
                self.end_combat()
                return False

            # se não matou, continua combate
            return True

    def __str__(self):
        return f"Combat {self.target} (ranged={self.ranged})"

class Idle(Action):
    """
    Ação de espera com comportamentos variados:
      - mode='look_around' : muda direção do olhar periodicamente
      - mode='sleep'       : fica parado até ser perturbado
      - mode='patrol'      : alterna entre idle e movimentação curta
    """
    def __init__(
        self,
        character: Character,
        mode: str = "",
        duration_ms: int = 3000,
        chance_to_move: float = 0.3
    ):
        super().__init__(character=character)
        self.mode = mode
        self.duration_ms = duration_ms
        self.chance_to_move = chance_to_move
        
        self._started_ms = pygame.time.get_ticks()
        self._last_change_ms = 0
        self._change_interval = 2000

    def update(self, dt: float) -> bool:
        current_time = pygame.time.get_ticks()
        
        # Termina após o tempo determinado
        if current_time - self._started_ms > self.duration_ms:
            return False

        if self.mode == "look_around":
            self._look_around(current_time)
        elif self.mode == "patrol":
            self._patrol_behavior(current_time)
        elif self.mode == "sleep":
            self.character.action = "Sleep"
        elif self.mode == "":
           return True
        return True

    def _look_around(self, current_time: int):
        if current_time - self._last_change_ms > self._change_interval:
            # Muda a direção do olhar aleatoriamente
            angle = uniform(-45, 45)
            if self.character.direction.length_squared() > 0:
                self.character.direction = self.character.direction.rotate(angle)
            else:
                self.character.direction = pygame.Vector2(1, 0).rotate(uniform(0, 360))
            self._last_change_ms = current_time

    def _patrol_behavior(self, current_time: int):
        # Chance de iniciar movimento curto
        if (current_time - self._last_change_ms > self._change_interval and 
            random() < self.chance_to_move):
            # Alterna para movimento por um curto período
            short_move = Move(
                character=self.character,
                mode="wander",
                arrival_radius=60.0
            )
            # Dependendo da sua arquitetura, você pode trocar a ação atual
            self.character.set_action(short_move)


    def __str__(self):
        return "Sleeping"