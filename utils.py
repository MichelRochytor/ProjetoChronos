"""
LOTECA ANALYTICS PRO — Funções Utilitárias e Tratamento de Dados Históricos
Cálculos estatísticos, formatação de fases, parsing de datas e estimativas preditivas.
"""

import re
import unicodedata
from datetime import datetime
import pandas as pd # type: ignore


def normalizar_texto(texto: str) -> str:
    """
    Remove acentos, converte para minúsculas e remove espaços extras
    para permitir buscas flexíveis (ex: 'sao paulo' encontra 'São Paulo').
    """
    if not texto or not isinstance(texto, str):
        return ""
    # Decompõe caracteres acentuados e remove marcas não espaçadas
    nfkd = unicodedata.normalize('NFKD', texto)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.strip().lower()


def extrair_gols(placar) -> tuple[int, int]:
    """
    Extrai com segurança os gols do tempo normal via regex.
    Suporta formatos como '2-1', '2x1', '2 - 1', '1-1 (pen 4-3)', etc.
    """
    try:
        texto = str(placar).strip()
        m = re.search(r'(\d+)\s*[-–xX]\s*(\d+)', texto)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    return 0, 0


ALIASES_CLUBES = {
    # Nacionais - Série A e Tradicionais
    'vasco da gama': 'Vasco', 'vasco': 'Vasco', 'cr vasco da gama': 'Vasco',
    'atletico mineiro': 'Atlético-MG', 'atletico-mg': 'Atlético-MG', 'atletico mg': 'Atlético-MG', 'cam': 'Atlético-MG',
    'athletico paranaense': 'Athletico-PR', 'atletico paranaense': 'Athletico-PR',
    'athletico-pr': 'Athletico-PR', 'atletico-pr': 'Athletico-PR', 'cap': 'Athletico-PR',
    'atletico goianiense': 'Atlético-GO', 'atletico-go': 'Atlético-GO', 'atletico go': 'Atlético-GO', 'acg': 'Atlético-GO',
    'america mineiro': 'América-MG', 'america-mg': 'América-MG', 'america mg': 'América-MG',
    'red bull bragantino': 'Bragantino', 'rb bragantino': 'Bragantino', 'bragantino': 'Bragantino',
    'sport recife': 'Sport', 'sport': 'Sport', 'sport club do recife': 'Sport',
    'botafogo rj': 'Botafogo', 'botafogo-rj': 'Botafogo', 'botafogo': 'Botafogo', 'botafogo fr': 'Botafogo',
    'gremio': 'Grêmio', 'gremio fbpa': 'Grêmio', 'grêmio': 'Grêmio', 'grêmio fbpa': 'Grêmio',
    'sao paulo': 'São Paulo', 'sao paulo fc': 'São Paulo', 'são paulo': 'São Paulo', 'são paulo fc': 'São Paulo',
    'santos': 'Santos', 'santos fc': 'Santos',
    'palmeiras': 'Palmeiras', 'se palmeiras': 'Palmeiras', 'sociedade esportiva palmeiras': 'Palmeiras',
    'corinthians': 'Corinthians', 'sport club corinthians paulista': 'Corinthians', 'sc corinthians': 'Corinthians', 'corinthians paulista': 'Corinthians',
    'flamengo': 'Flamengo', 'cr flamengo': 'Flamengo', 'clube de regatas do flamengo': 'Flamengo',
    'fluminense': 'Fluminense', 'fluminense fc': 'Fluminense',
    'cruzeiro': 'Cruzeiro', 'cruzeiro ec': 'Cruzeiro',
    'internacional': 'Internacional', 'sc internacional': 'Internacional', 'inter': 'Internacional',
    'inter de limeira': 'Inter de Limeira', 'internacional de limeira': 'Inter de Limeira', 'inter limeira': 'Inter de Limeira', 'aa internacional de limeira': 'Inter de Limeira',
    'ceara': 'Ceará', 'ceara sc': 'Ceará', 'ceará': 'Ceará', 'ceará sc': 'Ceará',
    'fortaleza': 'Fortaleza', 'fortaleza ec': 'Fortaleza',
    'bahia': 'Bahia', 'ec bahia': 'Bahia', 'esporte clube bahia': 'Bahia',
    'vitoria': 'Vitória', 'ec vitoria': 'Vitória', 'vitória': 'Vitória', 'ec vitória': 'Vitória',
    'goias': 'Goiás', 'goias ec': 'Goiás', 'goiás': 'Goiás', 'goiás ec': 'Goiás',
    'cuiaba': 'Cuiabá', 'cuiaba ec': 'Cuiabá', 'cuiabá': 'Cuiabá', 'cuiabá ec': 'Cuiabá',
    'juventude': 'Juventude', 'ec juventude': 'Juventude',
    'coritiba': 'Coritiba', 'coritiba fc': 'Coritiba', 'coritiba fbc': 'Coritiba',
    'avai': 'Avaí', 'avai fc': 'Avaí', 'avaí': 'Avaí', 'avaí fc': 'Avaí',
    'chapecoense': 'Chapecoense', 'chapecoense-sc': 'Chapecoense', 'acf chapecoense': 'Chapecoense',
    'ponte preta': 'Ponte Preta', 'aa ponte preta': 'Ponte Preta',
    'guarani': 'Guarani', 'guarani fc': 'Guarani',
    'figueirense': 'Figueirense', 'figueirense fc': 'Figueirense',
    'criciuma': 'Criciúma', 'criciuma ec': 'Criciúma', 'criciúma': 'Criciúma', 'criciúma ec': 'Criciúma',
    'vila nova': 'Vila Nova', 'vila nova fc': 'Vila Nova',
    'nautico': 'Náutico', 'nautico capibaribe': 'Náutico', 'clube nautico capibaribe': 'Náutico', 'náutico': 'Náutico',
    'santa cruz': 'Santa Cruz', 'santa cruz fc': 'Santa Cruz',
    'sampaio correa': 'Sampaio Corrêa', 'sampaio corrêa': 'Sampaio Corrêa', 'sampaio correa fc': 'Sampaio Corrêa',
    'paysandu': 'Paysandu', 'paysandu sc': 'Paysandu',
    'remo': 'Remo', 'clube do remo': 'Remo',
    'crb': 'CRB', 'crb-al': 'CRB', 'crb al': 'CRB',
    'csa': 'CSA', 'csa-al': 'CSA', 'csa al': 'CSA',
    'america-rn': 'América-RN', 'america rn': 'América-RN', 'américa-rn': 'América-RN',
    'abc': 'ABC', 'abc-rn': 'ABC', 'abc fc': 'ABC',
    'londrina': 'Londrina', 'londrina ec': 'Londrina',
    'operario-pr': 'Operário-PR', 'operario ferroviario': 'Operário-PR', 'operário-pr': 'Operário-PR', 'operário ferroviário': 'Operário-PR',
    'mirassol': 'Mirassol', 'mirassol fc': 'Mirassol',
    'novorizontino': 'Novorizontino', 'gremio novorizontino': 'Novorizontino', 'grêmio novorizontino': 'Novorizontino',
    'ituano': 'Ituano', 'ituano fc': 'Ituano',
    'brusque': 'Brusque', 'brusque fc': 'Brusque',
    'amazonas': 'Amazonas', 'amazonas fc': 'Amazonas',
    'botafogo-sp': 'Botafogo-SP', 'botafogo sp': 'Botafogo-SP', 'botafogo fc sp': 'Botafogo-SP',
    'botafogo-pb': 'Botafogo-PB', 'botafogo pb': 'Botafogo-PB',
    'ferroviaria': 'Ferroviária', 'ferroviária': 'Ferroviária', 'ferroviaria-sp': 'Ferroviária',
    'volta redonda': 'Volta Redonda', 'volta redonda fc': 'Volta Redonda',
    'sao bernardo': 'São Bernardo', 'são bernardo': 'São Bernardo', 'sao bernardo fc': 'São Bernardo',
    'athletic club': 'Athletic Club-MG', 'athletic': 'Athletic Club-MG', 'athletic-mg': 'Athletic Club-MG',
    'tombense': 'Tombense', 'tombense fc': 'Tombense',
    'confianca': 'Confiança', 'confiança': 'Confiança', 'ad confianca': 'Confiança',
    'ypiranga': 'Ypiranga-RS', 'ypiranga-rs': 'Ypiranga-RS', 'ypiranga de erechim': 'Ypiranga-RS',
    'aparecidense': 'Aparecidense', 'aa aparecidense': 'Aparecidense',

    # Internacionais - Clubes Europeus e Sul-Americanos
    'real madrid': 'Real Madrid', 'real madrid cf': 'Real Madrid',
    'barcelona': 'Barcelona', 'fc barcelona': 'Barcelona',
    'atletico de madrid': 'Atlético de Madrid', 'atletico madrid': 'Atlético de Madrid', 'atlético madrid': 'Atlético de Madrid',
    'athletic bilbao': 'Athletic Bilbao',
    'sevilla': 'Sevilla', 'sevilla fc': 'Sevilla',
    'valencia': 'Valencia', 'valencia cf': 'Valencia',
    'villarreal': 'Villarreal', 'villarreal cf': 'Villarreal',
    'real betis': 'Real Betis', 'betis': 'Real Betis',
    'real sociedad': 'Real Sociedad',
    'manchester united': 'Manchester United', 'man united': 'Manchester United', 'man utd': 'Manchester United',
    'manchester city': 'Manchester City', 'man city': 'Manchester City',
    'arsenal': 'Arsenal', 'arsenal fc': 'Arsenal',
    'chelsea': 'Chelsea', 'chelsea fc': 'Chelsea',
    'liverpool': 'Liverpool', 'liverpool fc': 'Liverpool',
    'tottenham': 'Tottenham', 'tottenham hotspur': 'Tottenham', 'spurs': 'Tottenham',
    'newcastle': 'Newcastle', 'newcastle united': 'Newcastle',
    'aston villa': 'Aston Villa',
    'everton': 'Everton', 'everton fc': 'Everton',
    'west ham': 'West Ham', 'west ham united': 'West Ham',
    'wolverhampton': 'Wolverhampton', 'wolverhampton wanderers': 'Wolverhampton', 'wolves': 'Wolverhampton',
    'brighton': 'Brighton', 'brighton & hove albion': 'Brighton', 'brighton and hove albion': 'Brighton',
    'paris saint-germain': 'Paris Saint-Germain', 'psg': 'Paris Saint-Germain',
    'bayern munchen': 'Bayern München', 'bayern munich': 'Bayern München', 'bayern': 'Bayern München',
    'borussia dortmund': 'Borussia Dortmund', 'dortmund': 'Borussia Dortmund', 'bvb': 'Borussia Dortmund',
    'juventus': 'Juventus', 'juventus fc': 'Juventus',
    'internazionale': 'Inter de Milão', 'inter milao': 'Inter de Milão', 'inter milan': 'Inter de Milão',
    'milan': 'Milan', 'ac milan': 'Milan',
    'roma': 'Roma', 'as roma': 'Roma',
    'napoli': 'Napoli', 'ssc napoli': 'Napoli',
    'benfica': 'Benfica', 'sl benfica': 'Benfica',
    'porto': 'Porto', 'fc porto': 'Porto',
    'sporting': 'Sporting CP', 'sporting cp': 'Sporting CP', 'sporting lisboa': 'Sporting CP',
    'boca juniors': 'Boca Juniors', 'boca': 'Boca Juniors',
    'river plate': 'River Plate', 'river': 'River Plate',
    'penarol': 'Peñarol', 'peñarol': 'Peñarol',
    'nacional': 'Nacional-URU', 'club nacional': 'Nacional-URU',
    'olimpia': 'Olimpia', 'club olimpia': 'Olimpia',
    'cerro porteno': 'Cerro Porteño', 'cerro porteño': 'Cerro Porteño',
    'colo-colo': 'Colo-Colo', 'colo colo': 'Colo-Colo',
    'ldu': 'LDU Quito', 'ldu quito': 'LDU Quito',
    'independiente': 'Independiente', 'ca independiente': 'Independiente',
    'racing club': 'Racing', 'racing': 'Racing',
    'san lorenzo': 'San Lorenzo',
}


