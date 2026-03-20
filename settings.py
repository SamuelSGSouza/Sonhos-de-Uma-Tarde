import pygame
from random import choice, uniform, randint, random
from os.path import join, exists
from os import walk, listdir, getcwd
from os.path import isdir
from os.path import isfile
from os.path import splitext
from math import cos, radians, degrees, atan2, sin, acos, pi, hypot,copysign, ceil
from typing import Optional, Tuple, Union
from PIL import Image
from pathlib import Path
from collections import deque
from json import load, dump
import sys,textwrap
from time import time, perf_counter

pygame.init()
info = pygame.display.Info()
WINDOW_WIDTH, WINDOW_HEIGHT = info.current_w,info.current_h 
# WINDOW_WIDTH, WINDOW_HEIGHT = 1280,720 
TILE_SIZE = 64
DCS = 128 #default character size
HDCS = DCS/2 # Half default character size
HHDCS = DCS/4 #Quarter of default character size
HHHDCS = DCS/8 #Half Quarter of default character size
GRID_SIZE = TILE_SIZE
SCALE = 1.5
MARGEM_DE_ATAQUE = 0.5 #abaixo disso, seres que se encontrarem vão se atacar
LARGURA_MAPA = int(4100 * SCALE) # 200 tiles de largura
ALTURA_MAPA  = int(4100 * SCALE) # 200 tiles de altura
matriz_mapa_global =[[]]

#lendo sprite de flecha

arrow_surf =pygame.transform.scale(pygame.image.load(join(getcwd(), "Utils", "items", "arrow.png")), (64,64))


def load_character_images(default_folder_path, scale_on_attack) -> dict:
    frames = {}
    actions = ["Walk", "Idle", "Attack_1","Attack_2", "Run", "Dead", "Dying", "Hurt",]

    for act in actions:
        povs = ["Front", "Back", "Left", "Right", ]

        frames[act] = {}
        for pov in povs:
            full_dir_path = join(default_folder_path,"", pov,  act)
            dir_images = []
            for image in sorted(listdir(full_dir_path), key=lambda name: int(name.split(".")[0])):
                pov_image = pygame.image.load(join(full_dir_path, image)).convert_alpha()
                if act in ["Attack_1", "Attack_2", "Fishing"]:
                    scale = scale_on_attack
                    dir_images.append(pygame.transform.scale(pov_image, (DCS*scale, DCS*scale)))
                else:
                    dir_images.append(pygame.transform.scale(pov_image, (DCS, DCS)))
            frames[act][pov] = dir_images

    return frames

def load_scripts(path) -> dict:
    with open(join(path, "scripts.json"), 'r', encoding='utf-8') as f:
        dados = load(f)
        return dados
    
def load_finais():
    with open("finais.json", 'r', encoding='utf-8') as f:
        finais = load(f)
        return finais
FINAIS = load_finais()
# Cores
BACKGROUND = (25, 25, 50)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
TEXT_COLOR = (255, 255, 255)
TITLE_COLOR = (255, 215, 0)

# Fontes



#INICIO DO JOGO
class Button:
    def __init__(self, x, y, width, height, text, button_font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
        self.button_font = button_font
        
    def draw(self, surface):
        color = BUTTON_HOVER if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, TEXT_COLOR, self.rect, 3, border_radius=12)
        
        text_surf = self.button_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

TITLE_COLOR = (30, 60, 120)  # Azul escuro para bom contraste com fundo branco
SHADOW_COLOR = (180, 180, 200, 180)  # Azul claro com transparência
HIGHLIGHT_COLOR = (100, 150, 220)  # Azul mais claro para realce


def draw_gradient_title(screen, title_font, title_text):
    # Cria superfície para o título
    title = title_font.render(title_text, True, TITLE_COLOR)
    base_x = WINDOW_WIDTH // 2 - title.get_width() // 2
    base_y = 100
    
    # Desenha múltiplas camadas para efeito de profundidade
    offsets = [
        (3, 3, (150, 150, 180, 150)),  # Sombra principal
        (2, 2, (180, 180, 210, 120)),  # Sombra secundária
        (1, 1, (210, 210, 230, 80)),   # Borda externa
    ]
    
    for dx, dy, color in offsets:
        shadow = title_font.render(title_text, True, color)
        screen.blit(shadow, (base_x + dx, base_y + dy))
    
    # Desenha o título principal
    screen.blit(title, (base_x, base_y))
    
    # Adiciona um leve realce na parte superior
    highlight = title_font.render(title_text, True, HIGHLIGHT_COLOR)
    screen.blit(highlight, (base_x, base_y - 1))


