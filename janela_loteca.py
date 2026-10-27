"""
LOTECA ANALYTICS PRO — Interface Gráfica dos Concursos da Loteca (Caixa)
Exibição visual do concurso atual aberto para apostas (programação ativa),
simulador de volante interativo (cálculo oficial de duplos, triplos e custo da aposta),
navegação completa pelo histórico de concursos anteriores, colunas vencedoras,
rateio oficial de prêmios e exportação para CSV/TXT.
"""

import os
import queue
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from config import THEME, FONTS
from raspador_loteca import RaspadorLoteca


class JanelaLotecaConcursos(tk.Toplevel):
    """
    Janela para visualização e simulação dos concursos oficiais da Loteca (Caixa).
    - Exibe o CONCURSO ATUAL ABERTO PARA APOSTAS com volante interativo.
    - Permite alternar instantaneamente para os CONCURSOS ANTERIORES já apurados.
    - Calcula em tempo real o valor do volante conforme duplos e triplos marcados.
    - Permite copiar o volante formatado ou exportar histórico em lote para CSV.
    """

    def __init__(self, parent, raspador_loteca: RaspadorLoteca = None, ao_selecionar_jogo_callback = None):
        super().__init__(parent)
        self.raspador = raspador_loteca or RaspadorLoteca()
        self.ao_selecionar_jogo_callback = ao_selecionar_jogo_callback

        self.title("🎟️ LOTECA CAIXA — Concurso Atual Aberto & Histórico de Resultados")
        self.geometry("1220x840")
        self.minsize(1060, 700)
        self.configure(bg=THEME['bg_main'])
        #self.transient(parent)

        # Fila thread-safe para comunicação entre threads de raspagem e GUI
        self._fila_tarefas = queue.Queue()
        self._iniciar_loop_fila()

        # Estado dos concursos
        self.concurso_aberto_numero = None
        self.ultimo_apurado_numero = None
        self.concurso_exibido_numero = None
        self.concurso_dados = {}
        self.var_num_busca = tk.StringVar()

        # Estado do Volante de Apostas (Seq 1..14 -> set de colunas {'1', 'X', '2'})
        self.palpites_usuario = {i: set() for i in range(1, 15)}
        self.jogo_selecionado_seq = 1

        self._centralizar_janela(parent)
        self._construir_interface()
        self._carregar_concurso_inicial()

    def _iniciar_loop_fila(self):
        """Inicia polling de callbacks da thread secundária de forma 100% thread-safe."""
        self._processar_fila()

    def _processar_fila(self):
        """Processa todas as tarefas enviadas para a thread principal."""
        try:
            while True:
                fn, args = self._fila_tarefas.get_nowait()
                fn(*args)
        except queue.Empty:
            pass
        except Exception:
            pass
        try:
            if self.winfo_exists():
                self.after(40, self._processar_fila)
        except Exception:
            pass

    def _despachar_para_main(self, fn, *args):
        """Despacha com segurança da thread secundária para ser executado no loop do Tkinter."""
        self._fila_tarefas.put((fn, args))

    def _centralizar_janela(self, parent):
        try:
            self.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            w, h = 1220, 840
            x = px + max(0, (pw - w) // 2)
            y = py + max(0, (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _construir_interface(self):
        # ── 1. HEADER TOPO ────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=THEME['bg_header'], padx=18, pady=12)
        hdr.pack(fill='x')

        box_tit = tk.Frame(hdr, bg=THEME['bg_header'])
        box_tit.pack(side='left')

        tk.Label(
            box_tit, text="🎟️ LOTECA CAIXA — CONCURSO OFICIAL & VOLANTE DE APOSTAS",
            font=FONTS['title'], fg=THEME['text_primary'], bg=THEME['bg_header']
        ).pack(anchor='w')
        tk.Label(
            box_tit,
            text="Grade de 14 jogos oficiais da Caixa • Simulador de apostas com duplos e triplos • Histórico e rateio.",
            font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_header']
        ).pack(anchor='w')

        self.lbl_status_conexao = tk.Label(
            hdr, text="Conectando à API Caixa...",
            font=FONTS['badge'], fg=THEME['accent_blue'], bg=THEME['bg_subtle'],
            padx=12, pady=5
        )
        self.lbl_status_conexao.pack(side='right', padx=4)

        # ── 2. BARRA DE NAVEGAÇÃO & SELEÇÃO DE MODO ───────────────────────
        nav_bar = tk.Frame(self, bg=THEME['bg_card'], padx=14, pady=8, highlightbackground=THEME['border'], highlightthickness=1)
        nav_bar.pack(fill='x', padx=14, pady=(8, 4))

        # Botão Concurso Aberto (Destaque Principal)
        self.btn_modo_aberto = tk.Button(
            nav_bar, text="🟢 CONCURSO ABERTO P/ APOSTAR", command=self._ir_aberto,
            bg=THEME['win'], fg='#ffffff', font=FONTS['body_b'], relief='flat', padx=14, pady=4, cursor='hand2'
        )
        self.btn_modo_aberto.pack(side='left', padx=(0, 6))

        # Botão Concursos Anteriores (Histórico)
        self.btn_modo_apurado = tk.Button(
            nav_bar, text="📜 Concursos Anteriores (Apurados)", command=self._ir_ultimo_apurado,
            bg=THEME['bg_subtle'], fg=THEME['text_primary'], font=FONTS['body_b'], relief='flat', padx=12, pady=4, cursor='hand2'
        )
        self.btn_modo_apurado.pack(side='left', padx=(0, 14))

        # Separador visual
        tk.Frame(nav_bar, bg=THEME['border'], width=1, height=26).pack(side='left', padx=6, fill='y')

        btn_estilo = {
            'bg': THEME['bg_subtle'], 'fg': THEME['text_primary'], 'font': FONTS['badge'],
            'relief': 'flat', 'padx': 9, 'pady': 3, 'cursor': 'hand2'
        }

        self.btn_primeiro = tk.Button(nav_bar, text="⏮ Concurso 1", command=self._ir_primeiro, **btn_estilo)
        self.btn_primeiro.pack(side='left', padx=2)

        self.btn_anterior = tk.Button(nav_bar, text="◀ Anterior", command=self._ir_anterior, **btn_estilo)
        self.btn_anterior.pack(side='left', padx=2)

        # Caixa de busca direta por número
        box_busca = tk.Frame(nav_bar, bg=THEME['bg_card'])
        box_busca.pack(side='left', padx=10)

        tk.Label(box_busca, text="Ir p/ Concurso:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card']).pack(side='left', padx=3)
        self.ent_busca = tk.Entry(
            box_busca, textvariable=self.var_num_busca,
            width=7, font=FONTS['body_b'], bg=THEME['bg_main'], fg=THEME['text_primary'],
            insertbackground='#ffffff', relief='flat', highlightbackground=THEME['border'], highlightthickness=1
        )
        self.ent_busca.pack(side='left', padx=3)
        self.ent_busca.bind('<Return>', lambda e: self._buscar_concurso_digitado())

        btn_buscar = tk.Button(
            box_busca, text="🔍 Buscar", command=self._buscar_concurso_digitado,
            bg=THEME['accent_blue'], fg='#080c14', font=FONTS['badge'], relief='flat', padx=7, pady=2, cursor='hand2'
        )
        btn_buscar.pack(side='left', padx=2)

        self.btn_proximo = tk.Button(nav_bar, text="Próximo ▶", command=self._ir_proximo, **btn_estilo)
        self.btn_proximo.pack(side='left', padx=2)

        # Botão para exportação em massa para CSV
        btn_exportar = tk.Button(
            nav_bar, text="📥 Baixar Histórico em Lote (CSV)", command=self._abrir_modal_download_lote,
            bg=THEME['accent_purple'], fg='#ffffff', font=FONTS['badge'], relief='flat', padx=10, pady=4, cursor='hand2'
        )
        btn_exportar.pack(side='right', padx=2)

        # ── 3. CARDS DE KPIS DO CONCURSO ──────────────────────────────────
        self.cards_frame = tk.Frame(self, bg=THEME['bg_main'])
        self.cards_frame.pack(fill='x', padx=14, pady=4)

        kpis_defs = [
            ('concurso_data', 'CONCURSO / PRAZO', 'Consultando...', THEME['accent_blue']),
            ('status_concurso', 'STATUS DO CONCURSO', '-', THEME['win']),
            ('premio_destaque', 'PRÊMIO ESTIMADO (14 ACERTOS)', 'R$ -', THEME['win']),
            ('info_palpites', 'SEU VOLANTE DE APOSTAS', '0 de 14 palpites', THEME['draw']),
            ('custo_volante', 'CUSTO DA APOSTA', 'R$ 3,00 (Mínimo)', THEME['accent_purple']),
        ]

        self.kpi_labels = {}
        self.kpi_sublabels = {}
        for key, tit, def_val, cor in kpis_defs:
            card = tk.Frame(self.cards_frame, bg=THEME['bg_card'], padx=12, pady=7, highlightbackground=THEME['border'], highlightthickness=1)
            card.pack(side='left', fill='both', expand=True, padx=3)

            tk.Label(card, text=tit, font=FONTS['card_lbl'], fg=THEME['text_muted'], bg=THEME['bg_card']).pack(anchor='w')
            lbl_val = tk.Label(card, text=def_val, font=FONTS['header'], fg=cor, bg=THEME['bg_card'])
            lbl_val.pack(anchor='w', pady=(2, 0))
            self.kpi_labels[key] = lbl_val

        # ── 4. ÁREA CENTRAL: GRADE DOS 14 JOGOS ───────────────────────────
        tabela_frame = tk.Frame(self, bg=THEME['bg_card'], highlightbackground=THEME['border'], highlightthickness=1)
        tabela_frame.pack(fill='both', expand=True, padx=14, pady=4)

        tbl_hdr = tk.Frame(tabela_frame, bg=THEME['bg_subtle'], padx=10, pady=5)
        tbl_hdr.pack(fill='x')

        self.lbl_grade_tit = tk.Label(
            tbl_hdr, text="📋 GRADE OFICIAL DOS 14 JOGOS",
            font=FONTS['header'], fg=THEME['text_primary'], bg=THEME['bg_subtle']
        )
        self.lbl_grade_tit.pack(side='left')

        self.lbl_instrucao_tabela = tk.Label(
            tbl_hdr, text="💡 Clique nas colunas [ 1 ], [ X ], [ 2 ] para marcar palpites | Duplo clique para ver time",
            font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_subtle']
        )
        self.lbl_instrucao_tabela.pack(side='right')

        # Treeview da Grade de Jogos
        colunas = ('seq','placar', 'mandante','col1', 'colX', 'col2', 'visitante', 'dia_data', 'campeonato')
        self.tree_jogos = ttk.Treeview(
            tabela_frame, columns=colunas, show='headings', selectmode='browse', height=14
        )

        headers = [
            ('seq', 'Jogo', 60, 'center'),
            ('placar', 'Palpite / Placar', 110, 'center'),
            ('mandante', 'Mandante (Time 1)', 220, 'w'),
            ('col1', '[ 1 ] Casa', 75, 'center'),
            ('colX', '[ X ] Empate', 75, 'center'),
            ('col2', '[ 2 ] Fora', 75, 'center'),
            ('visitante', 'Visitante (Time 2)', 220, 'w'),
            ('dia_data', 'Data / Dia', 150, 'center'),
            ('campeonato', 'Competição', 180, 'w'),
        ]

        for col_id, col_name, width, align in headers:
            self.tree_jogos.heading(col_id, text=col_name)
            self.tree_jogos.column(col_id, width=width, anchor=align, stretch=(col_id in ('mandante', 'visitante', 'campeonato')))

        scroll_y = ttk.Scrollbar(tabela_frame, orient='vertical', command=self.tree_jogos.yview)
        self.tree_jogos.configure(yscrollcommand=scroll_y.set)

        self.tree_jogos.pack(side='left', fill='both', expand=True)
        scroll_y.pack(side='right', fill='y')

        # Eventos interativos
        self.tree_jogos.bind('<Button-1>', self._ao_clicar_treeview)
        self.tree_jogos.bind('<<TreeviewSelect>>', self._ao_selecionar_linha_treeview)
        self.tree_jogos.bind('<Double-1>', self._ao_duplo_clique_jogo)

        # Tags visuais de cores
        self.tree_jogos.tag_configure('palpite_seco', background='#0d1f2d', foreground='#38bdf8')
        self.tree_jogos.tag_configure('palpite_duplo', background='#0c261e', foreground='#34d399')
        self.tree_jogos.tag_configure('palpite_triplo', background='#24122b', foreground='#c084fc')
        self.tree_jogos.tag_configure('palpite_pendente', background=THEME['bg_card'], foreground=THEME['text_secondary'])

        self.tree_jogos.tag_configure('venceu_casa', background='#0c231a', foreground='#34d399')
        self.tree_jogos.tag_configure('venceu_fora', background='#241219', foreground='#fb7185')
        self.tree_jogos.tag_configure('empate', background='#221a0d', foreground='#fbbf24')
        self.tree_jogos.tag_configure('aguardando', background=THEME['bg_card'], foreground=THEME['text_primary'])

        # ── 5. TOOLBAR DE SIMULAÇÃO DE VOLANTE (PALPITES INTERATIVOS) ─────
        self.volante_frame = tk.Frame(self, bg=THEME['bg_card'], padx=14, pady=8, highlightbackground=THEME['border'], highlightthickness=1)
        self.volante_frame.pack(fill='x', padx=14, pady=(0, 4))

        # Linha 1: Botões de marcação rápida do jogo selecionado
        linha1 = tk.Frame(self.volante_frame, bg=THEME['bg_card'])
        linha1.pack(fill='x', pady=(0, 4))

        self.lbl_jogo_selecionado = tk.Label(
            linha1, text="🎮 Jogo Selecionado: Jogo 1",
            font=FONTS['body_b'], fg=THEME['accent_blue'], bg=THEME['bg_card']
        )
        self.lbl_jogo_selecionado.pack(side='left', padx=(0, 10))

        btn_pick_style = {'relief': 'flat', 'font': FONTS['badge'], 'padx': 8, 'pady': 2, 'cursor': 'hand2'}

        tk.Button(linha1, text="[ 1 ] Casa", command=lambda: self._marcar_jogo_atual('1'), bg='#065f46', fg='#34d399', **btn_pick_style).pack(side='left', padx=2)
        tk.Button(linha1, text="[ X ] Empate", command=lambda: self._marcar_jogo_atual('X'), bg='#78350f', fg='#fbbf24', **btn_pick_style).pack(side='left', padx=2)
        tk.Button(linha1, text="[ 2 ] Fora", command=lambda: self._marcar_jogo_atual('2'), bg='#881337', fg='#fb7185', **btn_pick_style).pack(side='left', padx=2)

        tk.Label(linha1, text="• Duplos:", font=FONTS['badge'], fg=THEME['text_muted'], bg=THEME['bg_card']).pack(side='left', padx=(6, 2))
        tk.Button(linha1, text="1X", command=lambda: self._definir_duplo_jogo_atual('1', 'X'), bg=THEME['bg_subtle'], fg=THEME['accent_blue'], **btn_pick_style).pack(side='left', padx=2)
        tk.Button(linha1, text="12", command=lambda: self._definir_duplo_jogo_atual('1', '2'), bg=THEME['bg_subtle'], fg=THEME['accent_blue'], **btn_pick_style).pack(side='left', padx=2)
        tk.Button(linha1, text="X2", command=lambda: self._definir_duplo_jogo_atual('X', '2'), bg=THEME['bg_subtle'], fg=THEME['accent_blue'], **btn_pick_style).pack(side='left', padx=2)

        tk.Label(linha1, text="• Triplo:", font=FONTS['badge'], fg=THEME['text_muted'], bg=THEME['bg_card']).pack(side='left', padx=(6, 2))
        tk.Button(linha1, text="1X2 Triplo", command=self._definir_triplo_jogo_atual, bg='#581c87', fg='#c084fc', **btn_pick_style).pack(side='left', padx=2)

        tk.Button(linha1, text="🧹 Limpar Jogo", command=self._limpar_jogo_atual, bg=THEME['bg_subtle'], fg=THEME['text_muted'], **btn_pick_style).pack(side='left', padx=(8, 2))

        # Linha 2: Ações globais do volante (Surpresinha, Copiar, Salvar)
        linha2 = tk.Frame(self.volante_frame, bg=THEME['bg_card'])
        linha2.pack(fill='x', pady=(2, 0))

        tk.Label(linha2, text="Ações do Cartão:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card']).pack(side='left', padx=(0, 6))

        tk.Button(
            linha2, text="🎲 Surpresinha (R$ 3,00)", command=lambda: self._gerar_surpresinha(qtd_duplos=1),
            bg=THEME['bg_subtle'], fg=THEME['win'], font=FONTS['badge'], relief='flat', padx=8, pady=2, cursor='hand2'
        ).pack(side='left', padx=2)

        tk.Button(
            linha2, text="🎲 Gerar 2 Duplos (R$ 6,00)", command=lambda: self._gerar_surpresinha(qtd_duplos=2),
            bg=THEME['bg_subtle'], fg=THEME['accent_blue'], font=FONTS['badge'], relief='flat', padx=8, pady=2, cursor='hand2'
        ).pack(side='left', padx=2)

        tk.Button(
            linha2, text="🧹 Limpar Volante", command=self._limpar_volante_inteiro,
            bg=THEME['bg_subtle'], fg=THEME['loss'], font=FONTS['badge'], relief='flat', padx=8, pady=2, cursor='hand2'
        ).pack(side='left', padx=2)

        self.btn_copiar_volante = tk.Button(
            linha2, text="📋 Copiar Volante", command=self._copiar_volante_clipboard,
            bg=THEME['accent_indigo'], fg='#ffffff', font=FONTS['badge'], relief='flat', padx=10, pady=2, cursor='hand2'
        )
        self.btn_copiar_volante.pack(side='right', padx=2)

        self.btn_salvar_volante = tk.Button(
            linha2, text="💾 Salvar Palpite (TXT)", command=self._salvar_volante_arquivo,
            bg=THEME['win'], fg='#ffffff', font=FONTS['badge'], relief='flat', padx=10, pady=2, cursor='hand2'
        )
        self.btn_salvar_volante.pack(side='right', padx=2)

        # ── 6. PAINEL INFERIOR: DETALHES DE PREMIAÇÃO E RATEIO ────────────
        bot_frame = tk.Frame(self, bg=THEME['bg_card'], padx=14, pady=8, highlightbackground=THEME['border'], highlightthickness=1)
        bot_frame.pack(fill='x', padx=14, pady=(0, 8))

        box_rateio = tk.Frame(bot_frame, bg=THEME['bg_card'])
        box_rateio.pack(side='left', fill='x', expand=True)

        self.lbl_rateio_tit = tk.Label(box_rateio, text="🏆 INFORMAÇÕES OFICIAIS:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card'])
        self.lbl_rateio_tit.pack(anchor='w')

        self.lbl_rateio_faixa1 = tk.Label(box_rateio, text="1º (14 acertos): -", font=FONTS['body_b'], fg=THEME['win'], bg=THEME['bg_card'])
        self.lbl_rateio_faixa1.pack(anchor='w', pady=(1, 0))

        self.lbl_rateio_faixa2 = tk.Label(box_rateio, text="2º (13 acertos): -", font=FONTS['body'], fg=THEME['text_primary'], bg=THEME['bg_card'])
        self.lbl_rateio_faixa2.pack(anchor='w')

        self.lbl_cidades_ganhadores = tk.Label(box_rateio, text="Cidades dos ganhadores: -", font=FONTS['subtitle'], fg=THEME['text_muted'], bg=THEME['bg_card'])
        self.lbl_cidades_ganhadores.pack(anchor='w', pady=(1, 0))

        # Estatísticas financeiras à direita
        box_fin = tk.Frame(bot_frame, bg=THEME['bg_card'])
        box_fin.pack(side='right')

        self.lbl_arrecadacao = tk.Label(box_fin, text="Arrecadação: -", font=FONTS['body'], fg=THEME['text_secondary'], bg=THEME['bg_card'])
        self.lbl_arrecadacao.pack(anchor='e')

        self.lbl_acumulado_esp = tk.Label(box_fin, text="Acumulado Especial: R$ -", font=FONTS['subtitle'], fg=THEME['accent_purple'], bg=THEME['bg_card'])
        self.lbl_acumulado_esp.pack(anchor='e')

        self.lbl_prox_info = tk.Label(box_fin, text="Próximo Concurso: -", font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_card'])
        self.lbl_prox_info.pack(anchor='e')

    # ── MÉTODOS DE CARREGAMENTO E NAVEGAÇÃO ────────────────────────────────
    def _carregar_concurso_inicial(self):
        """Carrega preferencialmente o concurso aberto para apostas em thread de fundo."""
        self.lbl_status_conexao.config(text="🔄 Consultando concurso atual...")

        def _tarefa():
            dados = self.raspador.obter_concurso(None)
            self._despachar_para_main(self._ao_receber_concurso, dados, True)

        threading.Thread(target=_tarefa, daemon=True).start()

    def _carregar_concurso_especifico(self, numero: int):
        """Carrega concurso específico por número."""
        self.lbl_status_conexao.config(text=f"🔄 Carregando Concurso {numero}...")

        def _tarefa():
            dados = self.raspador.obter_concurso(numero)
            self._despachar_para_main(self._ao_receber_concurso, dados, False)

        threading.Thread(target=_tarefa, daemon=True).start()

    def _ao_receber_concurso(self, dados: dict, is_inicial: bool = False):
        """Renderiza os dados do concurso recebido da Caixa na interface gráfica."""
        if 'erro' in dados:
            self.lbl_status_conexao.config(text="❌ Falha na conexão")
            messagebox.showerror("Erro Loteca", dados['erro'])
            return

        self.concurso_dados = dados
        num = dados.get('numero', 0)
        self.concurso_exibido_numero = num
        self.var_num_busca.set(str(num))

        eh_aberto = bool(dados.get('aberto_para_apostas', False))

        if eh_aberto:
            self.concurso_aberto_numero = num
            # Atualiza texto do botão do modo aberto com o número
            self.btn_modo_aberto.config(
                text=f"🟢 CONCURSO ABERTO ({num})", bg=THEME['win'], fg='#ffffff'
            )
            self.btn_modo_apurado.config(bg=THEME['bg_subtle'], fg=THEME['text_primary'])
            self.lbl_status_conexao.config(
                text=f"🟢 Concurso {num} ABERTO PARA APOSTAS", fg='#34d399', bg='#0c231a'
            )
        else:
            self.ultimo_apurado_numero = max(self.ultimo_apurado_numero or 0, num)
            self.btn_modo_aberto.config(
                text=f"🟢 Concurso Aberto ({self.concurso_aberto_numero or 'Novo'})",
                bg=THEME['bg_subtle'], fg='#34d399'
            )
            self.btn_modo_apurado.config(bg=THEME['accent_indigo'], fg='#ffffff')
            self.lbl_status_conexao.config(
                text=f"📜 Concurso {num} (Apurado)", fg=THEME['accent_blue'], bg=THEME['bg_subtle']
            )

        # 1. Atualização dos Cards de KPI
        if eh_aberto:
            periodo = dados.get('periodo_apostas', '') or f"Até {dados.get('data_fim_apostas', '')} às {dados.get('horario_fim_apostas', '')}"
            self.kpi_labels['concurso_data'].config(text=f"Conc. {num} • {periodo}")
            self.kpi_labels['status_concurso'].config(text="🟢 ABERTO PARA APOSTAS", fg=THEME['win'])
            est_premio = dados.get('estimativa_proximo', 0.0)
            self.kpi_labels['premio_destaque'].config(text=f"R$ {est_premio:,.2f}", fg=THEME['win'])
            self._atualizar_resumo_volante()
        else:
            dt_apuracao = dados.get('data_apuracao', '')
            self.kpi_labels['concurso_data'].config(text=f"Concurso {num} • {dt_apuracao}")

            if dados.get('acumulado', False):
                self.kpi_labels['status_concurso'].config(text="🔥 ACUMULOU!", fg=THEME['loss'])
            else:
                self.kpi_labels['status_concurso'].config(text="🏆 PREMIADO", fg=THEME['win'])

            premios = dados.get('premiacao', [])
            p14 = premios[0] if len(premios) > 0 else {}
            g14 = p14.get('ganhadores', 0)
            v14 = p14.get('valor_premio', 0.0)
            if g14 > 0:
                txt_p14 = f"R$ {v14:,.2f} ({g14} ganh.)"
            else:
                txt_p14 = "Sem acertador (Acumulou)"
            self.kpi_labels['premio_destaque'].config(text=txt_p14, fg=THEME['accent_blue'])

            col_resumo = dados.get('colunas_resumo', {})
            self.kpi_labels['info_palpites'].config(
                text=f"[1]: {col_resumo.get('1', 0)}  |  [X]: {col_resumo.get('X', 0)}  |  [2]: {col_resumo.get('2', 0)}",
                fg=THEME['text_primary']
            )

            arrec = dados.get('arrecadacao_total', 0.0)
            self.kpi_labels['custo_volante'].config(text=f"Arrecadado: R$ {arrec:,.2f}", fg=THEME['accent_purple'])

        # 2. Atualização da Grade dos 14 Jogos
        self.tree_jogos.delete(*self.tree_jogos.get_children())
        if eh_aberto:
            self.lbl_grade_tit.config(
                text=f"🟢 GRADE OFICIAL DE APOSTAS — CONCURSO {num} (Clique em [ 1 ], [ X ] ou [ 2 ] para apostar)"
            )
            self.lbl_instrucao_tabela.config(
                text="💡 Marque seus palpites diretamente nas colunas ou use a barra de atalhos abaixo"
            )
            self.volante_frame.pack(fill='x', padx=14, pady=(0, 4), before=self.children[list(self.children.keys())[-1]])
        else:
            self.lbl_grade_tit.config(
                text=f"📋 RESULTADOS OFICIAIS — CONCURSO {num} ({dados.get('data_apuracao', '')})"
            )
            self.lbl_instrucao_tabela.config(
                text="💡 Colunas vencedoras destacadas em verde/âmbar/rosa • Duplo clique para analisar time"
            )

        for j in dados.get('jogos', []):
            seq = j.get('seq')
            mandante = j.get('mandante_completo')
            visitante = j.get('visitante_completo')
            coluna = j.get('coluna')
            dia_data = f"{j.get('data_jogo', '')} ({j.get('dia_semana', '')})".strip()
            campeonato = j.get('campeonato', '') or 'Loteca'

            if eh_aberto:
                palpites = self.palpites_usuario.get(seq, set())
                col1_str = "[ 1 ]" if '1' in palpites else "-"
                colX_str = "[ X ]" if 'X' in palpites else "-"
                col2_str = "[ 2 ]" if '2' in palpites else "-"

                qtd = len(palpites)
                if qtd == 0:
                    status_palpite = "⚠️ Pendente"
                    tag = 'palpite_pendente'
                elif qtd == 1:
                    status_palpite = f"SECO: {''.join(sorted(palpites))}"
                    tag = 'palpite_seco'
                elif qtd == 2:
                    status_palpite = f"DUPLO: {''.join(sorted(palpites))}"
                    tag = 'palpite_duplo'
                else:
                    status_palpite = "TRIPLO: 1X2"
                    tag = 'palpite_triplo'

                valores = (
                    f"Jogo {seq}",status_palpite, mandante,col1_str, colX_str, col2_str, visitante, dia_data, campeonato
                )
            else:
                placar = j.get('placar_str', '- x -')
                col1_str = "●" if coluna == '1' else ""
                colX_str = "●" if coluna == 'X' else ""
                col2_str = "●" if coluna == '2' else ""

                tag = 'aguardando'
                if coluna == '1':
                    tag = 'venceu_casa'
                elif coluna == '2':
                    tag = 'venceu_fora'
                elif coluna == 'X':
                    tag = 'empate'

                valores = (
                    f"Jogo {seq}",placar, mandante,col1_str or "-", colX_str or "-", col2_str or "-", visitante, dia_data, campeonato
                )

            self.tree_jogos.insert('', 'end', iid=f"jogo_{seq}", values=valores, tags=(tag,))

        # Seleciona o primeiro jogo por padrão
        primeiro_item = f"jogo_{self.jogo_selecionado_seq}"
        if self.tree_jogos.exists(primeiro_item):
            self.tree_jogos.selection_set(primeiro_item)
            self._atualizar_label_jogo_selecionado(self.jogo_selecionado_seq)

        # 3. Painel Inferior de Detalhes
        if eh_aberto:
            dt_inicio = dados.get('data_inicio_apostas', '')
            dt_fim = dados.get('data_fim_apostas', '')
            hora_fim = dados.get('horario_fim_apostas', '15h00')
            self.lbl_rateio_tit.config(text="📅 CRONOGRAMA & REGRAS OFICIAIS:")
            self.lbl_rateio_faixa1.config(
                text=f"🕒 Período de Apostas: De {dt_inicio} até Sábado {dt_fim} às {hora_fim}"
            )
            est = dados.get('estimativa_proximo', 0.0)
            self.lbl_rateio_faixa2.config(
                text=f"💰 Estimativa de Prêmio: R$ {est:,.2f} para quem acertar os 14 jogos"
            )
            self.lbl_cidades_ganhadores.config(
                text="ℹ️ Aposta Mínima R$ 3,00 (dá direito a 1 DUPLO). Cada duplo adicional dobra o valor; cada triplo triplica."
            )
            self.lbl_arrecadacao.config(text="Status: Apostas Abertas em todo o Brasil")
            acum_esp = dados.get('acumulado_especial', 0.0)
            self.lbl_acumulado_esp.config(text=f"Acumulado Concurso Especial: R$ {acum_esp:,.2f}")
            dt_prox = dados.get('data_proximo', '')
            self.lbl_prox_info.config(text=f"Realização dos Jogos: {dt_prox or dt_fim}")
        else:
            self.lbl_rateio_tit.config(text="🏆 DETALHAMENTO DE PREMIAÇÃO (CAIXA):")
            premios = dados.get('premiacao', [])
            p14 = premios[0] if len(premios) > 0 else {}
            p13 = premios[1] if len(premios) > 1 else {}

            if p14:
                self.lbl_rateio_faixa1.config(
                    text=f"1º Prêmio (14 acertos): {p14.get('ganhadores', 0)} apostas ganhadoras — R$ {p14.get('valor_premio', 0.0):,.2f} cada"
                )
            if p13:
                self.lbl_rateio_faixa2.config(
                    text=f"2º Prêmio (13 acertos): {p13.get('ganhadores', 0)} apostas ganhadoras — R$ {p13.get('valor_premio', 0.0):,.2f} cada"
                )

            cidades = dados.get('cidades_ganhadores', [])
            if cidades:
                self.lbl_cidades_ganhadores.config(text=f"Cidades contempladas: {', '.join(cidades[:8])}")
            else:
                self.lbl_cidades_ganhadores.config(text="Nenhum ganhador com 14 acertos neste concurso.")

            arrec = dados.get('arrecadacao_total', 0.0)
            self.lbl_arrecadacao.config(text=f"Arrecadação Total: R$ {arrec:,.2f}")
            acum_esp = dados.get('acumulado_especial', 0.0)
            self.lbl_acumulado_esp.config(text=f"Acumulado Especial: R$ {acum_esp:,.2f}")
            prox_num = dados.get('proximo_concurso', num + 1)
            prox_dt = dados.get('data_proximo', '')
            self.lbl_prox_info.config(text=f"Próximo Concurso {prox_num} em {prox_dt}")

    # ── MÉTODOS DO SIMULADOR DE VOLANTE (INTERATIVIDADE) ───────────────────
    def _ao_clicar_treeview(self, event):
        """Ao clicar diretamente nas colunas [ 1 ], [ X ] ou [ 2 ], alterna o palpite do jogo."""
        eh_aberto = bool(self.concurso_dados.get('aberto_para_apostas', False))
        if not eh_aberto:
            return

        region = self.tree_jogos.identify_region(event.x, event.y)
        if region != 'cell':
            return

        col = self.tree_jogos.identify_column(event.x)
        item_id = self.tree_jogos.identify_row(event.y)
        if not item_id or not item_id.startswith('jogo_'):
            return

        seq = int(item_id.replace('jogo_', ''))
        self.jogo_selecionado_seq = seq
        self._atualizar_label_jogo_selecionado(seq)

        # Colunas na treeview: #3 é col1, #5 é colX, #6 é col2
        col_map = {'#4': '1', '#5': 'X', '#6': '2'}
        if col in col_map:
            escolha = col_map[col]
            self._alternar_palpite_jogo(seq, escolha)

    def _ao_selecionar_linha_treeview(self, event):
        """Quando o usuário clica em uma linha, atualiza o jogo em foco na barra de ferramentas."""
        sel = self.tree_jogos.selection()
        if sel and sel[0].startswith('jogo_'):
            seq = int(sel[0].replace('jogo_', ''))
            self.jogo_selecionado_seq = seq
            self._atualizar_label_jogo_selecionado(seq)

    def _atualizar_label_jogo_selecionado(self, seq: int):
        """Atualiza o texto que indica qual partida está sendo editada na toolbar."""
        jogos = self.concurso_dados.get('jogos', [])
        jogo = next((j for j in jogos if j.get('seq') == seq), None)
        if jogo:
            m = jogo.get('mandante_completo')
            v = jogo.get('visitante_completo')
            self.lbl_jogo_selecionado.config(text=f"🎮 Jogo {seq}: {m} x {v}")
        else:
            self.lbl_jogo_selecionado.config(text=f"🎮 Jogo {seq}")

    def _alternar_palpite_jogo(self, seq: int, coluna: str):
        """Adiciona ou remove uma coluna do palpite do jogo informado."""
        palpites = self.palpites_usuario.get(seq, set())
        if coluna in palpites:
            palpites.remove(coluna)
        else:
            palpites.add(coluna)
        self.palpites_usuario[seq] = palpites
        self._atualizar_linha_jogo(seq)
        self._atualizar_resumo_volante()

    def _marcar_jogo_atual(self, coluna: str):
        """Marca especificamente uma coluna no jogo em foco."""
        self._alternar_palpite_jogo(self.jogo_selecionado_seq, coluna)

    def _definir_duplo_jogo_atual(self, c1: str, c2: str):
        """Define o jogo selecionado como duplo exato (ex: 1X, 12, X2)."""
        self.palpites_usuario[self.jogo_selecionado_seq] = {c1, c2}
        self._atualizar_linha_jogo(self.jogo_selecionado_seq)
        self._atualizar_resumo_volante()

    def _definir_triplo_jogo_atual(self):
        """Define o jogo selecionado como Triplo (1X2)."""
        self.palpites_usuario[self.jogo_selecionado_seq] = {'1', 'X', '2'}
        self._atualizar_linha_jogo(self.jogo_selecionado_seq)
        self._atualizar_resumo_volante()

    def _limpar_jogo_atual(self):
        """Limpa as marcações do jogo em foco."""
        self.palpites_usuario[self.jogo_selecionado_seq] = set()
        self._atualizar_linha_jogo(self.jogo_selecionado_seq)
        self._atualizar_resumo_volante()

    def _atualizar_linha_jogo(self, seq: int):
        """Atualiza apenas a linha correspondente na Treeview sem redesenhar toda a grade."""
        item_id = f"jogo_{seq}"
        if not self.tree_jogos.exists(item_id):
            return

        jogos = self.concurso_dados.get('jogos', [])
        jogo = next((j for j in jogos if j.get('seq') == seq), None)
        if not jogo:
            return

        palpites = self.palpites_usuario.get(seq, set())
        col1_str = "[ 1 ]" if '1' in palpites else "-"
        colX_str = "[ X ]" if 'X' in palpites else "-"
        col2_str = "[ 2 ]" if '2' in palpites else "-"

        qtd = len(palpites)
        if qtd == 0:
            status_palpite = "⚠️ Pendente"
            tag = 'palpite_pendente'
        elif qtd == 1:
            status_palpite = f"SECO: {''.join(sorted(palpites))}"
            tag = 'palpite_seco'
        elif qtd == 2:
            status_palpite = f"DUPLO: {''.join(sorted(palpites))}"
            tag = 'palpite_duplo'
        else:
            status_palpite = "TRIPLO: 1X2"
            tag = 'palpite_triplo'

        dia_data = f"{jogo.get('data_jogo', '')} ({jogo.get('dia_semana', '')})".strip()
        campeonato = jogo.get('campeonato', '') or 'Loteca'

        novos_valores = (
            f"Jogo {seq}", status_palpite, jogo.get('mandante_completo'), col1_str, colX_str, col2_str,
            jogo.get('visitante_completo'), dia_data, campeonato
        )
        self.tree_jogos.item(item_id, values=novos_valores, tags=(tag,))

    def _atualizar_resumo_volante(self):
        """Calcula o total de secos, duplos, triplos, número de combinações e o custo oficial da aposta."""
        duplos = sum(1 for p in self.palpites_usuario.values() if len(p) == 2)
        triplos = sum(1 for p in self.palpites_usuario.values() if len(p) == 3)
        secos = sum(1 for p in self.palpites_usuario.values() if len(p) == 1)
        marcados = secos + duplos + triplos

        combinacoes = (2 ** duplos) * (3 ** triplos)
        # Regra oficial da Caixa: aposta simples/mínima custa R$ 3,00 (dá direito a 1 duplo ou 14 secos).
        # Acima de 2 combinações: combinacoes * R$ 1,50.
        if combinacoes <= 2:
            custo = 3.00
            txt_custo = "R$ 3,00 (Aposta Mínima)"
        else:
            custo = combinacoes * 1.50
            txt_custo = f"R$ {custo:,.2f} ({combinacoes} apostas)"

        self.kpi_labels['info_palpites'].config(
            text=f"{marcados}/14 jogos ({duplos}D • {triplos}T)", fg=THEME['win'] if marcados == 14 else THEME['draw']
        )
        self.kpi_labels['custo_volante'].config(text=txt_custo, fg=THEME['accent_purple'])

    def _gerar_surpresinha(self, qtd_duplos: int = 1):
        """Gera um palpite completo com duplos aleatórios e escolhas plausíveis nos 14 jogos."""
        jogos = self.concurso_dados.get('jogos', [])
        if not jogos or len(jogos) < 14:
            messagebox.showwarning("Aviso", "Não há 14 jogos carregados para gerar a aposta.")
            return

        indices_duplos = set(random.sample(range(1, 15), qtd_duplos))

        for i in range(1, 15):
            if i in indices_duplos:
                # Duplo aleatório
                opcoes_duplo = [{'1', 'X'}, {'1', '2'}, {'X', '2'}]
                self.palpites_usuario[i] = random.choice(opcoes_duplo)
            else:
                # Seco com peso ligeiro a favor do mandante (probabilidade estatística tradicional)
                escolha = random.choices(['1', 'X', '2'], weights=[0.45, 0.28, 0.27], k=1)[0]
                self.palpites_usuario[i] = {escolha}

            self._atualizar_linha_jogo(i)

        self._atualizar_resumo_volante()

    def _limpar_volante_inteiro(self):
        """Limpa todos os palpites do volante de apostas."""
        for i in range(1, 15):
            self.palpites_usuario[i] = set()
            self._atualizar_linha_jogo(i)
        self._atualizar_resumo_volante()

    def _formatar_texto_volante(self) -> str:
        """Gera texto organizado e legível com o cartão de apostas para impressão ou envio."""
        num = self.concurso_exibido_numero
        periodo = self.concurso_dados.get('periodo_apostas', '')
        est = self.concurso_dados.get('estimativa_proximo', 0.0)

        duplos = sum(1 for p in self.palpites_usuario.values() if len(p) == 2)
        triplos = sum(1 for p in self.palpites_usuario.values() if len(p) == 3)
        secos = sum(1 for p in self.palpites_usuario.values() if len(p) == 1)
        combinacoes = (2 ** duplos) * (3 ** triplos)
        custo = 3.00 if combinacoes <= 2 else combinacoes * 1.50

        linhas = [
            "==================================================",
            f"🎟️ LOTECA CAIXA — VOLANTE DE APOSTAS (CONCURSO {num})",
            "==================================================",
            f"Período: {periodo}",
            f"Estimativa de Prêmio: R$ {est:,.2f}",
            "--------------------------------------------------"
        ]

        jogos = self.concurso_dados.get('jogos', [])
        for seq in range(1, 15):
            jogo = next((j for j in jogos if j.get('seq') == seq), {})
            m = jogo.get('mandante_completo', f'Time 1 (Jogo {seq})')
            v = jogo.get('visitante_completo', f'Time 2 (Jogo {seq})')
            dt = f"{jogo.get('data_jogo', '')} {jogo.get('dia_semana', '')}".strip()

            cols = sorted(list(self.palpites_usuario.get(seq, set())))
            palpite_str = ' '.join(cols) if cols else "PENDENTE"
            tag_tipo = ""
            if len(cols) == 2:
                tag_tipo = " [DUPLO]"
            elif len(cols) == 3:
                tag_tipo = " [TRIPLO]"

            linhas.append(f"Jogo {seq:02d}: [ {palpite_str.ljust(5)} ] {m} x {v} ({dt}){tag_tipo}")

        linhas.extend([
            "--------------------------------------------------",
            "RESUMO DA APOSTA:",
            f"• Jogos Secos: {secos}",
            f"• Duplos: {duplos}",
            f"• Triplos: {triplos}",
            f"• Combinações / Apostas Simples: {combinacoes}",
            f"• Custo Total Estimado: R$ {custo:,.2f}",
            "==================================================",
            "Gerado por Loteca Analytics Pro"
        ])
        return "\n".join(linhas)

    def _copiar_volante_clipboard(self):
        """Copia os 14 palpites formatados para a área de transferência do sistema."""
        texto = self._formatar_texto_volante()
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.update()
        messagebox.showinfo("Copiado!", "Palpites do volante copiados com sucesso para a Área de Transferência!\nVocê pode colar no WhatsApp ou bloco de notas.")

    def _salvar_volante_arquivo(self):
        """Salva os 14 palpites em um arquivo .txt selecionado pelo usuário."""
        texto = self._formatar_texto_volante()
        num = self.concurso_exibido_numero
        nome_sugerido = f"loteca_volante_concurso_{num}.txt"

        caminho = filedialog.asksaveasfilename(
            parent=self, title="Salvar Palpite da Loteca",
            initialfile=nome_sugerido, defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
        )
        if caminho:
            try:
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write(texto)
                messagebox.showinfo("Sucesso", f"Palpite salvo com sucesso em:\n{caminho}")
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo:\n{str(e)}")

    # ── EVENTOS DE BOTÕES DE NAVEGAÇÃO ────────────────────────────────────
    def _ir_aberto(self):
        """Carrega e exibe diretamente o concurso aberto para apostas."""
        self.lbl_status_conexao.config(text="🔄 Carregando Concurso Aberto...")

        def _tarefa():
            dados = self.raspador.obter_programacao_atual()
            self._despachar_para_main(self._ao_receber_concurso, dados, False)

        threading.Thread(target=_tarefa, daemon=True).start()

    def _ir_ultimo_apurado(self):
        """Carrega e exibe o concurso mais recente já apurado."""
        self.lbl_status_conexao.config(text="🔄 Carregando último concurso apurado...")

        def _tarefa():
            dados = self.raspador.obter_ultimo_apurado()
            self._despachar_para_main(self._ao_receber_concurso, dados, False)

        threading.Thread(target=_tarefa, daemon=True).start()

    def _ir_primeiro(self):
        """Vai para o primeiro concurso histórico (Concurso 1)."""
        self._carregar_concurso_especifico(1)

    def _ir_anterior(self):
        """Navega para o concurso anterior."""
        if not self.concurso_exibido_numero:
            return

        eh_aberto = bool(self.concurso_dados.get('aberto_para_apostas', False))
        if eh_aberto:
            # Do aberto vai para o último apurado
            if self.ultimo_apurado_numero:
                self._carregar_concurso_especifico(self.ultimo_apurado_numero)
            else:
                self._carregar_concurso_especifico(self.concurso_exibido_numero - 1)
        elif self.concurso_exibido_numero > 1:
            self._carregar_concurso_especifico(self.concurso_exibido_numero - 1)

    def _ir_proximo(self):
        """Navega para o concurso seguinte ou avança para o concurso aberto."""
        if not self.concurso_exibido_numero:
            return

        # Se já estamos no concurso aberto, não há próximo ainda
        if self.concurso_dados.get('aberto_para_apostas', False):
            messagebox.showinfo("Aviso", "Você já está no concurso mais recente da Loteca (Aberto para Apostas).")
            return

        num_alvo = self.concurso_exibido_numero + 1
        if self.concurso_aberto_numero and num_alvo == self.concurso_aberto_numero:
            self._ir_aberto()
        else:
            self._carregar_concurso_especifico(num_alvo)

    def _buscar_concurso_digitado(self):
        """Busca o concurso digitado no campo de texto."""
        txt = self.var_num_busca.get().strip()
        try:
            num = int(txt)
            if num < 1:
                messagebox.showwarning("Aviso", "O número do concurso deve ser maior ou igual a 1.")
                return
            self._carregar_concurso_especifico(num)
        except ValueError:
            messagebox.showwarning("Aviso", "Digite um número inteiro de concurso válido.")

    def _ao_duplo_clique_jogo(self, event):
        """Ao clicar duas vezes em um jogo da grade, notifica callback ou exibe detalhes."""
        sel = self.tree_jogos.selection()
        if not sel:
            return
        item_id = sel[0]
        try:
            seq = int(item_id.replace("jogo_", ""))
            jogos = self.concurso_dados.get('jogos', [])
            jogo_sel = next((j for j in jogos if j.get('seq') == seq), None)
            if jogo_sel and self.ao_selecionar_jogo_callback:
                self.ao_selecionar_jogo_callback(jogo_sel)
            elif jogo_sel:
                m = jogo_sel.get('mandante_completo')
                v = jogo_sel.get('visitante_completo')
                p = jogo_sel.get('placar_str')
                col = jogo_sel.get('coluna')
                dt = jogo_sel.get('data_jogo')
                messagebox.showinfo(
                    f"Jogo {seq} — Loteca",
                    f"Confronto: {m} x {v}\nPlacar: {p}\nColuna Vencedora: [{col}]\nData: {dt}\nCompetição: {jogo_sel.get('campeonato')}"
                )
        except Exception:
            pass

    # ── MODAL DE DOWNLOAD DE LOTE DE CONCURSOS ─────────────────────────────
    def _abrir_modal_download_lote(self):
        """Abre janela modal para baixar histórico de múltiplos concursos em lote para CSV."""
        modal = tk.Toplevel(self)
        modal.title("📥 Baixar Histórico da Loteca para CSV")
        modal.geometry("540x360")
        modal.configure(bg=THEME['bg_card'])
        modal.transient(self)
        modal.grab_set()

        tk.Label(
            modal, text="📥 BAIXAR HISTÓRICO DE CONCURSOS (CAIXA)",
            font=FONTS['title'], fg=THEME['text_primary'], bg=THEME['bg_card'], padx=16, pady=12
        ).pack(anchor='w')

        desc_txt = (
            "Baixe múltiplos concursos e salve todos os 14 jogos de cada edição em um único arquivo CSV estruturado.\n"
            "Útil para alimentar bases de dados históricas e análises estatísticas."
        )
        tk.Label(
            modal, text=desc_txt, font=FONTS['subtitle'], fg=THEME['text_secondary'],
            bg=THEME['bg_card'], justify='left', padx=16
        ).pack(anchor='w')

        # Form de intervalo
        form_frame = tk.Frame(modal, bg=THEME['bg_card'], padx=16, pady=14)
        form_frame.pack(fill='x')

        num_max = self.ultimo_apurado_numero or (self.concurso_exibido_numero - 1 if self.concurso_dados.get('aberto_para_apostas') else self.concurso_exibido_numero) or 1270
        var_inicio = tk.StringVar(value=str(max(1, num_max - 50)))
        var_fim = tk.StringVar(value=str(num_max))

        tk.Label(form_frame, text="Concurso Inicial:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card']).grid(row=0, column=0, sticky='w', pady=4)
        ent_ini = tk.Entry(form_frame, textvariable=var_inicio, width=10, font=FONTS['body_b'], bg=THEME['bg_main'], fg=THEME['text_primary'], insertbackground='#ffffff')
        ent_ini.grid(row=0, column=1, sticky='w', padx=8, pady=4)

        tk.Label(form_frame, text="Concurso Final:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card']).grid(row=1, column=0, sticky='w', pady=4)
        ent_fim = tk.Entry(form_frame, textvariable=var_fim, width=10, font=FONTS['body_b'], bg=THEME['bg_main'], fg=THEME['text_primary'], insertbackground='#ffffff')
        ent_fim.grid(row=1, column=1, sticky='w', padx=8, pady=4)

        lbl_status_prog = tk.Label(modal, text="Pronto para iniciar.", font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_card'], padx=16)
        lbl_status_prog.pack(anchor='w', pady=(4, 2))

        prog_bar = ttk.Progressbar(modal, orient='horizontal', mode='determinate')
        prog_bar.pack(fill='x', padx=16, pady=4)

        cancelar_flag = False

        def _iniciar_download():
            nonlocal cancelar_flag
            try:
                ini = int(var_inicio.get().strip())
                fim = int(var_fim.get().strip())
                if ini > fim or ini < 1:
                    messagebox.showwarning("Aviso", "Intervalo inválido.")
                    return
            except ValueError:
                messagebox.showwarning("Aviso", "Digite números inteiros válidos.")
                return

            btn_dl.config(state='disabled')
            btn_cnc.config(state='normal')
            prog_bar['value'] = 0
            cancelar_flag = False

            def _prog_cb(pct, texto):
                def _up():
                    prog_bar['value'] = pct
                    lbl_status_prog.config(text=f"[{pct:.0f}%] {texto}")
                modal.after(0, _up)

            def _tarefa_dl():
                caminho_csv = os.path.join(self.raspador.PASTA_CACHE, 'dataset_loteca_historico.csv')
                total_salvo = self.raspador.baixar_historico_csv(
                    ini, fim, caminho_csv=caminho_csv,
                    callback_progresso=_prog_cb,
                    cancelar_fn=lambda: cancelar_flag
                )
                def _fim():
                    btn_dl.config(state='normal')
                    btn_cnc.config(state='disabled')
                    lbl_status_prog.config(text=f"🏁 Concluído! {total_salvo} concursos exportados.")
                    messagebox.showinfo(
                        "Download Concluído",
                        f"Histórico de {total_salvo} concursos salvo com sucesso em:\n{caminho_csv}"
                    )
                modal.after(0, _fim)

            threading.Thread(target=_tarefa_dl, daemon=True).start()

        def _cancelar():
            nonlocal cancelar_flag
            cancelar_flag = True
            btn_cnc.config(state='disabled')
            lbl_status_prog.config(text="Cancelando download...")

        btn_box = tk.Frame(modal, bg=THEME['bg_card'], padx=16, pady=12)
        btn_box.pack(fill='x')

        btn_dl = tk.Button(
            btn_box, text="🚀 Iniciar Download", command=_iniciar_download,
            bg=THEME['win'], fg='#ffffff', font=FONTS['body_b'], relief='flat', padx=14, pady=4, cursor='hand2'
        )
        btn_dl.pack(side='left', padx=(0, 8))

        btn_cnc = tk.Button(
            btn_box, text="Parar", command=_cancelar, state='disabled',
            bg=THEME['loss'], fg='#ffffff', font=FONTS['body'], relief='flat', padx=12, pady=4, cursor='hand2'
        )
        btn_cnc.pack(side='left', padx=(0, 8))

        tk.Button(
            btn_box, text="Fechar", command=modal.destroy,
            bg=THEME['bg_subtle'], fg=THEME['text_primary'], font=FONTS['body'], relief='flat', padx=12, pady=4, cursor='hand2'
        ).pack(side='left')
