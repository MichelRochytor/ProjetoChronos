"""
LOTECA ANALYTICS PRO — Módulo de Raspagem O Gol 2.0 Unificado
Extração paralela com quantidade totalmente livre de navegadores em segundo plano (Headless Chrome),
configuração LITE ultra-leve idêntica ao Raspador 2.0, pausas adequadas para renderização completa
e fila dinâmica de trabalho (Queue).
"""

import os
import csv
import time
import json
import queue
import re
import socket
import random
import subprocess
import atexit
from datetime import datetime, date
import threading
import unicodedata
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    curl_requests = None

def _normalizar_texto(txt: str) -> str:
    """Normaliza texto removendo acentos, pontuações e convertendo para minúsculas."""
    if not txt:
        return ''
    nfkd = unicodedata.normalize('NFKD', str(txt))
    ascii_txt = nfkd.encode('ASCII', 'ignore').decode('ASCII').lower()
    return re.sub(r'[^a-z0-9\s]', '', ascii_txt)

from bs4 import BeautifulSoup
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    webdriver = None
    Options = None
    By = None
    WebDriverWait = None
    EC = None

from config import _caminho, BASE_DIR

USER_AGENTS_ROTATIVOS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
]


class RaspadorGol:
    """
    Motor de raspagem de jogos do O Gol com quantidade arbitrária de navegadores simultâneos,
    rede Tor / VPN integrada com rotação automática de IP a cada execução e fila dinâmica concorrente.
    """

    ARQUIVO_CONFIG = os.path.join(BASE_DIR, 'campeonatos_links.json')

    def __init__(self):
        self.cancelar_execucao = False
        self.lock_json = threading.Lock()
        self.lock_tor = threading.Lock()
        self.proc_tor = None
        self.porta_socks_tor = 9050
        self.porta_ctrl_tor = 9051
        self.contador_circuito = random.randint(1000, 9999)
        self.ultimo_ip_tor = "Aguardando ativação"
        self._aviso_hibrido_workers = set()
        self.catalogo = self.carregar_catalogo()
        atexit.register(self.encerrar_tor)

    # ── 1. GERENCIAMENTO DO CATÁLOGO DE LINKS & PREFERÊNCIAS ───────────────
    def carregar_catalogo(self) -> dict:
        """Carrega o catálogo de links do arquivo JSON ou inicializa vazio."""
        caminho_cfg = _caminho('campeonatos_links.json')
        if os.path.exists(caminho_cfg):
            try:
                with open(caminho_cfg, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Aviso: Erro ao ler campeonatos_links.json: {e}")
        return {}

    def salvar_catalogo(self, catalogo: dict = None):
        """Salva o catálogo de links atualizado em disco de forma thread-safe."""
        if catalogo is not None:
            self.catalogo = catalogo

        caminho_cfg = _caminho('campeonatos_links.json')
        with self.lock_json:
            try:
                with open(caminho_cfg, 'w', encoding='utf-8') as f:
                    json.dump(self.catalogo, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Erro ao salvar campeonatos_links.json: {e}")

    def obter_motor_preferido(self) -> str:
        """Retorna o motor de raspagem configurado ('turbo' ou 'selenium'). Padrão: 'turbo'."""
        cfg = self.catalogo.get('_configuracoes', {})
        return cfg.get('motor', 'turbo')

    def salvar_preferencia_motor(self, motor: str):
        """Salva a preferência do motor de raspagem ('turbo' ou 'selenium')."""
        if '_configuracoes' not in self.catalogo:
            self.catalogo['_configuracoes'] = {}
        self.catalogo['_configuracoes']['motor'] = motor
        self.salvar_catalogo()

    def obter_preferencia_tor(self) -> bool:
        """Retorna se o uso da Rede Tor / VPN com rotação de IP está ativo. Padrão: True."""
        cfg = self.catalogo.get('_configuracoes', {})
        return bool(cfg.get('usar_tor', True))

    def salvar_preferencia_tor(self, usar_tor: bool):
        """Salva a preferência de uso da Rede Tor / VPN."""
        if '_configuracoes' not in self.catalogo:
            self.catalogo['_configuracoes'] = {}
        self.catalogo['_configuracoes']['usar_tor'] = bool(usar_tor)
        self.salvar_catalogo()

    def obter_num_navegadores_preferido(self) -> int:
        """Retorna a quantidade de navegadores simultâneos configurada pelo usuário."""
        cfg = self.catalogo.get('_configuracoes', {})
        return cfg.get('num_navegadores', 4)

    def salvar_preferencia_navegadores(self, qtd: int):
        """Salva a preferência do usuário de quantidade de navegadores simultâneos."""
        if '_configuracoes' not in self.catalogo:
            self.catalogo['_configuracoes'] = {}
        self.catalogo['_configuracoes']['num_navegadores'] = max(1, int(qtd))
        self.salvar_catalogo()

    # ── 1.B GERENCIADOR DE REDE TOR / VPN ROTATIVA INTEGRADA ───────────────
    @staticmethod
    def _porta_aberta(host: str, port: int, timeout: float = 0.8) -> bool:
        """Verifica se há serviço escutando na porta TCP informada."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    @staticmethod
    def _localizar_binario_tor() -> str:
        """Localiza o executável do Tor (embutido no projeto em .tor_bin ou instalado no sistema)."""
        candidatos = [
            _caminho('.tor_bin/usr/bin/tor'),
            os.path.join(BASE_DIR, '.tor_bin', 'usr', 'bin', 'tor'),
            '/usr/bin/tor',
            '/usr/sbin/tor',
            '/usr/local/bin/tor',
        ]
        for c in candidatos:
            if c and os.path.exists(c) and os.access(c, os.X_OK):
                return c
        return ''

    def garantir_tor_ativo(self, callback_log=None) -> bool:
        """
        Verifica se o proxy SOCKS5 da Rede Tor está ativo; se não estiver,
        inicia automaticamente o daemon Tor embutido (.tor_bin) em segundo plano.
        """
        with self.lock_tor:
            if self._porta_aberta('127.0.0.1', 9050):
                self.porta_socks_tor = 9050
                return True
            if self._porta_aberta('127.0.0.1', 9150):
                self.porta_socks_tor = 9150
                return True

            tor_bin = self._localizar_binario_tor()
            if not tor_bin:
                if callback_log:
                    callback_log("⚠️ [Tor VPN] Binário do Tor não encontrado. Continuando sem túnel Tor.")
                return False

            if callback_log:
                callback_log("🧅 [Tor VPN] Iniciando serviço da Rede Tor integrada em segundo plano...")

            pasta_dados_tor = _caminho('.tor_bin/data')
            os.makedirs(pasta_dados_tor, exist_ok=True)
            geoip_file = _caminho('.tor_bin/usr/share/tor/geoip')
            geoip6_file = _caminho('.tor_bin/usr/share/tor/geoip6')

            cmd = [
                tor_bin,
                '--SocksPort', '127.0.0.1:9050 IsolateSOCKSAuth',
                '--ControlPort', '127.0.0.1:9051',
                '--CookieAuthentication', '0',
                '--DataDirectory', pasta_dados_tor,
            ]
            if os.path.exists(geoip_file):
                cmd.extend(['--GeoIPFile', geoip_file])
            if os.path.exists(geoip6_file):
                cmd.extend(['--GeoIPv6File', geoip6_file])

            try:
                self.proc_tor = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                inicio = time.time()
                while time.time() - inicio < 35:
                    if self.proc_tor.poll() is not None:
                        break
                    linha = self.proc_tor.stdout.readline()
                    if not linha:
                        if self._porta_aberta('127.0.0.1', 9050):
                            return True
                        time.sleep(0.2)
                        continue
                    if 'Bootstrapped 100%' in linha:
                        self.porta_socks_tor = 9050
                        if callback_log:
                            callback_log("🧅 [Tor VPN] Rede Tor 100% conectada e pronta!")
                        return True
                    elif any(m in linha for m in ('Bootstrapped 25%', 'Bootstrapped 50%', 'Bootstrapped 75%')):
                        if callback_log:
                            m_pct = re.search(r'Bootstrapped \d+%', linha)
                            if m_pct:
                                callback_log(f"🧅 [Tor VPN] Conectando à rede Tor ({m_pct.group(0)})...")
                return self._porta_aberta('127.0.0.1', 9050)
            except Exception as e:
                if callback_log:
                    callback_log(f"⚠️ [Tor VPN] Erro ao iniciar Tor: {e}")
                return False

    def rotacionar_identidade_tor(self, callback_log=None) -> str:
        """
        Força a troca imediata do circuito/IP da Rede Tor enviando SIGNAL NEWNYM ao ControlPort
        e gerando credenciais SOCKS5 isoladas (IsolateSOCKSAuth). Retorna o novo IP público.
        """
        ativo = self.garantir_tor_ativo(callback_log=callback_log)
        if not ativo:
            return "Indisponível"

        # 1. Envia comando SIGNAL NEWNYM para a porta de controle do Tor (9051)
        try:
            with socket.create_connection(('127.0.0.1', self.porta_ctrl_tor), timeout=2.5) as s_ctrl:
                s_ctrl.sendall(b'AUTHENTICATE ""\r\nSIGNAL NEWNYM\r\nQUIT\r\n')
                _ = s_ctrl.recv(256)
        except Exception:
            pass

        # 2. Incrementa o identificador de circuito para garantir isolamento via IsolateSOCKSAuth
        with self.lock_tor:
            self.contador_circuito += 1
            novo_id = self.contador_circuito

        proxies = self._obter_proxies_tor_circuito(sufixo=f"rot_{novo_id}")
        novo_ip = None

        for url_ip in ('https://api.ipify.org?format=json', 'https://check.torproject.org/api/ip'):
            try:
                r = requests.get(url_ip, proxies=proxies, timeout=12)
                if r.status_code == 200:
                    dados_ip = r.json()
                    novo_ip = dados_ip.get('ip') or dados_ip.get('IP')
                    if novo_ip:
                        break
            except Exception:
                continue

        if novo_ip:
            self.ultimo_ip_tor = novo_ip
            if callback_log:
                callback_log(f"🧅 [Tor VPN] Identidade trocada! Novo IP Público Tor: {novo_ip}")
            return novo_ip
        else:
            if callback_log:
                callback_log(f"🧅 [Tor VPN] Novo circuito Tor #{novo_id} ativado em 127.0.0.1:{self.porta_socks_tor}!")
            return self.ultimo_ip_tor

    def _obter_proxies_tor_circuito(self, sufixo: str = 'main') -> dict:
        """Gera dicionário de proxies SOCKS5h com credenciais únicas para isolar circuitos Tor."""
        cred = f"chronos_{self.contador_circuito}_{sufixo}_{random.randint(100, 999)}"
        proxy_url = f"socks5h://{cred}:torpass@127.0.0.1:{self.porta_socks_tor}"
        return {'http': proxy_url, 'https': proxy_url}

    def encerrar_tor(self):
        """Encerra o subprocesso Tor gerenciado ao fechar a aplicação."""
        if self.proc_tor and self.proc_tor.poll() is None:
            try:
                self.proc_tor.terminate()
            except Exception:
                pass

    def atualizar_item_catalogo(self, chave: str, dados: dict):
        """Atualiza ou cria um item no catálogo."""
        self.catalogo[chave] = dados
        self.salvar_catalogo()

    def remover_item_catalogo(self, chave: str):
        """Remove um campeonato do catálogo."""
        if chave in self.catalogo:
            del self.catalogo[chave]
            self.salvar_catalogo()

    # ── 2. DETECÇÃO INTELIGENTE DE JOGOS JÁ ATUALIZADOS ─────────────────────
    def esta_atualizado(
        self,
        camp_info: dict,
        modo: str = 'rapido',
        ano_alvo: int = 2026,
        max_horas: int = 8,
        forcar: bool = False,
        ano_filtro: int = None
    ) -> bool:
        """
        Verifica se a importação pode ser ignorada para economizar tempo:
        - Se forcar=True, NUNCA ignora (reimportação forçada solicitada pelo usuário).
        - Se o CSV não existir ou for incompleto, NUNCA ignora.
        - Nos modos 'ano_especifico' e 'a_partir_de', verifica os arquivos do(s) ano(s) correspondente(s).
        - Se foi atualizado há menos de max_horas e possui quantidade normal de jogos, ignora.
        """
        if forcar:
            return False

        pasta = _caminho(camp_info.get('pasta_destino', ''))
        prefixo = camp_info.get('prefixo', '')

        if modo == 'ano_especifico' and ano_filtro:
            anos_verificar = [int(ano_filtro)]
        elif modo == 'a_partir_de' and ano_filtro:
            ano_ini = max(int(ano_filtro), int(camp_info.get('ano_inicial', 2026)))
            anos_verificar = list(range(ano_ini, 2027))
        elif modo == 'completo':
            ano_ini = int(camp_info.get('ano_inicial', 2026))
            anos_verificar = list(range(ano_ini, 2027))
        else:
            anos_verificar = [int(ano_alvo)]

        for ano_chk in anos_verificar:
            caminho_chk = os.path.join(pasta, f"{prefixo}{ano_chk}.csv")
            if not os.path.exists(caminho_chk) or os.path.getsize(caminho_chk) < 150:
                return False

        caminho_csv = os.path.join(pasta, f"{prefixo}{anos_verificar[-1]}.csv")

        # Verifica timestamp de última atualização no catálogo
        ultima_atualizacao = camp_info.get('ultima_atualizacao')
        if not ultima_atualizacao:
            return False

        try:
            dt_ult = datetime.fromisoformat(ultima_atualizacao)
            # Se foi atualizado dentro de max_horas
            if (datetime.now() - dt_ult).total_seconds() < max_horas * 3600:
                # Checa se o arquivo não está truncado
                with open(caminho_csv, 'r', encoding='utf-8') as f:
                    linhas = f.readlines()
                categoria = camp_info.get('categoria', '')
                if categoria == 'Nacional' and len(linhas) < 180:
                    return False
                return True
        except Exception:
            pass

        return False

    # ── 3. MOTOR TURBO HTTP (ULTRA-RÁPIDO — REQUISIÇÕES DIRETAS + TOR) ─────
    @staticmethod
    def _criar_session_http(pool_size: int = 15) -> requests.Session:
        """Cria e configura uma Session HTTP com connection pool, headers e retries automáticos."""
        s = requests.Session()
        retry = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=pool_size, pool_maxsize=pool_size)
        s.mount('https://', adapter)
        s.mount('http://', adapter)
        s.headers.update({
            'User-Agent': random.choice(USER_AGENTS_ROTATIVOS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.ogol.com.br/',
            'Connection': 'keep-alive',
        })
        return s

    def _requisitar_get_http(
        self,
        session: requests.Session,
        url: str,
        timeout: int = 22,
        usar_tor: bool = False,
        worker_id: int = 1,
        callback_log = None
    ):
        """
        Realiza GET HTTP priorizando o circuito isolado da Rede Tor (quando usar_tor=True).
        Se o nó de saída Tor sofrer bloqueio Cloudflare (403/503), rotaciona o circuito Tor
        automaticamente e, se necessário, utiliza camuflagem TLS Chrome (curl_cffi) para nunca perder jogos.
        """
        headers_req = {
            'User-Agent': random.choice(USER_AGENTS_ROTATIVOS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.ogol.com.br/',
        }

        if usar_tor:
            # Tenta até 2 circuitos Tor distintos (IsolateSOCKSAuth)
            for tent_tor in range(1, 3):
                proxies_tor = self._obter_proxies_tor_circuito(sufixo=f"w{worker_id}_t{tent_tor}")
                try:
                    if curl_requests is not None:
                        resp_tor = curl_requests.get(
                            url, proxies=proxies_tor, headers=headers_req,
                            impersonate="chrome120", timeout=timeout
                        )
                    else:
                        resp_tor = session.get(url, proxies=proxies_tor, headers=headers_req, timeout=timeout)

                    if resp_tor is not None and resp_tor.status_code == 200 and len(resp_tor.content) > 500:
                        return resp_tor
                except Exception:
                    pass

            # Fallback anti-bloqueio com camuflagem TLS Chrome caso Cloudflare bloqueie os Exit Nodes do Tor
            if worker_id not in self._aviso_hibrido_workers:
                self._aviso_hibrido_workers.add(worker_id)
                if callback_log:
                    callback_log(
                        f"🛡️ [Worker {worker_id}] Exit Node Tor ({self.ultimo_ip_tor}) filtrado pelo Cloudflare no O Gol; "
                        f"usando túnel híbrido com camuflagem TLS Chrome para garantir a extração..."
                    )

        # Requisição com camuflagem TLS Chrome (curl_cffi) ou sessão direta com rotação de User-Agent
        if curl_requests is not None:
            try:
                resp_cf = curl_requests.get(url, headers=headers_req, impersonate="chrome120", timeout=timeout)
                if resp_cf is not None and resp_cf.status_code == 200:
                    return resp_cf
            except Exception:
                pass

        return session.get(url, headers=headers_req, timeout=timeout)

    @staticmethod
    def _extrair_mapa_edicoes_soup(soup: BeautifulSoup) -> dict:
        """Extrai dicionário {ano: id_edicao} a partir de um objeto BeautifulSoup da página."""
        select = None
        for s in soup.find_all('select'):
            opts = s.find_all('option')
            if not opts:
                continue
            anos_encontrados = sum(1 for o in opts if re.search(r'^(19|20)\d{2}', o.text.strip()))
            if anos_encontrados >= 2:
                select = s
                break

        if not select:
            return {}

        edicoes = {}
        for opt in select.find_all('option'):
            txt = opt.text.strip()
            val = opt.get('value')
            m = re.search(r'((?:19|20)\d{2})', txt)
            if m and val and val.isdigit():
                edicoes[int(m.group(1))] = val
        return edicoes

    def _obter_mapa_edicoes_http(
        self,
        session: requests.Session,
        url: str,
        usar_tor: bool = False,
        worker_id: int = 1,
        callback_log = None
    ) -> dict:
        """Obtém dicionário {ano: id_edicao} varrendo especificamente o dropdown de temporadas."""
        if not url:
            return {}
        try:
            resp = self._requisitar_get_http(
                session, url, timeout=20, usar_tor=usar_tor,
                worker_id=worker_id, callback_log=callback_log
            )
            if not resp or resp.status_code != 200:
                return {}
            soup = BeautifulSoup(resp.content, 'html.parser')
            return self._extrair_mapa_edicoes_soup(soup)
        except Exception:
            return {}

    def _coletar_jogos_temporada_http(
        self,
        session: requests.Session,
        url_base: str,
        callback_log,
        worker_id: int,
        nome_campeonato: str = '',
        usar_tor: bool = False
    ) -> list:
        """Coleta e pagina todos os jogos de uma edição específica via HTTP direto com validação anti-contaminação e retries."""
        jogos = []
        url_atual = url_base
        pagina = 1
        max_paginas = 30

        while not self.cancelar_execucao and pagina <= max_paginas:
            # Retentativas robustas com backoff para resistir a timeouts do servidor do ogol
            resp = None
            for tentativa in range(1, 4):
                try:
                    resp = self._requisitar_get_http(
                        session, url_atual, timeout=25,
                        usar_tor=usar_tor, worker_id=worker_id, callback_log=callback_log
                    )
                    if resp and resp.status_code == 200:
                        break
                    time.sleep(1.0 * tentativa)
                except Exception as e:
                    if tentativa == 3 and callback_log:
                        callback_log(f"⚠️ [Worker {worker_id}] Falha de conexão na pág {pagina}: {e}")
                    time.sleep(1.2 * tentativa)

            if not resp or resp.status_code != 200:
                break

            soup = BeautifulSoup(resp.content, 'html.parser')

            # 🛡️ Validação Anti-Contaminação: impede puxar jogos de outros torneios (ex: campeonato russo / distrital)
            if pagina == 1 and nome_campeonato:
                titulo_norm = _normalizar_texto(soup.title.text if soup.title else '')
                h1_norm = _normalizar_texto(soup.find('h1').text if soup.find('h1') else '')
                termos_chave = [_normalizar_texto(t) for t in nome_campeonato.split() if len(t) > 2]
                termos_chave = [t for t in termos_chave if t and t not in ('campeonato', 'copa', 'futebol', 'brasil')]
                # Expansão de sinônimos para ligas internacionais cujas edições mudam de nome no O Gol
                if any(t in ('italiano', 'italia') for t in termos_chave):
                    termos_chave.extend(['serie a', 'italiana', 'italia', 'divisione nazionale', 'campionato'])
                if any(t in ('espanhol', 'espanha') for t in termos_chave):
                    termos_chave.extend(['la liga', 'laliga', 'primera division'])
                if any(t in ('ingles', 'inglaterra') for t in termos_chave):
                    termos_chave.extend(['premier league', 'first division'])
                if termos_chave:
                    pertence = any(t in titulo_norm or t in h1_norm for t in termos_chave)
                    if not pertence and 'competicoes' in titulo_norm:
                        cal_tag = soup.find('a', href=lambda h: h and '/calendario' in h)
                        if cal_tag and cal_tag.get('href'):
                            href = cal_tag['href']
                            prox = href if href.startswith('http') else ('https://www.ogol.com.br' + href)
                            if prox != url_atual:
                                url_atual = prox
                                continue
                    if not pertence:
                        if callback_log:
                            callback_log(f"⚠️ [Worker {worker_id}] Página ignorada por não pertencer a '{nome_campeonato}' (Título: '{soup.title.text if soup.title else ''}').")
                        return []

            tabela = soup.find('table', class_='zztable stats')
            if not tabela or not tabela.find('tbody'):
                # Se for página inicial de competição, tenta resolver para o link de calendário
                if pagina == 1:
                    cal_tag = soup.find('a', href=lambda h: h and '/calendario' in h)
                    if cal_tag and cal_tag.get('href'):
                        href = cal_tag['href']
                        prox = href if href.startswith('http') else ('https://www.ogol.com.br' + href)
                        if prox != url_atual:
                            url_atual = prox
                            continue
                break

            linhas = tabela.find('tbody').find_all('tr')
            if not linhas:
                break

            novos_nesta_pagina = 0
            for linha in linhas:
                try:
                    fase_td = linha.find('td', class_='phase')
                    data_td = linha.find('td', class_='date')
                    tc_td = linha.find('td', class_='text home')
                    res_td = linha.find('td', class_='result')
                    tv_td = linha.find('td', class_='text away')

                    if not tc_td or not tv_td:
                        continue

                    fase_raw = fase_td.text.strip() if fase_td else ''
                    data_raw = data_td.text.strip() if data_td else ''
                    tc = tc_td.text.strip()
                    placar = res_td.text.strip() if res_td else 'vs'
                    tv = tv_td.text.strip()

                    rodada = fase_raw.replace('R', '') if 'R' in fase_raw else fase_raw
                    try:
                        data_fmt = datetime.strptime(data_raw, '%Y-%m-%d').strftime('%d/%m/%y')
                    except ValueError:
                        data_fmt = data_raw

                    jogos.append([rodada, data_fmt, tc, placar or 'vs', tv])
                    novos_nesta_pagina += 1
                except Exception:
                    continue

            if novos_nesta_pagina == 0:
                break

            # Localiza link da próxima página:
            prox_url = None
            next_link = soup.find('a', class_=lambda c: c and 'next-link' in c)
            if next_link and next_link.get('href'):
                prox_url = next_link['href']
            else:
                pag_div = soup.find('div', class_='numbers') or soup.find('div', class_='zz-pagination')
                if pag_div:
                    prox_num = str(pagina + 1)
                    for a in pag_div.find_all('a'):
                        if a.text.strip() == prox_num and a.get('href'):
                            prox_url = a['href']
                            break

            if not prox_url:
                if novos_nesta_pagina >= 40 and ('page=' in url_atual or '?' in url_base or '/calendario' in url_base):
                    sep = '&' if '?' in url_base else '?'
                    prox_url = f"{url_base}{sep}fase_in=0&equipa=0&estado=&filtro=&op=calendario&page={pagina + 1}"
                else:
                    break

            if not prox_url.startswith('http'):
                prox_url = 'https://www.ogol.com.br' + prox_url

            if prox_url == url_atual:
                break

            url_atual = prox_url
            pagina += 1
            time.sleep(0.35)

        return jogos

    def _raspar_campeonato_turbo(
        self,
        chave: str,
        camp_info: dict,
        session: requests.Session,
        modo: str,
        callback_log,
        worker_id: int,
        ano_filtro: int = None,
        forcar: bool = False,
        usar_tor: bool = False
    ) -> bool:
        """Executa raspagem ultra-rápida de um campeonato via HTTP sem abrir navegador."""
        nome = camp_info.get('nome', chave)
        prefixo = camp_info.get('prefixo', chave)
        pasta_destino = _caminho(camp_info.get('pasta_destino', 'dados/brasil/estaduais'))
        os.makedirs(pasta_destino, exist_ok=True)

        url_alvo = camp_info.get('url_atual') if (modo == 'rapido' and camp_info.get('url_atual')) else (camp_info.get('url_inicial') or camp_info.get('url_atual'))
        ano_inicial = int(camp_info.get('ano_inicial', 2026))

        if not url_alvo:
            if callback_log:
                callback_log(f"⚠️ [Worker {worker_id}] {nome}: URL não configurada. Pulando...")
            return False

        if modo == 'rapido':
            nome_arquivo = f'{prefixo}2026.csv'
            caminho_csv = os.path.join(pasta_destino, nome_arquivo)
            if callback_log:
                callback_log(f"⚡ [Worker {worker_id}] Baixando {nome} (2026)...")

            jogos = self._coletar_jogos_temporada_http(
                session, url_alvo, callback_log, worker_id,
                nome_campeonato=nome, usar_tor=usar_tor
            )
            if jogos:
                with open(caminho_csv, mode='w', newline='', encoding='utf-8') as f:
                    escritor = csv.writer(f)
                    escritor.writerow(['Rodada', 'Data', 'Time da Casa', 'Placar', 'Time Visitante'])
                    escritor.writerows(jogos)
                if callback_log:
                    callback_log(f"💾 [Worker {worker_id}] {nome}: {len(jogos)} jogos salvos em {nome_arquivo}!")
            else:
                if callback_log:
                    callback_log(f"ℹ️ [Worker {worker_id}] {nome}: Nenhum jogo encontrado nesta edição.")

        elif modo == 'ano_especifico':
            ano_esp = int(ano_filtro or 2026)
            nome_arquivo = f'{prefixo}{ano_esp}.csv'
            caminho_csv = os.path.join(pasta_destino, nome_arquivo)

            if ano_esp < ano_inicial:
                if callback_log:
                    callback_log(f"ℹ️ [Worker {worker_id}] {nome}: Ano {ano_esp} é anterior ao ano inicial ({ano_inicial}). Pulando...")
                return False

            url_ano = None
            if ano_esp == 2026 and camp_info.get('url_atual'):
                url_ano = camp_info.get('url_atual')
            else:
                edicoes_map = self._obter_mapa_edicoes_http(
                    session, camp_info.get('url_atual') or camp_info.get('url_inicial'),
                    usar_tor=usar_tor, worker_id=worker_id, callback_log=callback_log
                )
                if not edicoes_map and camp_info.get('url_inicial'):
                    edicoes_map = self._obter_mapa_edicoes_http(
                        session, camp_info.get('url_inicial'),
                        usar_tor=usar_tor, worker_id=worker_id, callback_log=callback_log
                    )
                id_edicao = edicoes_map.get(ano_esp)
                if id_edicao:
                    url_ano = f"https://www.ogol.com.br/edicao_calendario.php?id_edicao={id_edicao}"
                elif ano_esp == ano_inicial and camp_info.get('url_inicial'):
                    url_ano = camp_info.get('url_inicial')

            if not url_ano:
                if callback_log:
                    callback_log(f"ℹ️ [Worker {worker_id}] {nome}: Edição do ano {ano_esp} não localizada no O Gol.")
                return False

            if callback_log:
                callback_log(f"🎯 [Worker {worker_id}] Baixando {nome} (Ano específico: {ano_esp})...")

            jogos = self._coletar_jogos_temporada_http(
                session, url_ano, callback_log, worker_id,
                nome_campeonato=nome, usar_tor=usar_tor
            )
            if jogos:
                with open(caminho_csv, mode='w', newline='', encoding='utf-8') as f:
                    escritor = csv.writer(f)
                    escritor.writerow(['Rodada', 'Data', 'Time da Casa', 'Placar', 'Time Visitante'])
                    escritor.writerows(jogos)
                if callback_log:
                    callback_log(f"💾 [Worker {worker_id}] {nome} ({ano_esp}): {len(jogos)} jogos salvos em {nome_arquivo}!")
            else:
                if callback_log:
                    callback_log(f"ℹ️ [Worker {worker_id}] {nome} ({ano_esp}): Nenhum jogo encontrado nesta edição.")

        else:
            # Modo 'a_partir_de' (do ano escolhido em diante) ou 'completo' (histórico completo)
            ano_corte = int(ano_filtro) if (modo == 'a_partir_de' and ano_filtro) else ano_inicial
            ano_inicio_efetivo = max(ano_inicial, ano_corte)

            if callback_log:
                if modo == 'a_partir_de':
                    callback_log(f"📅 [Worker {worker_id}] Mapeando temporadas de {nome} a partir de {ano_corte}...")
                else:
                    callback_log(f"📚 [Worker {worker_id}] Mapeando histórico completo de {nome}...")

            edicoes_map = self._obter_mapa_edicoes_http(
                session, camp_info.get('url_atual') or camp_info.get('url_inicial'),
                usar_tor=usar_tor, worker_id=worker_id, callback_log=callback_log
            )
            if not edicoes_map and camp_info.get('url_inicial'):
                edicoes_map = self._obter_mapa_edicoes_http(
                    session, camp_info.get('url_inicial'),
                    usar_tor=usar_tor, worker_id=worker_id, callback_log=callback_log
                )

            if not edicoes_map:
                edicoes_map = {ano: None for ano in range(ano_inicio_efetivo, 2027)}
            else:
                edicoes_map = {ano: id_ed for ano, id_ed in edicoes_map.items() if ano >= ano_corte}
                if 2026 >= ano_corte and 2026 not in edicoes_map and camp_info.get('url_atual'):
                    edicoes_map[2026] = None

            for ano, id_edicao in sorted(edicoes_map.items()):
                if self.cancelar_execucao:
                    break
                nome_arquivo = f'{prefixo}{ano}.csv'
                caminho_csv = os.path.join(pasta_destino, nome_arquivo)

                # Se não for forçado, for ano anterior e arquivo já existir com tamanho > 100 bytes, pula
                if not forcar and ano < 2026 and os.path.exists(caminho_csv) and os.path.getsize(caminho_csv) > 100:
                    continue

                if id_edicao:
                    url_ano = f"https://www.ogol.com.br/edicao_calendario.php?id_edicao={id_edicao}"
                elif ano == 2026 and camp_info.get('url_atual'):
                    url_ano = camp_info.get('url_atual')
                else:
                    url_ano = url_alvo

                if callback_log:
                    callback_log(f"📥 [Worker {worker_id}] Extraindo {nome} ({ano})...")

                jogos = self._coletar_jogos_temporada_http(
                    session, url_ano, callback_log, worker_id,
                    nome_campeonato=nome, usar_tor=usar_tor
                )
                if jogos:
                    with open(caminho_csv, mode='w', newline='', encoding='utf-8') as f:
                        escritor = csv.writer(f)
                        escritor.writerow(['Rodada', 'Data', 'Time da Casa', 'Placar', 'Time Visitante'])
                        escritor.writerows(jogos)
                    if callback_log:
                        callback_log(f"💾 [Worker {worker_id}] {nome} ({ano}): {len(jogos)} jogos salvos em {nome_arquivo}!")

        camp_info['ultima_atualizacao'] = datetime.now().isoformat()
        self.atualizar_item_catalogo(chave, camp_info)
        return True

    # ── 4. CRIAÇÃO DE NAVEGADOR HEADLESS LITE (SELENIUM CHROME) ────────────
    @staticmethod
    def _criar_driver_headless(usar_tor: bool = False, porta_tor: int = 9050):
        """
        Cria e configura o navegador exatamente no modo LITE ultra-leve do Raspador 2.0:
        - page_load_strategy eager (não trava aguardando scripts pesados de terceiros)
        - Imagens e notificações desabilitadas (carregamento leve)
        - Suporte a Proxy SOCKS5 da Rede Tor (--proxy-server=socks5://127.0.0.1:9050)
        """
        opcoes = Options()
        opcoes.page_load_strategy = 'eager'
        opcoes.add_argument("--disable-notifications")
        opcoes.add_argument("--blink-settings=imagesEnabled=false")
        opcoes.add_argument("--headless=new")
        opcoes.add_argument("--window-size=1920,1080")
        opcoes.add_argument("--disable-gpu")
        opcoes.add_argument("--disable-dev-shm-usage")
        opcoes.add_argument("--no-sandbox")
        opcoes.add_argument("--disable-blink-features=AutomationControlled")
        opcoes.add_argument(f"user-agent={random.choice(USER_AGENTS_ROTATIVOS)}")

        if usar_tor:
            opcoes.add_argument(f"--proxy-server=socks5://127.0.0.1:{porta_tor}")

        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0
        }
        opcoes.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(options=opcoes)
        driver.set_page_load_timeout(35)
        return driver

    # ── 4. RASPAGEM DE UM CAMPEONATO POR WORKER ────────────────────────────
    def _raspar_campeonato(
        self,
        chave: str,
        camp_info: dict,
        driver,
        modo: str,
        callback_log,
        worker_id: int,
        ano_filtro: int = None,
        forcar: bool = False
    ):
        """Executa a raspagem de um campeonato com pausas suficientes para carregamento completo."""
        nome = camp_info.get('nome', chave)
        prefixo = camp_info.get('prefixo', chave)
        pasta_destino = _caminho(camp_info.get('pasta_destino', 'dados/brasil/estaduais'))
        os.makedirs(pasta_destino, exist_ok=True)

        url_alvo = camp_info.get('url_atual') if (modo == 'rapido' and camp_info.get('url_atual')) else (camp_info.get('url_inicial') or camp_info.get('url_atual'))
        ano_inicial = int(camp_info.get('ano_inicial', 2026))

        if not url_alvo:
            if callback_log:
                callback_log(f"⚠️ [Nav {worker_id}] {nome}: URL não configurada. Pulando...")
            return False

        if callback_log:
            callback_log(f"🌐 [Nav {worker_id}] Acessando {nome}...")

        edicoes_map = {}
        try:
            driver.get(url_alvo)
            time.sleep(3.5) # Pausa inicial generosa para o DOM estabilizar como no raspador 2.0

            soup_comp = BeautifulSoup(driver.page_source, 'html.parser')
            edicoes_map = self._extrair_mapa_edicoes_soup(soup_comp)

            # Se for link da página principal da competição ou não for direto do calendário:
            if '/competicao/' in driver.current_url or ('/calendario' not in driver.current_url and 'edicao_calendario' not in driver.current_url):
                ano_busca = str(ano_filtro) if (modo == 'ano_especifico' and ano_filtro) else '2026'
                opt_alvo = soup_comp.find('option', string=re.compile(ano_busca))
                if opt_alvo and opt_alvo.get('value'):
                    ed_id = opt_alvo['value']
                    cal_href = f"https://www.ogol.com.br/edicao_calendario.php?id_edicao={ed_id}"
                    if callback_log:
                        callback_log(f"📅 [Nav {worker_id}] Edição {ano_busca} identificada (ID: {ed_id}). Acessando calendário...")
                    driver.get(cal_href)
                    time.sleep(3.5)
                else:
                    cal_tag = soup_comp.find('a', href=lambda h: h and '/calendario' in h)
                    if cal_tag:
                        cal_href = cal_tag.get('href')
                        if not cal_href.startswith('http'):
                            cal_href = "https://www.ogol.com.br" + cal_href
                        if callback_log:
                            callback_log(f"📅 [Nav {worker_id}] Acessando calendário: {cal_href}")
                        driver.get(cal_href)
                        time.sleep(3.5)
        except Exception as e:
            if callback_log:
                callback_log(f"❌ [Nav {worker_id}] Erro ao carregar página de {nome}: {e}")
            return False

        # Modos 'ano_especifico' ou 'a_partir_de' via mapa de edições quando disponível
        if modo in ('ano_especifico', 'a_partir_de') and edicoes_map:
            if modo == 'ano_especifico':
                ano_esp = int(ano_filtro or 2026)
                anos_alvo = [(ano_esp, edicoes_map.get(ano_esp))] if ano_esp in edicoes_map else []
                if not anos_alvo:
                    if callback_log:
                        callback_log(f"ℹ️ [Nav {worker_id}] {nome}: Edição {ano_esp} não encontrada.")
                    return False
            else:
                ano_corte = int(ano_filtro or ano_inicial)
                anos_alvo = [(a, ed_id) for a, ed_id in sorted(edicoes_map.items()) if a >= ano_corte]

            for ano_cur, ed_id in anos_alvo:
                if self.cancelar_execucao:
                    break
                nome_arquivo = f'{prefixo}{ano_cur}.csv'
                caminho_csv = os.path.join(pasta_destino, nome_arquivo)

                if modo != 'ano_especifico' and not forcar and ano_cur < 2026 and os.path.exists(caminho_csv) and os.path.getsize(caminho_csv) > 200:
                    if callback_log:
                        callback_log(f"⏩ [Nav {worker_id}] {nome_arquivo} já existe em disco. Pulando...")
                    continue

                if ed_id:
                    driver.get(f"https://www.ogol.com.br/edicao_calendario.php?id_edicao={ed_id}")
                    time.sleep(3.5)

                if callback_log:
                    callback_log(f"📥 [Nav {worker_id}] Extraindo {nome} ({ano_cur})...")
                jogos_coletados = self._coletar_jogos_temporada(driver, callback_log, worker_id, nome_campeonato=nome)

                if jogos_coletados:
                    with open(caminho_csv, mode='w', newline='', encoding='utf-8') as f:
                        escritor = csv.writer(f)
                        escritor.writerow(['Rodada', 'Data', 'Time da Casa', 'Placar', 'Time Visitante'])
                        escritor.writerows(jogos_coletados)
                    if callback_log:
                        callback_log(f"💾 [Nav {worker_id}] Salvo {len(jogos_coletados)} jogos em {nome_arquivo}")

            camp_info['ultima_atualizacao'] = datetime.now().isoformat()
            self.atualizar_item_catalogo(chave, camp_info)
            return True

        if modo == 'ano_especifico':
            temporada_atual = int(ano_filtro or 2026)
        elif modo == 'a_partir_de':
            temporada_atual = max(ano_inicial, int(ano_filtro or ano_inicial))
        elif modo != 'rapido':
            temporada_atual = ano_inicial
        else:
            temporada_atual = 2026

        while not self.cancelar_execucao:
            nome_arquivo = f'{prefixo}{temporada_atual}.csv'
            caminho_csv = os.path.join(pasta_destino, nome_arquivo)

            # Se for histórico e o arquivo de anos anteriores já existir com tamanho bom, pula temporada
            if modo in ('completo', 'a_partir_de') and not forcar and temporada_atual < 2026 and os.path.exists(caminho_csv) and os.path.getsize(caminho_csv) > 200:
                if callback_log:
                    callback_log(f"⏩ [Nav {worker_id}] {nome_arquivo} já existe em disco. Pulando...")
            else:
                if callback_log:
                    callback_log(f"📥 [Nav {worker_id}] Extraindo {nome} ({temporada_atual})...")
                jogos_coletados = self._coletar_jogos_temporada(driver, callback_log, worker_id, nome_campeonato=nome)

                if jogos_coletados:
                    with open(caminho_csv, mode='w', newline='', encoding='utf-8') as f:
                        escritor = csv.writer(f)
                        escritor.writerow(['Rodada', 'Data', 'Time da Casa', 'Placar', 'Time Visitante'])
                        escritor.writerows(jogos_coletados)
                    if callback_log:
                        callback_log(f"💾 [Nav {worker_id}] Salvo {len(jogos_coletados)} jogos em {nome_arquivo}")

            if modo in ('rapido', 'ano_especifico'):
                break

            # Avançar para próxima temporada no modo completo com pausas idênticas ao raspador 2.0
            try:
                botao_prox = driver.find_element(By.CSS_SELECTOR, "div.zz-enthdr-season a.zz-combo-arrow-right")
                driver.execute_script("arguments[0].click();", botao_prox)
                temporada_atual += 1
                time.sleep(5) # Pausa de 5s como no raspador 2.0

                aba_calendario = driver.find_element(By.XPATH, "//div[contains(@class, 'zz-enthdr-menu-bar-items')]//a[contains(@href, '/calendario')]")
                driver.execute_script("arguments[0].click();", aba_calendario)
                time.sleep(4) # Pausa de 4s como no raspador 2.0
            except Exception:
                if callback_log:
                    callback_log(f"✅ [Nav {worker_id}] Linha temporal concluída para {nome}!")
                break

        # Atualiza timestamp de última atualização
        camp_info['ultima_atualizacao'] = datetime.now().isoformat()
        self.atualizar_item_catalogo(chave, camp_info)
        return True

    def _coletar_jogos_temporada(self, driver, callback_log, worker_id: int, nome_campeonato: str = '') -> list:
        """Coleta e pagina todos os jogos de uma temporada específica dando tempo de carregar a tabela."""
        jogos = []
        pagina_atual = 1

        while not self.cancelar_execucao:
            # 1. Tratamento seguro de anúncio/pop-up preservando a aba principal
            try:
                botao_anuncio = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@style, 'z-index: 1000')]"))
                )
                driver.execute_script("arguments[0].click();", botao_anuncio)
                time.sleep(3) # Pausa de 3s idêntica ao raspador 2.0

                if len(driver.window_handles) > 1:
                    main_handle = driver.window_handles[0]
                    for h in list(driver.window_handles)[1:]:
                        try:
                            driver.switch_to.window(h)
                            driver.close()
                        except Exception:
                            pass
                    driver.switch_to.window(main_handle)
                    if callback_log:
                        callback_log(f">> [Nav {worker_id}] Pop-up fechado com segurança mantendo a página principal!")
            except Exception:
                pass

            time.sleep(2) # Pausa para o DOM estabilizar

            # 🛡️ Validação Anti-Contaminação
            if pagina_atual == 1 and nome_campeonato:
                try:
                    titulo_pag = _normalizar_texto(driver.title or '')
                    termos_chave = [_normalizar_texto(t) for t in nome_campeonato.split() if len(t) > 2]
                    termos_chave = [t for t in termos_chave if t and t not in ('campeonato', 'copa', 'futebol', 'brasil')]
                    if any(t in ('italiano', 'italia') for t in termos_chave):
                        termos_chave.extend(['serie a', 'italiana', 'italia', 'divisione nazionale', 'campionato'])
                    if any(t in ('espanhol', 'espanha') for t in termos_chave):
                        termos_chave.extend(['la liga', 'laliga', 'primera division'])
                    if any(t in ('ingles', 'inglaterra') for t in termos_chave):
                        termos_chave.extend(['premier league', 'first division'])
                    if termos_chave:
                        pertence = any(t in titulo_pag for t in termos_chave)
                        if not pertence and 'ogol' in titulo_pag:
                            h1_text = ""
                            try:
                                h1_elem = driver.find_element(By.TAG_NAME, "h1")
                                h1_text = _normalizar_texto(h1_elem.text or '')
                            except Exception:
                                pass
                            pertence = any(t in h1_text for t in termos_chave)
                            if not pertence and 'competicoes' not in titulo_pag:
                                if callback_log:
                                    callback_log(f"⚠️ [Nav {worker_id}] Página ignorada por não pertencer a '{nome_campeonato}' (Título: '{driver.title}').")
                                return []
                except Exception:
                    pass

            # 2. Localização da tabela com retentativas para garantir o carregamento
            tabela = None
            for tentativa in range(1, 5):
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                tabela = soup.find('table', class_='zztable stats')
                if tabela:
                    break
                time.sleep(2.5) # Aguarda a tabela renderizar

            if not tabela:
                if callback_log:
                    callback_log(f"⚠️ [Nav {worker_id}] Tabela não encontrada nesta página (sem jogos registrados ou fim das páginas).")
                break

            tbody = tabela.find('tbody')
            if not tbody:
                break

            linhas = tbody.find_all('tr')
            for linha in linhas:
                try:
                    fase_raw = linha.find('td', class_='phase').text.strip()
                    data_raw = linha.find('td', class_='date').text.strip()
                    time_casa = linha.find('td', class_='text home').text.strip()
                    placar = linha.find('td', class_='result').text.strip()
                    time_fora = linha.find('td', class_='text away').text.strip()

                    if not time_casa or not time_fora:
                        continue

                    rodada = fase_raw.replace('R', '') if 'R' in fase_raw else fase_raw
                    try:
                        data_fmt = datetime.strptime(data_raw, "%Y-%m-%d").strftime("%d/%m/%y")
                    except ValueError:
                        data_fmt = data_raw

                    jogos.append([rodada, data_fmt, time_casa, placar, time_fora])
                except Exception:
                    continue

            # 3. Avançar para a próxima página da temporada com suporte a 'next-link' e numeração
            avancou = False
            try:
                # 1º tenta a classe 'next-link' da paginação oficial do ogol
                btn_prox = driver.find_element(By.CSS_SELECTOR, "div.zz-pagination a.next-link, a.next-link")
                if btn_prox and btn_prox.is_displayed():
                    driver.execute_script("arguments[0].click();", btn_prox)
                    avancou = True
            except Exception:
                pass

            if not avancou:
                try:
                    prox_pag_str = str(pagina_atual + 1)
                    btn_prox = driver.find_element(By.XPATH, f"//div[contains(@class,'numbers')]//a[text()='{prox_pag_str}']")
                    driver.execute_script("arguments[0].click();", btn_prox)
                    avancou = True
                except Exception:
                    pass

            if not avancou:
                break

            pagina_atual += 1
            time.sleep(3) # Pausa idêntica ao raspador 2.0

        return jogos

    # ── 5. MOTOR MULTI-WORKER DINÂMICO (TURBO HTTP OU SELENIUM CHROME) ─────
    def executar_raspagem_paralela(
        self,
        chaves_selecionadas: list = None,
        num_navegadores: int = 4,
        modo: str = 'rapido',
        motor: str = None,
        forcar: bool = False,
        ano_filtro: int = None,
        usar_tor: bool = None,
        callback_progresso = None,
        callback_log = None,
        callback_concluido = None,
        callback_ip_tor = None
    ):
        """
        Dispara a fila de raspagem com a quantidade desejada de workers simultâneos.
        Quando usar_tor=True, ativa a Rede Tor embutida e força a rotação de circuito/IP a cada execução.
        """
        self.cancelar_execucao = False
        self._aviso_hibrido_workers.clear()

        if motor is None:
            motor = self.obter_motor_preferido()
        if usar_tor is None:
            usar_tor = self.obter_preferencia_tor()

        if not chaves_selecionadas:
            chaves_selecionadas = [k for k, v in self.catalogo.items() if not k.startswith('_') and v.get('ativo', True)]

        total_itens = len(chaves_selecionadas)
        if total_itens == 0:
            if callback_log:
                callback_log("ℹ️ Nenhum campeonato ativo selecionado para importação.")
            if callback_concluido:
                callback_concluido(0, 0)
            return

        try:
            num_nav_solicitado = int(num_navegadores)
        except (ValueError, TypeError):
            num_nav_solicitado = 4

        nav_efetivos = max(1, min(num_nav_solicitado, total_itens))

        if modo == 'ano_especifico' and ano_filtro:
            desc_modo = f"ANO ESPECÍFICO ({ano_filtro})"
        elif modo == 'a_partir_de' and ano_filtro:
            desc_modo = f"A PARTIR DE {ano_filtro} -> 2026"
        else:
            desc_modo = modo.upper()

        def _tarefa_background():
            tor_efetivo = False
            if usar_tor:
                if callback_log:
                    callback_log("🧅 [Tor VPN] Trocando o circuito/IP da Rede Tor para esta execução...")
                novo_ip = self.rotacionar_identidade_tor(callback_log=callback_log)
                tor_efetivo = (novo_ip != "Indisponível")
                if callback_ip_tor:
                    callback_ip_tor(novo_ip)

            tag_tor = f", 🧅 TOR VPN ATIVA [IP: {self.ultimo_ip_tor}]" if tor_efetivo else ""
            if motor == 'turbo':
                if callback_log:
                    callback_log(f"⚡ Iniciando Motor Turbo HTTP com {nav_efetivos} conexões simultâneas...")
                    callback_log(f"📋 Fila com {total_itens} campeonatos (Modo: {desc_modo}{', FORÇADO' if forcar else ''}{tag_tor}).")
            else:
                if callback_log:
                    callback_log(f"🚀 Iniciando {nav_efetivos} navegadores em modo LITE simultaneamente (Headless Chrome)...")
                    callback_log(f"📋 Fila com {total_itens} campeonatos (Modo: {desc_modo}{', FORÇADO' if forcar else ''}{tag_tor}).")

            fila_trabalho = queue.Queue()
            for k in chaves_selecionadas:
                fila_trabalho.put(k)

            processados = 0
            atualizados_com_sucesso = 0
            ignorados_por_estarem_atuais = 0
            lock_contador = threading.Lock()

            # ── WORKER TURBO HTTP ──────────────────────────────────────────
            session_turbo = self._criar_session_http(pool_size=nav_efetivos + 5) if motor == 'turbo' else None

            def _worker_turbo(worker_id: int):
                nonlocal processados, atualizados_com_sucesso, ignorados_por_estarem_atuais
                while not self.cancelar_execucao:
                    try:
                        chave = fila_trabalho.get_nowait()
                    except queue.Empty:
                        break

                    camp_info = self.catalogo.get(chave, {})
                    nome = camp_info.get('nome', chave)

                    if not forcar and self.esta_atualizado(camp_info, modo=modo, forcar=forcar, ano_filtro=ano_filtro):
                        with lock_contador:
                            ignorados_por_estarem_atuais += 1
                            processados += 1
                            pct = (processados / total_itens) * 100
                        if callback_log:
                            callback_log(f"⚡ [Worker {worker_id}] {nome} já está atualizado hoje. Poupando tempo!")
                        if callback_progresso:
                            callback_progresso(pct, f"Poupado: {nome}", worker_id)
                        fila_trabalho.task_done()
                        continue

                    # Rotaciona token de circuito Tor a cada campeonato
                    if tor_efetivo:
                        with self.lock_tor:
                            self.contador_circuito += 1

                    sucesso = self._raspar_campeonato_turbo(
                        chave, camp_info, session_turbo, modo, callback_log, worker_id,
                        ano_filtro=ano_filtro, forcar=forcar, usar_tor=tor_efetivo
                    )

                    with lock_contador:
                        processados += 1
                        if sucesso:
                            atualizados_com_sucesso += 1
                        pct = (processados / total_itens) * 100

                    if callback_progresso:
                        callback_progresso(pct, f"Processado: {nome}", worker_id)

                    fila_trabalho.task_done()

            # ── WORKER SELENIUM CHROME ─────────────────────────────────────
            def _worker_selenium(worker_id: int):
                nonlocal processados, atualizados_com_sucesso, ignorados_por_estarem_atuais
                driver = None
                try:
                    driver = self._criar_driver_headless(usar_tor=tor_efetivo, porta_tor=self.porta_socks_tor)
                    if callback_log:
                        callback_log(f"🤖 [Navegador {worker_id}] Pronto e aguardando tarefas...")

                    while not self.cancelar_execucao:
                        try:
                            chave = fila_trabalho.get_nowait()
                        except queue.Empty:
                            break

                        camp_info = self.catalogo.get(chave, {})
                        nome = camp_info.get('nome', chave)

                        if not forcar and self.esta_atualizado(camp_info, modo=modo, forcar=forcar, ano_filtro=ano_filtro):
                            with lock_contador:
                                ignorados_por_estarem_atuais += 1
                                processados += 1
                                pct = (processados / total_itens) * 100
                            if callback_log:
                                callback_log(f"⚡ [Navegador {worker_id}] {nome} já está atualizado hoje. Poupando tempo!")
                            if callback_progresso:
                                callback_progresso(pct, f"Poupado: {nome} (Atualizado)", worker_id)
                            fila_trabalho.task_done()
                            continue

                        sucesso = self._raspar_campeonato(
                            chave, camp_info, driver, modo, callback_log, worker_id,
                            ano_filtro=ano_filtro, forcar=forcar
                        )

                        with lock_contador:
                            processados += 1
                            if sucesso:
                                atualizados_com_sucesso += 1
                            pct = (processados / total_itens) * 100

                        if callback_progresso:
                            callback_progresso(pct, f"Processado: {nome}", worker_id)

                        fila_trabalho.task_done()

                except Exception as e:
                    if callback_log:
                        callback_log(f"❌ [Navegador {worker_id}] Erro: {e}")
                finally:
                    if driver:
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        if callback_log:
                            callback_log(f"🛑 [Navegador {worker_id}] Finalizado.")

            # Lança workers
            threads = []
            target_fn = _worker_turbo if motor == 'turbo' else _worker_selenium
            for w_id in range(nav_efetivos):
                t = threading.Thread(target=target_fn, args=(w_id + 1,), daemon=True)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            if callback_progresso:
                callback_progresso(100.0, "Concluído!", 0)

            msg_fim = f"🏁 Concluído! {atualizados_com_sucesso} atualizados, {ignorados_por_estarem_atuais} poupados por já estarem atualizados hoje."
            if callback_log:
                callback_log(msg_fim)

            if callback_concluido:
                callback_concluido(atualizados_com_sucesso, ignorados_por_estarem_atuais)

        threading.Thread(target=_tarefa_background, daemon=True).start()

    def cancelar(self):
        """Sinaliza parada de todos os workers em execução."""
        self.cancelar_execucao = True
