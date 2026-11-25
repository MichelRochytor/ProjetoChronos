"""
LOTECA ANALYTICS PRO — Modais do Simulador e Conferência de Palpites
Janelas visuais ricas para salvar palpites, gerenciar bilhetes salvos,
conferir acertos jogo a jogo e comparar desempenhos em lote.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from config import THEME, FONTS
from gerenciador_palpites import GerenciadorPalpitesLoteca


def _centralizar_modal(modal: tk.Toplevel, parent: tk.Widget, largura: int, altura: int):
    """Centraliza a janela modal sobre o parent ou na tela com dimensões fixas."""
    try:
        modal.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - largura) // 2)
        y = py + max(0, (ph - altura) // 2)
        modal.geometry(f"{largura}x{altura}+{x}+{y}")
    except Exception:
        modal.geometry(f"{largura}x{altura}")


class ModalSalvarPalpite(tk.Toplevel):
    """
    Diálogo para salvar um palpite simulado no banco local do app.
    Permite dar nome personalizado à aposta e exibe resumo de duplos, triplos e custo.
    """

    def __init__(
        self,
        parent,
        numero_concurso: int,
        palpites_dict: dict,
        custo: float,
        combinacoes: int,
        secos: int,
        duplos: int,
        triplos: int,
        times_resumo: list,
        gerenciador_palpites: GerenciadorPalpitesLoteca,
        ao_salvar_sucesso = None
    ):
        super().__init__(parent)
        self.numero_concurso = numero_concurso
        self.palpites_dict = palpites_dict
        self.custo = custo
        self.combinacoes = combinacoes
        self.secos = secos
        self.duplos = duplos
        self.triplos = triplos
        self.times_resumo = times_resumo
        self.gerenciador = gerenciador_palpites
        self.ao_salvar_sucesso = ao_salvar_sucesso

        self.title("💾 Salvar Palpite no Simulador — Loteca")
        self.configure(bg=THEME['bg_card'])
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        _centralizar_modal(self, parent, 520, 320)
        self._construir_interface()
        self.bind('<Escape>', lambda e: self.destroy())

    def _construir_interface(self):
        # Topo
        hdr = tk.Frame(self, bg=THEME['bg_header'], padx=18, pady=12)
        hdr.pack(fill='x')

        tk.Label(
            hdr, text="💾 SALVAR PALPITE NO SIMULADOR",
            font=FONTS['title'], fg=THEME['text_primary'], bg=THEME['bg_header']
        ).pack(anchor='w')
        tk.Label(
            hdr, text=f"Loteca Concurso {self.numero_concurso} • Salve para conferir quando sair o resultado",
            font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_header']
        ).pack(anchor='w')

        # Conteúdo
        corpo = tk.Frame(self, bg=THEME['bg_card'], padx=20, pady=14)
        corpo.pack(fill='both', expand=True)

        # Resumo da Aposta
        resumo_box = tk.Frame(corpo, bg=THEME['bg_subtle'], padx=12, pady=10, highlightbackground=THEME['border'], highlightthickness=1)
        resumo_box.pack(fill='x', pady=(0, 14))

        tk.Label(
            resumo_box,
            text=f"📊 Estrutura: {self.secos} Secos • {self.duplos} Duplos • {self.triplos} Triplos",
            font=FONTS['body_b'], fg=THEME['text_primary'], bg=THEME['bg_subtle']
        ).pack(anchor='w')
        tk.Label(
            resumo_box,
            text=f"💰 Custo Estimado: R$ {self.custo:,.2f} ({self.combinacoes} combinações / apostas simples)",
            font=FONTS['subtitle'], fg=THEME['win'], bg=THEME['bg_subtle']
        ).pack(anchor='w', pady=(2, 0))

        # Campo Nome
        tk.Label(
            corpo, text="Nome / Identificador da Aposta:",
            font=FONTS['body_b'], fg=THEME['text_secondary'], bg=THEME['bg_card']
        ).pack(anchor='w', pady=(0, 4))

        qtd_existente = self.gerenciador.contar_palpites(self.numero_concurso)
        nome_sugerido = f"Aposta {qtd_existente + 1} ({self.duplos}D {self.triplos}T)"
        self.var_nome = tk.StringVar(value=nome_sugerido)

        self.ent_nome = tk.Entry(
            corpo, textvariable=self.var_nome, font=FONTS['body_b'],
            bg=THEME['bg_main'], fg=THEME['text_primary'], insertbackground='#ffffff',
            relief='flat', highlightbackground=THEME['border_light'], highlightthickness=1
        )
        self.ent_nome.pack(fill='x', ipady=4, pady=(0, 14))
        self.ent_nome.focus_set()
        self.ent_nome.select_range(0, tk.END)
        self.ent_nome.bind('<Return>', lambda e: self._salvar())

        # Botões Rodapé
        btn_box = tk.Frame(corpo, bg=THEME['bg_card'])
        btn_box.pack(fill='x', side='bottom')

        tk.Button(
            btn_box, text="Salvar Palpite", command=self._salvar,
            bg=THEME['win'], fg='#ffffff', font=FONTS['body_b'],
            relief='flat', padx=16, pady=6, cursor='hand2', activebackground='#059669'
        ).pack(side='right', padx=(8, 0))

        tk.Button(
            btn_box, text="Cancelar", command=self.destroy,
            bg=THEME['bg_subtle'], fg=THEME['text_primary'], font=FONTS['body'],
            relief='flat', padx=12, pady=6, cursor='hand2'
        ).pack(side='right')

    def _salvar(self):
        nome = self.var_nome.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Digite um nome para identificar o seu palpite.", parent=self)
            return

        item = self.gerenciador.salvar_palpite(
            numero_concurso=self.numero_concurso,
            nome=nome,
            palpites_dict=self.palpites_dict,
            custo=self.custo,
            combinacoes=self.combinacoes,
            secos=self.secos,
            duplos=self.duplos,
            triplos=self.triplos,
            times_resumo=self.times_resumo
        )

        if self.ao_salvar_sucesso:
            self.ao_salvar_sucesso(item)

        self.destroy()
        messagebox.showinfo(
            "Palpite Salvo!",
            f"✅ O palpite '{nome}' foi salvo com sucesso para o Concurso {self.numero_concurso}!\n\n"
            f"Quando o resultado oficial sair, você poderá conferir seus acertos no botão '📂 Meus Palpites Salvos'.",
            parent=self.master
        )


class ModalConferenciaLoteca(tk.Toplevel):
    """
    Modal com relatório detalhado de conferência de um palpite contra os resultados da Loteca.
    Destaca jogos acertados (verde), errados (vermelho) e pendentes (âmbar),
    calcula acertos totais e exibe a faixa de premiação atingida.
    """

    def __init__(self, parent, resultado_conferencia: dict, dados_concurso: dict = None):
        super().__init__(parent)
        self.res = resultado_conferencia
        self.concurso = dados_concurso or {}
        self.num_concurso = self.concurso.get('numero') or self.res.get('numero_concurso', 0)

        self.title(f"🎯 Conferência de Palpite — Loteca Concurso {self.num_concurso}")
        self.geometry("920x680")
        self.minsize(800, 560)
        self.configure(bg=THEME['bg_main'])
        self.transient(parent)
        self.grab_set()

        _centralizar_modal(self, parent, 920, 680)
        self._construir_interface()
        self.bind('<Escape>', lambda e: self.destroy())

    def _construir_interface(self):
        total_acertos = self.res.get('total_acertos', 0)
        total_erros = self.res.get('total_erros', 0)
        total_pendentes = self.res.get('total_pendentes', 0)
        custo = self.res.get('custo', 3.0)
        combinacoes = self.res.get('combinacoes', 1)
        nome = self.res.get('nome_palpite', 'Aposta')
        data_cria = self.res.get('data_criacao', '')

        # ── 1. HEADER / BANNER DE RESULTADO ──────────────────────────────────
        hdr_bg = THEME['bg_header']
        if total_acertos == 14:
            banner_bg = '#064e3b'
            banner_fg = '#34d399'
            banner_tit = "🏆 14 ACERTOS — PARABÉNS! VOCÊ ACERTOU OS 14 JOGOS DA LOTECA!"
            banner_sub = "Você atingiu a pontuação máxima e garantiu a Faixa Principal de Premiação!"
        elif total_acertos == 13:
            banner_bg = '#0c364c'
            banner_fg = '#38bdf8'
            banner_tit = "🥈 13 ACERTOS — PARABÉNS! VOCÊ FEZ 13 PONTOS (2º PRÊMIO)!"
            banner_sub = "Excelente resultado! Você entrou na faixa oficial de premiação dos 13 acertos."
        elif total_pendentes > 0:
            banner_bg = '#451a03'
            banner_fg = '#fbbf24'
            banner_tit = f"⏳ CONFERÊNCIA PARCIAL: {total_acertos} ACERTO(S) ATÉ AGORA"
            banner_sub = f"Existem {total_pendentes} partida(s) ainda aguardando resultado oficial da Caixa."
        else:
            banner_bg = '#1e293b'
            banner_fg = THEME['text_primary']
            faltam = 13 - total_acertos
            banner_tit = f"📊 RESULTADO FINAL: {total_acertos} / 14 ACERTOS"
            banner_sub = f"Não atingiu a faixa de premiação neste concurso (faltaram {faltam} acerto(s) para 13 pontos)."

        banner = tk.Frame(self, bg=banner_bg, padx=18, pady=12, highlightbackground=banner_fg, highlightthickness=1)
        banner.pack(fill='x', padx=14, pady=(12, 6))

        tk.Label(banner, text=banner_tit, font=FONTS['title'], fg=banner_fg, bg=banner_bg).pack(anchor='w')
        tk.Label(banner, text=banner_sub, font=FONTS['subtitle'], fg=THEME['text_secondary'], bg=banner_bg).pack(anchor='w', pady=(2, 0))

        # ── 2. CARDS DE KPIS DA CONFERÊNCIA ──────────────────────────────────
        kpi_frame = tk.Frame(self, bg=THEME['bg_main'])
        kpi_frame.pack(fill='x', padx=14, pady=4)

        # Buscar dados de premiação oficial se existirem
        premios = self.concurso.get('premiacao', [])
        p14 = premios[0] if len(premios) > 0 else {}
        p13 = premios[1] if len(premios) > 1 else {}

        if total_acertos == 14 and p14.get('valor_premio'):
            txt_premio = f"R$ {p14.get('valor_premio', 0.0):,.2f}"
            cor_premio = THEME['win']
        elif total_acertos == 13 and p13.get('valor_premio'):
            txt_premio = f"R$ {p13.get('valor_premio', 0.0):,.2f}"
            cor_premio = THEME['accent_blue']
        elif total_pendentes > 0:
            txt_premio = "Aguardando Apuração"
            cor_premio = THEME['draw']
        else:
            txt_premio = "Sem Premiação"
            cor_premio = THEME['text_muted']

        kpis = [
            ("TOTAL ACERTOS", f"{total_acertos} / 14", THEME['win'] if total_acertos >= 13 else THEME['accent_blue']),
            ("TOTAL ERROS", f"{total_erros} / 14", THEME['loss'] if total_erros > 0 else THEME['text_secondary']),
            ("CUSTO DO BILHETE", f"R$ {custo:,.2f}", THEME['accent_purple']),
            ("RETORNO / PRÊMIO", txt_premio, cor_premio)
        ]

        for tit, val, cor in kpis:
            card = tk.Frame(kpi_frame, bg=THEME['bg_card'], padx=12, pady=7, highlightbackground=THEME['border'], highlightthickness=1)
            card.pack(side='left', fill='both', expand=True, padx=3)
            tk.Label(card, text=tit, font=FONTS['card_lbl'], fg=THEME['text_muted'], bg=THEME['bg_card']).pack(anchor='w')
            tk.Label(card, text=val, font=FONTS['header'], fg=cor, bg=THEME['bg_card']).pack(anchor='w', pady=(2, 0))

        # ── 3. TABELA COM O DETALHAMENTO DOS 14 JOGOS ───────────────────────
        tbl_frame = tk.Frame(self, bg=THEME['bg_card'], highlightbackground=THEME['border'], highlightthickness=1)
        tbl_frame.pack(fill='both', expand=True, padx=14, pady=6)

        tbl_hdr = tk.Frame(tbl_frame, bg=THEME['bg_subtle'], padx=10, pady=6)
        tbl_hdr.pack(fill='x')

        tk.Label(
            tbl_hdr, text=f"📋 CONFERÊNCIA JOGO A JOGO: {nome} {f'({data_cria})' if data_cria else ''}",
            font=FONTS['header'], fg=THEME['text_primary'], bg=THEME['bg_subtle']
        ).pack(side='left')

        colunas = ('seq', 'jogo', 'placar', 'col_oficial', 'meu_palpite', 'tipo', 'status')
        self.tree = ttk.Treeview(tbl_frame, columns=colunas, show='headings', selectmode='browse', height=14)

        headers = [
            ('seq', 'Jogo', 55, 'center'),
            ('jogo', 'Partida / Confronto Oficial', 290, 'w'),
            ('placar', 'Placar Final', 95, 'center'),
            ('col_oficial', 'Coluna Oficial', 95, 'center'),
            ('meu_palpite', 'Seu Palpite', 95, 'center'),
            ('tipo', 'Tipo', 70, 'center'),
            ('status', 'Conferência', 120, 'center'),
        ]

        for col_id, col_name, width, align in headers:
            self.tree.heading(col_id, text=col_name)
            self.tree.column(col_id, width=width, anchor=align, stretch=(col_id == 'jogo'))

        scroll_y = ttk.Scrollbar(tbl_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scroll_y.pack(side='right', fill='y')

        # Tags de cores para as linhas
        self.tree.tag_configure('acertou', background='#062d1f', foreground='#34d399')
        self.tree.tag_configure('errou', background='#2d0e14', foreground='#fb7185')
        self.tree.tag_configure('pendente', background='#271c08', foreground='#fbbf24')

        # Preencher linhas
        for d in self.res.get('detalhes', []):
            seq = d.get('seq')
            m = d.get('mandante')
            v = d.get('visitante')
            placar = d.get('placar_str', '- x -')
            col_ofic = d.get('coluna_oficial', '-')
            palp_str = d.get('palpite_str', '-')
            tipo = d.get('tipo_palpite', 'Seco')
            acertou = d.get('acertou')

            if acertou is True:
                status_txt = "✅ ACERTOU"
                tag = 'acertou'
            elif acertou is False:
                status_txt = "❌ ERROU"
                tag = 'errou'
            else:
                status_txt = "⏳ Aguardando"
                tag = 'pendente'

            col_ofic_str = f"[ {col_ofic} ]" if col_ofic in ('1', 'X', '2') else "-"
            meu_palp_str = f"[ {palp_str} ]" if palp_str != '-' else "⚠️ Vazio"

            vals = (
                f"Jogo {seq}", f"{m} x {v}", placar, col_ofic_str, meu_palp_str, tipo, status_txt
            )
            self.tree.insert('', 'end', values=vals, tags=(tag,))

        # ── 4. BARRA DE AÇÕES INFERIOR ───────────────────────────────────────
        bar_bot = tk.Frame(self, bg=THEME['bg_main'], padx=14, pady=8)
        bar_bot.pack(fill='x')

        tk.Button(
            bar_bot, text="📋 Copiar Relatório", command=self._copiar_relatorio,
            bg=THEME['accent_indigo'], fg='#ffffff', font=FONTS['body_b'],
            relief='flat', padx=14, pady=5, cursor='hand2'
        ).pack(side='left', padx=(0, 6))

        tk.Button(
            bar_bot, text="Fechar", command=self.destroy,
            bg=THEME['bg_subtle'], fg=THEME['text_primary'], font=FONTS['body'],
            relief='flat', padx=16, pady=5, cursor='hand2'
        ).pack(side='right')

    def _copiar_relatorio(self):
        """Gera e copia texto estruturado com a conferência para a área de transferência."""
        linhas = [
            "==================================================",
            f"🎯 RELATÓRIO DE CONFERÊNCIA DA LOTECA (CONCURSO {self.num_concurso})",
            f"Aposta: {self.res.get('nome_palpite', 'Aposta')}",
            f"Data: {self.res.get('data_criacao', '')}",
            f"Status: {self.res.get('status_faixa', '')}",
            f"Acertos: {self.res.get('total_acertos', 0)} / 14 | Erros: {self.res.get('total_erros', 0)}",
            "--------------------------------------------------"
        ]
        for d in self.res.get('detalhes', []):
            st = "ACERTOU" if d.get('acertou') is True else ("ERROU" if d.get('acertou') is False else "PENDENTE")
            linhas.append(
                f"Jogo {d.get('seq'):02d}: [ {d.get('palpite_str')} ] vs Oficial [ {d.get('coluna_oficial')} ] "
                f"({st}) — {d.get('mandante')} {d.get('placar_str')} {d.get('visitante')}"
            )
        linhas.extend([
            "--------------------------------------------------",
            "Gerado por Loteca Analytics Pro",
            "=================================================="
        ])
        texto = "\n".join(linhas)
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.update()
        messagebox.showinfo("Copiado!", "Relatório completo de conferência copiado para a Área de Transferência!", parent=self)


class ModalMeusPalpitesLoteca(tk.Toplevel):
    """
    Modal de gerenciamento de todas as apostas salvas pelo usuário.
    Permite visualizar, carregar no volante, conferir contra os resultados e excluir bilhetes.
    """

    def __init__(
        self,
        parent,
        numero_concurso: int,
        dados_concurso: dict,
        gerenciador_palpites: GerenciadorPalpitesLoteca,
        raspador_loteca,
        ao_carregar_palpite = None,
        ao_novo_palpite = None
    ):
        super().__init__(parent)
        self.numero_concurso = numero_concurso
        self.dados_concurso = dados_concurso or {}
        self.gerenciador = gerenciador_palpites
        self.raspador = raspador_loteca
        self.ao_carregar_palpite = ao_carregar_palpite
        self.ao_novo_palpite = ao_novo_palpite

        self.title("📂 Meus Palpites Salvos — Loteca")
        self.geometry("960x600")
        self.minsize(840, 500)
        self.configure(bg=THEME['bg_main'])
        self.transient(parent)
        self.grab_set()

        self.var_filtro_concurso = tk.StringVar(value="deste")
        _centralizar_modal(self, parent, 960, 600)
        self._construir_interface()
        self._carregar_tabela()
        self.bind('<Escape>', lambda e: self.destroy())

    def _construir_interface(self):
        # ── 1. HEADER ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=THEME['bg_header'], padx=18, pady=12)
        hdr.pack(fill='x')

        tk.Label(
            hdr, text="📂 MEUS PALPITES SALVOS — LOTECA",
            font=FONTS['title'], fg=THEME['text_primary'], bg=THEME['bg_header']
        ).pack(anchor='w')
        tk.Label(
            hdr, text="Gerencie suas apostas salvas, carregue no volante para edição ou confira os resultados oficiais.",
            font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_header']
        ).pack(anchor='w')

        # ── 2. BARRA DE FILTRO ───────────────────────────────────────────────
        bar_filtro = tk.Frame(self, bg=THEME['bg_card'], padx=14, pady=8, highlightbackground=THEME['border'], highlightthickness=1)
        bar_filtro.pack(fill='x', padx=14, pady=(8, 4))

        tk.Label(
            bar_filtro, text="Filtrar Apostas:", font=FONTS['badge'],
            fg=THEME['text_secondary'], bg=THEME['bg_card']
        ).pack(side='left', padx=(0, 8))

        rb_deste = tk.Radiobutton(
            bar_filtro, text=f"Apenas Concurso Atual ({self.numero_concurso})",
            variable=self.var_filtro_concurso, value="deste",
            command=self._carregar_tabela, font=FONTS['body_b'],
            bg=THEME['bg_card'], fg=THEME['text_primary'], selectcolor=THEME['bg_subtle'],
            activebackground=THEME['bg_card'], activeforeground=THEME['text_primary']
        )
        rb_deste.pack(side='left', padx=(0, 10))

        rb_todos = tk.Radiobutton(
            bar_filtro, text="Todos os Concursos Salvos",
            variable=self.var_filtro_concurso, value="todos",
            command=self._carregar_tabela, font=FONTS['body'],
            bg=THEME['bg_card'], fg=THEME['text_secondary'], selectcolor=THEME['bg_subtle'],
            activebackground=THEME['bg_card'], activeforeground=THEME['text_primary']
        )
        rb_todos.pack(side='left', padx=(0, 10))

        self.lbl_contagem = tk.Label(
            bar_filtro, text="", font=FONTS['badge'],
            fg=THEME['win'], bg=THEME['bg_card']
        )
        self.lbl_contagem.pack(side='right')

        # ── 3. TREEVIEW DOS PALPITES SALVOS ──────────────────────────────────
        tbl_frame = tk.Frame(self, bg=THEME['bg_card'], highlightbackground=THEME['border'], highlightthickness=1)
        tbl_frame.pack(fill='both', expand=True, padx=14, pady=4)

        colunas = ('concurso', 'nome', 'data', 'config', 'custo', 'status_apuracao')
        self.tree = ttk.Treeview(tbl_frame, columns=colunas, show='headings', selectmode='browse', height=12)

        headers = [
            ('concurso', 'Concurso', 90, 'center'),
            ('nome', 'Identificador / Nome da Aposta', 250, 'w'),
            ('data', 'Data / Criação', 140, 'center'),
            ('config', 'Estrutura (S/D/T)', 150, 'center'),
            ('custo', 'Custo (R$)', 100, 'center'),
            ('status_apuracao', 'Status da Conferência', 200, 'center'),
        ]

        for col_id, col_name, width, align in headers:
            self.tree.heading(col_id, text=col_name)
            self.tree.column(col_id, width=width, anchor=align, stretch=(col_id == 'nome'))

        scroll_y = ttk.Scrollbar(tbl_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scroll_y.pack(side='right', fill='y')

        self.tree.bind('<Double-1>', lambda e: self._conferir_selecionado())

        # Tags visuais de status
        self.tree.tag_configure('tag_14', background='#062d1f', foreground='#34d399')
        self.tree.tag_configure('tag_13', background='#0c2c3b', foreground='#38bdf8')
        self.tree.tag_configure('tag_pontos', background='#162035', foreground=THEME['text_primary'])
        self.tree.tag_configure('tag_pendente', background='#241c0c', foreground='#fbbf24')

        # ── 4. BARRA DE BOTÕES DE AÇÃO ───────────────────────────────────────
        bar_acoes = tk.Frame(self, bg=THEME['bg_card'], padx=14, pady=10, highlightbackground=THEME['border'], highlightthickness=1)
        bar_acoes.pack(fill='x', padx=14, pady=(4, 10))

        btn_estilo = {'relief': 'flat', 'font': FONTS['body_b'], 'padx': 12, 'pady': 5, 'cursor': 'hand2'}

        # Ações Primárias (Esquerda)
        tk.Button(
            bar_acoes, text="📥 Carregar no Volante", command=self._carregar_selecionado,
            bg=THEME['accent_indigo'], fg='#ffffff', activebackground='#4f46e5', **btn_estilo
        ).pack(side='left', padx=(0, 6))

        tk.Button(
            bar_acoes, text="🎯 Conferir Este Palpite", command=self._conferir_selecionado,
            bg=THEME['win'], fg='#ffffff', activebackground='#059669', **btn_estilo
        ).pack(side='left', padx=(0, 6))

        tk.Button(
            bar_acoes, text="📊 Comparar Todos Deste Concurso", command=self._comparar_todos_em_lote,
            bg=THEME['bg_subtle'], fg=THEME['accent_blue'], **btn_estilo
        ).pack(side='left', padx=(0, 6))

        # Ações Secundárias (Direita)
        tk.Button(
            bar_acoes, text="Fechar", command=self.destroy,
            bg=THEME['bg_subtle'], fg=THEME['text_primary'], font=FONTS['body'], relief='flat', padx=12, pady=5, cursor='hand2'
        ).pack(side='right')

        tk.Button(
            bar_acoes, text="🗑️ Excluir Palpite", command=self._excluir_selecionado,
            bg=THEME['bg_subtle'], fg=THEME['loss'], **btn_estilo
        ).pack(side='right', padx=(0, 8))

        if self.ao_novo_palpite:
            tk.Button(
                bar_acoes, text="➕ Novo Palpite Limpo", command=self._novo_palpite,
                bg=THEME['bg_subtle'], fg=THEME['text_primary'], **btn_estilo
            ).pack(side='right', padx=(0, 8))

    def _obter_jogos_concurso(self, num_concurso: int) -> list:
        """Obtém jogos oficiais do concurso (do cache ou da janela atual)."""
        if self.dados_concurso.get('numero') == num_concurso and self.dados_concurso.get('jogos'):
            return self.dados_concurso.get('jogos', [])

        # Tenta obter do raspador
        dados = self.raspador.obter_concurso(num_concurso)
        return dados.get('jogos', [])

    def _carregar_tabela(self):
        """Preenche a tabela com os palpites salvos filtrados e calcula status em tempo real."""
        self.tree.delete(*self.tree.get_children())
        filtro = self.var_filtro_concurso.get()

        if filtro == "deste":
            palpites = self.gerenciador.listar_palpites(self.numero_concurso)
            self.lbl_contagem.config(text=f"Total: {len(palpites)} aposta(s) no Concurso {self.numero_concurso}")
        else:
            palpites = self.gerenciador.listar_palpites(None)
            self.lbl_contagem.config(text=f"Total: {len(palpites)} aposta(s) salvas no sistema")

        for p in palpites:
            c_num = p.get('numero_concurso', 0)
            id_palp = p.get('id')
            nome = p.get('nome', 'Aposta')
            dt = p.get('data_criacao', '')
            secos = p.get('secos', 14)
            duplos = p.get('duplos', 0)
            triplos = p.get('triplos', 0)
            custo = p.get('custo', 3.0)
            config_str = f"{secos}S • {duplos}D • {triplos}T"

            # Conferir status
            jogos = self._obter_jogos_concurso(c_num)
            tem_resultados = any(j.get('coluna') in ('1', 'X', '2') for j in jogos)

            if tem_resultados and jogos:
                conf = self.gerenciador.conferir_palpite(p, jogos)
                acertos = conf.get('total_acertos', 0)
                if acertos == 14:
                    status_str = "🏆 14 ACERTOS (1º Prêmio)"
                    tag = 'tag_14'
                elif acertos == 13:
                    status_str = "🥈 13 ACERTOS (2º Prêmio)"
                    tag = 'tag_13'
                elif conf.get('total_pendentes', 0) > 0:
                    status_str = f"⏳ {acertos}/14 ({conf.get('total_pendentes')} pendentes)"
                    tag = 'tag_pendente'
                else:
                    status_str = f"🎯 {acertos} / 14 Acertos"
                    tag = 'tag_pontos'
            else:
                status_str = "⏳ Aguardando Resultados"
                tag = 'tag_pendente'

            vals = (
                f"Conc. {c_num}", nome, dt, config_str, f"R$ {custo:,.2f}", status_str
            )
            self.tree.insert('', 'end', iid=id_palp, values=vals, tags=(tag,))

    def _obter_selecionado(self) -> dict:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma aposta na lista.", parent=self)
            return None
        id_palp = sel[0]
        return self.gerenciador.obter_palpite(id_palp)

    def _carregar_selecionado(self):
        """Carrega a aposta selecionada no volante da janela principal."""
        palpite = self._obter_selecionado()
        if not palpite:
            return

        if self.ao_carregar_palpite:
            self.ao_carregar_palpite(palpite)

        self.destroy()

    def _conferir_selecionado(self):
        """Executa conferência detalhada e abre o relatório da aposta selecionada."""
        palpite = self._obter_selecionado()
        if not palpite:
            return

        c_num = palpite.get('numero_concurso')
        jogos = self._obter_jogos_concurso(c_num)

        if not jogos:
            messagebox.showwarning("Aviso", f"Não foi possível obter os dados oficiais do Concurso {c_num}.", parent=self)
            return

        resultado_conf = self.gerenciador.conferir_palpite(palpite, jogos)

        # Se concurso for o mesmo da janela principal, passa os dados completos
        dados_conc = self.dados_concurso if self.dados_concurso.get('numero') == c_num else self.raspador.obter_concurso(c_num)
        ModalConferenciaLoteca(self, resultado_conf, dados_conc)

    def _comparar_todos_em_lote(self):
        """Compara e exibe ranking de todas as apostas salvas do concurso."""
        palpites = self.gerenciador.listar_palpites(self.numero_concurso)
        if not palpites:
            messagebox.showwarning("Aviso", f"Não há palpites salvos para o Concurso {self.numero_concurso}.", parent=self)
            return

        jogos = self._obter_jogos_concurso(self.numero_concurso)
        if not jogos:
            messagebox.showwarning("Aviso", "Não há dados oficiais disponíveis para este concurso.", parent=self)
            return

        ModalRankingLote(self, palpites, jogos, self.numero_concurso, self.dados_concurso)

    def _excluir_selecionado(self):
        """Exclui a aposta selecionada com confirmação."""
        palpite = self._obter_selecionado()
        if not palpite:
            return

        nome = palpite.get('nome')
        if messagebox.askyesno("Excluir Palpite", f"Deseja realmente excluir o palpite '{nome}'?", parent=self):
            self.gerenciador.excluir_palpite(palpite.get('id'))
            self._carregar_tabela()

    def _novo_palpite(self):
        """Limpa o volante na janela principal para novo preenchimento."""
        if self.ao_novo_palpite:
            self.ao_novo_palpite()
        self.destroy()


class ModalRankingLote(tk.Toplevel):
    """
    Modal de classificação comparativa de todos os bilhetes salvos em um concurso.
    Ordena pelo número de acertos (do maior para o menor) e destaca bilhetes premiados.
    """

    def __init__(self, parent, lista_palpites: list, jogos_oficiais: list, numero_concurso: int, dados_concurso: dict = None):
        super().__init__(parent)
        self.lista_palpites = lista_palpites
        self.jogos_oficiais = jogos_oficiais
        self.numero_concurso = numero_concurso
        self.dados_concurso = dados_concurso or {}

        self.title(f"📊 Comparativo em Lote — Loteca Concurso {numero_concurso}")
        self.geometry("860x520")
        self.minsize(740, 440)
        self.configure(bg=THEME['bg_main'])
        self.transient(parent)
        self.grab_set()

        _centralizar_modal(self, parent, 860, 520)
        self._construir_interface()
        self.bind('<Escape>', lambda e: self.destroy())

    def _construir_interface(self):
        hdr = tk.Frame(self, bg=THEME['bg_header'], padx=18, pady=12)
        hdr.pack(fill='x')

        tk.Label(
            hdr, text=f"📊 RANKING DE APOSTAS SALVAS — CONCURSO {self.numero_concurso}",
            font=FONTS['title'], fg=THEME['text_primary'], bg=THEME['bg_header']
        ).pack(anchor='w')
        tk.Label(
            hdr, text=f"Comparação simultânea de {len(self.lista_palpites)} aposta(s) salvas contra os resultados oficiais.",
            font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_header']
        ).pack(anchor='w')

        # Conferência de todos
        resultados = []
        for p in self.lista_palpites:
            res = GerenciadorPalpitesLoteca.conferir_palpite(p, self.jogos_oficiais)
            resultados.append((res, p))

        # Ordenar por mais acertos
        resultados.sort(key=lambda x: x[0].get('total_acertos', 0), reverse=True)

        tbl_frame = tk.Frame(self, bg=THEME['bg_card'], highlightbackground=THEME['border'], highlightthickness=1)
        tbl_frame.pack(fill='both', expand=True, padx=14, pady=10)

        colunas = ('pos', 'nome', 'acertos', 'erros', 'config', 'custo', 'premio')
        tree = ttk.Treeview(tbl_frame, columns=colunas, show='headings', selectmode='browse', height=10)

        headers = [
            ('pos', 'Pos.', 50, 'center'),
            ('nome', 'Aposta', 240, 'w'),
            ('acertos', 'Acertos', 90, 'center'),
            ('erros', 'Erros', 70, 'center'),
            ('config', 'Estrutura', 120, 'center'),
            ('custo', 'Custo', 90, 'center'),
            ('premio', 'Situação Oficial', 180, 'center'),
        ]

        for col_id, col_name, width, align in headers:
            tree.heading(col_id, text=col_name)
            tree.column(col_id, width=width, anchor=align, stretch=(col_id == 'nome'))

        scroll_y = ttk.Scrollbar(tbl_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scroll_y.set)

        tree.pack(side='left', fill='both', expand=True)
        scroll_y.pack(side='right', fill='y')

        tree.tag_configure('ouro', background='#062d1f', foreground='#34d399')
        tree.tag_configure('prata', background='#0c2c3b', foreground='#38bdf8')
        tree.tag_configure('comum', background=THEME['bg_card'], foreground=THEME['text_primary'])

        for idx, (res, p) in enumerate(resultados, 1):
            ac = res.get('total_acertos', 0)
            er = res.get('total_erros', 0)
            custo = p.get('custo', 3.0)
            cfg = f"{p.get('secos', 14)}S • {p.get('duplos', 0)}D • {p.get('triplos', 0)}T"

            if ac == 14:
                sit = "🏆 1º PRÊMIO (14 ACERTOS)"
                tag = 'ouro'
            elif ac == 13:
                sit = "🥈 2º PRÊMIO (13 ACERTOS)"
                tag = 'prata'
            elif res.get('total_pendentes', 0) > 0:
                sit = f"⏳ {res.get('total_pendentes')} pendentes"
                tag = 'comum'
            else:
                sit = f"Não premiado ({ac}/14)"
                tag = 'comum'

            vals = (f"#{idx}", p.get('nome'), f"{ac} / 14", er, cfg, f"R$ {custo:,.2f}", sit)
            tree.insert('', 'end', values=vals, tags=(tag,))

        bot = tk.Frame(self, bg=THEME['bg_main'], padx=14, pady=8)
        bot.pack(fill='x')

        tk.Button(
            bot, text="Fechar", command=self.destroy,
            bg=THEME['bg_subtle'], fg=THEME['text_primary'], font=FONTS['body'], relief='flat', padx=14, pady=4, cursor='hand2'
        ).pack(side='right')
