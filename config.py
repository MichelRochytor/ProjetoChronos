"""
LOTECA ANALYTICS PRO — Configurações, Temas e Paleta Visual
Dark Theme Analytics (Moderno e Elegante)
"""

import os
import glob

# ============================================================================
# CONFIGURAÇÃO DE CAMINHOS E DIRETÓRIOS
# ============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _caminho(relativo: str) -> str:
    """
    Localiza caminhos relativos ao projeto de forma inteligente,
    garantindo que funcione independente de onde o script foi invocado.
    """
    candidatos = [
        os.path.join(BASE_DIR, relativo),
        os.path.join(BASE_DIR, '..', relativo),
        os.path.join(os.getcwd(), relativo),
    ]
    if relativo.startswith('dados/') and os.path.basename(BASE_DIR) == 'dados':
        candidatos.append(os.path.join(BASE_DIR, relativo[len('dados/'):]))

    for p in candidatos:
        if os.path.exists(p) or glob.glob(p):
            return p

    return candidatos[0]


# ============================================================================
# PALETA DE CORES — DARK THEME ANALYTICS
# ============================================================================

THEME = {
    'bg_main':       '#080c14',  # Fundo principal escuro cinematográfico
    'bg_header':     '#0d1424',  # Topo / Header
    'bg_card':       '#121929',  # Cartões e painéis com elevação
    'bg_card_alt':   '#162035',  # Linhas alternadas / hover
    'bg_subtle':     '#1a263d',  # Contêineres sutis
    'border':        '#223049',  # Bordas
    'border_light':  '#2d3f60',  # Bordas em foco
    'text_primary':  '#f8fafc',  # Branco brilhante
    'text_secondary':'#94a3b8',  # Cinza suave
    'text_muted':    '#64748b',  # Cinza escuro discreto
    
    # Cores de Ação e Status
    'accent_blue':   '#38bdf8',  # Azul Sky
    'accent_indigo': '#6366f1',  # Índigo moderno
    'accent_purple': '#a855f7',  # Púrpura vivo
    'accent_amber':  '#f59e0b',  # Âmbar destaque
    'win':           '#10b981',  # Verde vitória (Emerald)
    'draw':          '#f59e0b',  # Laranja/âmbar empate
    'loss':          '#f43f5e',  # Vermelho derrota (Rose)
    
    # Cores de Competições
    'comp_serie_a':  '#3b82f6',  # Azul
    'comp_serie_b':  '#8b5cf6',  # Roxo
    'comp_cdb':      '#10b981',  # Verde / Ouro
    'comp_lib':      '#fbbf24',  # Dourado Glória Eterna
    'comp_sud':      '#06b6d4',  # Ciano elétrico
    'comp_estadual': '#14b8a6',  # Teal / Verde Água para Estaduais
    'comp_todas':    '#ec4899',  # Rosa
    
    # Tags e Alertas
    'tag_cup_alert': '#f97316',  # Laranja fogo (alerta de copa próxima)
    'tag_rest_warn': '#e11d48',  # Vermelho desgaste
}

FONTS = {
    'title':    ('Segoe UI', 15, 'bold'),
    'subtitle': ('Segoe UI', 9),
    'header':   ('Segoe UI', 11, 'bold'),
    'card_kpi': ('Segoe UI', 16, 'bold'),
    'card_lbl': ('Segoe UI', 8, 'bold'),
    'body':     ('Segoe UI', 10),
    'body_b':   ('Segoe UI', 10, 'bold'),
    'mono':     ('Courier New', 9),
    'mono_b':   ('Courier New', 9, 'bold'),
    'badge':    ('Segoe UI', 8, 'bold'),
    'score':    ('Segoe UI', 22, 'bold'),
}

