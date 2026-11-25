"""
Projeto Chronos — Ponto de Entrada Principal
Interface Gráfica Avançada de Análise Esportiva & Raspagem O Gol Unificada

Acervo Histórico Completo:
- Brasileirão Série A: desde a 1ª edição (1971 a 2026 — 56 temporadas)
- Brasileirão Série B: desde 1971 a 2026 (45 temporadas)
- Copa do Brasil: desde a 1ª edição (1989 a 2026 — 38 temporadas)
- Copa Libertadores: todas as edições locais (2006 a 2022)
- Copa Sudamericana: todas as edições locais (2006 a 2022)
- Campeonatos Estaduais: Paulista, Carioca, Mineiro, Gaúcho, Goiano, Baiano, Capixaba, etc.
- Ligas Europeias: Premier League (1888-2026), La Liga (1928-2026), Italiano Serie A (1897-2026), Campeonato Francês Ligue 1 (1932-2026)
- Cruzamento e Contexto de Copas (Desgaste, Calendário, Risco de Poupança)
- Histórico H2H Bilateral Multicompetições (acumulado desde 1971)
- Importador O Gol 2.0 integrado com múltiplos navegadores concorrentes em background.

Arquitetura Modular:
- config.py               : Paleta Dark Theme, fontes, constantes e caminhos
- utils.py                : Normalização fonética, cálculo de probabilidades, momentum, fases e gols
- gerenciador_dados.py    : Classe GerenciadorDados (caching, indexação e estaduais)
- barra_h2h.py            : Classe BarraH2HVisual (widget canvas proporcional)
- janela_raio_x.py        : Classe JanelaRaioXJogo (modal cirúrgica de partida)
- raspador_gol.py         : Classe RaspadorGol (raspagem paralela multi-navegador headless)
- janela_importacao.py    : Classe JanelaGerenciadorImportacao (gestor de links e importador)
- app_analise_loteca.py   : Classe AppAnaliseLoteca (janela principal e controles)
"""

# Re-exportação para compatibilidade total com importações existentes
from config import (
    BASE_DIR,
    _caminho,
    THEME,
    FONTS,
    COMPETICOES,
    CORES_COMPETICAO,
    ABREV_COMPETICAO,
)

from utils import (
    normalizar_texto,
    extrair_gols,
    parse_data_historica,
    formatar_fase_universal,
    peso_ordem_fase,
    calcular_momentum,
    calcular_desespero,
    estimar_probabilidades,
    avaliar_features_ia,
)

from gerenciador_dados import GerenciadorDados
from barra_h2h import BarraH2HVisual
from janela_raio_x import JanelaRaioXJogo
from raspador_gol import RaspadorGol
from janela_importacao import JanelaGerenciadorImportacao
from raspador_loteca import RaspadorLoteca
from gerenciador_palpites import GerenciadorPalpitesLoteca
from janela_loteca import JanelaLotecaConcursos
from app_analise_loteca import AppAnaliseLoteca


def main():
    """Inicializa e executa o aplicativo Loteca Analytics Pro."""
    app = AppAnaliseLoteca()
    app.mainloop()


if __name__ == '__main__':
    main()