def canonicalizar_nome_time(nome: str) -> str:
    """
    Uniformiza nomes de times entre diferentes arquivos históricos e competições.
    Ex: 'Vasco da Gama' -> 'Vasco', 'Athletico Paranaense' -> 'Athletico-PR',
        'CR Flamengo' -> 'Flamengo', 'SE Palmeiras' -> 'Palmeiras'.
    """
    if not nome or not isinstance(nome, str):
        return ""
    n = nome.strip()
    if not n or n.lower() == 'nan':
        return ""

    # Normalização NFKD para buscas sem acento
    nfkd = unicodedata.normalize('NFKD', n)
    s_sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)]).strip()
    s_low = s_sem_acento.lower()

    if s_low in ALIASES_CLUBES:
        return ALIASES_CLUBES[s_low]

    # Limpeza de prefixos/sufixos comuns (ex: 'EC Bahia' -> 'bahia', 'Santos FC' -> 'santos')
    s_limpo = re.sub(r'^(ec|fc|se|cr|ca|aa|sc|ad|gremio|grêmio)\s+', '', s_low)
    s_limpo = re.sub(r'\s+(fc|sc|ec|sp|rj|mg|ba|pr|rs|sc|go|al|pe|ce|rn|pb|ma|pa|am|pi|se|es)$', '', s_limpo)
    if s_limpo in ALIASES_CLUBES:
        return ALIASES_CLUBES[s_limpo]

    return n


