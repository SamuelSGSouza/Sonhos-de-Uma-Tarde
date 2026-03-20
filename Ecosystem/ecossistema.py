from settings import *
from pytmx import load_pygame
from sprites import *
from Utils.monsters import *
from Utils.effects import *
from Utils.items import *
from Utils.actions import *
from Utils.classes_raiz import *

class Map:

    def __init__(self, all_sprites, collision_sprites, all_creatures:pygame.sprite.Group, player_group, winter_curse_group):
        self.map = load_pygame(join(getcwd(), "Ecosystem", "Winter", "Tiles", "tileset", "Winter.tmx"))
        self.village_pits:list[set] = []

        #Loading ground and details in one image
        camadas_terreno = [
            "Ground 1", "Ground 2", "Ground 4","Ground Details", "Water Cliffs",
        ]
        ## Pegamos o tamanho total do mapa (em tiles) e convertendo para pixels
        map_width = self.map.width * 16 * SCALE
        map_height = self.map.height * 16 * SCALE

        ## Criamos uma surface única para o terreno
        map_surface = pygame.Surface((map_width, map_height), pygame.SRCALPHA).convert_alpha()

        ## Desenha cada camada dentro da surface
        for camada in camadas_terreno:
            layer = self.map.get_layer_by_name(camada)
            for x, y, image in layer.tiles():
                scaled_image = pygame.transform.scale(image, (image.width * SCALE, image.height * SCALE)).convert_alpha()
                map_surface.blit(scaled_image, (x * 16 * SCALE, y * 16 * SCALE))
        ##
        StaticMap(all_sprites, map_surface)
        all_sprites.att_world_size(map_width, map_height)


        

        fixed_objects_layer =  self.map.get_layer_by_name("Fixed Objects")
        for obj in fixed_objects_layer:
            CollisionSprites(all_sprites, collision_sprites, pos=(obj.x*SCALE, obj.y*SCALE), surface=pygame.transform.scale(obj.image, (obj.image.width*SCALE, obj.image.height*SCALE)))
        
        fixed_objects_layer =  self.map.get_layer_by_name("Invisible Objects")
        for obj in fixed_objects_layer:
            CollisionSprites(all_sprites, collision_sprites, pos=(obj.x*SCALE, obj.y*SCALE), surface=pygame.transform.scale(obj.image, (obj.image.width*SCALE, obj.image.height*SCALE)), is_invisible=True)
        
        fixed_objects_layer =  self.map.get_layer_by_name("Fixed Houses")
        for obj in fixed_objects_layer:
            CollisionSprites(all_sprites, collision_sprites, pos=(obj.x*SCALE, obj.y*SCALE), surface=pygame.transform.scale(obj.image, (obj.image.width*SCALE, obj.image.height*SCALE)), is_fixed_house=True)
        
        moveable_objects =  self.map.get_layer_by_name("Moveable Objects")
        for obj in moveable_objects:
            MoveableSprites(all_sprites, collision_sprites, pos=(obj.x*SCALE, obj.y*SCALE), surface=pygame.transform.scale(obj.image, (obj.image.width*SCALE, obj.image.height*SCALE)))
        
        christmas_trees =  self.map.get_layer_by_name("Christmas tree 3")
        for obj in christmas_trees:
            CollisionSprites(all_sprites, collision_sprites, pos=(obj.x*SCALE, obj.y*SCALE), surface=pygame.transform.scale(obj.image, (obj.image.width*SCALE, obj.image.height*SCALE)))
        
        orcs_houses_layer =  self.map.get_layer_by_name("Orcs Houses")
        for obj in orcs_houses_layer:
            CollisionSprites(all_sprites, collision_sprites, pos=(obj.x*SCALE, obj.y*SCALE), surface=pygame.transform.scale(obj.image, (obj.image.width*SCALE, obj.image.height*SCALE)))
        
        orcs_houses_layer =  self.map.get_layer_by_name("Chief Orcs Houses")
        for obj in orcs_houses_layer:
            CollisionSprites(all_sprites, collision_sprites, pos=(obj.x*SCALE, obj.y*SCALE), surface=pygame.transform.scale(obj.image, (obj.image.width*SCALE, obj.image.height*SCALE)))
        
        fixed_objects_layer =  self.map.get_layer_by_name("Village Pit")
        for obj in fixed_objects_layer:
            CollisionSprites(all_sprites, collision_sprites, pos=(obj.x*SCALE, obj.y*SCALE), surface=pygame.transform.scale(obj.image, (obj.image.width*SCALE, obj.image.height*SCALE)))
            self.village_pits.append((obj.x*SCALE - (obj.image.width*SCALE)/2, obj.y*SCALE + obj.image.height*SCALE +16))

        getable_objects_layer =  self.map.get_layer_by_name("Getable Objects")
        for obj in getable_objects_layer:
            surface = pygame.transform.scale(obj.image, (obj.image.width*SCALE, obj.image.height*SCALE)).convert_alpha()
            CollisionSprites(all_sprites, collision_sprites, pos=(obj.x*SCALE, obj.y*SCALE), surface=surface, item=Jar(all_sprites, collision_sprites,surface), is_getable=True)
        
        getable_objects_layer =  self.map.get_layer_by_name("Trees")
        for obj in getable_objects_layer:
            surface = pygame.transform.scale(obj.image, (obj.image.width*SCALE*1.5, obj.image.height*SCALE*1.5)).convert_alpha()
            CollisionSprites(all_sprites, collision_sprites, pos=(obj.x*SCALE, obj.y*SCALE), surface=surface, item=Jar(all_sprites, collision_sprites,surface), is_tree=True)
        
        getable_objects_layer =  self.map.get_layer_by_name("Roof")
        for obj in getable_objects_layer:
            surface = pygame.transform.scale(obj.image, (obj.image.width*SCALE, obj.image.height*SCALE)).convert_alpha()
            CollisionSprites(all_sprites, pos=(obj.x*SCALE, obj.y*SCALE), surface=surface, is_roof=True)
        
        #AnimatedSprite
        animations_root_path = join(getcwd(), 'Ecosystem', "Winter", "animated_objects")
        animation_objects = ["Lamps", "Tochs", "Windows", "Doors", "Funnels","Firecamps", "Orcs Houses", "Chief Orcs Houses"]
        for animated in animation_objects:
            animations_folder = join(animations_root_path, animated)
            
            lightable_objects_layer = self.map.get_layer_by_name(animated)
            for obj in lightable_objects_layer:

                if animated in ["Funnels", "Doors", "Scaled", "Windows", ]:
                    AnimatedSprite(all_sprites,root=animations_folder,obj = obj.image, use_center=False,pos=(obj.x*SCALE, obj.y*SCALE), is_detail=True, has_light=True)

                else:
                    AnimatedSprite(all_sprites,collision_sprites,root=animations_folder,obj = obj.image, use_center=False,pos=(obj.x*SCALE, obj.y*SCALE), has_light=True)

        water = join(animations_root_path, "Water_1")
        image_surf = pygame.image.load([join(water, "off", img) for img in listdir(join(water, "off"))][0]).convert_alpha()
        AnimatedSprite(all_sprites,collision_sprites,root=water,obj = image_surf, use_center=True,pos=(3834, 4367))
        water = join(animations_root_path, "Water_2")
        image_surf = pygame.image.load([join(water, "off", img) for img in listdir(join(water, "off"))][0]).convert_alpha()
        AnimatedSprite(all_sprites,collision_sprites,root=water,obj = image_surf, use_center=True,pos=(4436, 4057))
        water = join(animations_root_path, "Water_3")
        image_surf = pygame.image.load([join(water, "off", img) for img in listdir(join(water, "off"))][0]).convert_alpha()
        AnimatedSprite(all_sprites,collision_sprites,root=water,obj = image_surf, use_center=True,pos=(4436, 4457))
        water = join(animations_root_path, "Water_2")
        image_surf = pygame.image.load([join(water, "off", img) for img in listdir(join(water, "off"))][0]).convert_alpha()
        AnimatedSprite(all_sprites,collision_sprites,root=water,obj = image_surf, use_center=True,pos=(4131, 4275))
        water = join(animations_root_path, "Water_3")
        image_surf = pygame.image.load([join(water, "off", img) for img in listdir(join(water, "off"))][0]).convert_alpha()
        AnimatedSprite(all_sprites,collision_sprites,root=water,obj = image_surf, use_center=True,pos=(4074, 4575))
        water = join(animations_root_path, "Water_2")
        image_surf = pygame.image.load([join(water, "off", img) for img in listdir(join(water, "off"))][0]).convert_alpha()
        AnimatedSprite(all_sprites,collision_sprites,root=water,obj = image_surf, use_center=True,pos=(4817, 4222))
        
        
        # WinterCurseSprites(all_sprites, collision_sprites, winter_curse_group, pos=(4617, 4322), duration=4000, stacks=3)
        # getable_objects_layer =  self.map.get_layer_by_name("Getable_Objects")
        # inventory_objects_layer =  self.map.get_layer_by_name("Inventory_Objects")
        # moveable_objects_layer =  self.map.get_layer_by_name("Moveable_Objects")

        # objects_root_path = join(getcwd(), "Ecosystem", "Swamp", "graphics", "objects")

        

        
                

        
        # for obj in getable_objects_layer:
            
        #     
        # for obj in moveable_objects_layer:
        #     MoveableSprites(all_sprites, collision_sprites, pos=(obj.x*scale, obj.y*scale), surface=pygame.transform.scale(obj.image, (obj.image.width*scale, obj.image.height*scale)))


        

        

        # for i in range(0,12):
        #     initial_position = (1000, 5000)
        #     monster = Orc(all_sprites, collision_sprites=collision_sprites, initial_position=initial_position, creatures_sprites=all_creatures, )
        #     all_creatures.add(monster)
            
        # for _ in range(0,10):
        #     initial_position = (randint(5660,6101), randint(3809, 4600))
        #     monster = Ghost(all_sprites, collision_sprites=collision_sprites, initial_position=initial_position, creatures_sprites=all_creatures, )
        #     all_creatures.add(monster)
        

        
        
        
        """
        Um ecossistema possui:
        imagem de mapa
        monstros típicos
        som ambiente

        ambientes:
            Terras Secas:
                São chamadas assim apenas por não estarem submersas, mas ainda
                são áreas de terra húmida pantanosa

            Lagoas venenosa:
                As lagoas nesse pântano possuem uma toxicidade alta para seres não adaptados,
                então atravessá-las sem cuidado pode causar envenenamento.
                Quando chove, as lagoas enchem, cobrindo a terra seca. Assim, apenas
                as terras altas se tornam passagens

            Terras Altas
                são os únicos locais que não ficam submersos durante as chuvas que alagam os lagos

        monstros:
            Plantas Carnívoras:
                Limite do ecossistema:
                    Igual quantidade de sapos

                Drops:
                    vegetais - podem ser comidos crus ou cozinhados

                Características físicas:
                    Possuem uma pequena parte exposta que se assemelha à plantas medicinais
                    Possuem cipós que se extendem por 4x o seu tamanho e são usados para prender presas que entram em sua área de ação

                    Quando está se alimentando, se fecha igual um cone

                Características Comportamentais:
                    Vive sempre parada no mesmo local, usa sua aparência para atrair vítimas em busca de antídoto

                    Caso um animal que não possua feromônio de insetos entre em sua área de ação,
                    os cipós fecham o alvo no local e a única forma de sair é derrotando a planta.
                
                    
                Áreas acessíveis:
                    Terras Secas
                    Terrenos altos

            Enxame de insetos:
                Limite do ecossistema:
                    4x a quantidade de sapos

                Drops:
                    Feromônios de insetos - Impede que plantas carnívoras identifiquem o usuário como alimento (possui tempo limite)

                Características Físicas:
                    Enxame de insetos que ficam se movendo em conjunto
                    São em torno de 3 a 4x menores que os sapos
                    Não são visto como alimento pelas plantas carnívoras

                Características Comportamentais:
                    Vive sempre ao redor da coolmeia pendurada em árvores

                    Se estiver com fome:
                        procura por alguma planta venenosa e começa a se alimentar dela, até que ela morra.
                
                        
                Áreas acessíveis:
                    Terras Secas
                    Terrenos altos

            Serpente Venenosa:
                Limite do ecossistema:
                    mesma quantidade de sapos

                Drops:
                    carne de cobra - Pode ser comida crua ou ser assada

                Características Físicas:
                    Uma cobra venenosa que se alimenta praticamente de insetos

                Características Comportamentais:
                    vive principalmente nos matos altos espalhados pelo pantanal

                    Se estiver com fome:
                        se move procurando ninhos de insetos e 
                        usa seus feromônios para atrai-los e se alimentar deles                
                                                
                Áreas acessíveis:
                    Terras Secas



            Sapo do pântano:
                Limite do ecossistema:
                    10

                Drops:
                    Pele de sapo - Se vestida, permite entrar em áreas venenosas
                    Carne de sapo - Pode ser usada para atrair animais ou ser assada para comer

                Características físicas
                    É um tipo de sapo gigante.



                Características Comportamentais
                    Normalmente vagam pelo pântano durante o dia.
                    À noite, vão dormir em vitória-régias que se fecham como casulos

                    Se estiver com fome:
                        Se há outros sapos com fome:
                            Eles caçam uma cobra e usam sua carne para atrair jacarés da água
                            Juntos eles atacam o jacaré e os sobreviventes se alimentam dele
                        
                        Se não há outros sapos com fome:
                            Vai até a beira do lago e espera para atacar um jacaré sozinho

                    Se estiver envenenado:
                        Procura a planta medicinal mais próxima e a come

                
                Áreas acessíveis:
                    Lagos venenosos
                    Terras Secas
                    Terrenos altos

            
            Jacaré do pântano:
                Limite do Ecossistema:
                    metade da quantidade de sapos

                Características físicas
                    É um jacaré verde que pode ter de 2 a 4x o tamanho do Sapo do pântano.
                    
                    Possui imunidade a venenos

                Drops:
                    Pele de jacaré - Caso vestida, assusta sapos e os impede de se aproximar
                    carne de jacaré - Pode ser usada para atrair animais ou ser assada para comer

                Características Comportamentais
                    Fica próximo à beira dos lagos esperando por possíveis presas.
                    Carnes soltas na margem próxima a eles o atraem

                    Está ativo em qualquer horário do dia

                    Se estiver com fome:
                        Caso não se alimente após um longo período, começa a vagar pelo pântano
                        Se estiver em terreno seco, perde velocidade e força

                Áreas acessíveis:
                    Lagos venenosos
                    Terras Secas
                    
                    
                    
        """