def draw_menu(screen, play_button,continuar_button, quit_button, title_font, bg_image, bg_pos, loop):
    

    

    
    # Título
    title = title_font.render("A Décima Primeira Hora do Inverno", True, TITLE_COLOR)
    title_shadow = title_font.render("A Décima Primeira Hora do Inverno", True, (150, 150, 150))
    
    
    # Instrução
    instruction_font = pygame.font.SysFont('arial', 18)
    instruction = instruction_font.render("Use o mouse para navegar no menu", True, (180, 180, 180))
    screen.blit(instruction, (WINDOW_WIDTH//2 - instruction.get_width()//2, WINDOW_HEIGHT - 40))

    screen.fill((10, 10, 15)) 
    screen.blit(bg_image, bg_pos)

    draw_gradient_title(screen, title_font, "A Décima Primeira Hora do Inverno")


    # Desenha botões
    play_button.draw(screen)
    if loop != 1:
        continuar_button.draw(screen)
    quit_button.draw(screen)

def scale_and_center(image, target_size):
    target_w, target_h = target_size
    img_w, img_h = image.get_size()

    # Calcula o fator de escala mantendo proporção
    scale = max(target_w / img_w, target_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    scaled_image = pygame.transform.smoothscale(image, (new_w, new_h))

    # Centraliza
    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2

    return scaled_image, (x, y)

def main_menu(screen, title_font, button_font, snow):
    with open(join(getcwd(),"save.json"), "r", encoding="utf-8") as f:
        loop = load(f)["loop"]
    # Cria botões centralizados
    continue_button_width = 300
    quit_button_y_pos = 400 if loop == 1 else 500
    button_width, button_height = 250, 60
    novo_jogo_button = Button(WINDOW_WIDTH//2 - button_width//2, 300, button_width, button_height, "NOVO JOGO",button_font=button_font)
    continuar_button = Button(WINDOW_WIDTH//2 - continue_button_width//2, 400, continue_button_width, button_height, f"CONTINUAR LOOP {loop}",button_font=button_font)
    quit_button = Button(WINDOW_WIDTH//2 - button_width//2, quit_button_y_pos, button_width, button_height, "SAIR",button_font=button_font)
    
    clock = pygame.time.Clock()
    
    bg_image = pygame.image.load('Utils/Background_3.png').convert_alpha()

    bg_image, bg_pos = scale_and_center(
        bg_image,
        (WINDOW_WIDTH, WINDOW_HEIGHT)
    )

    bg_image.set_alpha(70)



    while True:
        dt = clock.tick(240) / 1000  
        mouse_pos = pygame.mouse.get_pos()
        
        # Verifica eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and quit_button.check_hover(mouse_pos) == True:
                pygame.quit()
                sys.exit()
                
            # Verifica clique nos botões
            if novo_jogo_button.is_clicked(mouse_pos, event):
                return "NOVO JOGO"  # Retorna para iniciar o jogo
            
            if continuar_button.is_clicked(mouse_pos, event):
                return "CONTINUAR"  # Retorna para iniciar o jogo
                
            if quit_button.is_clicked(mouse_pos, event):
                pygame.quit()
                sys.exit()
        
        # Atualiza estado dos botões (hover)
        novo_jogo_button.check_hover(mouse_pos)
        continuar_button.check_hover(mouse_pos)
        quit_button.check_hover(mouse_pos)
        # Desenha tudo
        draw_menu(screen, novo_jogo_button,continuar_button, quit_button, title_font, bg_image, bg_pos, loop)
        

        snow.update(dt, )
        snow.draw(screen)

        # Atualiza display
        pygame.display.flip()
              
        
        clock.tick(60)
 
#FIM DO JOGO
class EndingEvent:
    """
    Evento de encerramento para Pygame com fade-in/out e imagens ao lado dos créditos.
    - screen: pygame.Surface principal
    - ending_text: str | List[str] explicação do final (parágrafos)
    - credits_dir: pasta com arquivos .txt dos créditos
    - options: dict (ver defaults abaixo)
    """

    def __init__(self, screen: pygame.Surface, final_title,ending_text, credits_dir: str, options: dict = None):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass
        pygame.font.init()
        self.final_title = final_title
        self.screen = screen
        self.w, self.h = screen.get_size()
        self.ending_text = ending_text if isinstance(ending_text, list) else ending_text.split("\n")
        self.credits_dir = credits_dir

        # opções padrão
        self.options = {
            "font_path": None,
            "font_size": 22,
            "title_size": 48,
            "scroll_speed": 60,           # px/s
            "music_path": None,
            "bg_color": (6, 6, 20),
            "text_color": (240, 240, 240),
            "title_color": (255, 200, 80),
            "wait_before_credits": 200.0,
            "wrap_margin": 140,
            "fps": 60,
            "fade_in": 1.0,               # seconds for fade-in
            "fade_out": 1.0,              # seconds for fade-out at the end
            "images_dir": None,           # se None, usa credits_dir
            "max_image_height": 320,
            "export_all_credits": False,  # se True, grava all_credits.txt em credits_dir
            "all_credits_name": "all_credits.txt"
        }
        if options:
            self.options.update(options)

        if not self.options["images_dir"]:
            self.options["images_dir"] = self.credits_dir

        # fontes
        if self.options["font_path"]:
            try:
                self.font = pygame.font.Font(self.options["font_path"], self.options["font_size"])
                self.title_font = pygame.font.Font(self.options["font_path"], self.options["title_size"])
            except Exception:
                self.font = pygame.font.SysFont(None, self.options["font_size"])
                self.title_font = pygame.font.SysFont(None, self.options["title_size"])
        else:
            self.font = pygame.font.SysFont(None, self.options["font_size"])
            self.title_font = pygame.font.SysFont(None, self.options["title_size"])

        # música
        self.music_loaded = False
        if self.options["music_path"] and isfile(self.options["music_path"]):
            try:
                pygame.mixer.music.load(self.options["music_path"])
                self.music_loaded = True
            except Exception:
                print("Aviso: não foi possível carregar a música de créditos.")

        self.clock = pygame.time.Clock()

    # ------------------------
    # leitura e processamento
    # ------------------------
    def _read_credits_files(self) -> list[dict]:
        """
        Lê arquivos .txt da pasta, retorna lista de entries:
        [{'name':basename, 'lines':[...], 'image_path': optional str}]
        Ordenados por nome do arquivo.
        """
        if not isdir(self.credits_dir):
            return [{"name": "(nenhum)", "lines": ["(Nenhum arquivo de créditos encontrado)"], "image_path": None}]

        files = [f for f in listdir(self.credits_dir) if f.lower().endswith(".txt")]
        files.sort()
        if not files:
            return [{"name": "(nenhum)", "lines": ["(Nenhum arquivo de créditos encontrado)"], "image_path": None}]

        entries = []
        for fname in files:
            fpath = join(self.credits_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    content = fh.read().strip()
            except UnicodeDecodeError:
                with open(fpath, "r", encoding="latin-1") as fh:
                    content = fh.read().strip()

            lines = content.splitlines() if content else []
            basename = splitext(fname)[0]

            # procurar imagem associada (mesmo basename ou que comece com basename) na pasta images_dir
            image_path = self._find_associated_image(basename)
            entries.append({"name": basename, "lines": lines, "image_path": image_path})

        if self.options["export_all_credits"]:
            self._export_all_credits(entries)

        return entries

    def _find_associated_image(self, basename: str) -> Optional[str]:
        img_dir = self.options["images_dir"]
        if not isdir(img_dir):
            return None
        candidates = []
        for ext in (".png", ".jpg", ".jpeg", ".bmp", ".webp"):
            direct = join(img_dir, basename + ext)
            if isfile(direct):
                return direct
        # se não direto, buscar por arquivos que comecem com basename_
        for f in listdir(img_dir):
            low = f.lower()
            if low.startswith(basename.lower()):
                if any(low.endswith(e) for e in (".png", ".jpg", ".jpeg", ".bmp", ".webp")):
                    return join(img_dir, f)
        return None

    def _export_all_credits(self, entries: list[dict]):
        try:
            out_path = join(self.credits_dir, self.options["all_credits_name"])
            with open(out_path, "w", encoding="utf-8") as fh:
                for e in entries:
                    fh.write(f"--- {e['name']} ---\n")
                    fh.write("\n".join(e["lines"]))
                    fh.write("\n\n")
            print("Arquivo concatenado gerado em:", out_path)
        except Exception as e:
            print("Erro ao exportar all_credits:", e)

    def _wrap_lines(self, lines:list, max_width: int) -> list:
        wrapped = []
        avg_char_w = max(1, self.font.size("M")[0])
        max_chars = max(20, max_width // avg_char_w)
        for line in lines:
            if line.strip() == "":
                wrapped.append("")
            else:
                wrapped.extend(textwrap.wrap(line, width=max_chars))
        return wrapped

    def _load_and_scale_image(self, path: str) -> Optional[pygame.Surface]:
        if not path or not isfile(path):
            return None
        try:
            img = pygame.image.load(path).convert_alpha()
            ih = img.get_height()
            iw = img.get_width()
            max_h = self.options["max_image_height"]
            if ih > max_h:
                scale = max_h / ih *2
                new_w = max(1, int(iw * scale))
                new_h = max(1, int(ih * scale))
                img = pygame.transform.smoothscale(img, (new_w, new_h))
            return img
        except Exception:
            return None

    # ------------------------
    # render do bloco de créditos em surface
    # ------------------------
    def _build_credits_surface(self, entries) -> pygame.Surface:
        """
        Monta uma surface com todos os blocos de créditos empilhados, cada bloco
        contendo texto (wrap) e, se houver, a imagem ao lado direito.
        """
        margin = 40
        content_width = self.w - self.options["wrap_margin"]  # espaço para texto + imagem
        line_spacing = 8

        # first pass: create rendered surfaces and measure total height
        blocks = []
        total_h = 0
        for e in entries:
            # carregar imagem (scaled)
            img = self._load_and_scale_image(e.get("image_path"))
            img_w = img.get_width() if img else 0
            # reserve some space between text and image
            gap = 16 if img else 0
            text_area_width = content_width - img_w - gap - 2 * margin

            wrapped = self._wrap_lines(e["lines"], max(20, text_area_width))
            # if no lines, create a small spacer
            if not wrapped:
                wrapped = [""]

            text_surfaces = [self.font.render(l, True, self.options["text_color"]) for l in wrapped]

            # compute block height
            block_h = sum(s.get_height() + line_spacing for s in text_surfaces)
            # add some separation between blocks
            block_h += 30

            blocks.append({"name": e["name"], "text_surfaces": text_surfaces, "image": img, "img_w": img_w, "gap": gap, "block_h": block_h})
            total_h += block_h

        total_h += self.h  # margem extra para rolar até sumir
        credits_surf = pygame.Surface((self.w, max(total_h, self.h)), flags=pygame.SRCALPHA)
        credits_surf.fill((0, 0, 0, 0))

        # second pass: blit each block
        y = self.h  # start from below screen
        for block in blocks:
            # optional: draw block title (the file name) in bold-ish on top
            title_surf = self.font.render(block["name"], True, self.options["title_color"])
            credits_surf.blit(title_surf, ((self.w - title_surf.get_width()) // 2, y))
            y += title_surf.get_height() + 6

            # compute left text start
            text_x = margin
            # compute area for image on right area (centered vertically to block)
            img = block["image"]
            img_h = img.get_height() if img else 0
            # render lines
            for ts in block["text_surfaces"]:
                credits_surf.blit(ts, (text_x, y))
                y += ts.get_height() + line_spacing

            # if image exists, blit it at right side of the block (aligned top to the first line)
            if img:
                # place image to the right with margin
                img_x = self.w - margin - block["img_w"]
                # place vertically: align with title top + small offset
                img_y = y - sum(ts.get_height() + line_spacing for ts in block["text_surfaces"]) - 10
                credits_surf.blit(img, (img_x, img_y))

            y += 30  # separation

        return credits_surf

    # ------------------------
    # fade utilities
    # ------------------------
    def _do_fade(self, surface_callable, duration: float, fade_in=True):
        """
        Faz fade-in ou fade-out aplicando uma máscara preta com alpha variável sobre a tela.
        surface_callable() deve pintar a tela base (sem o overlay) antes do overlay ser aplicado.
        """
        if duration <= 0:
            surface_callable()
            pygame.display.flip()
            return

        steps = max(1, int(self.options["fps"] * duration))
        for i in range(steps + 1):
            t = i / steps
            alpha = int((1.0 - t) * 255) if fade_in else int(t * 255)
            if fade_in:
                # fade-in: start black (alpha=255), go to transparent (alpha=0)
                overlay_alpha = int((1.0 - t) * 255)
            else:
                # fade-out: start transparent (alpha=0) go to black (alpha=255)
                overlay_alpha = int(t * 255)

            surface_callable()
            overlay = pygame.Surface((self.w, self.h))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(overlay_alpha)
            self.screen.blit(overlay, (0, 0))
            pygame.display.flip()
            self.clock.tick(self.options["fps"])

    # ------------------------
    # execução do evento
    # ------------------------
    def run(self):
        bg = self.options["bg_color"]
        text_color = self.options["text_color"]
        title_color = self.options["title_color"]
        fps = self.options["fps"]

        # --- Stage 1: mostrar explicação do final com fade-in ---
        expl_lines = []
        for paragraph in self.ending_text:
            expl_lines.extend(textwrap.wrap(paragraph, width=80))
            expl_lines.append("")

        expl_surfaces = [self.font.render(l, True, text_color) for l in expl_lines]
        title_surf = self.title_font.render(self.final_title, True, title_color)

        # start music if available
        if self.music_loaded:
            try:
                pygame.mixer.music.play(-1)
            except Exception:
                pass

        def draw_explanation():
            self.screen.fill(bg)
            self.screen.blit(title_surf, ((self.w - title_surf.get_width()) // 2, 12))
            total_h = sum(s.get_height() + 6 for s in expl_surfaces)
            y_start = int(self.h * 0.35 - total_h // 2 + title_surf.height *2)
            y = y_start
            for surf in expl_surfaces:
                self.screen.blit(surf, ((self.w - surf.get_width()) // 2, y+12))
                y += surf.get_height() + 6
            tip = self.font.render("Pressione Enter/Esc para pular os créditos", True, text_color)
            self.screen.blit(tip, ((self.w - tip.get_width()) // 2, int(self.h * 0.9)))

        # fade-in explanation
        self._do_fade(draw_explanation, self.options["fade_in"], fade_in=True)

        # wait a bit or until key
        waiting = True
        start_time = pygame.time.get_ticks() / 1000.0
        while waiting:
            dt = self.clock.tick(fps) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    if self.music_loaded:
                        pygame.mixer.music.stop()
                    return "quit"
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                        waiting = False
            if pygame.time.get_ticks() / 1000.0 - start_time >= self.options["wait_before_credits"]:
                waiting = False
            draw_explanation()
            pygame.display.flip()

        # fade-out explanation
        self._do_fade(draw_explanation, self.options["fade_out"], fade_in=False)

        # --- Stage 2: carregar e mostrar créditos com imagens ---
        entries = self._read_credits_files()
        credits_surface = self._build_credits_surface(entries)
        y_pos = self.h
        speed = self.options["scroll_speed"]
        paused = False
        running = True

        # small helper to draw credits frame
        def draw_credits():
            self.screen.fill(bg)
            # blit visible portion of credits_surface
            self.screen.blit(credits_surface, (0, int(y_pos)))
            hint = self.font.render("Espaço: Pausar  /  Esc/Enter: Pular", True, text_color)
            self.screen.blit(hint, (10, self.h - hint.get_height() - 10))

        # fade-in credits
        self._do_fade(draw_credits, self.options["fade_in"], fade_in=True)

        while running:
            dt = self.clock.tick(fps) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    if self.music_loaded:
                        pygame.mixer.music.stop()
                    return "quit"
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        if self.music_loaded:
                            pygame.mixer.music.stop()
                        return "skipped"
                    if ev.key == pygame.K_SPACE:
                        paused = not paused
                    if ev.key == pygame.K_RETURN:
                        # if self.music_loaded:
                        #     pygame.mixer.music.stop()
                        return "skipped"

            if not paused:
                y_pos -= speed * dt

            draw_credits()
            pygame.display.flip()

            # quando todo conteúdo passou
            if y_pos + credits_surface.get_height() < 0:
                running = False

        # fade-out credits
        self._do_fade(draw_credits, self.options["fade_out"], fade_in=False)

        # if self.music_loaded:
        #     pygame.mixer.music.stop()
        return "done"
    
def define_final(player):
    if player.loop == 1:
        Titulo = "A Primeira Morte"
        Final = (
            "A morte veio cedo demais para ter significado.\n"
            "Você caiu antes de entender as regras, antes de compreender por que o sol parecia sempre nascer igual, antes mesmo de suspeitar que o mundo não avançava — apenas repetia.\n\n"
            "A vila queimou. Gritos se misturaram ao estalar da madeira, e então… silêncio.\n"
            "Por um instante, tudo pareceu definitivo. Seu corpo imóvel no chão frio, a tragédia consumada, o fracasso absoluto.\n"
            "Mas algo recusou o encerramento.\n"
            "Quando a escuridão tomou seus sentidos, ela não trouxe descanso — trouxe retorno. O mesmo céu. O mesmo dia. O mesmo começo.\n"
            "Você morreu.\n"
            "E ainda assim, nada terminou.\n"
            "O ciclo apenas começou."
        )
    elif player.loop == 2:
        Titulo = "Ignorância Persistente"
        Final = (
            "Você o encontrou caído entre as árvores, respirando com dificuldade, cercado pelo cheiro de sangue e folhas úmidas."
            "Havia palavras ali. Havia respostas."
            "Mas você se foi."
            "A vila ardeu novamente. As chamas subiram com a mesma fúria de sempre, indiferentes à sua presença ou ausência. Pessoas morreram, outras fugiram, e o mundo seguiu seu roteiro imutável."
            "Desta vez, porém, a morte não parecia surpresa — parecia negligência."
            "Enquanto sua visão escurecia, uma sensação incômoda o acompanhou: a certeza de que algo importante havia sido deixado para trás, apodrecendo na floresta junto com um orc que nunca foi ouvido."
            "O loop recomeça.\nE a pergunta permanece:\nquantas vezes será preciso repetir o erro antes de enxergá-lo?"
        )
    elif player.loop == 3:
        
        Titulo = "Fome Revelada"
        Final = (
            "As peças começaram a se encaixar tarde demais."
            "O orc ferido falou. O chefe da vila respondeu. Entre palavras duras e justificativas frágeis, uma verdade emergiu — simples, cruel e terrivelmente humana."
            "Eles não atacam por ódio."
            "Atacam porque têm fome."
            "Esse conhecimento, porém, não salvou ninguém."
            "Quando a destruição chegou, ela veio com o peso da ironia. Agora você entendia o problema… mas não tinha feito nada para mudá-lo."
            "Ao cair, seu corpo não carregava apenas feridas — carregava a culpa de quem finalmente compreendeu, mas compreendeu tarde demais."
            "O mundo se desfaz mais uma vez."
            "A informação sobrevive."
            "Você, não."
        )
    elif player.loop == 4:
        
        Titulo = "Dois Lados da Mesma Ruína"
        Final = (
            "Pela primeira vez, você ouviu ambos os lados.\n"
            "O orc caído. O líder da horda. Histórias de escassez, crianças famintas, promessas quebradas e uma guerra que não começou por escolha, mas por desespero.\n"
            "Eles não eram monstros.\n"
            "E isso tornava tudo pior.\n"
            "Quando o fim chegou, não houve ódio nos olhos que o encaravam — apenas resignação. O ataque não era pessoal. Era inevitável.\n"
            "Enquanto a vida escapava, você percebeu a cruel simetria: humanos protegendo o que têm, orcs lutando pelo que precisam.\n"
            "Nenhum lado venceu.\n" 
            "Apenas repetiram o erro.\n"
        )
    else:
        
        Titulo = "Dois Lados da Mesma Ruína"
        Final = (
            "Pela primeira vez, você ouviu ambos os lados.\n"
            "O orc caído. O líder da horda. Histórias de escassez, crianças famintas, promessas quebradas e uma guerra que não começou por escolha, mas por desespero.\n"
            "Eles não eram monstros.\n"
            "E isso tornava tudo pior.\n"
            "Quando o fim chegou, não houve ódio nos olhos que o encaravam — apenas resignação. O ataque não era pessoal. Era inevitável.\n"
            "Enquanto a vida escapava, você percebeu a cruel simetria: humanos protegendo o que têm, orcs lutando pelo que precisam.\n"
            "Nenhum lado venceu.\n" 
            "Apenas repetiram o erro.\n"
        )
    return {
       "titulo": Titulo,
        "texto": Final
    }
####################################################


def define_text_on_dead_ally(team_members:list=[], tipo_mental:str="raivoso", enemy_team_members:list = []) -> str:
    #frases se ainda tem membros vivos
    plural = True if enemy_team_members else False
    frases = []
    if team_members:
        if tipo_mental == "raivoso":
            if plural:
                frases = [
                    "Eles querem brincar com a nossa equipe? Beleza. Agora é GUERRA."
                    f"Agora são {len(team_members)} contra {len(enemy_team_members)}. Vamos nessa!"
                    "Se eles acham que vão sair vivos depois disso… estão muito enganados."
                    r"{nome_character}, viu isso? A gente vai devolver isso em dobro!".replace("{nome_character}", choice(team_members).personal_name)
                ]
            else:
                frases = [
                    r"{nome_character}, viu isso? A gente vai devolver isso em dobro!".replace("{nome_character}", choice(team_members).personal_name),
                    "Ele quer brincar com a nossa equipe? Beleza. Agora é GUERRA."
                ]
        else:
            frases = [
                "A perda é real, mas o perigo também. Mantenham a cabeça no lugar.",
                "Não podemos reverter isso, mas podemos impedir que aconteça novamente. Avancem com cautela."
                "Não deixem a raiva nos guiar. Vamos agir com precisão.",
                "Não podemos reverter isso, mas podemos impedir que aconteça novamente. Avancem com cautela."
            ]
    else:
        if tipo_mental == "raivoso":
            frases = [
                "Chega. Agora é pessoal.",
                "Por todos os deuses reais ou imaginários… Só um de nós sairá vivo!",
                "Hoje, perderam a misericórdia de minha lâmina."
            ]
        else:
            frases = [
                "Então… acabou. Eu sou o último.",
                "Não sobrou ninguém pra me responder… mas eu ainda preciso continuar.",
                "Último da equipe… brincamos sobre isso uma vez, mas não imaginei carregar esse título."
            ]

    return choice(frases)  
       

def draw_simple_speech_bubble(screen, font, text, x, y, 
                       max_width=320, padding=18,
                       bg_color=(139, 94, 60, 220),      # marrom claro semi-transparente
                       text_color=(255, 235, 200),       # bege claro (boa leitura)
                       border_color=(90, 55, 35)):       # marrom escuro
    """
    Caixa de diálogo estilo RPG com fundo marrom e aparência de caixa de texto.
    """

    # Divide o texto
    words = text.split(' ')
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.render(test_line, True, text_color).get_rect()

        if bbox.width <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    # Dimensões
    line_height = font.get_linesize()
    total_height = len(lines) * line_height + padding * 2

    max_line_width = max(font.render(line, True, text_color).get_rect().width for line in lines)
    total_width = max_line_width + padding * 2

    # --- Sombra abaixo da caixa ---
    shadow_surf = pygame.Surface((total_width + 4, total_height + 4), pygame.SRCALPHA)
    pygame.draw.rect(
        shadow_surf,
        (0, 0, 0, 90),
        (2, 2, total_width, total_height),
        border_radius=10
    )
    screen.blit(shadow_surf, (x - total_width // 2, y - total_height - 48))

    # --- Caixa principal ---
    bubble_surface = pygame.Surface((total_width, total_height), pygame.SRCALPHA)

    # Fundo
    pygame.draw.rect(
        bubble_surface,
        bg_color,
        (0, 0, total_width, total_height),
        border_radius=10
    )

    # Borda
    pygame.draw.rect(
        bubble_surface,
        border_color,
        (0, 0, total_width, total_height),
        width=3,
        border_radius=10
    )

    # Desenha o texto
    text_y = padding
    for line in lines:
        text_surface = font.render(line, True, text_color)
        bubble_surface.blit(text_surface, (padding, text_y))   # alinhado à esquerda
        text_y += line_height

    # Desenha na tela (centralizado no eixo X)
    screen.blit(bubble_surface, (x - total_width // 2, y - total_height - 50))

def draw_speech_bubble(screen, font, text, x, y, max_width=300, padding=15, bg_color=(242, 237, 204, 255), text_color=(101, 67, 33), border_color=(139, 108, 66)):
    """
    Exibe uma caixa de diálogo estilo pergaminho/papel antigo com quebra de texto automática
    
    Parâmetros:
    screen: Superfície onde desenhar
    font: Fonte renderizada
    text: Texto a ser exibido
    x, y: Posição base da caixa
    max_width: Largura máxima da caixa
    padding: Espaçamento interno
    bg_color: Cor do fundo estilo pergaminho (R, G, B, Alpha)
    text_color: Cor do texto marrom escuro
    border_color: Cor da borda marrom
    """
    
    # Divide o texto em linhas que cabem na largura máxima
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        # Calcula o tamanho do texto com a nova palavra
        bbox = font.render(test_line, True, text_color).get_rect()
        
        if bbox.width <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))

    # Calcula dimensões da caixa
    line_height = font.get_linesize()
    total_height = len(lines) * line_height + padding * 2
    
    # Encontra a linha mais larga para definir a largura da caixa
    max_line_width = 0
    for line in lines:
        line_width = font.render(line, True, text_color).get_rect().width
        max_line_width = max(max_line_width, line_width)
    total_width = max_line_width + padding * 2

    # Cria superfície semitransparente
    bubble_surface = pygame.Surface((total_width, total_height), pygame.SRCALPHA)
    
    # CORES PARA EFEITO DE PAPEL ENVELHECIDO
    parchment_dark = (194, 178, 152, 255)   # Tom mais escuro para sombras
    parchment_light = (235, 224, 203, 255)  # Tom mais claro para realces
    
    # Desenha o fundo principal estilo pergaminho
    pygame.draw.rect(bubble_surface, bg_color, 
                    (0, 0, total_width, total_height), 
                    border_radius=8)
    
    # Adiciona textura de papel - pequenas variações de cor
    for i in range(0, total_width, 3):
        for j in range(0, total_height, 3):
            if (i + j) % 6 == 0:  # Padrão de textura
                alpha_var = randint(5, 15)
                texture_color = (bg_color[0] - 10, bg_color[1] - 10, bg_color[2] - 10, alpha_var)
                pygame.draw.rect(bubble_surface, texture_color, (i, j, 2, 2))
    
    # Borda estilo papel antigo com múltiplas camadas
    # Camada externa mais escura
    pygame.draw.rect(bubble_surface, (120, 90, 60),
                    (0, 0, total_width, total_height),
                    width=3, border_radius=10)
    
    # Camada interna marrom médio
    pygame.draw.rect(bubble_surface, border_color,
                    (2, 2, total_width-4, total_height-4),
                    width=2, border_radius=8)
    
    # Realce interno bege claro
    pygame.draw.rect(bubble_surface, parchment_light,
                    (4, 4, total_width-8, total_height-8),
                    width=1, border_radius=6)

    # Desenha o texto linha por linha
    text_y = padding
    for line in lines:
        text_surface = font.render(line, True, text_color)
        text_x = (total_width - text_surface.get_width()) // 2
        bubble_surface.blit(text_surface, (text_x, text_y))
        text_y += line_height

    # Adiciona pequenos detalhes decorativos nos cantos
    corner_size = 8
    # Cantos superiores
    pygame.draw.line(bubble_surface, border_color, (10, 5), (corner_size, 5), 2)
    pygame.draw.line(bubble_surface, border_color, (5, 10), (5, corner_size), 2)
    pygame.draw.line(bubble_surface, border_color, (total_width-10, 5), (total_width-corner_size, 5), 2)
    pygame.draw.line(bubble_surface, border_color, (total_width-5, 10), (total_width-5, corner_size), 2)
    # Cantos inferiores
    pygame.draw.line(bubble_surface, border_color, (10, total_height-5), (corner_size, total_height-5), 2)
    pygame.draw.line(bubble_surface, border_color, (5, total_height-10), (5, total_height-corner_size), 2)
    pygame.draw.line(bubble_surface, border_color, (total_width-10, total_height-5), (total_width-corner_size, total_height-5), 2)
    pygame.draw.line(bubble_surface, border_color, (total_width-5, total_height-10), (total_width-5, total_height-corner_size), 2)

    # Posiciona a caixa na tela (centralizada horizontalmente acima do personagem)
    screen.blit(bubble_surface, (x - total_width // 2, y - total_height - 50))

def show_modal_old(screen, font, main_text, options, max_width=400, padding=20, bg_color=(242, 255, 255, 255), text_color=(91, 37, 3), border_color=(139, 108, 66), chat_end=False):
    """
    Exibe um modal estilo pergaminho com texto principal e opções clicáveis.
    A função é bloqueante e retorna o índice da opção selecionada pelo usuário.
    Adiciona efeito de hover nas opções.
    
    Parâmetros:
    screen: Superfície principal do Pygame
    font: Fonte renderizada
    main_text: Texto principal a ser exibido
    options: Lista de strings com as opções
    max_width: Largura máxima da caixa
    padding: Espaçamento interno
    bg_color: Cor do fundo estilo pergaminho (R, G, B, Alpha)
    text_color: Cor do texto marrom escuro
    border_color: Cor da borda marrom
    
    Retorna:
    int: Índice da opção selecionada (0-based)
    """
    
    hover_text_color = (131, 97, 63)  # Cor mais clara para hover
    highlight_color = (235, 224, 203, 128)  # Cor de destaque semitransparente
    
    # Divide o texto principal em linhas que cabem na largura máxima
    words = main_text.split(' ')
    main_lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.render(test_line, True, text_color).get_rect()
        
        if bbox.width <= max_width:
            current_line.append(word)
        else:
            main_lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        main_lines.append(' '.join(current_line))
    
    # Calcula larguras das opções
    option_lines = options
    option_widths = [font.render(opt, True, text_color).get_rect().width for opt in option_lines]
    
    # Encontra a largura máxima baseada em texto principal e opções
    max_line_width = 0
    for line in main_lines:
        line_width = font.render(line, True, text_color).get_rect().width
        max_line_width = max(max_line_width, line_width)
    max_line_width = max_width
    
    total_width = max_line_width + padding * 2
    
    # Calcula altura
    line_height = font.get_linesize()
    num_lines = len(main_lines) + len(option_lines)
    extra_space = line_height  # Espaço extra entre texto principal e opções
    total_height = num_lines * line_height + extra_space + padding * 2
    
    # Centraliza o modal na tela
    screen_width, screen_height = screen.get_size()
    pos_x = (screen_width - total_width) // 2
    pos_y = (screen_height - total_height) // 2
    
    # Função para desenhar o modal com hover
    def draw_modal(hovered=None):
        modal_surface = pygame.Surface((total_width, total_height), pygame.SRCALPHA)
        
        # CORES PARA EFEITO DE PAPEL ENVELHECIDO
        parchment_dark = (194, 178, 152, 255)   # Tom mais escuro para sombras
        parchment_light = (235, 224, 203, 255)  # Tom mais claro para realces
        
        # Desenha o fundo principal estilo pergaminho
        pygame.draw.rect(modal_surface, bg_color, 
                         (0, 0, total_width, total_height), 
                         border_radius=8)
        
        # Adiciona textura de papel
        for i in range(0, total_width, 3):
            for j in range(0, total_height, 3):
                if (i + j) % 6 == 0:
                    alpha_var = randint(5, 15)
                    texture_color = (bg_color[0] - 10, bg_color[1] - 10, bg_color[2] - 10, alpha_var)
                    pygame.draw.rect(modal_surface, texture_color, (i, j, 2, 2))
        
        # Borda estilo papel antigo
        pygame.draw.rect(modal_surface, (120, 90, 60),
                         (0, 0, total_width, total_height),
                         width=3, border_radius=10)
        
        pygame.draw.rect(modal_surface, border_color,
                         (2, 2, total_width-4, total_height-4),
                         width=2, border_radius=8)
        
        pygame.draw.rect(modal_surface, parchment_light,
                         (4, 4, total_width-8, total_height-8),
                         width=1, border_radius=6)
        
        # Desenha o texto principal
        text_y = padding
        for line in main_lines:
            text_surface = font.render(line, True, text_color)
            text_x = (total_width - text_surface.get_width()) // 2
            modal_surface.blit(text_surface, (text_x, text_y))
            text_y += line_height
        
        # Espaço extra antes das opções
        text_y += extra_space
        
        # Desenha as opções e armazena retângulos (relativos à modal_surface)
        option_rects.clear()
        for idx, opt in enumerate(option_lines):
            current_color = hover_text_color if idx == hovered else text_color
            opt_surface = font.render(opt, True, current_color)
            opt_x = (total_width - opt_surface.get_width()) // 2
            opt_rect = pygame.Rect(opt_x - 5, text_y - 2, opt_surface.get_width() + 10, line_height + 4)
            
            if idx == hovered:
                # Destaque de fundo
                pygame.draw.rect(modal_surface, highlight_color, opt_rect, border_radius=5)
            
            modal_surface.blit(opt_surface, (opt_x, text_y))
            option_rects.append(opt_rect)
            text_y += line_height
        
        # Detalhes decorativos nos cantos
        corner_size = 8
        pygame.draw.line(modal_surface, border_color, (10, 5), (corner_size, 5), 2)
        pygame.draw.line(modal_surface, border_color, (5, 10), (5, corner_size), 2)
        pygame.draw.line(modal_surface, border_color, (total_width-10, 5), (total_width-corner_size, 5), 2)
        pygame.draw.line(modal_surface, border_color, (total_width-5, 10), (total_width-5, corner_size), 2)
        pygame.draw.line(modal_surface, border_color, (10, total_height-5), (corner_size, total_height-5), 2)
        pygame.draw.line(modal_surface, border_color, (5, total_height-10), (5, total_height-corner_size), 2)
        pygame.draw.line(modal_surface, border_color, (total_width-10, total_height-5), (total_width-corner_size, total_height-5), 2)
        pygame.draw.line(modal_surface, border_color, (total_width-5, total_height-10), (total_width-5, total_height-corner_size), 2)
        
        # Blita na tela
        screen.blit(modal_surface, (pos_x, pos_y))
        pygame.display.flip()
    
    # Lista para retângulos das opções
    option_rects = []
    
    # Desenho inicial sem hover
    draw_modal(None)
    
    # Ajusta retângulos para coordenadas da tela
    def get_screen_option_rects():
        return [rect.move(pos_x, pos_y) for rect in option_rects]
    
    hovered = None
    clock = pygame.time.Clock()
    
    if chat_end == True:
        return
    # Loop bloqueante
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                screen_rects = get_screen_option_rects()
                for i, rect in enumerate(screen_rects):
                    if rect.collidepoint(mouse_pos):
                        return i
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
                screen_rects = get_screen_option_rects()
                new_hovered = None
                for i, rect in enumerate(screen_rects):
                    if rect.collidepoint(mouse_pos):
                        new_hovered = i
                        break
                if new_hovered != hovered:
                    hovered = new_hovered
                    draw_modal(hovered)

def show_modal(screen, font, main_text, options, max_width=500, padding=30, chat_end=False, name=""):
    """
    Exibe um modal com textos e botões centralizados.
    """

    COLORS = {
        'bg': (238, 221, 185),
        'border': (64, 38, 18),
        'text': (38, 24, 12),
        'text_name': (120, 82, 28),
        'option_bg': (214, 187, 138),
        'option_hover': (198, 163, 96),
        'accent': (191, 144, 0),
        'white': (255, 255, 255)
    }

    def wrap_text(text, width, font):
        # Primeiro, divide o texto pelas quebras de linha manuais (\n)
        paragraphs = text.split('\n')
        all_lines = []
        
        for paragraph in paragraphs:
            # Se o parágrafo estiver vazio (ex: "\n\n"), adiciona uma linha vazia
            if paragraph == "":
                all_lines.append("")
                continue
                
            words = paragraph.split(' ')
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                if font.size(test_line)[0] <= width:
                    current_line.append(word)
                else:
                    all_lines.append(' '.join(current_line))
                    current_line = [word]
            
            # Adiciona a última linha do parágrafo processado
            all_lines.append(' '.join(current_line))
            
        return all_lines

    # --- CÁLCULOS DE DIMENSÃO ---
    usable_width = max_width - (padding * 2)
    main_lines = []
    if name:
        main_lines.append(f"{name}: \n")
    main_lines += wrap_text(main_text, usable_width, font)
    
    # Encontra a largura da maior linha ou opção para definir o tamanho do modal
    max_content_width = 0
    for line in main_lines:
        max_content_width = max(max_content_width, font.size(line)[0])
    for opt in options:
        max_content_width = max(max_content_width, font.size(opt)[0])
    
    total_width = max_content_width + (padding * 2)
    line_height = font.get_linesize()
    total_height = (len(main_lines) * line_height) + (len(options) * (line_height + 15)) + (padding * 2) + 20
    
    modal_rect = pygame.Rect(0, 0, total_width, total_height)
    modal_rect.center = screen.get_rect().center
    
    def draw_ui(hovered_idx=None):
        # Fundo do Modal
        bg_surf = pygame.Surface((total_width, total_height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, COLORS['bg'], (0, 0, total_width, total_height), border_radius=12)
        pygame.draw.rect(bg_surf, COLORS['border'], (0, 0, total_width, total_height), width=2, border_radius=12)
        
        # 1. Desenha Texto Principal CENTRALIZADO
        y_offset = padding


        for index, line in enumerate(main_lines):
            if name and index == 0: 
                text_surf = font.render(line, True, COLORS['text_name'])
                text_x = (total_width - text_surf.get_width()) // 2
                bg_surf.blit(text_surf, (10, 12))
                y_offset += line_height
            else:
                text_surf = font.render(line, True, COLORS['text'])
                
                # Cálculo do X centralizado: (Largura Total - Largura da Linha) / 2
                text_x = (total_width - text_surf.get_width()) // 2
                bg_surf.blit(text_surf, (text_x, y_offset))
                y_offset += line_height
        
        y_offset += 20 
        
        # 2. Desenha Opções CENTRALIZADAS
        option_rects = []
        for i, opt in enumerate(options):
            is_hovered = (i == hovered_idx)
            color = COLORS['accent'] if is_hovered else COLORS['option_bg']
            
            # Ajustamos a largura do botão para o conteúdo ou para o máximo disponível
            opt_text_surf = font.render(opt, True, COLORS['white'] if is_hovered else COLORS['text'])
            
            # Definimos o retângulo do botão (um pouco maior que o texto)
            button_w = max_content_width 
            button_h = line_height + 10
            button_x = (total_width - button_w) // 2
            
            opt_box = pygame.Rect(button_x, y_offset, button_w, button_h)
            pygame.draw.rect(bg_surf, color, opt_box, border_radius=6)
            
            # Texto centralizado dentro do botão
            text_pos = (opt_box.centerx - opt_text_surf.get_width() // 2, 
                        opt_box.centery - opt_text_surf.get_height() // 2)
            bg_surf.blit(opt_text_surf, text_pos)
            
            # Guardar o rect global para colisão
            global_rect = opt_box.move(modal_rect.topleft)
            option_rects.append(global_rect)
            
            y_offset += line_height + 15
 
        screen.blit(bg_surf, modal_rect.topleft)
        return option_rects

    # --- LOOP DE EVENTOS (Igual ao anterior) ---
    clock = pygame.time.Clock()
    hovered_idx = None

    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen_option_rects = draw_ui(hovered_idx)
        pygame.display.flip()

        if chat_end: return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.MOUSEMOTION:
                hovered_idx = None
                for i, rect in enumerate(screen_option_rects):
                    if rect.collidepoint(mouse_pos):
                        hovered_idx = i
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(screen_option_rects):
                    if rect.collidepoint(mouse_pos):
                        return i
        clock.tick(60)


# === Helpers geométricos ============================================
def angle_of(vec: pygame.Vector2) -> float:
    # pygame usa x para direita e y para baixo; atan2 já lida bem.
    return degrees(atan2(vec.y, vec.x))

def dir_from_angle(angle_deg: float) -> pygame.Vector2:
    rad = radians(angle_deg)
    return pygame.Vector2(cos(rad), sin(rad))

def load_with_alpha(path, alpha_factor=1.0):
    img = Image.open(path).convert("RGBA")
    r, g, b, a = img.split()
    a = a.point(lambda p: int(p * alpha_factor))
    img = Image.merge("RGBA", (r, g, b, a))
    return pygame.image.frombytes(img.tobytes(), img.size, img.mode)

def load_snow_images(folder):
    images = []
    for name in listdir(folder):
        if name.lower().endswith((".png", ".gif")):
            img = pygame.image.load(join(folder, name)).convert_alpha()
            images.append(img)
    return images

def create_light_sprite(radius: int) -> pygame.Surface:
    """Gera UMA imagem de luz radial com alpha, pra ser reutilizada."""
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    for y in range(size):
        for x in range(size):
            dx = x - radius
            dy = y - radius
            dist = hypot(dx, dy)

            if dist >= radius:
                continue

            # 0 no centro → 1 na borda
            d = dist / radius

            # t = 1 no centro, 0 na borda
            t = 1.0 - d

            # curva suave (t^2)
            alpha = int(255 * (t * t))

            # preto com alpha (vamos SUBTRAIR isso da escuridão)
            surf.set_at((x, y), (0, 0, 0, alpha))

    return surf

def desenhar_matriz_mapa(surface, matriz, tilesize, offset):
    
    for y, linha in enumerate(matriz):
        for x, valor in enumerate(linha):

            if valor == 1:
                cor = (255, 0, 0) 

                # borda fina para visualizar melhor
                pygame.draw.rect(
                    surface,
                    cor,
                    (x * tilesize+ offset.x, y * tilesize+offset.y, tilesize, tilesize),
                    1  # espessura (1 pixel)
                )

def gerar_matriz_mapa(largura_mapa: int, altura_mapa: int, tilesize: int, grupo_de_obstaculos: pygame.sprite.Group) -> list[list[int]]:
    """
    Gera uma matriz 2D (lista de listas) representando o mapa do jogo.

    Args:
        largura_mapa (int): Largura total do mapa em pixels.
        altura_mapa (int): Altura total do mapa em pixels.
        tilesize (int): O tamanho de cada célula do grid em pixels (ex: 32).
        grupo_de_obstaculos (pygame.sprite.Group): Um grupo de sprites contendo todos os
                                                   objetos fixos/paredes.

    Returns:
        list[list[int]]: Uma matriz onde 1 representa um obstáculo e 0 um espaço livre.
    """
    # Calcula as dimensões da matriz com base no tamanho do mapa e do tile
    grid_largura = largura_mapa // tilesize
    grid_altura = altura_mapa // tilesize
    

    # 1. Inicializa a matriz com zeros (espaços livres)
    # Usamos list comprehension para criar uma matriz 2D de forma eficiente
    matriz = [[0 for _ in range(grid_largura)] for _ in range(grid_altura)]

    # 2. Itera sobre cada célula da matriz para verificar se há obstáculos
    for y in range(grid_altura):
        for x in range(grid_largura):
            # Cria um retângulo temporário para representar a célula atual do grid
            celula_rect = pygame.Rect(x * tilesize, y * tilesize, tilesize, tilesize)
            
            # 3. Verifica se este retângulo colide com QUALQUER obstáculo no grupo
            for obstaculo in grupo_de_obstaculos:
                # Usamos colliderect para uma verificação rápida de colisão entre retângulos
                if celula_rect.colliderect(obstaculo.hitbox):
                    # Se houver colisão, marca a célula como 1 (obstáculo)
                    matriz[y][x] = 1
                    # Uma vez que encontramos uma colisão para esta célula,
                    # não precisamos verificar outros obstáculos nela.
                    break 
                    
    return matriz

def criar_surface_debug_matriz(matriz: list[list[int]], tilesize: int, 
                              cor_obstaculo=(255, 0, 0, 100),   # Vermelho semi-transparente
                              cor_caminho=(0, 0, 255, 100),   # Azul semi-transparente
                              cor_fundo=(0, 0, 0, 0),
                              caminho = [],
                              finais=[]
                              ) -> pygame.Surface:     # Transparente
    """
    Cria uma Surface única com o grid de colisão já desenhado.
    Pode ser blitada diretamente na tela para debug.
    """
    

    altura = len(matriz)
    largura = len(matriz[0]) if altura > 0 else 0
    
    # Cria uma surface com fundo transparente
    surface = pygame.Surface((largura * tilesize, altura * tilesize), pygame.SRCALPHA)
    surface.fill(cor_fundo)  # Fundo transparente

        
    # Desenha apenas as células que são obstáculo
    for y in range(altura):
        for x in range(largura):
            
            if (x,y) in finais and matriz[y][x] == 1:
                
                rect = pygame.Rect(x * tilesize, y * tilesize, tilesize, tilesize)
                pygame.draw.rect(surface, (0,255,255), rect)
            if (x,y) in finais:
                rect = pygame.Rect(x * tilesize, y * tilesize, tilesize, tilesize)
                pygame.draw.rect(surface, (0,255,0), rect)
            elif (x,y) in caminho and matriz[y][x] == 1:
                rect = pygame.Rect(x * tilesize, y * tilesize, tilesize, tilesize)
                pygame.draw.rect(surface, (255,255,255), rect)
            elif (x,y) in caminho:
                rect = pygame.Rect(x * tilesize, y * tilesize, tilesize, tilesize)
                pygame.draw.rect(surface, cor_caminho, rect)
            elif matriz[y][x] == 1:
                rect = pygame.Rect(x * tilesize, y * tilesize, tilesize, tilesize)
                pygame.draw.rect(surface, cor_obstaculo, rect)
            
    
    # Opcional: desenhar a grade (linhas finas) para ver melhor os tiles
    cor_grid = (50, 50, 50, 80)  # Cinza bem claro e transparente
    for x in range(largura + 1):
        pygame.draw.line(surface, cor_grid, (x * tilesize, 0), (x * tilesize, altura * tilesize))
    for y in range(altura + 1):
        pygame.draw.line(surface, cor_grid, (0, y * tilesize), (largura * tilesize, y * tilesize))

    return surface

def imprimir_matriz(matriz: list[list[int]]):
    """Função auxiliar para visualizar a matriz gerada no console."""
    for linha in matriz:
        # Converte cada número em string e junta com um espaço
        print(" ".join(map(str, linha)))

def pixel_para_grid_corrigido(pos_pixel: tuple[int, int], tilesize: int) -> tuple[int, int]:
    """
    Converte coordenadas de pixel (x, y) para coordenadas de grid (linha, coluna).
    """
    coluna = pos_pixel[0] // tilesize
    linha = pos_pixel[1] // tilesize
    
    # A função de busca espera (linha, coluna)
    return (linha, coluna)

def calcula_rota_correta(grid, start, goal):
    rota = calcula_rota(grid, start, goal)
    if rota:
        return [(r[1]*GRID_SIZE, r[0]*GRID_SIZE) for r in rota]
    
    return []

def calcula_rota(grid, start, goal):
    start = pixel_para_grid_corrigido(start, GRID_SIZE)
    goal = pixel_para_grid_corrigido(goal, GRID_SIZE)
    rows, cols = len(grid), len(grid[0])
    queue = deque([start])
    visited = set([start])
    parent = {start: None}

    # direções (4-way). Mantive como antes.
    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    # --- Novo: marca temporariamente goal e vizinhança imediata como livre ---
    temporarily_free = set()
    radius = 1  # raio em células; ajuste se quiser maior
    gr, gc = int(goal[0]), int(goal[1])
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            nr, nc = gr + dr, gc + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                temporarily_free.add((nr, nc))
    # -----------------------------------------------------------------------

    while queue:
        current = queue.popleft()
        if current == goal:
            # Reconstrói caminho de forma segura
            path = []
            node = current
            while node is not None:
                path.append(node)
                node = parent[node]
            return path[::-1]  # do início ao fim

        r, c = current
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            neigh = (nr, nc)
            if 0 <= nr < rows and 0 <= nc < cols:
                # permite se a célula for 0 no grid OU estiver marcada como temporariamente livre
                is_free = (grid[int(nr)][int(nc)] == 0)
                if is_free and neigh not in visited:
                    visited.add(neigh)
                    parent[neigh] = current
                    queue.append(neigh)

    return None

def calcula_rota_manhattan(grid, start, goal):
    start = pixel_para_grid_corrigido(start, GRID_SIZE)
    goal = pixel_para_grid_corrigido(goal, GRID_SIZE)
    rows, cols = len(grid), len(grid[0])
    queue = deque([start])
    visited = set([start])
    parent = {start: None}

    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    # inicializa melhor nó alcançável como o próprio start
    def manhattan(a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])

    best_node = start
    best_dist = manhattan(start, goal)

    # se start é já o objetivo
    if start == goal:
        return [start]

    while queue:
        current = queue.popleft()

        # atualiza melhor nó alcançado
        d = manhattan(current, goal)
        if d < best_dist:
            best_dist = d
            best_node = current

        if current == goal:
            # Reconstrói caminho de forma segura
            path = []
            node = current
            while node is not None:
                path.append(node)
                node = parent[node]
            return path[::-1]  # do início ao fim

        r, c = current
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            neigh = (nr, nc)
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[int(nr)][int(nc)] == 0 and neigh not in visited:
                    visited.add(neigh)
                    parent[neigh] = current
                    queue.append(neigh)

    # se chegou aqui, não encontrou goal — tenta reconstruir até best_node (o mais próximo alcançado)
    if best_node is not None and best_node in parent:
        path = []
        node = best_node
        while node is not None:
            path.append(node)
            node = parent[node]
        return path[::-1]

    # nenhum nó alcançável (situação rara)
    return None


def draw_health_bar(
    surf, x, y, height,
    current, maximum,
    segment_hp=10,
    segment_width=20,
    gap=3,
    border_color=(30,30,30),
    bg_color=(41,41,41),
    health_color=(78,200,120),
    empty_color=(60,60,60),
    border_radius=None,
    show_border=True
):
    """
    Desenha uma barra de vida segmentada, com largura adaptável baseada na vida máxima.
    - surf: surface do pygame
    - x,y,height: posição e altura da barra (largura é calculada automaticamente)
    - current, maximum: vida atual e máxima
    - segment_hp: quantidade de HP por segmento (default 10)
    - segment_width: largura em pixels por segmento (default 20)
    - gap: espaçamento (px) entre segmentos
    - colors: cores configuráveis
    - border_radius: radius dos cantos (se None, fica height//2)
    """

    if maximum <= 0:
        return

    # Calcular número de segmentos baseado na vida máxima
    segments = ceil(maximum / segment_hp)
    if segments < 1:
        segments = 1

    # Calcular largura total da barra
    total_gaps = gap * (segments - 1)
    width = segments * segment_width + total_gaps

    x = x-width//2
    # radius padrão (meio da altura para ficar "pill")
    if border_radius is None:
        border_radius = height // 2

    # retângulo de fundo e borda
    outer_rect = pygame.Rect(x-1, y-1, width+2, height+2)
    if show_border:
        pygame.draw.rect(surf, border_color, outer_rect, border_radius=border_radius)

    inner_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surf, bg_color, inner_rect, border_radius=border_radius)

    # se a largura é pequena demais, desenha barra simples
    if width <= total_gaps:
        filled_ratio = max(0.0, min(1.0, current / maximum))
        filled_w = int(width * filled_ratio)
        if filled_w > 0:
            pygame.draw.rect(surf, health_color, (x, y, filled_w, height), border_radius=border_radius)
        return

    # largura de cada segmento (fixa, baseada no param)
    seg_w = segment_width
    health_ratio = max(0.0, min(1.0, current / maximum))
    total_segments_filled = health_ratio * segments  # pode ser fracionário

    # desenhar cada segmento (fundo escuro + preenchimento parcial/total)
    for i in range(segments):
        seg_x = x + i * (seg_w + gap)
        seg_rect = pygame.Rect(int(seg_x), y, int(seg_w), int(height))

        # desenha "vácuo" do segmento (empty)
        pygame.draw.rect(surf, empty_color, seg_rect, border_radius=border_radius//2)

        # calcular quanto deste segmento deve ser preenchido (0..1)
        fill_amount = max(0.0, min(1.0, total_segments_filled - i))
        if fill_amount > 0:
            fill_w = int(seg_rect.width * fill_amount)
            fill_rect = pygame.Rect(seg_rect.x, seg_rect.y, fill_w, seg_rect.height)

            # desenhar preenchimento com cantos arredondados somente se for segmento inteiro
            if fill_amount >= 0.995:
                pygame.draw.rect(surf, health_color, seg_rect, border_radius=seg_rect.height//2)
            else:
                pygame.draw.rect(surf, health_color, fill_rect)

            # brilho sutil no topo para dar profundidade (linha fina)
            highlight_h = max(1, seg_rect.height // 6)
            highlight_rect = pygame.Rect(fill_rect.x, fill_rect.y, fill_rect.width, highlight_h)
            # cor do highlight: um pouco mais clara que health_color
            hc = health_color
            hl = (min(255, int(hc[0] + 30)), min(255, int(hc[1] + 30)), min(255, int(hc[2] + 30)))
            pygame.draw.rect(surf, hl, highlight_rect, border_radius=0)

    # separadores finos (opcionalmente desenhar linhas sutis entre segmentos)
    sep_color = (20, 20, 20)  # quase preto (contraste sutil)
    for i in range(1, segments):
        line_x = int(x + i * seg_w + (i - 0.5) * gap)
        pygame.draw.line(surf, sep_color, (line_x, y + 3), (line_x, y + height - 3), 1)

    # opcional: pequeno "sombreamento" interno inferior para dar profundidade
    shadow_h = max(1, height // 8)
    shadow_rect = pygame.Rect(x, y + height - shadow_h, width, shadow_h)
    shadow_color = (0, 0, 0)
    s = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
    s.fill((*shadow_color, 40))  # alpha leve
    surf.blit(s, (shadow_rect.x, shadow_rect.y))

def draw_thirst_bar(
    surf, x, y, width, height,
    empty_color=(0,0,200),
):
    """
    Desenha uma barra de vida segmentada.
    - surf: surface do pygame
    - x,y,width,height: posição e tamanho total da barra
    - current, maximum: vida atual e máxima
    - segments: número de subdivisões (inteiro >=1)
    - gap: espaçamento (px) entre segmentos
    - colors: cores configuráveis
    - border_radius: radius dos cantos (se None, fica height//2)
    """
    seg_rect = pygame.Rect(x,y, width, height)
    pygame.draw.rect(surf, empty_color, seg_rect, border_radius=12)
    
def desenhar_menu_transformacoes(
    screen: pygame.Surface,
    sprites: list[pygame.Surface],
    mouse_pos: tuple[int, int],
    mouse_click: bool,
    estado_info: dict,
    player
):
    """
    Desenha o menu de personagens transformáveis no canto direito.

    estado_info deve ser um dict mutável:
    {"aberto": False}
    """

    largura_tela, altura_tela = screen.get_size()
    raio = 24
    margem = 16
    espacamento = 60

    # ---------- Botão de informação ----------
    botao_info = pygame.Rect(largura_tela - 60, 20, 40, 40)

    pygame.draw.circle(screen, (40, 120, 255), botao_info.center, 20)
    pygame.draw.circle(screen, (255, 255, 255), botao_info.center, 20, 2)

    fonte = pygame.font.SysFont(None, 26)
    texto_i = fonte.render("i", True, (255, 255, 255))
    screen.blit(texto_i, texto_i.get_rect(center=botao_info.center))

    if botao_info.collidepoint(mouse_pos):
        estado_info["aberto"] = True
    else:
        estado_info["aberto"] = False

    # ---------- Aba de informações ----------
    if estado_info["aberto"]:
        painel = pygame.Rect(largura_tela - 380, 80, 300, 160)
        pygame.draw.rect(screen, (20, 20, 30), painel, border_radius=12)
        pygame.draw.rect(screen, (80, 160, 255), painel, 2, border_radius=12)

        linhas = [
            "Transformações disponíveis",
            "",
            "- Digite 1 a 8 para trasformar-se",
            "- Cada forma tem habilidades",
            "- Use com estratégia"
        ]

        for i, linha in enumerate(linhas):
            txt = fonte.render(linha, True, (220, 220, 220))
            screen.blit(txt, (painel.x + 16, painel.y + 16 + i * 26))

    # ---------- Lista de personagens ----------
    x = largura_tela - raio - margem
    y_inicial = 150

    for i, sprite in enumerate(sprites):
        y = y_inicial + i * espacamento
        centro = (x, y)

        # Glow
        pygame.draw.circle(screen, (80, 160, 255), centro, raio + 4)
        pygame.draw.circle(screen, (20, 20, 20), centro, raio)

        # Máscara circular
        sprite_redimensionado = pygame.transform.smoothscale(sprite.frames["Idle"]["Front"][int(player.frame_index) % len(sprite.frames["Idle"]["Front"])], (raio * 2, raio * 2))
        mask_surface = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)

        pygame.draw.circle(mask_surface, (255, 255, 255), (raio, raio), raio)
        mask_surface.blit(sprite_redimensionado, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        screen.blit(mask_surface, (x - raio, y - raio))


def play_noise(char, noise_options: list, cooldown=300, volume=None):
    if not noise_options:
        return

    agora = pygame.time.get_ticks()

    if not hasattr(char, "ultimo_som"):
        char.ultimo_som = 0

    if agora - char.ultimo_som < cooldown:
        return

    char.ultimo_som = agora

    distancia = (char.position_vector - char.player_sprite.position_vector).length()
    DISTANCIA_MAX = WINDOW_HEIGHT

    if distancia >= DISTANCIA_MAX:
        return

    if not volume:
        volume = 1 - (distancia / DISTANCIA_MAX)
        volume = max(0.0, min(1.0, volume))
        volume = volume/4

    dx = char.position_vector.x - char.player_sprite.position_vector.x
    pan = max(-1, min(1, dx / DISTANCIA_MAX))

    left = volume * (1 - max(0, pan))
    right = volume * (1 + min(0, pan))

    canal = pygame.mixer.find_channel()
    if not canal:
        return

    som = choice(noise_options)
    canal.set_volume(left, right)
    canal.play(som)

def som_loop():
    som = pygame.mixer.Sound("Sounds/loop_concluded.mp3")
    canal = pygame.mixer.find_channel()
    if not canal:
        return
    canal.set_volume(22, 22)
    canal.play(som)

def embaralha_palavras(txt:str) -> str:
    resultado = []

    for char in txt:
        if 'a' <= char <= 'z':
            # se for 'z', volta para 'a'
            resultado.append('a' if char == 'z' else chr(ord(char) + 1))
        elif 'A' <= char <= 'Z':
            # se for 'Z', volta para 'A'
            resultado.append('A' if char == 'Z' else chr(ord(char) + 1))
        else:
            # números, pontos e qualquer outro caractere ficam iguais
            resultado.append(char)

    return ''.join(resultado)

