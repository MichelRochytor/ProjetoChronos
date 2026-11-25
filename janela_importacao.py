"""
LOTECA ANALYTICS PRO — Interface do Gerenciador de Importação e Links
Permite configurar URLs, pastas e anos de todos os campeonatos (incluindo estaduais),
controlar quantidade totalmente livre de navegadores headless em segundo plano e acompanhar progresso em tempo real.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading

from config import THEME, FONTS
from raspador_gol import RaspadorGol


class JanelaGerenciadorImportacao(tk.Toplevel):
    """
    Janela modal para gerenciamento de links, parâmetros de importação
    e execução concorrente de múltiplos navegadores em segundo plano (sem limite de instâncias).
    """

    def __init__(self, parent, raspador: RaspadorGol, ao_concluir_callback=None):
        super().__init__(parent)
        self.raspador = raspador
        self.ao_concluir_callback = ao_concluir_callback

        self.title("🌐 Gerenciador de Importação O Gol 2.0 & Catálogo de Campeonatos")
        self.geometry("1180x790")
        self.minsize(1020, 660)
        self.configure(bg=THEME['bg_main'])
        self.transient(parent)

        self.var_categoria_filtro = tk.StringVar(value="Todos")
        self.var_num_navegadores = tk.IntVar(value=self.raspador.obter_num_navegadores_preferido())
        self.var_modo = tk.StringVar(value="rapido")
        self.var_ano_filtro = tk.StringVar(value="2025")
        self.var_motor = tk.StringVar(value=self.raspador.obter_motor_preferido())
        self.var_forcar_atualizacao = tk.BooleanVar(value=True)
        self.var_usar_tor = tk.BooleanVar(value=self.raspador.obter_preferencia_tor())

        self._centralizar_janela(parent)
        self._construir_interface()
        self._preencher_tabela()

    def _centralizar_janela(self, parent):
        try:
            self.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            w, h = 1180, 790
            x = px + max(0, (pw - w) // 2)
            y = py + max(0, (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _ao_mudar_motor(self):
        """Atualiza rótulo de concorrência dependendo do motor escolhido."""
        motor = self.var_motor.get()
        if motor == 'turbo':
            self.lbl_nav_tit.config(text="⚡ Conexões Simultâneas:")
            self.lbl_nav_sub.config(text="(Threads HTTP)")
        else:
            self.lbl_nav_tit.config(text="🤖 Navegadores Simultâneos:")
            self.lbl_nav_sub.config(text="(Headless Chrome)")

    def _ao_alternar_tor(self):
        """Atualiza status visual quando o usuário ativa/desativa a Rede Tor VPN."""
        ativo = self.var_usar_tor.get()
        self.raspador.salvar_preferencia_tor(ativo)
        if ativo:
            ip_atual = self.raspador.ultimo_ip_tor
            txt_ip = f"🧅 IP: {ip_atual}" if ip_atual and ip_atual != "Aguardando ativação" else "🧅 Troca automática ao rodar"
            self.lbl_ip_tor.config(text=txt_ip, fg=THEME['accent_purple'])
            self.btn_trocar_ip.config(state='normal')
        else:
            self.lbl_ip_tor.config(text="(Tor Desativado)", fg=THEME['text_muted'])
            self.btn_trocar_ip.config(state='disabled')

    def _atualizar_badge_ip_tor(self, novo_ip: str):
        """Atualiza de forma thread-safe o rótulo do IP Tor na interface."""
        def _upd():
            if novo_ip and novo_ip != "Indisponível":
                self.lbl_ip_tor.config(text=f"🧅 IP Tor: {novo_ip}", fg=THEME['win'])
            else:
                self.lbl_ip_tor.config(text="⚠️ Tor Indisponível", fg=THEME['draw'])
        self.after(0, _upd)

    def _trocar_ip_tor_manual(self):
        """Aciona a rotação imediata de circuito/IP da Rede Tor pelo botão da interface."""
        self.btn_trocar_ip.config(state='disabled', text="⏳...")
        self.lbl_ip_tor.config(text="🧅 Trocando circuito...", fg=THEME['draw'])

        def _worker_rot():
            novo_ip = self.raspador.rotacionar_identidade_tor(callback_log=self._adicionar_log)
            def _done():
                self.btn_trocar_ip.config(state='normal', text="🔄 Trocar IP")
                if novo_ip and novo_ip != "Indisponível":
                    self.lbl_ip_tor.config(text=f"🧅 IP Tor: {novo_ip}", fg=THEME['win'])
                else:
                    self.lbl_ip_tor.config(text="⚠️ Falha no Tor", fg=THEME['loss'])
            self.after(0, _done)

        threading.Thread(target=_worker_rot, daemon=True).start()

    def _ao_mudar_modo(self):
        """Atualiza o estado e a dica do seletor de ano conforme o modo de importação."""
        modo = self.var_modo.get()
        ano_sel = self.var_ano_filtro.get().strip() or "2025"
        if modo == 'ano_especifico':
            self.cb_ano_filtro.config(state='normal')
            self.lbl_ano_dica.config(text=f"🎯 Importar somente o ano {ano_sel}", fg=THEME['draw'])
        elif modo == 'a_partir_de':
            self.cb_ano_filtro.config(state='normal')
            self.lbl_ano_dica.config(text=f"📅 Importar de {ano_sel} até 2026", fg=THEME['accent_blue'])
        elif modo == 'rapido':
            self.cb_ano_filtro.config(state='normal')
            self.lbl_ano_dica.config(text="⚡ Importar temporada atual (2026)", fg=THEME['text_muted'])
        else:
            self.cb_ano_filtro.config(state='normal')
            self.lbl_ano_dica.config(text="📚 Importar todo o histórico do catálogo", fg=THEME['text_muted'])

    def _ao_selecionar_ano_combo(self, _event=None):
        """Se o usuário escolher um ano no combobox enquanto está em 'rapido' ou 'completo', muda para 'ano_especifico'."""
        if self.var_modo.get() in ('rapido', 'completo'):
            self.var_modo.set('ano_especifico')
        self._ao_mudar_modo()

    def _construir_interface(self):
        # ── 1. HEADER ─────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=THEME['bg_header'], padx=18, pady=12)
        hdr.pack(fill='x')

        tk.Label(
            hdr, text="🌐 IMPORTADOR O GOL 2.0 — CATÁLOGO DE LINKS, MULTI-MOTOR & REDE TOR VPN",
            font=FONTS['title'], fg=THEME['text_primary'], bg=THEME['bg_header']
        ).pack(anchor='w')
        tk.Label(
            hdr,
            text="Motor Turbo HTTP ou Chrome Headless com Rede Tor / VPN integrada (troca automática de IP a cada execução e por campeonato).",
            font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_header']
        ).pack(anchor='w')

        # ── 2. PAINEL DE CONTROLE SUPERIOR (EM 2 LINHAS ORGANIZADAS) ──────
        ctrl_frame = tk.Frame(self, bg=THEME['bg_card'], padx=16, pady=10, highlightbackground=THEME['border'], highlightthickness=1)
        ctrl_frame.pack(fill='x', padx=14, pady=(10, 8))

        # ── LINHA 1: Motor, Conexões Simultâneas, Tor VPN, Forçar Atualização e Filtro de Categoria
        linha_ctrl_1 = tk.Frame(ctrl_frame, bg=THEME['bg_card'])
        linha_ctrl_1.pack(fill='x', pady=(0, 8))

        # 2.1 Seletor de Motor de Raspagem (Turbo vs Selenium)
        box_motor = tk.Frame(linha_ctrl_1, bg=THEME['bg_card'])
        box_motor.pack(side='left', padx=(0, 16))
        tk.Label(box_motor, text="🚀 Motor de Raspagem:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card']).pack(anchor='w')
        
        box_radios_motor = tk.Frame(box_motor, bg=THEME['bg_card'])
        box_radios_motor.pack(anchor='w', pady=2)
        rb_turbo = tk.Radiobutton(
            box_radios_motor, text="⚡ Turbo HTTP", variable=self.var_motor, value="turbo",
            command=self._ao_mudar_motor,
            bg=THEME['bg_card'], fg=THEME['accent_blue'], selectcolor=THEME['bg_main'], activebackground=THEME['bg_card'], font=FONTS['body_b']
        )
        rb_turbo.pack(side='left')
        rb_chrome = tk.Radiobutton(
            box_radios_motor, text="🤖 Chrome Lite", variable=self.var_motor, value="selenium",
            command=self._ao_mudar_motor,
            bg=THEME['bg_card'], fg=THEME['text_primary'], selectcolor=THEME['bg_main'], activebackground=THEME['bg_card'], font=FONTS['body']
        )
        rb_chrome.pack(side='left', padx=(6, 0))

        # 2.2 Quantidade Livre de Conexões / Navegadores Concorrentes
        box_nav = tk.Frame(linha_ctrl_1, bg=THEME['bg_card'])
        box_nav.pack(side='left', padx=(0, 16))
        
        lbl_nav_box = tk.Frame(box_nav, bg=THEME['bg_card'])
        lbl_nav_box.pack(fill='x')
        self.lbl_nav_tit = tk.Label(lbl_nav_box, text="⚡ Conexões Simultâneas:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card'])
        self.lbl_nav_tit.pack(side='left')
        self.lbl_nav_sub = tk.Label(lbl_nav_box, text="(Threads HTTP)", font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_card'])
        self.lbl_nav_sub.pack(side='left', padx=4)

        valores_sugeridos = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 30, 36, 50]
        self.cb_nav = ttk.Combobox(
            box_nav, textvariable=self.var_num_navegadores,
            values=valores_sugeridos,
            state='normal',
            width=7
        )
        self.cb_nav.pack(anchor='w', pady=2)

        # 2.3 Rede Tor / VPN Rotativa
        box_tor = tk.Frame(linha_ctrl_1, bg=THEME['bg_card'])
        box_tor.pack(side='left', padx=(0, 16))
        lbl_tor_top = tk.Frame(box_tor, bg=THEME['bg_card'])
        lbl_tor_top.pack(fill='x')
        tk.Label(lbl_tor_top, text="🧅 VPN / Rede Tor:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card']).pack(side='left')
        self.lbl_ip_tor = tk.Label(lbl_tor_top, text="🧅 Troca automática ao rodar", font=FONTS['badge'], fg=THEME['accent_purple'], bg=THEME['bg_card'])
        self.lbl_ip_tor.pack(side='left', padx=6)

        linha_ctrl_tor = tk.Frame(box_tor, bg=THEME['bg_card'])
        linha_ctrl_tor.pack(anchor='w', pady=2)
        chk_tor = tk.Checkbutton(
            linha_ctrl_tor, text="🧅 Usar Tor (Trocar IP toda vez)", variable=self.var_usar_tor,
            command=self._ao_alternar_tor,
            bg=THEME['bg_card'], fg=THEME['accent_purple'], selectcolor=THEME['bg_main'], activebackground=THEME['bg_card'], font=FONTS['body_b']
        )
        chk_tor.pack(side='left')

        self.btn_trocar_ip = tk.Button(
            linha_ctrl_tor, text="🔄 Trocar IP", command=self._trocar_ip_tor_manual,
            bg=THEME['bg_subtle'], fg=THEME['accent_blue'], font=FONTS['badge'], relief='flat', padx=8, pady=1, cursor='hand2'
        )
        self.btn_trocar_ip.pack(side='left', padx=(6, 0))

        # 2.4 Forçar Atualização (Sem pular)
        box_forcar = tk.Frame(linha_ctrl_1, bg=THEME['bg_card'])
        box_forcar.pack(side='left', padx=(0, 14))
        tk.Label(box_forcar, text="🔄 Forçar Atualização:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card']).pack(anchor='w')
        chk_forcar = tk.Checkbutton(
            box_forcar, text="⚡ Forçar (Não pular)", variable=self.var_forcar_atualizacao,
            bg=THEME['bg_card'], fg=THEME['win'], selectcolor=THEME['bg_main'], activebackground=THEME['bg_card'], font=FONTS['body_b']
        )
        chk_forcar.pack(anchor='w', pady=2)

        # 2.5 Filtro de Categoria
        box_cat = tk.Frame(linha_ctrl_1, bg=THEME['bg_card'])
        box_cat.pack(side='right')
        tk.Label(box_cat, text="Filtrar Categoria:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card']).pack(anchor='w')
        cats_padrao = ["Todos", "Estadual", "Nacional", "Continental", "Internacional", "Copa Regional"]
        for k_c, v_c in self.raspador.catalogo.items():
            if not k_c.startswith('_') and isinstance(v_c, dict):
                cat_item = v_c.get('categoria', '')
                if cat_item and cat_item not in cats_padrao:
                    cats_padrao.append(cat_item)
        self.cb_cat = ttk.Combobox(
            box_cat, textvariable=self.var_categoria_filtro,
            values=cats_padrao,
            state='readonly', width=14
        )
        self.cb_cat.pack(anchor='w', pady=2)
        self.cb_cat.bind('<<ComboboxSelected>>', lambda e: self._preencher_tabela())

        # Divisor sutil entre Linha 1 e Linha 2
        tk.Frame(ctrl_frame, bg=THEME['border'], height=1).pack(fill='x', pady=(2, 8))

        # ── LINHA 2: Modo de Importação (Rápido / Ano Específico / Do Ano em Diante / Completo) + Seletor de Ano
        linha_ctrl_2 = tk.Frame(ctrl_frame, bg=THEME['bg_card'])
        linha_ctrl_2.pack(fill='x')

        box_modo = tk.Frame(linha_ctrl_2, bg=THEME['bg_card'])
        box_modo.pack(side='left', padx=(0, 24))
        tk.Label(box_modo, text="⚡ Modo / Período de Importação:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card']).pack(anchor='w')
        box_radios_modo = tk.Frame(box_modo, bg=THEME['bg_card'])
        box_radios_modo.pack(anchor='w', pady=2)

        rb_rapido = tk.Radiobutton(
            box_radios_modo, text="Rápido (2026)", variable=self.var_modo, value="rapido",
            command=self._ao_mudar_modo,
            bg=THEME['bg_card'], fg=THEME['text_primary'], selectcolor=THEME['bg_main'], activebackground=THEME['bg_card'], font=FONTS['body']
        )
        rb_rapido.pack(side='left')

        rb_ano_esp = tk.Radiobutton(
            box_radios_modo, text="🎯 Ano Específico", variable=self.var_modo, value="ano_especifico",
            command=self._ao_mudar_modo,
            bg=THEME['bg_card'], fg=THEME['draw'], selectcolor=THEME['bg_main'], activebackground=THEME['bg_card'], font=FONTS['body_b']
        )
        rb_ano_esp.pack(side='left', padx=(12, 0))

        rb_apartir = tk.Radiobutton(
            box_radios_modo, text="📅 Do Ano em Diante (Ano -> 2026)", variable=self.var_modo, value="a_partir_de",
            command=self._ao_mudar_modo,
            bg=THEME['bg_card'], fg=THEME['accent_blue'], selectcolor=THEME['bg_main'], activebackground=THEME['bg_card'], font=FONTS['body_b']
        )
        rb_apartir.pack(side='left', padx=(12, 0))

        rb_completo = tk.Radiobutton(
            box_radios_modo, text="📚 Completo (Histórico)", variable=self.var_modo, value="completo",
            command=self._ao_mudar_modo,
            bg=THEME['bg_card'], fg=THEME['text_primary'], selectcolor=THEME['bg_main'], activebackground=THEME['bg_card'], font=FONTS['body']
        )
        rb_completo.pack(side='left', padx=(12, 0))

        # Seletor de Ano ao lado dos modos
        box_ano = tk.Frame(linha_ctrl_2, bg=THEME['bg_card'])
        box_ano.pack(side='left', padx=(0, 16))
        tk.Label(box_ano, text="📅 Ano Selecionado:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_card']).pack(anchor='w')

        linha_combo_ano = tk.Frame(box_ano, bg=THEME['bg_card'])
        linha_combo_ano.pack(anchor='w', pady=2)

        anos_disponiveis = [str(a) for a in range(2026, 1901, -1)]
        self.cb_ano_filtro = ttk.Combobox(
            linha_combo_ano, textvariable=self.var_ano_filtro,
            values=anos_disponiveis,
            state='normal',
            width=9
        )
        self.cb_ano_filtro.pack(side='left')
        self.cb_ano_filtro.bind('<<ComboboxSelected>>', self._ao_selecionar_ano_combo)
        self.cb_ano_filtro.bind('<KeyRelease>', lambda e: self._ao_mudar_modo())

        self.lbl_ano_dica = tk.Label(
            linha_combo_ano, text="⚡ Importar temporada atual (2026)",
            font=FONTS['body_b'], fg=THEME['text_muted'], bg=THEME['bg_card']
        )
        self.lbl_ano_dica.pack(side='left', padx=(10, 0))

        self._ao_mudar_motor()
        self._ao_mudar_modo()
        self._ao_alternar_tor()

        # ── 3. TABELA DO CATÁLOGO DE CAMPEONATOS ──────────────────────────
        tbl_container = tk.Frame(self, bg=THEME['bg_card'], highlightbackground=THEME['border'], highlightthickness=1)
        tbl_container.pack(fill='both', expand=True, padx=14, pady=4)

        # Barra de ferramentas da tabela
        tb_bar = tk.Frame(tbl_container, bg=THEME['bg_subtle'], padx=10, pady=6)
        tb_bar.pack(fill='x')

        btn_marcar = tk.Button(
            tb_bar, text="☑ Marcar Todos", command=lambda: self._marcar_desmarcar_todos(True),
            bg=THEME['bg_card'], fg=THEME['text_primary'], font=FONTS['badge'], relief='flat', padx=8, pady=2, cursor='hand2'
        )
        btn_marcar.pack(side='left', padx=2)

        btn_desmarcar = tk.Button(
            tb_bar, text="☐ Desmarcar Todos", command=lambda: self._marcar_desmarcar_todos(False),
            bg=THEME['bg_card'], fg=THEME['text_primary'], font=FONTS['badge'], relief='flat', padx=8, pady=2, cursor='hand2'
        )
        btn_desmarcar.pack(side='left', padx=2)

        btn_editar = tk.Button(
            tb_bar, text="✏️ Editar Links / Parâmetros", command=self._editar_selecionado,
            bg=THEME['accent_indigo'], fg='#ffffff', font=FONTS['badge'], relief='flat', padx=10, pady=2, cursor='hand2'
        )
        btn_editar.pack(side='left', padx=8)

        btn_novo = tk.Button(
            tb_bar, text="➕ Adicionar Campeonato", command=self._adicionar_campeonato,
            bg=THEME['win'], fg='#ffffff', font=FONTS['badge'], relief='flat', padx=10, pady=2, cursor='hand2'
        )
        btn_novo.pack(side='left', padx=2)

        btn_remover = tk.Button(
            tb_bar, text="🗑️ Remover", command=self._remover_selecionado,
            bg=THEME['loss'], fg='#ffffff', font=FONTS['badge'], relief='flat', padx=8, pady=2, cursor='hand2'
        )
        btn_remover.pack(side='left', padx=2)

        self.lbl_contagem = tk.Label(tb_bar, text="", font=FONTS['subtitle'], fg=THEME['text_muted'], bg=THEME['bg_subtle'])
        self.lbl_contagem.pack(side='right')

        # Treeview
        colunas = ('Ativo', 'Categoria', 'Campeonato', 'Prefixo', 'Ano Inicial', 'Pasta Destino', 'Última Atualização', 'Status')
        self.tree_catalogo = ttk.Treeview(tbl_container, columns=colunas, show='headings', selectmode='browse', height=10)

        larguras = {
            'Ativo': 60, 'Categoria': 110, 'Campeonato': 200, 'Prefixo': 110,
            'Ano Inicial': 85, 'Pasta Destino': 220, 'Última Atualização': 130, 'Status': 110
        }
        for c in colunas:
            self.tree_catalogo.heading(c, text=c)
            self.tree_catalogo.column(c, width=larguras.get(c, 100), anchor='center' if c in ['Ativo', 'Ano Inicial', 'Última Atualização', 'Status'] else 'w')

        vsb = ttk.Scrollbar(tbl_container, orient='vertical', command=self.tree_catalogo.yview)
        self.tree_catalogo.configure(yscrollcommand=vsb.set)

        self.tree_catalogo.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.tree_catalogo.bind('<Double-1>', lambda e: self._alternar_ativo_duplo_clique())

        # ── 4. BARRA DE PROGRESSO & LOGS ──────────────────────────────────
        log_frame = tk.Frame(self, bg=THEME['bg_card'], padx=14, pady=8, highlightbackground=THEME['border'], highlightthickness=1)
        log_frame.pack(fill='both', expand=True, padx=14, pady=(4, 10))

        prog_topo = tk.Frame(log_frame, bg=THEME['bg_card'])
        prog_topo.pack(fill='x', pady=(0, 4))

        self.lbl_progresso_msg = tk.Label(
            prog_topo, text="Pronto para iniciar importação.",
            font=FONTS['body_b'], fg=THEME['text_primary'], bg=THEME['bg_card']
        )
        self.lbl_progresso_msg.pack(side='left')

        self.lbl_pct = tk.Label(prog_topo, text="0%", font=FONTS['card_lbl'], fg=THEME['accent_blue'], bg=THEME['bg_card'])
        self.lbl_pct.pack(side='right')

        self.progress_bar = ttk.Progressbar(log_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill='x', pady=(0, 6))

        # Console de logs
        self.txt_log = tk.Text(
            log_frame, bg=THEME['bg_subtle'], fg=THEME['text_primary'], font=FONTS['mono'],
            height=6, relief='flat', highlightbackground=THEME['border'], highlightthickness=1, padx=8, pady=6
        )
        self.txt_log.pack(fill='both', expand=True)

        # ── 5. BOTÕES DE AÇÃO INFERIORES ──────────────────────────────────
        btn_bar = tk.Frame(self, bg=THEME['bg_header'], padx=16, pady=8)
        btn_bar.pack(fill='x', side='bottom')

        self.btn_iniciar = tk.Button(
            btn_bar, text="⚡ Iniciar Importação em Segundo Plano", command=self._iniciar_importacao,
            bg=THEME['win'], fg='#ffffff', font=FONTS['body_b'], relief='flat', padx=16, pady=6, cursor='hand2'
        )
        self.btn_iniciar.pack(side='left')

        self.btn_parar = tk.Button(
            btn_bar, text="⏹️ Parar Importação", command=self._parar_importacao, state='disabled',
            bg=THEME['loss'], fg='#ffffff', font=FONTS['body_b'], relief='flat', padx=14, pady=6, cursor='hand2'
        )
        self.btn_parar.pack(side='left', padx=10)

        btn_fechar = tk.Button(
            btn_bar, text="Fechar", command=self.destroy,
            bg=THEME['bg_subtle'], fg=THEME['text_primary'], font=FONTS['body'], relief='flat', padx=14, pady=6, cursor='hand2'
        )
        btn_fechar.pack(side='right')

    # ── MÉTODOS DE CONTROLE DA TABELA ─────────────────────────────────────
    def _preencher_tabela(self):
        """Atualiza itens exibidos na tabela conforme o catálogo e o filtro ativo."""
        self.tree_catalogo.delete(*self.tree_catalogo.get_children())
        cat_filtro = self.var_categoria_filtro.get()

        total = 0
        ativos = 0

        for chave, camp in self.raspador.catalogo.items():
            if chave.startswith('_'):
                continue

            categoria = camp.get('categoria', 'Estadual')
            if cat_filtro != 'Todos' and categoria != cat_filtro:
                continue

            total += 1
            is_ativo = camp.get('ativo', True)
            if is_ativo:
                ativos += 1

            ativo_str = "✅ Sim" if is_ativo else "❌ Não"

            ult_att = camp.get('ultima_atualizacao')
            if ult_att:
                try:
                    dt = datetime.fromisoformat(ult_att)
                    ult_str = dt.strftime('%d/%m/%Y %H:%M')
                except Exception:
                    ult_str = str(ult_att)[:16]
            else:
                ult_str = "-"

            # Status de atualização
            if self.raspador.campeonato_finalizado(camp):
                status_str = "🏁 Finalizado"
            elif self.raspador.esta_atualizado(camp, modo='rapido'):
                status_str = "🟢 Atualizado Hoje"
            else:
                status_str = "🟡 Pendente"

            valores = (
                ativo_str,
                categoria,
                camp.get('nome', chave),
                camp.get('prefixo', chave),
                camp.get('ano_inicial', 2026),
                camp.get('pasta_destino', ''),
                ult_str,
                status_str
            )
            self.tree_catalogo.insert('', 'end', iid=chave, values=valores)

        self.lbl_contagem.config(text=f"Exibindo {total} campeonatos ({ativos} ativos para importação)")

    def _alternar_ativo_duplo_clique(self):
        """Alterna estado ativo/inativo ao dar duplo clique."""
        sel = self.tree_catalogo.selection()
        if not sel:
            return
        chave = sel[0]
        camp = self.raspador.catalogo.get(chave)
        if camp:
            camp['ativo'] = not camp.get('ativo', True)
            self.raspador.atualizar_item_catalogo(chave, camp)
            self._preencher_tabela()

    def _marcar_desmarcar_todos(self, ativar: bool):
        """Marca ou desmarca todos os campeonatos visíveis."""
        cat_filtro = self.var_categoria_filtro.get()
        for chave, camp in self.raspador.catalogo.items():
            if chave.startswith('_'):
                continue
            if cat_filtro == 'Todos' or camp.get('categoria') == cat_filtro:
                camp['ativo'] = ativar
        self.raspador.salvar_catalogo()
        self._preencher_tabela()

    def _adicionar_campeonato(self):
        """Abre modal para adicionar um novo campeonato ao catálogo."""
        self._abrir_modal_edicao(None)

    def _editar_selecionado(self):
        """Abre modal para editar o campeonato selecionado na tabela."""
        sel = self.tree_catalogo.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um campeonato na tabela para editar.")
            return
        self._abrir_modal_edicao(sel[0])

    def _remover_selecionado(self):
        """Remove o campeonato selecionado do catálogo."""
        sel = self.tree_catalogo.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um campeonato na tabela para remover.")
            return
        chave = sel[0]
        nome = self.raspador.catalogo.get(chave, {}).get('nome', chave)
        if messagebox.askyesno("Confirmar", f"Deseja remover '{nome}' do catálogo de links?"):
            self.raspador.remover_item_catalogo(chave)
            self._preencher_tabela()

    def _abrir_modal_edicao(self, chave_existente: str = None):
        """Diálogo modal para adicionar ou editar parâmetros do campeonato."""
        modal = tk.Toplevel(self)
        modal.title("Editar Campeonato & Links" if chave_existente else "Novo Campeonato")
        modal.geometry("640x520")
        modal.configure(bg=THEME['bg_card'])
        modal.transient(self)
        modal.grab_set()

        dados = self.raspador.catalogo.get(chave_existente, {}) if chave_existente else {}

        campos = [
            ("Identificador (Chave interna):", 'chave', chave_existente or ""),
            ("Nome do Campeonato:", 'nome', dados.get('nome', '')),
            ("Prefixo do Arquivo CSV:", 'prefixo', dados.get('prefixo', '')),
            ("Categoria (Estadual, Nacional, etc):", 'categoria', dados.get('categoria', 'Estadual')),
            ("Pasta de Destino:", 'pasta_destino', dados.get('pasta_destino', 'dados/brasil/estaduais/')),
            ("Ano Inicial:", 'ano_inicial', str(dados.get('ano_inicial', 2026))),
            ("URL Inicial (Ano Base / Calendário):", 'url_inicial', dados.get('url_inicial', '')),
            ("URL Atual (Temporada Ativa):", 'url_atual', dados.get('url_atual', '')),
        ]

        entradas = {}
        for idx, (label_txt, var_name, valor_padrao) in enumerate(campos):
            f = tk.Frame(modal, bg=THEME['bg_card'], padx=14, pady=3)
            f.pack(fill='x')
            tk.Label(f, text=label_txt, font=FONTS['body_b'], fg=THEME['text_secondary'], bg=THEME['bg_card']).pack(anchor='w')
            ent = tk.Entry(f, font=FONTS['body'], bg=THEME['bg_subtle'], fg=THEME['text_primary'], insertbackground='#ffffff')
            ent.insert(0, valor_padrao)
            ent.pack(fill='x', pady=2)
            if var_name == 'chave' and chave_existente:
                ent.config(state='disabled')
            entradas[var_name] = ent

        def _salvar():
            nova_chave = chave_existente or entradas['chave'].get().strip()
            if not nova_chave:
                messagebox.showerror("Erro", "O identificador é obrigatório!")
                return

            try:
                ano_ini = int(entradas['ano_inicial'].get().strip())
            except ValueError:
                ano_ini = 2026

            novo_dado = {
                'nome': entradas['nome'].get().strip() or nova_chave,
                'prefixo': entradas['prefixo'].get().strip() or nova_chave,
                'categoria': entradas['categoria'].get().strip() or 'Estadual',
                'pasta_destino': entradas['pasta_destino'].get().strip(),
                'ano_inicial': ano_ini,
                'url_inicial': entradas['url_inicial'].get().strip(),
                'url_atual': entradas['url_atual'].get().strip(),
                'ativo': dados.get('ativo', True),
                'ultima_atualizacao': dados.get('ultima_atualizacao')
            }

            self.raspador.atualizar_item_catalogo(nova_chave, novo_dado)
            modal.destroy()
            self._preencher_tabela()
            messagebox.showinfo("Sucesso", "Campeonato salvo no catálogo com sucesso!")

        btn_box = tk.Frame(modal, bg=THEME['bg_card'], pady=12)
        btn_box.pack(fill='x')
        tk.Button(
            btn_box, text="💾 Salvar", command=_salvar,
            bg=THEME['win'], fg='#ffffff', font=FONTS['body_b'], relief='flat', padx=16, pady=4, cursor='hand2'
        ).pack(side='left', padx=14)
        tk.Button(
            btn_box, text="Cancelar", command=modal.destroy,
            bg=THEME['bg_subtle'], fg=THEME['text_primary'], font=FONTS['body'], relief='flat', padx=12, pady=4, cursor='hand2'
        ).pack(side='left')

    # ── MÉTODOS DE EXECUÇÃO DA RASPAGEM ───────────────────────────────────
    def _iniciar_importacao(self):
        """Dispara a importação paralela com a quantidade de navegadores informada."""
        chaves_ativas = [k for k, v in self.raspador.catalogo.items() if not k.startswith('_') and v.get('ativo', True)]
        if not chaves_ativas:
            messagebox.showwarning("Aviso", "Nenhum campeonato está marcado como ativo para importação!")
            return

        # Obter número livre de navegadores informado pelo usuário
        try:
            val_txt = str(self.cb_nav.get()).strip()
            num_nav = int(val_txt)
        except (ValueError, TypeError):
            num_nav = 4

        num_nav = max(1, num_nav)
        self.raspador.salvar_preferencia_navegadores(num_nav)

        modo = self.var_modo.get()
        motor = self.var_motor.get()
        ano_filtro = None

        if modo in ('ano_especifico', 'a_partir_de'):
            try:
                ano_filtro = int(str(self.var_ano_filtro.get()).strip())
                if not (1900 <= ano_filtro <= 2030):
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Ano Inválido", "Informe um ano válido entre 1900 e 2026 no campo '📅 Ano'.")
                return

        self.btn_iniciar.config(state='disabled')
        self.btn_parar.config(state='normal')
        self.progress_bar['value'] = 0
        self.lbl_pct.config(text="0%")
        self.txt_log.delete('1.0', 'end')

        usar_tor = self.var_usar_tor.get()
        self.raspador.salvar_preferencia_motor(motor)
        self.raspador.salvar_preferencia_tor(usar_tor)

        if usar_tor:
            self.lbl_ip_tor.config(text="🧅 Rotacionando IP...", fg=THEME['draw'])

        tipo_worker = "conexões HTTP Turbo" if motor == 'turbo' else "navegadores Chrome"
        if modo == 'ano_especifico':
            desc_modo_log = f"Ano Específico ({ano_filtro})"
        elif modo == 'a_partir_de':
            desc_modo_log = f"Do Ano {ano_filtro} em diante ({ano_filtro} -> 2026)"
        elif modo == 'completo':
            desc_modo_log = "Completo (Histórico)"
        else:
            desc_modo_log = "Rápido (2026)"

        self._adicionar_log(f"Iniciando raspagem com {num_nav} {tipo_worker} no modo '{desc_modo_log}' (Tor VPN: {'ATIVO' if usar_tor else 'DESATIVADO'})...")

        self.raspador.executar_raspagem_paralela(
            chaves_selecionadas=chaves_ativas,
            num_navegadores=num_nav,
            modo=modo,
            motor=motor,
            forcar=self.var_forcar_atualizacao.get(),
            ano_filtro=ano_filtro,
            usar_tor=usar_tor,
            callback_progresso=self._ao_progredir,
            callback_log=self._adicionar_log,
            callback_concluido=self._ao_concluir,
            callback_ip_tor=self._atualizar_badge_ip_tor
        )

    def _parar_importacao(self):
        """Interrompe a importação."""
        self.raspador.cancelar()
        self._adicionar_log("⚠️ Solicitação de cancelamento enviada aos navegadores...")
        self.btn_parar.config(state='disabled')

    def _ao_progredir(self, pct: float, msg: str, worker_id: int):
        """Atualiza a barra de progresso e rótulos de status."""
        def _update():
            self.progress_bar['value'] = pct
            self.lbl_pct.config(text=f"{pct:.0f}%")
            self.lbl_progresso_msg.config(text=msg)
        self.after(0, _update)

    def _adicionar_log(self, texto: str):
        """Adiciona mensagem no console de logs da interface."""
        def _log():
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.txt_log.insert('end', f"[{timestamp}] {texto}\n")
            self.txt_log.see('end')
        self.after(0, _log)

    def _ao_concluir(self, atualizados: int, poupados: int):
        """Callback executado ao terminar todos os workers."""
        def _finish():
            self.btn_iniciar.config(state='normal')
            self.btn_parar.config(state='disabled')
            self.lbl_progresso_msg.config(text=f"Concluído: {atualizados} atualizados, {poupados} poupados.")
            self._preencher_tabela()

            if self.ao_concluir_callback:
                self.ao_concluir_callback(atualizados, poupados)

            messagebox.showinfo(
                "Importação Finalizada",
                f"Processamento concluído com sucesso!\n\n"
                f"• Atualizados / Importados: {atualizados}\n"
                f"• Poupados (Já estavam atualizados hoje): {poupados}"
            )
        self.after(0, _finish)
