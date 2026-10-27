import json
from datetime import datetime

with open('campeonatos_links.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

agora = datetime.now().isoformat()

data['premierleague'] = {
    "nome": "Premier League",
    "prefixo": "premierA",
    "categoria": "Internacional",
    "pasta_destino": "dados/inglaterra/premier",
    "ano_inicial": 1888,
    "url_inicial": "https://www.ogol.com.br/edicao/division-one-1888-89/813/calendario",
    "url_atual": "https://www.ogol.com.br/edicao/premier-league-2026-27/219695/calendario",
    "ativo": True,
    "ultima_atualizacao": agora
}

data['laliga'] = {
    "nome": "La Liga",
    "prefixo": "laligaA",
    "categoria": "Internacional",
    "pasta_destino": "dados/espanha/laligaA",
    "ano_inicial": 1928,
    "url_inicial": "https://www.ogol.com.br/edicao/la-liga-1928-1929/2107/calendario",
    "url_atual": "https://www.ogol.com.br/edicao/laliga-ea-sports-2026-27/219487/calendario",
    "ativo": True,
    "ultima_atualizacao": agora
}

data['europaleague'] = {
    "nome": "UEFA Europa League",
    "prefixo": "europaleague",
    "categoria": "Internacional",
    "pasta_destino": "dados/internacional/europaleague",
    "ano_inicial": 1971,
    "url_inicial": "https://www.ogol.com.br/edicao/uefa-cup-1971-72/1712/calendario",
    "url_atual": "https://www.ogol.com.br/edicao/uefa-europa-league-2026-27/219039/calendario",
    "ativo": True,
    "ultima_atualizacao": agora
}

with open('campeonatos_links.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("JSON atualizado com sucesso!")