def parse_data_historica(data_str, ano_campeonato=None):
    """
    Converte datas de qualquer época histórica (desde 1888 a 2026).
    Usa fast-path de alta performance (resolvendo 220.000 datas em <0.5s) e
    ancora anos de 2 dígitos com precisão máxima no século da competição.
    """
    if pd.isna(data_str) if 'pd' in globals() else not data_str:
        return None
    d_str = str(data_str).strip()
    if not d_str or d_str in ['0000-00-00', '-', 'nan', 'None']:
        return None

    # Fast path 1: dd/mm/yy ou dd/mm/yyyy
    if '/' in d_str:
        partes = d_str.split('/')
        if len(partes) == 3:
            try:
                dia = int(partes[0])
                mes = int(partes[1])
                ano = int(partes[2])
                if ano < 100:
                    seculo = ((ano_campeonato or 2000) // 100) * 100
                    candidatos = [seculo - 100 + ano, seculo + ano, seculo + 100 + ano]
                    ano = min(candidatos, key=lambda a: abs(a - (ano_campeonato or 2000)))
                return datetime(ano, mes, dia)
            except Exception:
                pass

    # Fast path 2: yyyy-mm-dd
    if '-' in d_str and len(d_str) >= 10:
        partes = d_str.split('-')
        if len(partes) == 3 and len(partes[0]) == 4:
            try:
                return datetime(int(partes[0]), int(partes[1]), int(partes[2]))
            except Exception:
                pass

    # Fallback geral robusto
    formatos = ['%d/%m/%y', '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y']
    for fmt in formatos:
        try:
            dt = datetime.strptime(d_str, fmt)
            if ano_campeonato is not None and fmt == '%d/%m/%y':
                ano_2dig = dt.year % 100
                seculo = (ano_campeonato // 100) * 100
                candidatos = [seculo - 100 + ano_2dig, seculo + ano_2dig, seculo + 100 + ano_2dig]
                melhor_ano = min(candidatos, key=lambda a: abs(a - ano_campeonato))
                dt = dt.replace(year=melhor_ano)
            return dt
        except Exception:
            continue
    return None


def formatar_fase_universal(r_raw, f_raw, comp="") -> str:
    """
    Formata fases e rodadas para qualquer época histórica (1971 a 2026).
    """
    r_str = str(r_raw).strip() if pd.notna(r_raw) else ''
    f_str = str(f_raw).strip() if pd.notna(f_raw) else ''
    val = r_str or f_str

    if not val or val == 'nan':
        return 'Fase Única'

    mapa_especial = {
        '1F': '1ª Fase', '2F': '2ª Fase', '3F': '3ª Fase', '4F': '4ª Fase',
        '1/8': 'Oitavas de Final', 'O': 'Oitavas de Final',
        'QF': 'Quartas de Final', 'Q': 'Quartas de Final',
        'SF': 'Semifinais', 'S': 'Semifinais',
        'F': 'Final',
        'PR': 'Fase Preliminar', 'FG': 'Fase de Grupos'
    }
    if val in mapa_especial:
        return mapa_especial[val]

    # Número de rodada pura (ex: '1', '02', '38')
    if re.match(r'^\d+$', val):
        return f"Rodada {int(val):02d}"

    # Letra de grupo (ex: 'A', 'B', 'C' dos anos 70/80)
    if re.match(r'^[A-Za-z]$', val):
        return f"Grupo {val.upper()}"

    return val


def peso_ordem_fase(nome) -> int:
    """
    Ordena fases de forma cronológica lógica (1ª Fase, Grupos, ..., Final).
    """
    n = str(nome).lower()
    if 'final' in n and 'semi' not in n and 'oitav' not in n and 'quart' not in n:
        return 999
    if 'semi' in n:
        return 900
    if 'quart' in n or 'qf' in n:
        return 800
    if 'oitav' in n or '1/8' in n:
        return 700

    m_rod = re.search(r'rodada\s*(\d+)', n)
    if m_rod:
        return int(m_rod.group(1))

    m_fase = re.search(r'(\d+)\s*ª?\s*fase', n)
    if m_fase:
        return int(m_fase.group(1)) * 10

    m_grp = re.search(r'grupo\s*([a-z])', n)
    if m_grp:
        return 100 + (ord(m_grp.group(1)) - ord('a'))

    return 500


UF_CLUBES_CONHECIDOS = {
    'Palmeiras': 'SP', 'Corinthians': 'SP', 'São Paulo': 'SP', 'Santos': 'SP', 'Bragantino': 'SP',
    'Ponte Preta': 'SP', 'Guarani': 'SP', 'Mirassol': 'SP', 'Novorizontino': 'SP', 'Ituano': 'SP',
    'Botafogo-SP': 'SP', 'Ferroviária': 'SP', 'São Bernardo': 'SP', 'Inter de Limeira': 'SP', 'Portuguesa': 'SP',
    'Flamengo': 'RJ', 'Fluminense': 'RJ', 'Vasco': 'RJ', 'Botafogo': 'RJ', 'Volta Redonda': 'RJ', 'Bangu': 'RJ',
    'Atlético-MG': 'MG', 'Cruzeiro': 'MG', 'América-MG': 'MG', 'Tombense': 'MG', 'Athletic Club-MG': 'MG',
    'Grêmio': 'RS', 'Internacional': 'RS', 'Juventude': 'RS', 'Ypiranga-RS': 'RS', 'Caxias': 'RS', 'Brasil de Pelotas': 'RS',
    'Athletico-PR': 'PR', 'Coritiba': 'PR', 'Londrina': 'PR', 'Operário-PR': 'PR', 'Paraná': 'PR',
    'Avaí': 'SC', 'Figueirense': 'SC', 'Criciúma': 'SC', 'Chapecoense': 'SC', 'Brusque': 'SC', 'Joinville': 'SC',
    'Bahia': 'BA', 'Vitória': 'BA',
    'Sport': 'PE', 'Náutico': 'PE', 'Santa Cruz': 'PE',
    'Ceará': 'CE', 'Fortaleza': 'CE', 'Ferroviário': 'CE',
    'Goiás': 'GO', 'Atlético-GO': 'GO', 'Vila Nova': 'GO', 'Aparecidense': 'GO',
    'Cuiabá': 'MT',
    'Paysandu': 'PA', 'Remo': 'PA',
    'CRB': 'AL', 'CSA': 'AL', 'ASA': 'AL',
    'América-RN': 'RN', 'ABC': 'RN',
    'Sampaio Corrêa': 'MA',
    'Botafogo-PB': 'PB',
    'Confiança': 'SE',
    'Amazonas': 'AM', 'Manaus': 'AM',
}


def extrair_numero_rodada(rodada_val, fase_formatada: str = "", idx_jogo: int = 0, total_times: int = 20) -> int:
    """
    Extrai o número da rodada atual (1 a 38) a partir da coluna Rodada,
    da Fase_Formatada ou da posição cronológica da partida no campeonato.
    """
    for candidato in (rodada_val, fase_formatada):
        if candidato is not None and (not pd.isna(candidato) if 'pd' in globals() else True):
            s = str(candidato).strip()
            if re.match(r'^\d+$', s):
                return max(1, min(38, int(s)))
            m_rod = re.search(r'rodada\s*(\d+)', s, flags=re.IGNORECASE)
            if m_rod:
                return max(1, min(38, int(m_rod.group(1))))
            m_f = re.search(r'^(\d+)\s*ª?\s*fase', s, flags=re.IGNORECASE)
            if m_f:
                return max(1, min(38, int(m_f.group(1))))

    s_fase = str(fase_formatada or '').lower()
    if 'preliminar' in s_fase:
        return 1
    if 'grupo' in s_fase:
        return 3
    if 'oitav' in s_fase or '1/8' in s_fase:
        return 5
    if 'quart' in s_fase or 'qf' in s_fase:
        return 6
    if 'semi' in s_fase:
        return 7
    if 'final' in s_fase:
        return 8

    jogos_por_rodada = max(1, total_times // 2)
    return max(1, min(38, (idx_jogo // jogos_por_rodada) + 1))


def calcular_momentum(deque_res) -> float:
    """
    Calcula a pontuação ponderada das últimas 5 partidas (mais recentes pesam mais).
    """
    if not deque_res:
        return 1.5
    pontos_map = {'V': 3, 'E': 1, 'D': 0}
    vals = [pontos_map.get(r, 0) for r in deque_res]
    pesos = range(1, len(vals) + 1)
    return sum(v * p for v, p in zip(vals, pesos)) / sum(pesos)


def calcular_desespero(pos: int, rodada: int) -> float:
    """
    Calcula índice de desespero/urgência baseado na posição na tabela e rodada.
    Times na zona de rebaixamento ou brigando pelo título na reta final têm maior urgência.
    """
    if rodada < 5 or pos <= 0:
        return 0.0
    if pos <= 3:
        urgencia = 1.0
    elif pos <= 8:
        urgencia = 0.7
    elif pos >= 17:
        urgencia = 1.3
    elif pos >= 14:
        urgencia = 0.6
    else:
        urgencia = 0.1
    return round(urgencia * (min(rodada, 38) / 38.0), 4)


def calcular_soberba(
    risco_copa: float,
    pos_time: int,
    pos_adv: int,
    mom_time: float = 1.5,
    mom_adv: float = 1.5
) -> float:
    """
    Calcula o risco de relaxamento/soberba de uma equipe (0.0 a 1.0).
    Combina foco dividido com Copa próxima + enfrentamento de adversário fraco na tabela.
    """
    risco_base = float(risco_copa or 0.0)
    adv_fraco = (pos_adv >= 14) or (pos_time > 0 and pos_adv > 0 and (pos_adv - pos_time) >= 5)

    if risco_base > 0:
        if adv_fraco:
            gap_bonus = max(0.10, min(0.35, (pos_adv - pos_time) * 0.025)) if (pos_time > 0 and pos_adv > pos_time) else 0.15
            return round(min(1.0, risco_base + gap_bonus), 4)
        return round(min(1.0, risco_base * 0.90), 4)

    # Sem copa próxima, mas favorito destacado na ponta contra adversário na parte baixa
    if pos_time > 0 and pos_adv > 0 and pos_time <= 6 and pos_adv >= 15:
        gap = pos_adv - pos_time
        mom_bonus = max(0.0, (mom_time - mom_adv) * 0.04)
        return round(min(0.35, max(0.05, (gap - 7) * 0.02 + mom_bonus)), 4)

    return 0.0


def estimar_probabilidades(
    mom_m: float, mom_v: float,
    atk_m: float, def_v: float,
    h2h_taxa_m: float, classico: int = 0,
    risco_copa: float = 0.0,
    pos_m: int = 0, pos_v: int = 0,
    saldo_5_m: int = 0, saldo_5_v: int = 0,
    des_m: float = 0.0, des_v: float = 0.0,
    soberba_m: float = 0.0, soberba_v: float = 0.0,
    h2h_aprov_m: float = None,
    eh_serie_b: int = 0
) -> dict:
    """
    Calcula probabilidades estatísticas estimadas para vitória do mandante,
    empate e vitória do visitante, combinando todas as dimensões de features.
    """
    # Força base do mandante (vantagem de casa ~1.25)
    score_m = 1.25 * (atk_m / 1.3 if atk_m > 0 else 1.0)
    score_v = 1.00 * (def_v / 1.3 if def_v > 0 else 1.0)

    # Influência do momentum (0 a 3)
    score_m += (mom_m - 1.5) * 0.25
    score_v += (mom_v - 1.5) * 0.25

    # Influência de posição na tabela e saldo recente
    if pos_m > 0 and pos_v > 0:
        gap_pos = (pos_v - pos_m) / 20.0
        score_m += max(-0.20, min(0.20, gap_pos * 0.22))
        score_v += max(-0.20, min(0.20, -gap_pos * 0.22))

    score_m += max(-0.15, min(0.15, (saldo_5_m - saldo_5_v) * 0.02))

    # Retrospecto direto (h2h_taxa_m e h2h_aprov_m)
    taxa_ref = (h2h_taxa_m * 0.5 + h2h_aprov_m * 0.5) if h2h_aprov_m is not None else h2h_taxa_m
    if taxa_ref > 0:
        score_m += (taxa_ref - 0.5) * 0.35

    # Urgência / Desespero
    score_m += (des_m - des_v) * 0.10

    # Penalidade por soberba / desgaste de copa
    sob_m_efetiva = soberba_m if soberba_m > 0 else risco_copa
    if sob_m_efetiva > 0:
        score_m -= sob_m_efetiva * 0.35
    if soberba_v > 0:
        score_v -= soberba_v * 0.25

    # Se for clássico regional, forças se aproximam
    if classico == 1:
        dif = score_m - score_v
        score_m -= dif * 0.35
        score_v += dif * 0.15

    score_m = max(0.2, score_m)
    score_v = max(0.2, score_v)

    # Probabilidades brutas
    soma = score_m + score_v
    ratio_m = score_m / soma
    ratio_v = score_v / soma

    # Fator de empate aumenta em clássicos, Série B ou quando as forças são equivalentes
    equilibrio = 1.0 - abs(ratio_m - ratio_v)
    base_empate = 0.26 + (0.08 * equilibrio)
    if classico == 1:
        base_empate += 0.04
    if eh_serie_b == 1:
        base_empate += 0.02

    resto = 1.0 - base_empate
    pct_m = round(resto * ratio_m, 3)
    pct_v = round(resto * ratio_v, 3)
    pct_e = round(1.0 - pct_m - pct_v, 3)

    # Normalizar para somar exatamente 1.0
    tot = pct_m + pct_e + pct_v
    pct_m /= tot
    pct_e /= tot
    pct_v /= tot

    # Determinar favorito e risco de zebra
    if pct_m >= pct_v + 0.18:
        favorito = "Mandante"
        zebra = "Visitante (Zebra Alta)" if pct_v < 0.20 else "Visitante (Possível)"
    elif pct_v >= pct_m + 0.15:
        favorito = "Visitante"
        zebra = "Mandante (Zebra)" if pct_m < 0.22 else "Mandante (Possível)"
    else:
        favorito = "Equilibrado / Aberto"
        zebra = "Baixo (Jogo Pareio)"

    return {
        'pct_m': pct_m,
        'pct_e': pct_e,
        'pct_v': pct_v,
        'favorito': favorito,
        'zebra': zebra
    }


def _pontuar_sequencia(seq_str: str) -> tuple[float, float]:
    """
    Calcula o aproveitamento (0.0 a 1.0) e a pontuação IA (0.0 a 10.0)
    a partir da string de sequência recente (ex: 'VVDVE').
    """
    s = str(seq_str or '').strip().upper()
    validos = [c for c in s if c in ('V', 'E', 'D')]
    if not validos:
        return 0.5, 5.0
    pts_map = {'V': 3, 'E': 1, 'D': 0}
    soma = sum(pts_map[c] for c in validos)
    aprov = soma / (len(validos) * 3.0)
    return aprov, round(aprov * 10.0, 2)


CATEGORIAS_FEATURES_IA = [
    "1. Contexto e Identificação",
    "2. Tabela e Classificação",
    "3. Desempenho de Gols (Histórico da Temporada)",
    "4. Força Relativa (Métricas de Domínio)",
    "5. Momentum e Forma Atual",
    "6. Sensores Psicológicos e Calendário",
    "7. Memória H2H",
]


def avaliar_features_ia(
    jogo,
    ctx_m: dict = None,
    ctx_v: dict = None,
    h2h: dict = None
) -> dict:
    """
    Calcula e estrutura o diagnóstico completo de TODAS AS 42 FEATURES da IA
    organizadas nas 7 categorias oficiais para inspeção manual e pontuação analítica:
      1. Contexto e Identificação (3 features)
      2. Tabela e Classificação (5 features)
      3. Desempenho de Gols - Histórico da Temporada (8 features)
      4. Força Relativa - Métricas de Domínio (6 features)
      5. Momentum e Forma Atual (5 features)
      6. Sensores Psicológicos e Calendário (8 features)
      7. Memória H2H (7 features)
    """
    m_nome = str(jogo.get('Time da Casa', 'Mandante')).strip()
    v_nome = str(jogo.get('Time Visitante', 'Visitante')).strip()

    def _safe_float(val, default=0.0):
        try:
            if val is None or (pd.isna(val) if 'pd' in globals() else False):
                return default
            return float(val)
        except Exception:
            return default

    def _safe_int(val, default=0):
        try:
            if val is None or (pd.isna(val) if 'pd' in globals() else False):
                return default
            return int(float(val))
        except Exception:
            return default

    # ── Extração Segura das 42 Features ───────────────────────────────────
    # 1. Contexto e Identificação
    fase_fmt = str(jogo.get('Fase_Formatada', '') or '')
    rodada = _safe_int(jogo.get('Rodada', None), extrair_numero_rodada(jogo.get('Rodada'), fase_fmt))
    if rodada <= 0:
        rodada = extrair_numero_rodada(None, fase_fmt)
    eh_serie_b = _safe_int(jogo.get('Eh_Serie_B', 0), 0)
    eh_classico = _safe_int(jogo.get('É_Clássico', 0), 0)

    # 2. Tabela e Classificação
    pos_m = _safe_int(jogo.get('Posicao_Mandante', 0), 0)
    pos_v = _safe_int(jogo.get('Posicao_Visitante', 0), 0)
    tem_tabela = (pos_m > 0 and pos_v > 0)
    diff_pos_default = abs(pos_m - pos_v) if tem_tabela else 0
    diferenca_posicao = _safe_int(jogo.get('Diferenca_Posicao', diff_pos_default), diff_pos_default)
    equil_default = 1 if (tem_tabela and diferenca_posicao <= 3) else 0
    equilibrio_posicao = _safe_int(jogo.get('Equilibrio_Posicao', equil_default), equil_default)
    jogo6_default = 1 if (tem_tabela and diferenca_posicao <= 4) else 0
    jogo_de_6_pontos = _safe_int(jogo.get('Jogo_de_6_Pontos', jogo6_default), jogo6_default)

    # 3. Desempenho de Gols (Histórico da Temporada)
    atk_m = _safe_float(jogo.get('Forca_Atk_M', 1.0), 1.0)
    def_v = _safe_float(jogo.get('Forca_Def_V', 1.0), 1.0)
    media_gm_casa = _safe_float(jogo.get('Media_GM_Casa', atk_m * 1.3), atk_m * 1.3)
    media_gs_casa = _safe_float(jogo.get('Media_GS_Casa', 1.0), 1.0)
    media_gm_fora = _safe_float(jogo.get('Media_GM_Fora', 1.0), 1.0)
    media_gs_fora = _safe_float(jogo.get('Media_GS_Fora', def_v * 1.3), def_v * 1.3)
    sg_casa_m = _safe_int(jogo.get('Saldo_Gols_Casa_Mandante', jogo.get('Saldo_5_M', 0)), 0)
    sg_fora_v = _safe_int(jogo.get('Saldo_Gols_Fora_Visitante', jogo.get('Saldo_5_V', 0)), 0)
    saldo_5_m = _safe_int(jogo.get('Saldo_Ultimos_5_Casa_Mandante', jogo.get('Saldo_5_M', 0)), 0)
    saldo_5_v = _safe_int(jogo.get('Saldo_Ultimos_5_Fora_Visitante', jogo.get('Saldo_5_V', 0)), 0)

    # 4. Força Relativa (Métricas de Domínio)
    sinal_dom = _safe_float(jogo.get('Sinal_Dominio', atk_m * def_v), atk_m * def_v)
    soma_forca = _safe_float(jogo.get('Soma_Forca_Atk_Def', atk_m + def_v), atk_m + def_v)
    prod_forca = _safe_float(jogo.get('Produto_Forca_Atk_Def', atk_m * def_v), atk_m * def_v)
    diff_forca = _safe_float(jogo.get('Diferenca_Forca_Atk_Def', abs(atk_m - def_v)), abs(atk_m - def_v))

    # 5. Momentum e Forma Atual
    seq_5_m = str(jogo.get('Sequencia_5_Mandante', jogo.get('Seq_5_M', '-')) or '-')
    seq_5_v = str(jogo.get('Sequencia_5_Visitante', jogo.get('Seq_5_V', '-')) or '-')
    mom_m = _safe_float(jogo.get('Momentum_M', 1.5), 1.5)
    mom_v = _safe_float(jogo.get('Momentum_V', 1.5), 1.5)
    delta_mom = _safe_float(jogo.get('Delta_Momentum', mom_m - mom_v), mom_m - mom_v)

    # 6. Sensores Psicológicos e Calendário
    prox_copa_m_def = ctx_m.get('proxima_copa_id') or ctx_m.get('alerta_texto', 'Sem Copa (0)') if ctx_m else str(jogo.get('Alerta_Copa', 'Sem Copa (0)'))
    prox_copa_v_def = ctx_v.get('proxima_copa_id') or ctx_v.get('alerta_texto', 'Sem Copa (0)') if ctx_v else 'Sem Copa (0)'
    prox_copa_m = str(jogo.get('Proxima_Copa_Mandante', prox_copa_m_def) or 'Sem Copa (0)')
    prox_copa_v = str(jogo.get('Proxima_Copa_Visitante', prox_copa_v_def) or 'Sem Copa (0)')
    if prox_copa_m == '-':
        prox_copa_m = 'Sem Copa (0)'
    if prox_copa_v == '-':
        prox_copa_v = 'Sem Copa (0)'

    des_m = _safe_float(jogo.get('Desespero_Mandante', 0.0), 0.0)
    des_v = _safe_float(jogo.get('Desespero_Visitante', 0.0), 0.0)
    delta_des = _safe_float(jogo.get('Delta_Desespero', des_m - des_v), des_m - des_v)

    risco_copa_m = ctx_m.get('risco_soberba', 0.0) if ctx_m else _safe_float(jogo.get('Risco_Soberba', 0.0), 0.0)
    risco_copa_v = ctx_v.get('risco_soberba', 0.0) if ctx_v else 0.0
    sob_m_def = calcular_soberba(risco_copa_m, pos_m, pos_v, mom_m, mom_v)
    sob_v_def = calcular_soberba(risco_copa_v, pos_v, pos_m, mom_v, mom_m)
    soberba_m = _safe_float(jogo.get('Soberba_Mandante', sob_m_def), sob_m_def)
    soberba_v = _safe_float(jogo.get('Soberba_Visitante', sob_v_def), sob_v_def)
    delta_soberba = _safe_float(jogo.get('Delta_Soberba', soberba_m - soberba_v), soberba_m - soberba_v)

    # 7. Memória H2H
    vits_m_mando_def = h2h.get('vits_m_mando', 0) if h2h else 0
    vits_v_mando_def = h2h.get('vits_v_mando', 0) if h2h else 0
    emp_mando_def = h2h.get('empates_mando', 0) if h2h else 0
    tot_mando = h2h.get('total_mando', 0) if h2h else 0
    tot_geral = h2h.get('total_geral', 0) if h2h else 0
    aprov_h2h_def = h2h.get('aproveitamento_m', 0.5) if h2h else 0.5

    h2h_vits_m_casa = _safe_int(jogo.get('H2H_Vits_M_Casa', vits_m_mando_def), vits_m_mando_def)
    h2h_derrotas_m_casa = _safe_int(jogo.get('H2H_Derrotas_M_Casa', vits_v_mando_def), vits_v_mando_def)
    h2h_vits_v_fora = _safe_int(jogo.get('H2H_Vits_V_Fora', vits_v_mando_def), vits_v_mando_def)
    h2h_derrotas_v_fora = _safe_int(jogo.get('H2H_Derrotas_V_Fora', vits_m_mando_def), vits_m_mando_def)
    h2h_empates = _safe_int(jogo.get('H2H_Empates_H2H', emp_mando_def), emp_mando_def)
    h2h_taxa_vits_m = _safe_float(jogo.get('H2H_Taxa_Vits_M', h2h.get('taxa_m_geral', 0.5) if h2h else 0.5), 0.5)
    h2h_aprov_m = _safe_float(jogo.get('H2H_Aproveitamento_M', aprov_h2h_def), aprov_h2h_def)

    if tot_mando == 0:
        tot_mando = h2h_vits_m_casa + h2h_derrotas_m_casa + h2h_empates

    lista_features = []

    def _add_feat(
        cat_idx: int,
        codigo: str,
        descricao: str,
        valor_bruto: str,
        val_m_str: str,
        pts_m: float,
        pts_v: float,
        val_v_str: str,
        peso_max: float = 5.0,
        nota_extra: str = ""
    ):
        num_feat = len(lista_features) + 1
        cat_nome = CATEGORIAS_FEATURES_IA[cat_idx - 1]
        pts_m_r = round(float(pts_m), 2)
        pts_v_r = round(float(pts_v), 2)
        diff = round(pts_m_r - pts_v_r, 2)
        if diff > 0.05:
            venc = 'M'
            comp_str = f"🟢 +{diff:.2f} {m_nome[:11]}"
        elif diff < -0.05:
            venc = 'V'
            comp_str = f"🔴 +{abs(diff):.2f} {v_nome[:11]}"
        else:
            venc = 'E'
            comp_str = "🟡 Neutro (0.00)"
        if nota_extra:
            comp_str = f"{comp_str} • {nota_extra}"

        lista_features.append({
            'num': num_feat,
            'categoria_num': cat_idx,
            'categoria': cat_nome,
            'nome': f"{num_feat:02d}. {codigo}",
            'codigo': codigo,
            'descricao': descricao,
            'valor_bruto': valor_bruto,
            'val_m': val_m_str,
            'pts_m': pts_m_r,
            'pts_v': pts_v_r,
            'val_v': val_v_str,
            'diff': diff,
            'vencedor': venc,
            'peso_max': peso_max,
            'comparativo_str': comp_str,
        })

    # =========================================================================
    # 1. CONTEXTO E IDENTIFICAÇÃO (3 Features)
    # =========================================================================
    fase_contexto = "Reta Final" if rodada >= 30 else ("Início" if rodada <= 5 else "Temporada Regular")
    _add_feat(
        1, "Rodada",
        "O número da rodada atual (1 a 38).",
        f"Rodada {rodada}",
        f"Rodada {rodada} (Casa)",
        2.50 + (0.25 if rodada >= 30 else 0.0),
        2.00,
        f"Rodada {rodada} (Fora)",
        5.0,
        fase_contexto
    )

    _add_feat(
        1, "Eh_Serie_B",
        "Booleano (0 ou 1) indicando se o jogo pertence à Série B.",
        f"{eh_serie_b} ({'Sim - Série B' if eh_serie_b == 1 else 'Não'})",
        "Série B (Mando Forte)" if eh_serie_b == 1 else "Outra Divisão/Copa",
        3.00 if eh_serie_b == 1 else 2.50,
        2.00 if eh_serie_b == 1 else 2.50,
        "Série B (Visitante)" if eh_serie_b == 1 else "Outra Divisão/Copa",
        5.0,
        "Fator casa maior na B" if eh_serie_b == 1 else "Padrão normal"
    )

    _add_feat(
        1, "É_Clássico",
        "Booleano indicando se os times são da mesma região geográfica.",
        f"{eh_classico} ({'Sim ⚡ Clássico' if eh_classico == 1 else 'Não'})",
        "Mesma UF/Região" if eh_classico == 1 else "Regiões Distintas",
        2.50 if eh_classico == 1 else 3.00,
        2.50 if eh_classico == 1 else 2.00,
        "Mesma UF/Região" if eh_classico == 1 else "Regiões Distintas",
        5.0,
        "Equilibra mando" if eh_classico == 1 else "Mando normal"
    )

    # =========================================================================
    # 2. TABELA E CLASSIFICAÇÃO (5 Features)
    # =========================================================================
    pts_pos_m = max(0.5, (21 - min(pos_m, 20)) * 0.25) if pos_m > 0 else 2.50
    pts_pos_m_ref = 2.63  # Posição média (#10.5)
    _add_feat(
        2, "Posicao_Mandante",
        "Posição atual do mandante na tabela.",
        f"#{pos_m}º lugar" if pos_m > 0 else "N/A (Copa)",
        f"#{pos_m}º na Tabela" if pos_m > 0 else "Fase Eliminatória",
        pts_pos_m,
        pts_pos_m_ref if pos_m > 0 else 2.50,
        "Ref. Média (#10º)" if pos_m > 0 else "Fase Eliminatória",
        5.0,
        "G4/Topo" if 1 <= pos_m <= 4 else ("Z4/Alerta" if pos_m >= 17 else "Meio de Tabela")
    )

    pts_pos_v = max(0.5, (21 - min(pos_v, 20)) * 0.25) if pos_v > 0 else 2.50
    _add_feat(
        2, "Posicao_Visitante",
        "Posição atual do visitante na tabela.",
        f"#{pos_v}º lugar" if pos_v > 0 else "N/A (Copa)",
        "Ref. Média (#10º)" if pos_v > 0 else "Fase Eliminatória",
        pts_pos_m_ref if pos_v > 0 else 2.50,
        pts_pos_v,
        f"#{pos_v}º na Tabela" if pos_v > 0 else "Fase Eliminatória",
        5.0,
        "G4/Topo" if 1 <= pos_v <= 4 else ("Z4/Alerta" if pos_v >= 17 else "Meio de Tabela")
    )

    gap_sinal = (pos_v - pos_m) if tem_tabela else 0
    pts_gap_m = min(5.0, max(0.0, 2.5 + gap_sinal * 0.15))
    pts_gap_v = min(5.0, max(0.0, 2.5 - gap_sinal * 0.15))
    _add_feat(
        2, "Diferenca_Posicao",
        "Gap de posições entre os dois times.",
        f"{diferenca_posicao} pos (Δ {gap_sinal:+d})" if tem_tabela else "0 (Copa)",
        f"{gap_sinal:+d} pos vs Adv" if tem_tabela else "0 pos",
        pts_gap_m,
        pts_gap_v,
        f"{-gap_sinal:+d} pos vs Adv" if tem_tabela else "0 pos",
        5.0,
        f"Gap de {diferenca_posicao} posições"
    )

    _add_feat(
        2, "Equilibrio_Posicao",
        "Indica se a distância na tabela é menor ou igual a 3 posições.",
        f"{equilibrio_posicao} ({'Sim (≤3 pos)' if equilibrio_posicao == 1 else 'Não (>3 pos)'})",
        f"Dist. {diferenca_posicao} pos (≤3)" if equilibrio_posicao == 1 else f"Dist. {diferenca_posicao} pos (>3)",
        2.50,
        2.50,
        f"Dist. {diferenca_posicao} pos (≤3)" if equilibrio_posicao == 1 else f"Dist. {diferenca_posicao} pos (>3)",
        5.0,
        "Tabela colada" if equilibrio_posicao == 1 else "Distância ampla"
    )

    _add_feat(
        2, "Jogo_de_6_Pontos",
        "Indica se a distância na tabela é menor ou igual a 4 posições.",
        f"{jogo_de_6_pontos} ({'Sim 🔥 (≤4 pos)' if jogo_de_6_pontos == 1 else 'Não (>4 pos)'})",
        "Confronto Direto Casa" if jogo_de_6_pontos == 1 else "Jogo Normal",
        2.80 if jogo_de_6_pontos == 1 else 2.50,
        2.50,
        "Confronto Direto Fora" if jogo_de_6_pontos == 1 else "Jogo Normal",
        5.0,
        "Duelo direto na tabela" if jogo_de_6_pontos == 1 else "Objetivos distintos"
    )

    # =========================================================================
    # 3. DESEMPENHO DE GOLS - HISTÓRICO DA TEMPORADA (8 Features)
    # =========================================================================
    _add_feat(
        3, "Media_GM_Casa",
        "Média de gols marcados pelo mandante em casa.",
        f"{media_gm_casa:.2f} gols/jogo",
        f"Marca {media_gm_casa:.2f} G/J (Casa)",
        min(5.0, media_gm_casa * 2.0),
        2.60,
        "Média Liga: 1.30 G/J",
        5.0,
        "Ataque forte em casa" if media_gm_casa >= 1.5 else "Ataque modesto"
    )

    _add_feat(
        3, "Media_GS_Casa",
        "Média de gols sofridos pelo mandante em casa.",
        f"{media_gs_casa:.2f} gols/jogo",
        f"Sofre {media_gs_casa:.2f} G/J (Casa)",
        max(0.0, min(5.0, (2.0 - media_gs_casa) * 2.2)),
        min(5.0, media_gs_casa * 2.2),
        f"Explora {media_gs_casa:.2f} G/J",
        5.0,
        "Defesa sólida em casa" if media_gs_casa <= 0.9 else "Defesa cede gols"
    )

    _add_feat(
        3, "Media_GM_Fora",
        "Média de gols marcados pelo visitante fora.",
        f"{media_gm_fora:.2f} gols/jogo",
        "Média Liga: 1.00 G/J",
        2.00,
        min(5.0, media_gm_fora * 2.0),
        f"Marca {media_gm_fora:.2f} G/J (Fora)",
        5.0,
        "Visitante perigoso" if media_gm_fora >= 1.2 else "Ataque visitante tímido"
    )

    _add_feat(
        3, "Media_GS_Fora",
        "Média de gols sofridos pelo visitante fora.",
        f"{media_gs_fora:.2f} gols/jogo",
        f"Explora {media_gs_fora:.2f} G/J",
        min(5.0, media_gs_fora * 2.0),
        max(0.0, min(5.0, (2.2 - media_gs_fora) * 2.0)),
        f"Sofre {media_gs_fora:.2f} G/J (Fora)",
        5.0,
        "Defesa visitante vulnerável" if media_gs_fora >= 1.4 else "Defesa visitante firme"
    )

    _add_feat(
        3, "Saldo_Gols_Casa_Mandante",
        "Saldo acumulado do mandante jogando em casa.",
        f"{sg_casa_m:+d} gols",
        f"SG Casa: {sg_casa_m:+d} gols",
        min(5.0, max(0.0, 2.5 + sg_casa_m * 0.20)),
        2.50,
        "Ref. Equilíbrio (0)",
        5.0,
        "Saldo positivo em casa" if sg_casa_m > 0 else ("Saldo negativo" if sg_casa_m < 0 else "Saldo zerado")
    )

    _add_feat(
        3, "Saldo_Gols_Fora_Visitante",
        "Saldo acumulado do visitante jogando fora.",
        f"{sg_fora_v:+d} gols",
        "Ref. Equilíbrio (0)",
        2.50,
        min(5.0, max(0.0, 2.5 + sg_fora_v * 0.20)),
        f"SG Fora: {sg_fora_v:+d} gols",
        5.0,
        "Bom saldo fora" if sg_fora_v > 0 else ("Saldo negativo fora" if sg_fora_v < 0 else "Saldo zerado")
    )

    _add_feat(
        3, "Saldo_Ultimos_5_Casa_Mandante",
        "Soma do saldo de gols nos últimos 5 jogos em casa do mandante.",
        f"{saldo_5_m:+d} gols (Últ. 5)",
        f"SG 5J Casa: {saldo_5_m:+d}",
        min(5.0, max(0.0, 2.5 + saldo_5_m * 0.35)),
        2.50,
        "Ref. Equilíbrio (0)",
        5.0,
        f"Recente casa: {saldo_5_m:+d}"
    )

    _add_feat(
        3, "Saldo_Ultimos_5_Fora_Visitante",
        "Soma do saldo de gols nos últimos 5 jogos fora do visitante.",
        f"{saldo_5_v:+d} gols (Últ. 5)",
        "Ref. Equilíbrio (0)",
        2.50,
        min(5.0, max(0.0, 2.5 + saldo_5_v * 0.35)),
        f"SG 5J Fora: {saldo_5_v:+d}",
        5.0,
        f"Recente fora: {saldo_5_v:+d}"
    )

    # =========================================================================
    # 4. FORÇA RELATIVA - MÉTRICAS DE DOMÍNIO (6 Features)
    # =========================================================================
    _add_feat(
        4, "Forca_Atk_M",
        "Razão entre gols marcados em casa e a média da liga.",
        f"{atk_m:.3f}x",
        f"Força Atk: {atk_m:.2f}x",
        min(5.0, max(0.5, atk_m * 2.5)),
        2.50,
        "Média Liga: 1.00x",
        5.0,
        "Acima da média" if atk_m > 1.05 else ("Abaixo da média" if atk_m < 0.95 else "Na média")
    )

    _add_feat(
        4, "Forca_Def_V",
        "Razão entre gols sofridos fora e a média da liga.",
        f"{def_v:.3f}x",
        f"Cede {def_v:.2f}x ao Atk M",
        min(5.0, max(0.5, def_v * 2.5)),
        min(5.0, max(0.5, (2.0 - min(def_v, 1.8)) * 2.5)),
        f"Ratio GS Fora: {def_v:.2f}x",
        5.0,
        "Defesa V vazada (>1.0)" if def_v > 1.05 else "Defesa V sólida (<1.0)"
    )

    inv_dom = (1.0 / max(0.25, sinal_dom)) if sinal_dom > 0 else 1.0
    _add_feat(
        4, "Sinal_Dominio",
        "Produto da força de ataque do mandante pela força de defesa do visitante.",
        f"{sinal_dom:.3f}",
        f"Domínio: {sinal_dom:.2f}x",
        min(5.0, max(0.5, sinal_dom * 2.5)),
        min(5.0, max(0.5, inv_dom * 2.5)),
        f"Contenção: {inv_dom:.2f}x",
        5.0,
        "Pressão ofensiva M" if sinal_dom > 1.1 else "Jogo controlado"
    )

    _add_feat(
        4, "Soma_Forca_Atk_Def",
        "Soma das forças de ataque/defesa.",
        f"{soma_forca:.3f}",
        f"Atk+DefV: {soma_forca:.2f}",
        min(5.0, max(0.5, soma_forca * 1.25)),
        min(5.0, max(0.5, (4.0 - min(soma_forca, 3.6)) * 1.25)),
        "Ref. Soma: 2.00",
        5.0,
        "Tendência Over/Domínio" if soma_forca > 2.1 else "Tendência Under/Trancado"
    )

    _add_feat(
        4, "Produto_Forca_Atk_Def",
        "Multiplicação das forças.",
        f"{prod_forca:.3f}",
        f"Atk×DefV: {prod_forca:.2f}",
        min(5.0, max(0.5, prod_forca * 2.5)),
        min(5.0, max(0.5, (2.0 - min(prod_forca, 1.8)) * 2.5)),
        "Ref. Produto: 1.00",
        5.0,
        f"Índice {prod_forca:.2f}"
    )

    gap_atk_def = atk_m - def_v
    _add_feat(
        4, "Diferenca_Forca_Atk_Def",
        "Diferença absoluta entre ataque M e defesa V.",
        f"{diff_forca:.3f} (Δ {gap_atk_def:+.2f})",
        f"|Atk - DefV| = {diff_forca:.2f}",
        min(5.0, max(0.5, 2.5 + gap_atk_def * 1.5)),
        min(5.0, max(0.5, 2.5 - gap_atk_def * 1.5)),
        f"Gap: {gap_atk_def:+.2f}",
        5.0,
        f"Desnível de {diff_forca:.2f}"
    )

    # =========================================================================
    # 5. MOMENTUM E FORMA ATUAL (5 Features)
    # =========================================================================
    aprov_seq_m, pts_seq_m_10 = _pontuar_sequencia(seq_5_m)
    aprov_seq_v, pts_seq_v_10 = _pontuar_sequencia(seq_5_v)

    _add_feat(
        5, "Sequencia_5_Mandante",
        "String com os últimos 5 resultados (V/E/D).",
        f"{seq_5_m} ({aprov_seq_m:.0%})",
        f"{seq_5_m} ({aprov_seq_m:.0%})",
        pts_seq_m_10 * 0.5,
        2.50,
        "Ref. Neutro (50%)",
        5.0,
        f"Forma M: {seq_5_m}"
    )

    _add_feat(
        5, "Sequencia_5_Visitante",
        "String com os últimos 5 resultados do visitante.",
        f"{seq_5_v} ({aprov_seq_v:.0%})",
        "Ref. Neutro (50%)",
        2.50,
        pts_seq_v_10 * 0.5,
        f"{seq_5_v} ({aprov_seq_v:.0%})",
        5.0,
        f"Forma V: {seq_5_v}"
    )

    _add_feat(
        5, "Momentum_M",
        "Valor numérico ponderado da forma atual do mandante.",
        f"{mom_m:.3f} / 3.00",
        f"Momentum M: {mom_m:.2f}",
        (mom_m / 3.0) * 5.0,
        2.50,
        "Ref. Neutro: 1.50",
        5.0,
        "Em alta 🔥" if mom_m >= 2.0 else ("Em baixa 📉" if mom_m <= 1.0 else "Estável")
    )

    _add_feat(
        5, "Momentum_V",
        "Valor numérico ponderado da forma atual do visitante.",
        f"{mom_v:.3f} / 3.00",
        "Ref. Neutro: 1.50",
        2.50,
        (mom_v / 3.0) * 5.0,
        f"Momentum V: {mom_v:.2f}",
        5.0,
        "Em alta 🔥" if mom_v >= 2.0 else ("Em baixa 📉" if mom_v <= 1.0 else "Estável")
    )

    _add_feat(
        5, "Delta_Momentum",
        "Diferença de Momentum entre os dois times.",
        f"{delta_mom:+.3f}",
        f"Δ {delta_mom:+.2f} p/ {m_nome[:10]}",
        min(5.0, max(0.0, 2.5 + delta_mom * 1.25)),
        min(5.0, max(0.0, 2.5 - delta_mom * 1.25)),
        f"Δ {-delta_mom:+.2f} p/ {v_nome[:10]}",
        5.0,
        f"Diferencial {delta_mom:+.2f}"
    )

    # =========================================================================
    # 6. SENSORES PSICOLÓGICOS E CALENDÁRIO (8 Features)
    # =========================================================================
    tem_copa_m = (prox_copa_m not in ('Sem Copa (0)', 'Sem Copa Próxima (0)', '-', '0'))
    tem_copa_v = (prox_copa_v not in ('Sem Copa (0)', 'Sem Copa Próxima (0)', '-', '0'))

    _add_feat(
        6, "Proxima_Copa_Mandante",
        "Identificador de competição/fase de copa próxima.",
        prox_copa_m,
        prox_copa_m,
        max(0.5, 2.5 - risco_copa_m * 2.0) if tem_copa_m else 2.50,
        2.50,
        "Sem desgaste no M" if not tem_copa_m else "Adv c/ foco dividido",
        5.0,
        "Atenção ao calendário M" if tem_copa_m else "Calendário livre M"
    )

    _add_feat(
        6, "Proxima_Copa_Visitante",
        "Identificador para o visitante.",
        prox_copa_v,
        "Sem desgaste no V" if not tem_copa_v else "Adv c/ foco dividido",
        2.50,
        max(0.5, 2.5 - risco_copa_v * 2.0) if tem_copa_v else 2.50,
        prox_copa_v,
        5.0,
        "Atenção ao calendário V" if tem_copa_v else "Calendário livre V"
    )

    _add_feat(
        6, "Desespero_Mandante",
        "Nível de urgência baseado em título ou rebaixamento.",
        f"{des_m:.3f}",
        f"Urgência M: {des_m:.2f}",
        min(5.0, 2.0 + des_m * 2.2),
        2.50,
        "Ref. Base: 0.25",
        5.0,
        "Must-win alto 🔥" if des_m >= 0.6 else "Pressão normal"
    )

    _add_feat(
        6, "Desespero_Visitante",
        "Nível de urgência do visitante.",
        f"{des_v:.3f}",
        "Ref. Base: 0.25",
        2.50,
        min(5.0, 2.0 + des_v * 2.2),
        f"Urgência V: {des_v:.2f}",
        5.0,
        "Must-win alto 🔥" if des_v >= 0.6 else "Pressão normal"
    )

    _add_feat(
        6, "Delta_Desespero",
        "Diferença entre os níveis de desespero.",
        f"{delta_des:+.3f}",
        f"Δ Urgência: {delta_des:+.2f}",
        min(5.0, max(0.0, 2.5 + delta_des * 2.0)),
        min(5.0, max(0.0, 2.5 - delta_des * 2.0)),
        f"Δ Urgência: {-delta_des:+.2f}",
        5.0,
        f"Gap de pressão {delta_des:+.2f}"
    )

    _add_feat(
        6, "Soberba_Mandante",
        "Risco de relaxamento do mandante (ter copa + adversário fraco).",
        f"{soberba_m:.3f} ({soberba_m:.0%})",
        f"Risco Relax. M: {soberba_m:.0%}",
        max(0.0, 2.5 - soberba_m * 2.5),
        2.50,
        "Foco Total (0%)" if soberba_m == 0 else "Favorece Zebra V",
        5.0,
        "Risco de salto alto ⚠️" if soberba_m >= 0.25 else "Focado ✅"
    )

    _add_feat(
        6, "Soberba_Visitante",
        "Risco de relaxamento do visitante.",
        f"{soberba_v:.3f} ({soberba_v:.0%})",
        "Foco Total (0%)" if soberba_v == 0 else "Favorece Casa M",
        2.50,
        max(0.0, 2.5 - soberba_v * 2.5),
        f"Risco Relax. V: {soberba_v:.0%}",
        5.0,
        "Risco de poupar ⚠️" if soberba_v >= 0.25 else "Focado ✅"
    )

    _add_feat(
        6, "Delta_Soberba",
        "Diferença de soberba entre os dois.",
        f"{delta_soberba:+.3f}",
        f"Δ Soberba: {delta_soberba:+.2f}",
        min(5.0, max(0.0, 2.5 - delta_soberba * 2.5)),
        min(5.0, max(0.0, 2.5 + delta_soberba * 2.5)),
        f"Δ Soberba: {-delta_soberba:+.2f}",
        5.0,
        "Penaliza quem relaxa mais"
    )

    # =========================================================================
    # 7. MEMÓRIA H2H (7 Features)
    # =========================================================================
    _add_feat(
        7, "H2H_Vits_M_Casa",
        "Histórico de vitórias do mandante contra este visitante específico em casa.",
        f"{h2h_vits_m_casa} vitórias (em {tot_mando}J)",
        f"{h2h_vits_m_casa}V em Casa",
        min(5.0, 2.0 + h2h_vits_m_casa * 0.45),
        2.00,
        f"Mando de {m_nome[:10]}",
        5.0,
        f"{h2h_vits_m_casa}V do mandante em casa"
    )

    _add_feat(
        7, "H2H_Derrotas_M_Casa",
        "Histórico de derrotas do mandante contra este visitante em casa.",
        f"{h2h_derrotas_m_casa} derrotas (em {tot_mando}J)",
        f"Sofreu {h2h_derrotas_m_casa}D em Casa",
        2.00,
        min(5.0, 2.0 + h2h_derrotas_m_casa * 0.45),
        f"Impôs {h2h_derrotas_m_casa}D ao M",
        5.0,
        f"{h2h_derrotas_m_casa}D do mandante em casa"
    )

    _add_feat(
        7, "H2H_Vits_V_Fora",
        "Histórico de vitórias do visitante contra este mandante fora.",
        f"{h2h_vits_v_fora} vitórias (em {tot_mando}J)",
        f"Mando de {m_nome[:10]}",
        2.00,
        min(5.0, 2.0 + h2h_vits_v_fora * 0.45),
        f"{h2h_vits_v_fora}V Fora",
        5.0,
        f"{h2h_vits_v_fora}V do visitante fora"
    )

    _add_feat(
        7, "H2H_Derrotas_V_Fora",
        "Histórico de derrotas do visitante contra este mandante fora.",
        f"{h2h_derrotas_v_fora} derrotas (em {tot_mando}J)",
        f"Impôs {h2h_derrotas_v_fora}D ao V",
        min(5.0, 2.0 + h2h_derrotas_v_fora * 0.45),
        2.00,
        f"Sofreu {h2h_derrotas_v_fora}D Fora",
        5.0,
        f"{h2h_derrotas_v_fora}D do visitante fora"
    )

    taxa_emp_mando = (h2h_empates / tot_mando) if tot_mando > 0 else 0.0
    _add_feat(
        7, "H2H_Empates_H2H",
        "Total de empates históricos entre esses dois times nesse mando.",
        f"{h2h_empates} empates ({taxa_emp_mando:.0%} do mando)",
        f"{h2h_empates}E em {tot_mando}J",
        2.50,
        2.50,
        f"{h2h_empates}E em {tot_mando}J",
        5.0,
        f"Tendência de empate ({taxa_emp_mando:.0%})" if taxa_emp_mando >= 0.35 else "Normal"
    )

    _add_feat(
        7, "H2H_Taxa_Vits_M",
        "Percentual de vitórias do mandante no confronto direto.",
        f"{h2h_taxa_vits_m:.1%} ({h2h_taxa_vits_m:.3f})",
        f"Taxa Vit M: {h2h_taxa_vits_m:.1%}",
        h2h_taxa_vits_m * 5.0,
        max(0.0, (1.0 - h2h_taxa_vits_m) * 5.0),
        f"Taxa Não-Vit M: {(1.0 - h2h_taxa_vits_m):.1%}",
        5.0,
        f"Total H2H: {tot_geral}J"
    )

    _add_feat(
        7, "H2H_Aproveitamento_M",
        "Métrica de aproveitamento histórico com fator de dúvida (time-decay).",
        f"{h2h_aprov_m:.1%} ({h2h_aprov_m:.3f})",
        f"Aprov. Decay M: {h2h_aprov_m:.1%}",
        h2h_aprov_m * 5.0,
        max(0.0, (1.0 - h2h_aprov_m) * 5.0),
        f"Aprov. Decay V: {(1.0 - h2h_aprov_m):.1%}",
        5.0,
        "Ponderado por recência"
    )

    # ── Consolidação por Categoria e Geral ────────────────────────────────
    resumo_categorias = []
    for idx_c, nome_c in enumerate(CATEGORIAS_FEATURES_IA, start=1):
        feats_c = [f for f in lista_features if f['categoria_num'] == idx_c]
        pm_c = round(sum(f['pts_m'] for f in feats_c), 2)
        pv_c = round(sum(f['pts_v'] for f in feats_c), 2)
        resumo_categorias.append({
            'categoria_num': idx_c,
            'categoria': nome_c,
            'qtd_features': len(feats_c),
            'pts_m': pm_c,
            'pts_v': pv_c,
            'diff': round(pm_c - pv_c, 2),
        })

    total_pts_m = round(sum(f['pts_m'] for f in lista_features), 2)
    total_pts_v = round(sum(f['pts_v'] for f in lista_features), 2)
    soma_total = total_pts_m + total_pts_v
    pct_score_m = (total_pts_m / soma_total) if soma_total > 0 else 0.5
    pct_score_v = (total_pts_v / soma_total) if soma_total > 0 else 0.5
    diff_total = round(total_pts_m - total_pts_v, 2)

    vits_feat_m = sum(1 for f in lista_features if f['vencedor'] == 'M')
    vits_feat_v = sum(1 for f in lista_features if f['vencedor'] == 'V')
    emp_feat = sum(1 for f in lista_features if f['vencedor'] == 'E')

    return {
        'features': lista_features,
        'categorias': CATEGORIAS_FEATURES_IA,
        'resumo_categorias': resumo_categorias,
        'total_features': len(lista_features),
        'total_pts_m': total_pts_m,
        'total_pts_v': total_pts_v,
        'pct_score_m': pct_score_m,
        'pct_score_v': pct_score_v,
        'diff_total': diff_total,
        'vits_feat_m': vits_feat_m,
        'vits_feat_v': vits_feat_v,
        'emp_feat': emp_feat,
    }