COMPETICOES = [
    'Brasileirão Série A',
    'Brasileirão Série B',
    'Brasileirão Série C',
    'Brasileirão Série D',
    'Copa do Brasil',
    'Libertadores',
    'Sudamericana',
    'UEFA Champions League',
    'UEFA Europa League',
    'Premier League',
    'La Liga',
    'Italiano',
    'Campeonato Paulista',
    'Campeonato Carioca',
    'Campeonato Mineiro',
    'Campeonato Gaúcho',
    'Campeonato Goiano',
    'Campeonato Baiano',
    'Campeonato Pernambucano',
    'Campeonato Capixaba',
    'Campeonato Paranaense',
    'Campeonato Catarinense',
    'Campeonato Cearense',
    'Copa do Nordeste',
    'Copa Verde',
    'Estaduais (Todos)',
    'Todas as Competições',
]

CORES_COMPETICAO = {
    'Copa do Brasil':          THEME['comp_cdb'],
    'Libertadores':            THEME['comp_lib'],
    'Sudamericana':            THEME['comp_sud'],
    'UEFA Champions League':   THEME['accent_indigo'],
    'UEFA Europa League':      THEME['accent_blue'],
    'Premier League':          THEME['accent_purple'],
    'La Liga':                 THEME['tag_cup_alert'],
    'Italiano':                 THEME['accent_purple'],
    'Copa do Nordeste':        THEME['comp_cdb'],
    'Copa Verde':              THEME['comp_estadual'],
    'Brasileirão Série A':     THEME['comp_serie_a'],
    'Brasileirão Série B':     THEME['comp_serie_b'],
    'Brasileirão Série C':     '#0284c7',
    'Brasileirão Série D':     '#0369a1',
    'Campeonato Paulista':     THEME['comp_estadual'],
    'Campeonato Carioca':      THEME['comp_estadual'],
    'Campeonato Mineiro':      THEME['comp_estadual'],
    'Campeonato Gaúcho':       THEME['comp_estadual'],
    'Campeonato Goiano':       THEME['comp_estadual'],
    'Campeonato Baiano':       THEME['comp_estadual'],
    'Campeonato Pernambucano': THEME['comp_estadual'],
    'Campeonato Capixaba':     THEME['comp_estadual'],
    'Campeonato Paranaense':   THEME['comp_estadual'],
    'Campeonato Catarinense':  THEME['comp_estadual'],
    'Campeonato Cearense':     THEME['comp_estadual'],
    'Estaduais (Todos)':       THEME['comp_estadual'],
    'Todas as Competições':    THEME['comp_todas'],
}

ABREV_COMPETICAO = {
    'Brasileirão Série A':     'SÉRIE A',
    'Brasileirão Série B':     'SÉRIE B',
    'Brasileirão Série C':     'SÉRIE C',
    'Brasileirão Série D':     'SÉRIE D',
    'Copa do Brasil':          'C.BRASIL',
    'Libertadores':            'LIBERTAD',
    'Sudamericana':            'SUDAMER',
    'UEFA Champions League':   'CHAMPIONS',
    'UEFA Europa League':      'EUROPA LEAGUE',
    'Premier League':          'PREMIER',
    'La Liga':                 'LA LIGA',
    'Italiano':                 'ITALIANO',
    'Copa do Nordeste':        'C.NORDESTE',
    'Copa Verde':              'C.VERDE',
    'Campeonato Paulista':     'PAULISTÃO',
    'Campeonato Carioca':      'CARIOCÃO',
    'Campeonato Mineiro':      'MINEIRO',
    'Campeonato Gaúcho':       'GAÚCHO',
    'Campeonato Goiano':       'GOIANO',
    'Campeonato Baiano':       'BAIANO',
    'Campeonato Pernambucano': 'PERNAMBUC',
    'Campeonato Capixaba':     'CAPIXABA',
    'Campeonato Paranaense':   'PARANAENSE',
    'Campeonato Catarinense':  'CATARINENSE',
    'Campeonato Cearense':     'CEARENSE',
    'Estaduais (Todos)':       'ESTADUAL',
}

