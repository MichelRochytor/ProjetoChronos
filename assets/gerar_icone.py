"""
Script de geração de ícone de alta fidelidade para o Projeto Chronos.
Gera ícone moderno no formato Squircle / Cyber-Dark com bola de futebol tecnológica,
anel de energia neon e raio Chronos ⚡.
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter


def gerar_icone_chronos(caminho_saida: str, tamanho: int = 512):
    # Renderizar em 4x (2048x2048) para supersampling perfeito
    S = 2048
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = S // 2, S // 2
    r_squircle = 880  # Raio base da caixa arredondada
    corner_radius = 420

    # 1. Base Squircle com cantos arredondados (estilo moderno GNOME/macOS)
    x0, y0 = cx - r_squircle, cy - r_squircle
    x1, y1 = cx + r_squircle, cy + r_squircle

    # Fundo degradê escuro
    base_bg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    base_draw = ImageDraw.Draw(base_bg)
    base_draw.rounded_rectangle([x0, y0, x1, y1], radius=corner_radius, fill=(10, 15, 28, 255))

    # Gradiente vertical no fundo
    for y in range(y0, y1):
        t = (y - y0) / (y1 - y0)
        # Transição de #0d1527 para #050811
        r = int(14 * (1 - t) + 6 * t)
        g = int(22 * (1 - t) + 10 * t)
        b = int(42 * (1 - t) + 20 * t)
        base_draw.line([(x0, y), (x1, y)], fill=(r, g, b, 255))

    # Máscara arredondada para o fundo
    mask_squircle = Image.new("L", (S, S), 0)
    mask_draw = ImageDraw.Draw(mask_squircle)
    mask_draw.rounded_rectangle([x0, y0, x1, y1], radius=corner_radius, fill=255)

    img.paste(base_bg, (0, 0), mask_squircle)

    # 2. Brilho de fundo (Radial Glow ciano/esmeralda no centro)
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for r in range(650, 0, -10):
        alpha = int(45 * (1 - r / 650))
        # Cor de glow esmeralda / ciano (#06b6d4)
        glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(16, 185, 129, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)

    # 3. Anel de Borda Neon do Squircle com gradiente sutil
    borda_img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    borda_draw = ImageDraw.Draw(borda_img)
    borda_draw.rounded_rectangle([x0, y0, x1, y1], radius=corner_radius, outline=(56, 189, 248, 220), width=18)
    borda_draw.rounded_rectangle([x0 + 12, y0 + 12, x1 - 12, y1 - 12], radius=corner_radius - 8, outline=(16, 185, 129, 140), width=8)
    img = Image.alpha_composite(img, borda_img)
    draw = ImageDraw.Draw(img)

    # 4. Anéis Orbitais de Dados / Cronômetro (Representando Chronos e Estatística)
    # Círculo externo tecnológico pontilhado/segmentado
    r_orbit = 680
    draw.ellipse([cx - r_orbit, cy - r_orbit, cx + r_orbit, cy + r_orbit], outline=(34, 48, 73, 180), width=10)

    # Arcos de medição de dados
    draw.arc([cx - r_orbit, cy - r_orbit, cx + r_orbit, cy + r_orbit], start=-45, end=45, fill=(56, 189, 248, 240), width=16)
    draw.arc([cx - r_orbit, cy - r_orbit, cx + r_orbit, cy + r_orbit], start=135, end=225, fill=(16, 185, 129, 240), width=16)

    # Marcadores de horas/dados ao redor do círculo
    for ang in range(0, 360, 30):
        rad = math.radians(ang)
        x_m1 = cx + (r_orbit - 35) * math.cos(rad)
        y_m1 = cy + (r_orbit - 35) * math.sin(rad)
        x_m2 = cx + (r_orbit + 35) * math.cos(rad)
        y_m2 = cy + (r_orbit + 35) * math.sin(rad)
        cor_tick = (56, 189, 248, 200) if ang % 90 == 0 else (100, 116, 139, 130)
        draw.line([(x_m1, y_m1), (x_m2, y_m2)], fill=cor_tick, width=10 if ang % 90 == 0 else 6)

    # 5. Geometria da Bola de Futebol / Conexões Neurais
    # Círculo central da bola
    r_ball = 460
    ball_bg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ball_draw = ImageDraw.Draw(ball_bg)
    ball_draw.ellipse([cx - r_ball, cy - r_ball, cx + r_ball, cy + r_ball], fill=(13, 20, 36, 235), outline=(56, 189, 248, 255), width=16)

    # Pentágono central
    r_pent = 160
    pontos_pentagono = []
    for i in range(5):
        ang_p = math.radians(-90 + i * 72)
        px = cx + r_pent * math.cos(ang_p)
        py = cy + r_pent * math.sin(ang_p)
        pontos_pentagono.append((px, py))

    # Preenchimento do pentágono central com gradiente brilhante ciano/esmeralda
    ball_draw.polygon(pontos_pentagono, fill=(16, 185, 129, 230), outline=(56, 189, 248, 255), width=12)

    # Linhas radiais saindo do pentágono para a borda da bola (gomos da bola)
    r_outer_points = 340
    for i in range(5):
        px, py = pontos_pentagono[i]
        ang_ext = math.radians(-90 + i * 72)
        ex = cx + r_outer_points * math.cos(ang_ext)
        ey = cy + r_outer_points * math.sin(ang_ext)
        ball_draw.line([(px, py), (ex, ey)], fill=(56, 189, 248, 220), width=12)

        # Pequenos nós luminosos nas junções
        r_node = 16
        ball_draw.ellipse([ex - r_node, ey - r_node, ex + r_node, ey + r_node], fill=(255, 255, 255, 255))

        # Conectar com o nó adjacente formando hexágonos
        ang_prox = math.radians(-90 + ((i + 1) % 5) * 72)
        ex_prox = cx + r_outer_points * math.cos(ang_prox)
        ey_prox = cy + r_outer_points * math.sin(ang_prox)
        # Ponto intermediário na borda
        ang_mid = math.radians(-90 + i * 72 + 36)
        bx = cx + r_ball * math.cos(ang_mid)
        by = cy + r_ball * math.sin(ang_mid)
        ball_draw.line([(ex, ey), (bx, by)], fill=(34, 197, 94, 200), width=10)
        ball_draw.line([(bx, by), (ex_prox, ey_prox)], fill=(34, 197, 94, 200), width=10)

    img = Image.alpha_composite(img, ball_bg)

    # 6. Raio Dourado e Brilhante Chronos ⚡ no centro frontal
    raio_img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    raio_draw = ImageDraw.Draw(raio_img)

    # Coordenadas do raio dinâmico ⚡ estilizado
    raio_coords = [
        (cx + 80, cy - 380),   # Topo
        (cx - 140, cy - 40),   # Meio esquerdo recuo
        (cx - 10, cy - 40),    # Meio centro entrada
        (cx - 100, cy + 380),  # Ponta inferior aguda
        (cx + 140, cy + 30),   # Meio direito avanço
        (cx + 10, cy + 30),    # Meio centro volta
    ]

    # Glow do raio
    glow_raio = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    glow_raio_draw = ImageDraw.Draw(glow_raio)
    glow_raio_draw.polygon(raio_coords, fill=(251, 191, 36, 180))
    glow_raio = glow_raio.filter(ImageFilter.GaussianBlur(35))
    img = Image.alpha_composite(img, glow_raio)

    # Raio em si com borda branca e corpo dourado elétrico
    raio_draw.polygon(raio_coords, fill=(252, 211, 77, 255), outline=(255, 255, 255, 255), width=14)
    img = Image.alpha_composite(img, raio_img)

    # 7. Redimensionar com filtro Lanczos para super nitidez
    final_img = img.resize((tamanho, tamanho), Image.Resampling.LANCZOS)
    pasta_destino = os.path.dirname(caminho_saida)
    if pasta_destino:
        os.makedirs(pasta_destino, exist_ok=True)
    final_img.save(caminho_saida, format="PNG")
    print(f"Ícone gerado com sucesso: {caminho_saida} ({tamanho}x{tamanho})")
    return final_img


if __name__ == "__main__":
    caminho = os.path.abspath("assets/icon.png")
    gerar_icone_chronos(caminho, 512)
    # Também gera tamanhos adicionais para a barra de tarefas e sistema
    gerar_icone_chronos("assets/icon_256.png", 256)
    gerar_icone_chronos("assets/icon_128.png", 128)
    gerar_icone_chronos("assets/icon_64.png", 64)
    gerar_icone_chronos("assets/icon_32.png", 32)
    # E instala no cache de ícones do usuário para o GNOME/Zorin
    icon_user = os.path.expanduser("~/.local/share/icons/hicolor/512x512/apps/projeto-chronos.png")
    gerar_icone_chronos(icon_user, 512)
