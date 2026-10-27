"""
LOTECA ANALYTICS PRO — Módulo de Consulta e Raspagem da Loteca (Caixa)
Consulta a API pública oficial da Loteca (Caixa Econômica Federal)
para obter concursos atuais, histórico de resultados, placares dos 14 jogos,
rateio de prêmios e exportação para CSV.
"""

import os
import json
import time
import urllib3
import requests
from datetime import datetime

from config import _caminho, BASE_DIR

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RaspadorLoteca:
    """
    Cliente e raspador da API pública oficial da Loteca Caixa.
    Possui cache inteligente em memória e em disco para navegação instantânea entre concursos.
    """

    URL_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api/loteca"
    URL_PROGRAMACAO = "https://servicebus2.caixa.gov.br/portaldeloterias/api/loteca/programacao"
    PASTA_CACHE = os.path.join(BASE_DIR, 'dados', 'loteca_cache')

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.cache_memoria = {}
        self.concurso_aberto_numero = None
        self.ultimo_concurso_numero = None
        os.makedirs(self.PASTA_CACHE, exist_ok=True)

    def obter_programacao_atual(self, forcar_atualizacao: bool = False) -> dict:
        """
        Consulta a programação oficial da Caixa para o concurso ATUAL aberto para apostas.
        Retorna os 14 confrontos agendados para o próximo final de semana, prazos e estimativa de prêmio.
        """
        if self.concurso_aberto_numero and not forcar_atualizacao:
            if self.concurso_aberto_numero in self.cache_memoria:
                return self.cache_memoria[self.concurso_aberto_numero]

        for tentativa in range(1, 4):
            try:
                resp = self.session.get(self.URL_PROGRAMACAO, verify=False, timeout=12)
                if resp.status_code == 200:
                    dados_raw = resp.json()
                    if isinstance(dados_raw, list) and len(dados_raw) > 0:
                        prog_formatada = self._formatar_dados_programacao(dados_raw[0])
                        num_conc = prog_formatada.get('numero')
                        if num_conc:
                            self.concurso_aberto_numero = num_conc
                            self.cache_memoria[num_conc] = prog_formatada
                        return prog_formatada
                    elif isinstance(dados_raw, dict):
                        prog_formatada = self._formatar_dados_programacao(dados_raw)
                        num_conc = prog_formatada.get('numero')
                        if num_conc:
                            self.concurso_aberto_numero = num_conc
                            self.cache_memoria[num_conc] = prog_formatada
                        return prog_formatada
                time.sleep(0.5)
            except Exception as e:
                if tentativa == 3:
                    return {'erro': f'Falha ao obter programação atual da Loteca: {str(e)}'}
                time.sleep(1)

        return {'erro': 'Não foi possível obter a programação atual de apostas da Loteca.'}

    def _formatar_dados_programacao(self, data: dict) -> dict:
        """Formata o JSON retornado pelo endpoint /programacao da Caixa."""
        numero = data.get('nuConcurso') or data.get('numero') or 0
        dt_inicio = data.get('dataInicioApostas', '')
        dt_fim = data.get('dataFimApostas', '')
        hora_fim = data.get('horarioFimApostas', '')
        hora_fim_str = f"{hora_fim}h00" if hora_fim else "15h00"
        periodo_apostas = f"De {dt_inicio} até {dt_fim} às {hora_fim_str}" if dt_fim else "Apostas Abertas"

        estimativa_prox = float(data.get('valorEstimadoProximoConcurso', 0.0) or 0.0)
        acumulado_prox = float(data.get('valorAcumuladoProximoConcurso', 0.0) or 0.0)
        dt_prox = data.get('dataProximoConcurso', '')

        jogos = []
        for idx, j in enumerate(data.get('listaJogos', [])):
            seq = j.get('nuSequencial') or (idx + 1)
            time_m = (j.get('nomeEquipeUm') or '').strip()
            uf_m = (j.get('siglaUFUm') or '').strip()
            time_v = (j.get('nomeEquipeDois') or '').strip()
            uf_v = (j.get('siglaUFDois') or '').strip()

            dt_bruta = j.get('dtJogo', '')
            dt_apenas = dt_bruta.split(' ')[0] if ' ' in dt_bruta else dt_bruta
            dia_sem = j.get('diaSemana', '').strip()

            jogos.append({
                'seq': seq,
                'mandante': time_m,
                'uf_mandante': uf_m,
                'mandante_completo': f"{time_m} ({uf_m})" if uf_m else time_m,
                'visitante': time_v,
                'uf_visitante': uf_v,
                'visitante_completo': f"{time_v} ({uf_v})" if uf_v else time_v,
                'gols_mandante': None,
                'gols_visitante': None,
                'placar_str': 'Aguardando',
                'coluna': '-',
                'dia_semana': dia_sem,
                'data_jogo': dt_apenas,
                'campeonato': (j.get('nomeCampeonato') or '').strip()
            })

        premiacao = [
            {'faixa': '1º Prêmio (14 acertos)', 'ganhadores': 0, 'valor_premio': estimativa_prox},
            {'faixa': '2º Prêmio (13 acertos)', 'ganhadores': 0, 'valor_premio': 0.0}
        ]

        return {
            'numero': numero,
            'aberto_para_apostas': True,
            'status': 'ABERTO PARA APOSTAS',
            'data_inicio_apostas': dt_inicio,
            'data_fim_apostas': dt_fim,
            'horario_fim_apostas': hora_fim_str,
            'periodo_apostas': periodo_apostas,
            'data_apuracao': f"Previsto: {dt_prox or dt_fim}",
            'acumulado': False,
            'estimativa_proximo': estimativa_prox,
            'acumulado_proximo': acumulado_prox,
            'acumulado_especial': float(data.get('valorAcumuladoConcurso_0_5', 0.0) or 0.0),
            'arrecadacao_total': 0.0,
            'proximo_concurso': numero,
            'data_proximo': dt_prox,
            'premiacao': premiacao,
            'cidades_ganhadores': [],
            'jogos': jogos,
            'colunas_resumo': {'1': 0, 'X': 0, '2': 0}
        }

    def obter_ultimo_apurado(self, forcar_atualizacao: bool = False) -> dict:
        """Obtém o concurso mais recente que já foi apurado (encerrado)."""
        return self._obter_concurso_apurado(None, forcar_atualizacao=forcar_atualizacao)

    def obter_concurso(self, numero: int = None, forcar_atualizacao: bool = False) -> dict:
        """
        Obtém os dados completos de um concurso.
        - Se numero for None: tenta primeiro obter o concurso ABERTO PARA APOSTAS.
          Se não houver aberto ou falhar, retorna o último concurso apurado.
        - Se numero for especificado:
          Verifica se corresponde ao concurso aberto (programação). Caso contrário, consulta o histórico.
        """
        # Se for None, o usuário quer ver o concurso atual para apostar!
        if numero is None:
            prog = self.obter_programacao_atual(forcar_atualizacao=forcar_atualizacao)
            if 'erro' not in prog and prog.get('jogos'):
                return prog
            # Se não houver programação ativa, recorre ao último apurado
            return self._obter_concurso_apurado(None, forcar_atualizacao=forcar_atualizacao)

        # Se número bater com o concurso aberto em cache
        if self.concurso_aberto_numero and numero == self.concurso_aberto_numero:
            return self.obter_programacao_atual(forcar_atualizacao=forcar_atualizacao)

        # 1. Verifica cache em memória
        if not forcar_atualizacao and numero in self.cache_memoria:
            return self.cache_memoria[numero]

        # 2. Verifica cache em disco
        caminho_disco = os.path.join(self.PASTA_CACHE, f"concurso_{numero}.json")
        if not forcar_atualizacao and os.path.exists(caminho_disco):
            try:
                with open(caminho_disco, 'r', encoding='utf-8') as f:
                    dados_disco = json.load(f)
                self.cache_memoria[numero] = dados_disco
                return dados_disco
            except Exception:
                pass

        # 3. Consulta concurso apurado na API
        resultado = self._obter_concurso_apurado(numero, forcar_atualizacao=forcar_atualizacao)
        if 'erro' in resultado:
            # Pode ser que o número seja o concurso aberto ainda não identificado
            prog = self.obter_programacao_atual(forcar_atualizacao=forcar_atualizacao)
            if 'erro' not in prog and prog.get('numero') == numero:
                return prog

        return resultado

    def _obter_concurso_apurado(self, numero: int = None, forcar_atualizacao: bool = False) -> dict:
        """Consulta o endpoint oficial de concursos já apurados (/api/loteca ou /api/loteca/{numero})."""
        url = f"{self.URL_BASE}/{numero}" if numero else self.URL_BASE

        for tentativa in range(1, 4):
            try:
                resp = self.session.get(url, verify=False, timeout=12)
                if resp.status_code == 200:
                    dados_raw = resp.json()
                    concurso_formatado = self._formatar_dados_concurso(dados_raw)

                    num_conc = concurso_formatado.get('numero')
                    if num_conc:
                        self.cache_memoria[num_conc] = concurso_formatado
                        if numero is None:
                            self.ultimo_concurso_numero = num_conc

                        # Salva em disco se for concurso já apurado
                        if concurso_formatado.get('data_apuracao'):
                            try:
                                caminho_disco = os.path.join(self.PASTA_CACHE, f"concurso_{num_conc}.json")
                                with open(caminho_disco, 'w', encoding='utf-8') as f:
                                    json.dump(concurso_formatado, f, indent=2, ensure_ascii=False)
                            except Exception:
                                pass

                    return concurso_formatado
                time.sleep(0.5)
            except Exception as e:
                if tentativa == 3:
                    return {'erro': f'Falha ao consultar concurso apurado {numero or "atual"}: {str(e)}'}
                time.sleep(1)

        return {'erro': f'Não foi possível obter os dados do concurso {numero or "atual"}.'}

    def _formatar_dados_concurso(self, data: dict) -> dict:
        """Formata o JSON retornado pela Caixa em uma estrutura limpa e tipada para a UI."""
        numero = data.get('numero', 0)
        data_apuracao = data.get('dataApuracao', '')
        acumulado = bool(data.get('acumulado', False))
        estimativa_prox = float(data.get('valorEstimadoProximoConcurso', 0.0) or 0.0)
        acumulado_prox = float(data.get('valorAcumuladoProximoConcurso', 0.0) or 0.0)
        acumulado_especial = float(data.get('valorAcumuladoConcursoEspecial', 0.0) or 0.0)
        arrecadacao_total = float(data.get('valorArrecadado', 0.0) or 0.0)
        prox_concurso = data.get('numeroConcursoProximo', numero + 1)
        data_prox = data.get('dataProximoConcurso', '')

        # Rateio de Prêmios
        premiacao = []
        for r in data.get('listaRateioPremio', []):
            premiacao.append({
                'faixa': r.get('descricaoFaixa', ''),
                'ganhadores': int(r.get('numeroDeGanhadores', 0) or 0),
                'valor_premio': float(r.get('valorPremio', 0.0) or 0.0)
            })

        # Cidades dos Ganhadores
        cidades_ganhadores = []
        for g in data.get('listaMunicipioUFGanhadores', []):
            cid = g.get('nomeMunicipio', '').strip()
            uf = g.get('siglaUF', '').strip()
            qtd = g.get('numeroGanhadores', 1)
            cidades_ganhadores.append(f"{cid}/{uf} ({qtd})")

        # Grade dos 14 Jogos
        jogos = []
        colunas_resumo = {'1': 0, 'X': 0, '2': 0}

        for j in data.get('listaResultadoEquipeEsportiva', []):
            seq = j.get('nuSequencial', len(jogos) + 1)
            time_m = (j.get('nomeEquipeUm') or '').strip()
            uf_m = (j.get('siglaUFUm') or '').strip()
            time_v = (j.get('nomeEquipeDois') or '').strip()
            uf_v = (j.get('siglaUFDois') or '').strip()

            gm = j.get('nuGolEquipeUm')
            gv = j.get('nuGolEquipeDois')

            if gm is not None and gv is not None and str(gm).isdigit() and str(gv).isdigit():
                gm_int = int(gm)
                gv_int = int(gv)
                placar_str = f"{gm_int} x {gv_int}"
                if gm_int > gv_int:
                    coluna = '1'
                    colunas_resumo['1'] += 1
                elif gv_int > gm_int:
                    coluna = '2'
                    colunas_resumo['2'] += 1
                else:
                    coluna = 'X'
                    colunas_resumo['X'] += 1
            else:
                gm_int = None
                gv_int = None
                placar_str = "- x -"
                coluna = '-'

            jogos.append({
                'seq': seq,
                'mandante': time_m,
                'uf_mandante': uf_m,
                'mandante_completo': f"{time_m} ({uf_m})" if uf_m else time_m,
                'visitante': time_v,
                'uf_visitante': uf_v,
                'visitante_completo': f"{time_v} ({uf_v})" if uf_v else time_v,
                'gols_mandante': gm_int,
                'gols_visitante': gv_int,
                'placar_str': placar_str,
                'coluna': coluna,
                'dia_semana': j.get('diaSemana', ''),
                'data_jogo': j.get('dtJogo', ''),
                'campeonato': j.get('nomeCampeonato', '')
            })

        return {
            'numero': numero,
            'data_apuracao': data_apuracao,
            'acumulado': acumulado,
            'estimativa_proximo': estimativa_prox,
            'acumulado_proximo': acumulado_prox,
            'acumulado_especial': acumulado_especial,
            'arrecadacao_total': arrecadacao_total,
            'proximo_concurso': prox_concurso,
            'data_proximo': data_prox,
            'premiacao': premiacao,
            'cidades_ganhadores': cidades_ganhadores,
            'jogos': jogos,
            'colunas_resumo': colunas_resumo
        }

    def baixar_historico_csv(
        self,
        inicio: int,
        fim: int,
        caminho_csv: str = None,
        callback_progresso = None,
        callback_log = None,
        cancelar_fn = None
    ) -> int:
        """
        Baixa um intervalo de concursos da Loteca e exporta diretamente para CSV estruturado.
        Compatível com dataset histórico analítico.
        """
        import csv

        if caminho_csv is None:
            caminho_csv = _caminho('dados/brasil/loteca/dataset_loteca_historico.csv')

        os.makedirs(os.path.dirname(os.path.abspath(caminho_csv)), exist_ok=True)
        total = max(1, (fim - inicio) + 1)
        salvos = 0

        existe_arquivo = os.path.exists(caminho_csv) and os.path.getsize(caminho_csv) > 20
        with open(caminho_csv, mode='a', newline='', encoding='utf-8') as f:
            escritor = csv.writer(f)
            if not existe_arquivo:
                escritor.writerow([
                    'Concurso', 'Data_Apuracao', 'Jogo_Num', 'Mandante', 'UF_Mandante',
                    'Gols_Mandante', 'Placar', 'Gols_Visitante', 'Visitante', 'UF_Visitante',
                    'Coluna', 'Dia_Semana', 'Data_Jogo', 'Campeonato'
                ])

            for idx, num_conc in enumerate(range(inicio, fim + 1)):
                if cancelar_fn and cancelar_fn():
                    if callback_log:
                        callback_log("⚠️ Download em lote cancelado pelo usuário.")
                    break

                concurso = self.obter_concurso(num_conc)
                if 'erro' in concurso:
                    if callback_log:
                        callback_log(f"⚠️ Concurso {num_conc}: {concurso['erro']}")
                    continue

                for j in concurso.get('jogos', []):
                    escritor.writerow([
                        num_conc,
                        concurso.get('data_apuracao', ''),
                        j.get('seq'),
                        j.get('mandante'),
                        j.get('uf_mandante'),
                        j.get('gols_mandante'),
                        j.get('placar_str'),
                        j.get('gols_visitante'),
                        j.get('visitante'),
                        j.get('uf_visitante'),
                        j.get('coluna'),
                        j.get('dia_semana'),
                        j.get('data_jogo'),
                        j.get('campeonato'),
                    ])

                salvos += 1
                pct = ((idx + 1) / total) * 100
                if callback_progresso:
                    callback_progresso(pct, f"Concurso {num_conc} ({concurso.get('data_apuracao', '')})")
                if callback_log:
                    callback_log(f"✅ Concurso {num_conc} ({concurso.get('data_apuracao', '')}) salvo no CSV!")
                time.sleep(0.3)

        return salvos
