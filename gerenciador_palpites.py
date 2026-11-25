"""
LOTECA ANALYTICS PRO — Gerenciador e Persistência de Palpites da Loteca
Armazena bilhetes/palpites gerados pelo usuário, permite salvar apostas para
concursos futuros, listar apostas anteriores e conferir automaticamente os acertos
quando os resultados oficiais da Caixa forem publicados.
"""

import os
import json
import time
from datetime import datetime
from config import BASE_DIR


class GerenciadorPalpitesLoteca:
    """
    Gerencia a persistência local em JSON dos palpites de apostas da Loteca.
    Oferece métodos para salvar, carregar, listar, excluir e conferir palpites
    contra os resultados oficiais da Caixa Econômica Federal.
    """

    ARQUIVO_PADRAO = os.path.join(BASE_DIR, 'dados', 'loteca_palpites_salvos.json')

    def __init__(self, caminho_arquivo: str = None):
        self.caminho_arquivo = caminho_arquivo or self.ARQUIVO_PADRAO
        pasta = os.path.dirname(self.caminho_arquivo)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        self._carregar_dados()

    def _carregar_dados(self):
        """Carrega os palpites salvos do arquivo JSON local."""
        if os.path.exists(self.caminho_arquivo):
            try:
                with open(self.caminho_arquivo, 'r', encoding='utf-8') as f:
                    self._dados = json.load(f)
                    if not isinstance(self._dados, dict):
                        self._dados = {}
            except Exception:
                self._dados = {}
        else:
            self._dados = {}

    def _salvar_dados(self):
        """Salva atomicamente o estado em disco."""
        try:
            temp_path = f"{self.caminho_arquivo}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self._dados, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.caminho_arquivo)
        except Exception as e:
            print(f"Erro ao salvar palpites da Loteca: {e}")

    def salvar_palpite(
        self,
        numero_concurso: int,
        nome: str,
        palpites_dict: dict,
        custo: float = 3.0,
        combinacoes: int = 1,
        secos: int = 14,
        duplos: int = 0,
        triplos: int = 0,
        times_resumo: list = None
    ) -> dict:
        """
        Salva um novo palpite para o concurso informado.
        - palpites_dict: {1: {'1', 'X'}, 2: {'1'}, ...} ou { '1': ['1', 'X'], ... }
        """
        self._carregar_dados()
        str_concurso = str(numero_concurso)
        if str_concurso not in self._dados:
            self._dados[str_concurso] = []

        # Converter chaves e sets para tipos serializáveis em JSON
        palpites_serializaveis = {}
        for seq in range(1, 15):
            val = palpites_dict.get(seq) or palpites_dict.get(str(seq)) or set()
            if isinstance(val, (set, tuple)):
                palpites_serializaveis[str(seq)] = sorted(list(val))
            elif isinstance(val, list):
                palpites_serializaveis[str(seq)] = sorted(val)
            elif isinstance(val, str) and val:
                palpites_serializaveis[str(seq)] = [val]
            else:
                palpites_serializaveis[str(seq)] = []

        timestamp = int(time.time())
        agora_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        id_palpite = f"palpite_{numero_concurso}_{timestamp}_{len(self._dados[str_concurso]) + 1}"

        item = {
            'id': id_palpite,
            'numero_concurso': int(numero_concurso),
            'nome': (nome or f"Aposta {len(self._dados[str_concurso]) + 1}").strip(),
            'data_criacao': agora_str,
            'timestamp': timestamp,
            'palpites': palpites_serializaveis,
            'custo': float(custo),
            'combinacoes': int(combinacoes),
            'secos': int(secos),
            'duplos': int(duplos),
            'triplos': int(triplos),
            'times_resumo': times_resumo or []
        }

        self._dados[str_concurso].append(item)
        self._salvar_dados()
        return item

    def listar_palpites(self, numero_concurso: int = None) -> list:
        """
        Retorna lista de palpites salvos.
        Se numero_concurso for informado, filtra por aquele concurso.
        Retorna ordenado do mais recente para o mais antigo.
        """
        self._carregar_dados()
        if numero_concurso is not None:
            lista = self._dados.get(str(numero_concurso), [])
            return sorted(lista, key=lambda x: x.get('timestamp', 0), reverse=True)

        todos = []
        for c_num, lista in self._dados.items():
            todos.extend(lista)
        return sorted(todos, key=lambda x: x.get('timestamp', 0), reverse=True)

    def obter_palpite(self, id_palpite: str) -> dict:
        """Busca um palpite específico pelo ID."""
        self._carregar_dados()
        for lista in self._dados.values():
            for p in lista:
                if p.get('id') == id_palpite:
                    return p
        return None

    def excluir_palpite(self, id_palpite: str) -> bool:
        """Exclui um palpite pelo ID."""
        self._carregar_dados()
        alterado = False
        for c_num, lista in self._dados.items():
            nova_lista = [p for p in lista if p.get('id') != id_palpite]
            if len(nova_lista) != len(lista):
                self._dados[c_num] = nova_lista
                alterado = True
                break

        if alterado:
            self._salvar_dados()
            return True
        return False

    def contar_palpites(self, numero_concurso: int = None) -> int:
        """Retorna o número de palpites salvos para o concurso (ou no total)."""
        self._carregar_dados()
        if numero_concurso is not None:
            return len(self._dados.get(str(numero_concurso), []))
        return sum(len(l) for l in self._dados.values())

    @staticmethod
    def conferir_palpite(palpite: dict, jogos_oficiais: list) -> dict:
        """
        Compara o palpite do usuário com os 14 confrontos e resultados oficiais da Caixa.
        
        Retorna um dicionário estruturado com:
        - total_acertos: int (0..14)
        - total_erros: int (0..14)
        - total_pendentes: int (jogos sem coluna oficial definida)
        - premiado_14: bool
        - premiado_13: bool
        - status_faixa: str ('1º Prêmio (14 acertos)', '2º Prêmio (13 acertos)', ou 'Não premiado')
        - detalhes: lista dos 14 jogos contendo:
            {
              'seq': int,
              'mandante': str,
              'visitante': str,
              'placar_str': str,
              'coluna_oficial': str ('1', 'X', '2', ou '-'),
              'palpite_usuario': list (ex: ['1', 'X']),
              'palpite_str': str (ex: '1X'),
              'acertou': bool or None,
              'tipo_palpite': 'Seco' | 'Duplo' | 'Triplo' | 'Vazio'
            }
        """
        palpites_dict = palpite.get('palpites', {})
        jogos_map = {j.get('seq'): j for j in jogos_oficiais if j.get('seq')}

        total_acertos = 0
        total_erros = 0
        total_pendentes = 0
        detalhes = []

        for seq in range(1, 15):
            jogo = jogos_map.get(seq, {})
            mandante = jogo.get('mandante_completo') or jogo.get('mandante', f"Jogo {seq}")
            visitante = jogo.get('visitante_completo') or jogo.get('visitante', f"Adversário {seq}")
            placar = jogo.get('placar_str', '- x -')
            coluna_oficial = str(jogo.get('coluna', '-')).strip()

            escolhas = palpites_dict.get(str(seq)) or palpites_dict.get(seq) or []
            if isinstance(escolhas, set):
                escolhas = sorted(list(escolhas))
            elif isinstance(escolhas, str):
                escolhas = [escolhas]

            palpite_str = ' '.join(escolhas) if escolhas else '-'
            qtd_esc = len(escolhas)
            if qtd_esc == 1:
                tipo_palp = 'Seco'
            elif qtd_esc == 2:
                tipo_palp = 'Duplo'
            elif qtd_esc >= 3:
                tipo_palp = 'Triplo'
            else:
                tipo_palp = 'Vazio'

            # Verifica acerto
            if coluna_oficial in ('1', 'X', '2'):
                if coluna_oficial in escolhas:
                    acertou = True
                    total_acertos += 1
                else:
                    acertou = False
                    total_erros += 1
            else:
                acertou = None
                total_pendentes += 1

            detalhes.append({
                'seq': seq,
                'mandante': mandante,
                'visitante': visitante,
                'placar_str': placar,
                'coluna_oficial': coluna_oficial,
                'palpite_usuario': escolhas,
                'palpite_str': palpite_str,
                'acertou': acertou,
                'tipo_palpite': tipo_palp
            })

        premiado_14 = (total_acertos == 14)
        premiado_13 = (total_acertos == 13)

        if premiado_14:
            status_faixa = "🏆 1º Prêmio (14 acertos)"
        elif premiado_13:
            status_faixa = "🥈 2º Prêmio (13 acertos)"
        elif total_pendentes > 0:
            status_faixa = f"⏳ Em Andamento ({total_pendentes} pendentes)"
        else:
            status_faixa = f"❌ Não Premiado ({total_acertos}/14 acertos)"

        return {
            'total_acertos': total_acertos,
            'total_erros': total_erros,
            'total_pendentes': total_pendentes,
            'premiado_14': premiado_14,
            'premiado_13': premiado_13,
            'status_faixa': status_faixa,
            'detalhes': detalhes,
            'custo': palpite.get('custo', 3.0),
            'combinacoes': palpite.get('combinacoes', 1),
            'nome_palpite': palpite.get('nome', 'Aposta'),
            'data_criacao': palpite.get('data_criacao', ''),
            'id_palpite': palpite.get('id', '')
        }
