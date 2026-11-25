"""
LOTECA ANALYTICS PRO — Janela Principal da Aplicação
Interface gráfica profissional com filtros dinâmicos, KPIs em tempo real,
ordenação de colunas, busca fonética/sem acento, carregamento direto do dataset
(atualizado automaticamente às 18h e 00h via GitHub Actions) e integração ao Importador O Gol 2.0.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import re
import pandas as pd # type: ignore

from config import THEME, FONTS, COMPETICOES, ABREV_COMPETICAO, _caminho
from utils import peso_ordem_fase, normalizar_texto
from gerenciador_dados import GerenciadorDados
from janela_raio_x import JanelaRaioXJogo
from raspador_gol import RaspadorGol
from janela_importacao import JanelaGerenciadorImportacao
from raspador_loteca import RaspadorLoteca
from janela_loteca import JanelaLotecaConcursos


class AutoScrollbar(ttk.Scrollbar):
    """Scrollbar que se oculta automaticamente quando todo o conteúdo cabe no espaço visível."""
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        super().set(lo, hi)


class AppAnaliseLoteca(tk.Tk):
    """
    Aplicação desktop principal do Loteca Analytics Pro.
    """

    def __init__(self):
        super().__init__()
        self.withdraw()  # Oculta a janela principal durante o splash
        self.title("Projeto Chronos ⚡")
        self.geometry("1420x880")
        self.minsize(1120, 720)
        self.configure(bg=THEME['bg_main'])

        self.gerenciador = GerenciadorDados()
        self.raspador = RaspadorGol()
        self.raspador_loteca = RaspadorLoteca()
        self.df_carregado = None
        self.fase_atual = None
        self.filtro_rapido = 'todos'
        self.sort_coluna = None
        self.sort_desc = False

        self._configurar_icone()
        self._centralizar_janela()
        self._configurar_estilos()
        self._construir_interface()
        self._configurar_atalhos()

        self._mostrar_splash_screen()

        # Carrega diretamente o dataset na abertura (sem rodar o raspador O Gol no startup;
        # a atualização automática ocorre às 18h e 00h via GitHub Actions)
        self.after(100, self._iniciar_carregamento)

    def _mostrar_splash_screen(self):
        """Exibe uma tela de carregamento animada chamada 'Projeto Chronos'."""
        self.splash = tk.Toplevel(self)
        self.splash.overrideredirect(True)
        self.splash.configure(bg=THEME['bg_main'])
        
        # Dimensões e centralização
        w, h = 600, 350
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.splash.geometry(f"{w}x{h}+{x}+{y}")
        self.splash.attributes('-topmost', True)
        
        # Borda no splash screen
        border_frame = tk.Frame(self.splash, bg=THEME['accent_indigo'], bd=2)
        border_frame.pack(fill='both', expand=True)
        
        inner_frame = tk.Frame(border_frame, bg=THEME['bg_main'])
        inner_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Conteúdo do Splash
        tk.Label(
            inner_frame, text="Projeto Chronos ⚡", 
            font=(FONTS['title'][0], 36, 'bold'), fg=THEME['text_primary'], bg=THEME['bg_main']
        ).pack(expand=True, pady=(70, 10))
        
        self.lbl_splash_status = tk.Label(
            inner_frame, text="Carregando jogos atuais...", 
            font=FONTS['subtitle'], fg=THEME['text_secondary'], bg=THEME['bg_main']
        )
        self.lbl_splash_status.pack(pady=10)
        
        self.progresso_splash = ttk.Progressbar(
            inner_frame, orient='horizontal', length=350, mode='indeterminate', style='Auto.Horizontal.TProgressbar'
        )
        self.progresso_splash.pack(pady=(0, 40))
        self.progresso_splash.start(10)

    def _configurar_icone(self):
        """Define o ícone oficial do Projeto Chronos na janela e barra de tarefas do sistema."""
        try:
            caminho_ico = _caminho("assets/icon.png")
            if os.path.exists(caminho_ico):
                self._app_icon = tk.PhotoImage(file=caminho_ico)
                self.iconphoto(True, self._app_icon)
        except Exception:
            pass

    def _centralizar_janela(self):
        """Centraliza a janela na tela do usuário."""
        try:
            self.update_idletasks()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            w, h = 1420, 880
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _configurar_atalhos(self):
        """Atalhos de teclado rápidos para agilidade operacional."""
        self.bind('<F5>', lambda e: self._iniciar_carregamento())
        self.bind('<Control-f>', lambda e: self.entry_busca.focus_set())
        self.bind('<Control-i>', lambda e: self._abrir_gerenciador_importacao())

    def _configurar_estilos(self):
        """Configura tema ttk escuro e estilos de Treeview."""
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure(
            'Dark.Treeview',
            background=THEME['bg_card'],
            foreground=THEME['text_primary'],
            fieldbackground=THEME['bg_card'],
            rowheight=32,
            font=FONTS['body'],
            borderwidth=0
        )
        style.configure(
            'Dark.Treeview.Heading',
            background=THEME['bg_header'],
            foreground=THEME['text_secondary'],
            font=FONTS['badge'],
            relief='flat',
            padding=[8, 6]
        )
        style.map(
            'Dark.Treeview',
            background=[('selected', THEME['accent_indigo'])],
            foreground=[('selected', '#ffffff')]
        )

        style.configure(
            'Dark.Vertical.TScrollbar',
            background=THEME['border'],
            troughcolor=THEME['bg_main'],
            borderwidth=0
        )
        style.configure(
            'Dark.Horizontal.TScrollbar',
            background=THEME['border'],
            troughcolor=THEME['bg_main'],
            borderwidth=0
        )

        style.configure(
            'Auto.Horizontal.TProgressbar',
            background=THEME['accent_blue'],
            troughcolor=THEME['bg_header'],
            borderwidth=0
        )

    def _construir_interface(self):
        # ── 1. HEADER SUPERIOR ───────────────────────────────────────────
        self.hdr = tk.Frame(self, bg=THEME['bg_header'], padx=18, pady=12)
        self.hdr.pack(fill='x', side='top')

        box_logo = tk.Frame(self.hdr, bg=THEME['bg_header'])
        box_logo.pack(side='left')
        tk.Label(
            box_logo, text="Projeto Chronos ⚡",
            font=FONTS['title'], fg=THEME['text_primary'], bg=THEME['bg_header']
        ).pack(anchor='w')
        tk.Label(
            box_logo,
            text="Acervo Histórico",
            font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_header']
        ).pack(anchor='w')

        # Controles Direita
        box_ctrl = tk.Frame(self.hdr, bg=THEME['bg_header'])
        box_ctrl.pack(side='right')

        # Botão Concursos da Loteca (Caixa)
        self.btn_loteca = tk.Button(
            box_ctrl, text="🎟️ Concursos da Loteca", command=self._abrir_janela_loteca,
            bg=THEME['accent_purple'], fg='#ffffff', font=FONTS['body_b'], relief='flat',
            activebackground='#9333ea', padx=12, pady=4, cursor='hand2'
        )
        self.btn_loteca.pack(side='left', padx=(0, 6))

        # Botão Importador O Gol
        self.btn_importador = tk.Button(
            box_ctrl, text="🌐 Importador O Gol", command=self._abrir_gerenciador_importacao,
            bg=THEME['accent_indigo'], fg='#ffffff', font=FONTS['body_b'], relief='flat',
            activebackground='#4f46e5', padx=12, pady=4, cursor='hand2'
        )
        self.btn_importador.pack(side='left', padx=(0, 10))

        # Torneio
        tk.Label(box_ctrl, text="Torneio:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_header']).pack(side='left', padx=(10, 4))
        self.var_competicao = tk.StringVar(value='Brasileirão Série A')
        
        # Obter competições dinamicamente mapeadas no disco
        comps_disponiveis = list(self.gerenciador.anos_por_competicao.keys())
        for c in COMPETICOES:
            if c not in comps_disponiveis:
                comps_disponiveis.append(c)

        self.cb_comp = ttk.Combobox(box_ctrl, textvariable=self.var_competicao, values=comps_disponiveis, state='readonly', width=22)
        self.cb_comp.pack(side='left', padx=(0, 10))
        self.cb_comp.bind('<<ComboboxSelected>>', lambda e: self._ao_mudar_competicao())

        # Temporada / Ano
        tk.Label(box_ctrl, text="Temporada:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_header']).pack(side='left', padx=(10, 4))
        self.var_ano = tk.StringVar(value='2026')
        anos_iniciais = [str(a) for a in self.gerenciador.anos_por_competicao.get('Brasileirão Série A', range(2026, 1970, -1))]
        self.cb_ano = ttk.Combobox(box_ctrl, textvariable=self.var_ano, values=anos_iniciais, state='readonly', width=8)
        self.cb_ano.pack(side='left', padx=(0, 10))
        self.cb_ano.bind('<<ComboboxSelected>>', lambda e: self._iniciar_carregamento())

        # Botão Carregar / Atualizar
        self.btn_carregar = tk.Button(
            box_ctrl, text="⚡ Atualizar", command=self._iniciar_carregamento,
            bg=THEME['win'], fg='#ffffff', font=FONTS['body_b'], relief='flat',
            activebackground='#059669', padx=12, pady=4, cursor='hand2'
        )
        self.btn_carregar.pack(side='left', padx=4)

        # ── 2. CARDS KPI ──────────────────────────────────────────────────
        self.kpi_bar = tk.Frame(self, bg=THEME['bg_main'], padx=14, pady=8)
        self.kpi_bar.pack(fill='x')

        self.kpis = {}
        
        def _on_enter_kpi(e, fr):
            fr.config(bg=THEME['bg_card_alt'], highlightbackground=THEME['accent_indigo'])
            for w in fr.winfo_children():
                w.config(bg=THEME['bg_card_alt'])
                
        def _on_leave_kpi(e, fr):
            fr.config(bg=THEME['bg_card'], highlightbackground=THEME['border'])
            for w in fr.winfo_children():
                w.config(bg=THEME['bg_card'])

        kpi_defs = [
            ('jogos',   '🏟️ TOTAL DE JOGOS', '0',   THEME['accent_blue']),
            ('gols',    '⚽ MÉDIA DE GOLS',  '0.0', THEME['accent_indigo']),
            ('vit_m',   '🟢 VITÓRIAS CASA',  '0%',  THEME['win']),
            ('emp',     '🟡 EMPATES',         '0%',  THEME['draw']),
            ('vit_v',   '🔴 VITÓRIAS FORA',  '0%',  THEME['loss']),
            ('alertas', '🏆 ALERTA DE COPA', '0',   THEME['tag_cup_alert'])
        ]
        for key, title, def_val, cor in kpi_defs:
            f = tk.Frame(
                self.kpi_bar, bg=THEME['bg_card'],
                highlightbackground=THEME['border'], highlightthickness=1, padx=12, pady=6, cursor="hand2"
            )
            f.pack(side='left', fill='both', expand=True, padx=4)
            lbl_tit = tk.Label(f, text=title, font=FONTS['card_lbl'], fg=THEME['text_muted'], bg=THEME['bg_card'])
            lbl_tit.pack(anchor='w')
            lbl_val = tk.Label(f, text=def_val, font=FONTS['card_kpi'], fg=cor, bg=THEME['bg_card'])
            lbl_val.pack(anchor='w')
            self.kpis[key] = lbl_val
            
            f.bind("<Enter>", lambda e, fr=f: _on_enter_kpi(e, fr))
            f.bind("<Leave>", lambda e, fr=f: _on_leave_kpi(e, fr))
            lbl_tit.bind("<Enter>", lambda e, fr=f: _on_enter_kpi(e, fr))
            lbl_tit.bind("<Leave>", lambda e, fr=f: _on_leave_kpi(e, fr))
            lbl_val.bind("<Enter>", lambda e, fr=f: _on_enter_kpi(e, fr))
            lbl_val.bind("<Leave>", lambda e, fr=f: _on_leave_kpi(e, fr))

        # ── 3. BARRA DE STATUS & BARRA DE PROGRESSO EM SEGUNDO PLANO ──────
        # Empacotada com side='bottom' antes dos painéis verticais para garantir
        # que ocupe toda a base da janela (eixo X) de ponta a ponta, liberando a área
        # central e a tabela para se expandirem livremente até a borda direita.
        self.status_bar = tk.Frame(self, bg=THEME['bg_header'], padx=14, pady=4)
        self.status_bar.pack(fill='x', side='bottom')

        self.lbl_status = tk.Label(
            self.status_bar, text="Iniciando acervo histórico...",
            font=FONTS['subtitle'], fg=THEME['text_secondary'], bg=THEME['bg_header']
        )
        self.lbl_status.pack(side='left')

        # Painel de progresso de importação em segundo plano
        self.box_prog_bg = tk.Frame(self.status_bar, bg=THEME['bg_header'])
        self.box_prog_bg.pack(side='right', padx=10)

        self.lbl_scraping_info = tk.Label(
            self.box_prog_bg, text="", font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_header']
        )
        self.lbl_scraping_info.pack(side='left', padx=6)

        self.progress_bar_bg = ttk.Progressbar(
            self.box_prog_bg, orient='horizontal', length=160, mode='determinate', style='Auto.Horizontal.TProgressbar'
        )
        self.progress_bar_bg.pack(side='left')
        self.box_prog_bg.pack_forget()

        # ── 4. PAINEL LATERAL ESQUERDO (FASES / RODADAS) ──────────────────
        self.sidebar = tk.Frame(self, bg=THEME['bg_card'], width=240, highlightbackground=THEME['border'], highlightthickness=1)
        self.sidebar.pack(side='left', fill='y', padx=(14, 0), pady=(0, 6))
        self.sidebar.pack_propagate(False)

        top_side = tk.Frame(self.sidebar, bg=THEME['bg_header'], padx=10, pady=8)
        top_side.pack(fill='x')
        self.lbl_sidebar_tit = tk.Label(top_side, text="RODADAS / FASES", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_header'])
        self.lbl_sidebar_tit.pack(side='left')

        self.listbox_fases = tk.Listbox(
            self.sidebar, bg=THEME['bg_card'], fg=THEME['text_primary'],
            selectbackground=THEME['accent_indigo'], selectforeground='#ffffff',
            activestyle='none', highlightthickness=0, relief='flat', font=FONTS['body_b'], cursor='hand2'
        )
        self.listbox_fases.pack(fill='both', expand=True, padx=6, pady=6)
        self.listbox_fases.bind('<<ListboxSelect>>', self._ao_selecionar_fase)

        # ── 5. ÁREA CENTRAL ───────────────────────────────────────────────
        self.area_central = tk.Frame(self, bg=THEME['bg_main'])
        self.area_central.pack(side='left', fill='both', expand=True, padx=(10, 14), pady=(0, 6))

        box_topo_tabela = tk.Frame(self.area_central, bg=THEME['bg_main'], pady=6)
        box_topo_tabela.pack(fill='x')

        self.lbl_fase_ativa = tk.Label(
            box_topo_tabela, text="Selecione uma fase...",
            font=FONTS['header'], fg=THEME['text_primary'], bg=THEME['bg_main']
        )
        self.lbl_fase_ativa.pack(side='left')

        # Filtros rápidos em botões
        box_filtros_rapidos = tk.Frame(box_topo_tabela, bg=THEME['bg_main'])
        box_filtros_rapidos.pack(side='left', padx=16)

        self.btn_f_todos = tk.Button(
            box_filtros_rapidos, text="Todos", command=lambda: self._set_filtro_rapido('todos'),
            bg=THEME['accent_indigo'], fg='#ffffff', font=FONTS['badge'], relief='flat', padx=8, pady=2, cursor='hand2'
        )
        self.btn_f_todos.pack(side='left', padx=2)

        self.btn_f_copas = tk.Button(
            box_filtros_rapidos, text="🔥 Copas", command=lambda: self._set_filtro_rapido('copa'),
            bg=THEME['bg_card'], fg=THEME['text_secondary'], font=FONTS['badge'], relief='flat', padx=8, pady=2, cursor='hand2'
        )
        self.btn_f_copas.pack(side='left', padx=2)

        self.btn_f_classicos = tk.Button(
            box_filtros_rapidos, text="⚡ Clássicos", command=lambda: self._set_filtro_rapido('classico'),
            bg=THEME['bg_card'], fg=THEME['text_secondary'], font=FONTS['badge'], relief='flat', padx=8, pady=2, cursor='hand2'
        )
        self.btn_f_classicos.pack(side='left', padx=2)

        # Campo de busca fonética/sem acento
        box_filtro = tk.Frame(box_topo_tabela, bg=THEME['bg_card'], highlightbackground=THEME['border'], highlightthickness=1, padx=6, pady=2)
        box_filtro.pack(side='right')
        tk.Label(box_filtro, text="🔍", bg=THEME['bg_card']).pack(side='left')
        self.var_busca = tk.StringVar()
        self.var_busca.trace_add('write', lambda *_: self._filtrar_jogos_tabela())
        self.entry_busca = tk.Entry(
            box_filtro, textvariable=self.var_busca, font=FONTS['body'], bg=THEME['bg_card'],
            fg=THEME['text_primary'], insertbackground='#ffffff', relief='flat', width=20
        )
        self.entry_busca.pack(side='left', padx=4)
        tk.Button(
            box_filtro, text="✕", font=('Segoe UI', 8), bg=THEME['bg_card'], fg=THEME['text_muted'],
            relief='flat', command=lambda: self.var_busca.set(''), cursor='hand2'
        ).pack(side='left')

        # Tabela Principal
        table_frame = tk.Frame(self.area_central, bg=THEME['bg_card'], highlightbackground=THEME['border'], highlightthickness=1)
        table_frame.pack(fill='both', expand=True)

        self.cols = (
            'Torneio', 'Fase/Rodada', 'Data', 'Mandante', 'Placar', 'Visitante',
            'Alerta Copa', 'Momentum', 'H2H %', 'Desespero', 'Clássico', 'Favorito IA'
        )
        self.tree = ttk.Treeview(table_frame, columns=self.cols, show='headings', style='Dark.Treeview', selectmode='browse')

        col_configs = {
            'Torneio':     {'width': 115, 'minwidth': 95,  'stretch': True},
            'Fase/Rodada': {'width': 125, 'minwidth': 100, 'stretch': True},
            'Data':        {'width': 80,  'minwidth': 75,  'stretch': False},
            'Mandante':    {'width': 160, 'minwidth': 125, 'stretch': True},
            'Placar':      {'width': 70,  'minwidth': 60,  'stretch': False},
            'Visitante':   {'width': 160, 'minwidth': 125, 'stretch': True},
            'Alerta Copa': {'width': 115, 'minwidth': 95,  'stretch': True},
            'Momentum':    {'width': 90,  'minwidth': 80,  'stretch': False},
            'H2H %':       {'width': 80,  'minwidth': 75,  'stretch': False},
            'Desespero':   {'width': 85,  'minwidth': 75,  'stretch': False},
            'Clássico':    {'width': 75,  'minwidth': 70,  'stretch': False},
            'Favorito IA': {'width': 130, 'minwidth': 110, 'stretch': True},
        }
        for c in self.cols:
            cfg = col_configs.get(c, {'width': 100, 'minwidth': 80, 'stretch': True})
            self.tree.heading(c, text=c, command=lambda col=c: self._ordenar_por_coluna(col))
            self.tree.column(c, width=cfg['width'], minwidth=cfg['minwidth'], stretch=cfg['stretch'], anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview, style='Dark.Vertical.TScrollbar')
        hsb = AutoScrollbar(table_frame, orient='horizontal', command=self.tree.xview, style='Dark.Horizontal.TScrollbar')
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.bind('<Double-1>', self._ao_dar_duplo_clique)
        self.tree.bind('<Return>', self._ao_dar_duplo_clique)

        # Dica / Ajuda
        dica_bar = tk.Frame(self.area_central, bg=THEME['bg_main'], pady=4)
        dica_bar.pack(fill='x')
        tk.Label(
            dica_bar,
            text="💡 Duplo clique em qualquer partida para abrir o Raio-X completo • Clique nos cabeçalhos para ordenar • Ctrl+F busca time",
            font=FONTS['subtitle'], fg=THEME['text_muted'], bg=THEME['bg_main']
        ).pack(side='left')

    # ── MÉTODOS DA LOTECA (CAIXA) & IMPORTADOR ────────────────────────────
    def _abrir_janela_loteca(self):
        """Abre a modal dos concursos da Loteca (Caixa) com grade e histórico."""
        JanelaLotecaConcursos(self, self.raspador_loteca, ao_selecionar_jogo_callback=self._ao_selecionar_jogo_loteca)

    def _ao_selecionar_jogo_loteca(self, jogo_loteca: dict):
        """Filtra o time selecionado da grade da Loteca no dashboard principal e abre o Raio-X."""
        m_loteca = jogo_loteca.get('mandante_completo') or jogo_loteca.get('mandante', '')
        v_loteca = jogo_loteca.get('visitante_completo') or jogo_loteca.get('visitante', '')
        m = jogo_loteca.get('mandante')
        if m:
            self.var_busca.set(m)

        # Encontrar a janela da loteca para usar como parent do Raio-X
        parent_win = self
        for widget in self.winfo_children():
            if isinstance(widget, tk.Toplevel) and "LOTECA" in widget.title():
                parent_win = widget
                break

        if self.df_carregado is not None and not self.df_carregado.empty:
            df = self.df_carregado
            m_norm = normalizar_texto(m_loteca).split(' - ')[0]
            v_norm = normalizar_texto(v_loteca).split(' - ')[0]

            def buscar_time(nome_time, serie):
                nome_base = nome_time.replace(" fc", "").replace(" ec", "").replace(" pr", "").strip()
                p1 = nome_base.split()[0] if nome_base else ""
                mask = serie.astype(str).apply(normalizar_texto).str.contains(nome_base, regex=False)
                if not mask.any() and len(p1) >= 4:
                    mask = serie.astype(str).apply(normalizar_texto).str.contains(p1, regex=False)
                return mask

            mask_m = buscar_time(m_norm, df['Time da Casa'])
            mask_v = buscar_time(v_norm, df['Time Visitante'])
            match_df = df[mask_m & mask_v]

            if not match_df.empty:
                if 'Data_Datetime' in match_df.columns:
                    match_df = match_df.sort_values(by='Data_Datetime', ascending=False)
                jogo_row = match_df.iloc[0]
                rx = JanelaRaioXJogo(parent_win, jogo_row, self.gerenciador)
                rx.lift()
                rx.focus_force()
            else:
                match_df_m = df[mask_m]
                if not match_df_m.empty:
                    if 'Data_Datetime' in match_df_m.columns:
                        match_df_m = match_df_m.sort_values(by='Data_Datetime', ascending=False)
                    jogo_row = match_df_m.iloc[0]
                    messagebox.showinfo("Raio-X Aproximado", f"Partida exata não encontrada.\nExibindo último jogo do mandante ({m_loteca}).", parent=parent_win)
                    rx = JanelaRaioXJogo(parent_win, jogo_row, self.gerenciador)
                    rx.lift()
                    rx.focus_force()
                else:
                    messagebox.showinfo("Raio-X Indisponível", f"Jogo {m_loteca} x {v_loteca} não encontrado na base.\nCertifique-se de carregar os dados no menu 'Competição' principal.", parent=parent_win)
        else:
            messagebox.showinfo("Sem Dados", "Nenhum dado carregado na janela principal.\nPor favor, selecione uma competição (ex: 'Todas as Competições') e carregue os dados antes de abrir o Raio-X.", parent=parent_win)

    def _abrir_gerenciador_importacao(self):
        """Abre a modal de gerenciamento de campeonatos e importação O Gol."""
        JanelaGerenciadorImportacao(self, self.raspador, ao_concluir_callback=self._ao_concluir_importacao)

    def _ao_concluir_importacao(self, atualizados: int, poupados: int):
        """Atualiza a base interna e a interface quando uma importação termina."""
        self.gerenciador.invalidar_cache()
        # Atualiza combobox de competições com novos estaduais se houver
        comps = list(self.gerenciador.anos_por_competicao.keys())
        self.cb_comp.config(values=comps)
        self._iniciar_carregamento()

    def _auto_atualizar_startup(self):
        """Carrega diretamente o dataset local sem acionar o raspador O Gol na abertura do app."""
        self._iniciar_carregamento()

    # ── MÉTODOS DE CONTROLE DA TABELA E INTERFACE ──────────────────────────
    def _set_filtro_rapido(self, tipo: str):
        """Alterna botões de filtros rápidos."""
        self.filtro_rapido = tipo
        botoes = [
            (self.btn_f_todos, 'todos'),
            (self.btn_f_copas, 'copa'),
            (self.btn_f_classicos, 'classico'),
        ]
        for btn, t in botoes:
            if t == tipo:
                btn.config(bg=THEME['accent_indigo'], fg='#ffffff')
            else:
                btn.config(bg=THEME['bg_card'], fg=THEME['text_secondary'])

        self._filtrar_jogos_tabela()

    def _ao_mudar_competicao(self):
        """Atualiza a lista de anos conforme o torneio selecionado."""
        comp = self.var_competicao.get()
        anos_comp = self.gerenciador.anos_por_competicao.get(comp, [])
        if not anos_comp:
            anos_comp = list(range(2026, 1970, -1))

        str_anos = [str(a) for a in anos_comp]
        self.cb_ano.config(values=str_anos)

        ano_atual = self.var_ano.get()
        if ano_atual not in str_anos and str_anos:
            self.var_ano.set(str_anos[0])
            self._iniciar_carregamento()
        else:
            self._filtrar_competicao()

    def _iniciar_carregamento(self):
        """Inicia carregamento dos dados em thread separada."""
        ano_str = self.var_ano.get()
        try:
            ano = int(ano_str)
        except ValueError:
            messagebox.showerror("Erro", "Ano inválido selecionado!")
            return

        self.btn_carregar.config(state='disabled', text="⏳ Carregando...")
        self.lbl_status.config(text=f"Processando acervo multicompetições para a temporada {ano}...")

        threading.Thread(target=self._tarefa_carregar_dados, args=(ano,), daemon=True).start()

    def _tarefa_carregar_dados(self, ano: int):
        try:
            df = self.gerenciador.carregar_ano_completo(ano)
            self.after(0, self._concluir_carregamento, ano, df)
        except Exception as e:
            self.after(0, self._falha_carregamento, str(e))

    def _falha_carregamento(self, erro_msg: str):
        if hasattr(self, 'splash') and self.splash.winfo_exists():
            self.progresso_splash.stop()
            self.splash.destroy()
            self.deiconify()
            self.lift()
        self.btn_carregar.config(state='normal', text="⚡ Atualizar")
        self.lbl_status.config(text=f"❌ Erro: {erro_msg}")
        messagebox.showerror("Erro ao Carregar Temporada", erro_msg)

    def _concluir_carregamento(self, ano: int, df: pd.DataFrame):
        self.df_carregado = df
        self.btn_carregar.config(state='normal', text="⚡ Atualizar")
        total_jogos = len(df)
        self.lbl_status.config(text=f"✅ Temporada {ano} carregada com sucesso! Total de {total_jogos} jogos disponíveis.")
        self._filtrar_competicao()

        if hasattr(self, 'splash') and self.splash.winfo_exists():
            self.progresso_splash.stop()
            self.splash.destroy()
            self.deiconify()
            self.lift()

    def _filtrar_competicao(self):
        """Filtra as fases disponíveis com base na competição ativa."""
        if self.df_carregado is None:
            return

        comp = self.var_competicao.get()
        df = self.df_carregado

        if comp == 'Estaduais (Todos)':
            df_comp = df[df['Competicao'].str.contains('Estadual|Campeonato Paulista|Campeonato Carioca|Campeonato Mineiro|Campeonato Gaúcho|Campeonato Baiano|Campeonato Goiano|Campeonato Pernambucano|Campeonato Capixaba', na=False)]
        elif comp != 'Todas as Competições':
            df_comp = df[df['Competicao'] == comp]
        else:
            df_comp = df

        self.listbox_fases.delete(0, 'end')
        fases_unicas = df_comp['Fase_Formatada'].dropna().unique()
        fases_ordenadas = sorted(fases_unicas, key=peso_ordem_fase)

        for f in fases_ordenadas:
            n_jogos = len(df_comp[df_comp['Fase_Formatada'] == f])
            self.listbox_fases.insert('end', f" {f} ({n_jogos})")

        if fases_ordenadas:
            fase_atual = fases_ordenadas[-1]
            if 'Data_Datetime' in df_comp.columns:
                agora = pd.Timestamp.now().normalize()
                df_valid = df_comp.dropna(subset=['Data_Datetime']).copy()
                if not df_valid.empty:
                    df_valid['Data_Norm'] = pd.to_datetime(df_valid['Data_Datetime']).dt.normalize()
                    df_futuro = df_valid[df_valid['Data_Norm'] >= agora]
                    if not df_futuro.empty:
                        idx_proximo = df_futuro['Data_Norm'].idxmin()
                        fase_atual = df_futuro.loc[idx_proximo, 'Fase_Formatada']
            
            idx_selecionado = fases_ordenadas.index(fase_atual) if fase_atual in fases_ordenadas else 0
            self.listbox_fases.selection_set(idx_selecionado)
            self.listbox_fases.see(idx_selecionado)
            self._exibir_fase(fase_atual)
        else:
            self.tree.delete(*self.tree.get_children())
            self.lbl_fase_ativa.config(text=f"Nenhum jogo cadastrado em {comp} no ano {self.var_ano.get()}.")
            self._atualizar_kpis(pd.DataFrame())

    def _ao_selecionar_fase(self, _=None):
        sel = self.listbox_fases.curselection()
        if not sel or self.df_carregado is None:
            return
        idx = sel[0]
        texto_item = self.listbox_fases.get(idx)
        nome_fase = re.sub(r'\s*\(\d+\)$', '', texto_item).strip()
        self._exibir_fase(nome_fase)

    def _exibir_fase(self, nome_fase: str):
        self.fase_atual = nome_fase
        comp = self.var_competicao.get()
        df = self.df_carregado
        if comp == 'Estaduais (Todos)':
            df = df[df['Competicao'].str.contains('Estadual|Campeonato Paulista|Campeonato Carioca|Campeonato Mineiro|Campeonato Gaúcho|Campeonato Baiano|Campeonato Goiano|Campeonato Pernambucano|Campeonato Capixaba', na=False)]
        elif comp != 'Todas as Competições':
            df = df[df['Competicao'] == comp]

        df_fase = df[df['Fase_Formatada'] == nome_fase]
        self.lbl_fase_ativa.config(text=f"{comp} ({self.var_ano.get()}) │ {nome_fase} ({len(df_fase)} partidas)")

        self._atualizar_kpis(df_fase)
        self._filtrar_jogos_tabela()

    def _atualizar_kpis(self, df_fase: pd.DataFrame):
        tot = len(df_fase)
        if tot == 0:
            for k in self.kpis:
                self.kpis[k].config(text='-')
            return

        gm = df_fase['Gols_Mandante'].sum()
        gv = df_fase['Gols_Visitante'].sum()
        media_gols = (gm + gv) / tot if tot > 0 else 0

        vit_m = (df_fase['Gols_Mandante'] > df_fase['Gols_Visitante']).sum()
        emp   = (df_fase['Gols_Mandante'] == df_fase['Gols_Visitante']).sum()
        vit_v = (df_fase['Gols_Mandante'] < df_fase['Gols_Visitante']).sum()

        alertas_copa = (df_fase['Alerta_Copa'] != '-').sum() if 'Alerta_Copa' in df_fase.columns else 0

        self.kpis['jogos'].config(text=str(tot))
        self.kpis['gols'].config(text=f"{media_gols:.2f}")
        self.kpis['vit_m'].config(text=f"{(vit_m/tot):.0%}")
        self.kpis['emp'].config(text=f"{(emp/tot):.0%}")
        self.kpis['vit_v'].config(text=f"{(vit_v/tot):.0%}")
        self.kpis['alertas'].config(text=str(alertas_copa))

    def _ordenar_por_coluna(self, coluna: str):
        """Alterna ordenação da coluna clicada."""
        if self.sort_coluna == coluna:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_coluna = coluna
            self.sort_desc = False

        for c in self.cols:
            txt = c
            if c == self.sort_coluna:
                txt += " ▼" if self.sort_desc else " ▲"
            self.tree.heading(c, text=txt)

        self._filtrar_jogos_tabela()

    def _filtrar_jogos_tabela(self):
        """Filtra, ordena e renderiza os jogos no Treeview."""
        if not self.fase_atual or self.df_carregado is None:
            return

        comp = self.var_competicao.get()
        df = self.df_carregado
        if comp == 'Estaduais (Todos)':
            df = df[df['Competicao'].str.contains('Estadual|Campeonato Paulista|Campeonato Carioca|Campeonato Mineiro|Campeonato Gaúcho|Campeonato Baiano|Campeonato Goiano|Campeonato Pernambucano|Campeonato Capixaba', na=False)]
        elif comp != 'Todas as Competições':
            df = df[df['Competicao'] == comp]

        df_fase = df[df['Fase_Formatada'] == self.fase_atual].copy()

        # Filtro Rápido
        if self.filtro_rapido == 'copa' and 'Alerta_Copa' in df_fase.columns:
            df_fase = df_fase[df_fase['Alerta_Copa'] != '-']
        elif self.filtro_rapido == 'classico' and 'É_Clássico' in df_fase.columns:
            df_fase = df_fase[df_fase['É_Clássico'] == 1]

        # Busca com normalização de acentos
        termo = normalizar_texto(self.var_busca.get())
        if termo:
            m_m = df_fase['Time da Casa'].astype(str).apply(normalizar_texto).str.contains(termo)
            m_v = df_fase['Time Visitante'].astype(str).apply(normalizar_texto).str.contains(termo)
            df_fase = df_fase[m_m | m_v]

        # Ordenação por Coluna
        if self.sort_coluna:
            col_map = {
                'Torneio': 'Competicao',
                'Fase/Rodada': 'Fase_Formatada',
                'Data': 'Data_Datetime',
                'Mandante': 'Time da Casa',
                'Placar': 'Gols_Mandante',
                'Visitante': 'Time Visitante',
                'Alerta Copa': 'Alerta_Copa',
                'Momentum': 'Momentum_M',
                'H2H %': 'H2H_Taxa_Vits_M',
                'Desespero': 'Desespero_Mandante',
                'Clássico': 'É_Clássico',
                'Favorito IA': 'Favorito'
            }
            campo = col_map.get(self.sort_coluna)
            if campo and campo in df_fase.columns:
                df_fase = df_fase.sort_values(by=campo, ascending=not self.sort_desc)

        self.tree.delete(*self.tree.get_children())

        self.tree.tag_configure('vit_m', background='#0e1b19', foreground=THEME['text_primary'])
        self.tree.tag_configure('emp',   background='#1a1912', foreground=THEME['text_primary'])
        self.tree.tag_configure('vit_v', background='#1f1214', foreground=THEME['text_primary'])
        self.tree.tag_configure('copa',  background='#141e2e', foreground=THEME['text_primary'])

        for orig_idx, row in df_fase.iterrows():
            gm = int(row.get('Gols_Mandante', 0))
            gv = int(row.get('Gols_Visitante', 0))

            tag = 'vit_m' if gm > gv else ('vit_v' if gv > gm else 'emp')
            if row.get('Competicao') in ['Copa do Brasil', 'Libertadores', 'Sudamericana']:
                tag = 'copa'

            comp_abrev = ABREV_COMPETICAO.get(row.get('Competicao'), str(row.get('Competicao', 'JOGO'))[:9].upper())
            mom_str = f"{float(row.get('Momentum_M', 0)):.1f} x {float(row.get('Momentum_V', 0)):.1f}"
            des_str = f"{float(row.get('Desespero_Mandante', 0)):.1f} x {float(row.get('Desespero_Visitante', 0)):.1f}"

            vals = (
                comp_abrev,
                row.get('Fase_Formatada', ''),
                row.get('Data', ''),
                row.get('Time da Casa', ''),
                row.get('Placar', ''),
                row.get('Time Visitante', ''),
                row.get('Alerta_Copa', '-'),
                mom_str,
                f"{float(row.get('H2H_Taxa_Vits_M', 0.5)):.0%}",
                des_str,
                '⚡' if row.get('É_Clássico', 0) == 1 else '-',
                str(row.get('Favorito', 'Aberto'))
            )
            self.tree.insert('', 'end', iid=str(orig_idx), values=vals, tags=(tag,))

    def _ao_dar_duplo_clique(self, _=None):
        """Abre a janela de Raio-X modal da partida com duplo clique."""
        sel = self.tree.selection()
        if not sel or self.df_carregado is None:
            return
        iid = sel[0]
        try:
            idx = int(iid)
            jogo_row = self.df_carregado.loc[idx]
        except (KeyError, ValueError):
            return

        JanelaRaioXJogo(self, jogo_row, self.gerenciador)
