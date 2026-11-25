"""
LOTECA ANALYTICS PRO — Janela Modal: Raio-X Completo do Jogo
Análise aprofundada da partida com contexto de copas, força de equipes, H2H bilateral e IA tática.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pandas as pd # type: ignore

from config import THEME, FONTS, CORES_COMPETICAO
from barra_h2h import BarraH2HVisual
from utils import canonicalizar_nome_time, avaliar_features_ia


class JanelaRaioXJogo(tk.Toplevel):
    """
    Janela modal detalhada com diagnóstico cirúrgico do confronto:
    - Contexto e desgaste de copas (Libertadores, Sul-Americana, Copa do Brasil)
    - Métricas avançadas de força, saldo e sequência recente
    - Histórico H2H completo (geral e com mando de campo)
    - Diagnóstico de IA com comparativo de todas as features, pontuações e alertas táticos
    """

    def __init__(self, parent, jogo: pd.Series, gerenciador):
        super().__init__(parent)
        self.gerenciador = gerenciador
        self.jogo = jogo

        m = str(jogo.get('Time da Casa', 'Mandante')).strip()
        v = str(jogo.get('Time Visitante', 'Visitante')).strip()
        placar = str(jogo.get('Placar', '?-?')).strip()
        fase = str(jogo.get('Fase_Formatada', '')).strip()
        comp = str(jogo.get('Competicao', 'Campeonato')).strip()

        self.title(f"⚡ Raio-X Esportivo │ {m} x {v} ({comp})")
        self.geometry('1140x830')
        self.minsize(960, 680)
        self.configure(bg=THEME['bg_main'])

        # Centralizar sobre a janela pai se possível
        self._centralizar_janela(parent)

        self._build_header(m, v, placar, fase, comp)
        self._build_tabs(m, v)

    def _centralizar_janela(self, parent):
        try:
            self.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            w = 1140
            h = 830
            x = px + max(0, (pw - w) // 2)
            y = py + max(0, (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _build_header(self, m: str, v: str, placar: str, fase: str, comp: str):
        hdr = tk.Frame(self, bg=THEME['bg_header'], pady=14, padx=22)
        hdr.pack(fill='x')

        sub_hdr = tk.Frame(hdr, bg=THEME['bg_header'])
        sub_hdr.pack(fill='x')

        cor_comp = CORES_COMPETICAO.get(comp, THEME['accent_blue'])

        badge_comp = tk.Label(
            sub_hdr, text=f"  {comp.upper()}  ",
            bg=cor_comp, fg='#080c14', font=FONTS['badge']
        )
        badge_comp.pack(side='left', padx=(0, 10))

        info_txt = f"{fase}   •   Data: {self.jogo.get('Data', 'N/D')}"
        if self.jogo.get('É_Clássico', 0) == 1:
            info_txt += "   •   ⚡ CLÁSSICO REGIONAL"
        tk.Label(
            sub_hdr, text=info_txt,
            fg=THEME['text_secondary'], bg=THEME['bg_header'], font=FONTS['subtitle']
        ).pack(side='left')

        # Placar grande
        scoreboard = tk.Frame(hdr, bg=THEME['bg_header'], pady=8)
        scoreboard.pack()

        tk.Label(
            scoreboard, text=m, font=FONTS['title'],
            fg=THEME['text_primary'], bg=THEME['bg_header'], width=20, anchor='e'
        ).grid(row=0, column=0, padx=10)

        tk.Label(
            scoreboard, text=placar, font=FONTS['score'],
            fg=THEME['accent_blue'], bg=THEME['bg_card'], padx=18, pady=2
        ).grid(row=0, column=1, padx=8)

        tk.Label(
            scoreboard, text=v, font=FONTS['title'],
            fg=THEME['text_primary'], bg=THEME['bg_header'], width=20, anchor='w'
        ).grid(row=0, column=2, padx=10)

    def _build_tabs(self, m: str, v: str):
        style = ttk.Style(self)
        style.configure('RaioX.TNotebook', background=THEME['bg_main'], borderwidth=0)
        style.configure(
            'RaioX.TNotebook.Tab',
            background=THEME['bg_card'], foreground=THEME['text_secondary'],
            font=FONTS['body_b'], padding=[16, 8]
        )
        style.map(
            'RaioX.TNotebook.Tab',
            background=[('selected', THEME['bg_subtle'])],
            foreground=[('selected', THEME['accent_blue'])]
        )

        nb = ttk.Notebook(self, style='RaioX.TNotebook')
        nb.pack(fill='both', expand=True, padx=16, pady=10)

        tab_copas = tk.Frame(nb, bg=THEME['bg_card'], padx=16, pady=14)
        nb.add(tab_copas, text='  🏆 Contexto de Copas & Calendário  ')

        tab_metricas = tk.Frame(nb, bg=THEME['bg_card'], padx=16, pady=14)
        nb.add(tab_metricas, text='  📊 Raio-X & Força  ')

        tab_desempenho = tk.Frame(nb, bg=THEME['bg_card'], padx=16, pady=14)
        nb.add(tab_desempenho, text='  🏟️ Desempenho (Casa/Fora)  ')

        tab_tabela = tk.Frame(nb, bg=THEME['bg_card'], padx=16, pady=14)
        nb.add(tab_tabela, text='  📋 Tabela do Campeonato  ')

        tab_h2h = tk.Frame(nb, bg=THEME['bg_card'], padx=16, pady=14)
        nb.add(tab_h2h, text='  🔁 Confronto Direto (H2H)  ')

        tab_ia = tk.Frame(nb, bg=THEME['bg_card'], padx=16, pady=14)
        nb.add(tab_ia, text='  🧠 Diagnóstico Tático & IA  ')

        self._render_tab_copas(tab_copas, m, v)
        self._render_tab_metricas(tab_metricas, m, v)
        self._render_tab_desempenho(tab_desempenho, m, v)
        self._render_tab_tabela(tab_tabela)
        self._render_tab_h2h(tab_h2h, m, v)
        self._render_tab_ia(tab_ia, m, v)

    # ── TAB 1: COPAS & CALENDÁRIO ─────────────────────────────────────────────
    def _render_tab_copas(self, parent, m: str, v: str):
        data_jogo = self.jogo.get('Data_Datetime')
        ctx_m = self.gerenciador.obter_contexto_copa(m, data_jogo)
        ctx_v = self.gerenciador.obter_contexto_copa(v, data_jogo)

        frame_cards = tk.Frame(parent, bg=THEME['bg_card'])
        frame_cards.pack(fill='x', pady=(0, 14))

        for idx, (time_nome, ctx, cor_time) in enumerate([
            (f"🏠 {m} (Mandante)", ctx_m, THEME['accent_blue']),
            (f"✈️ {v} (Visitante)", ctx_v, THEME['accent_indigo'])
        ]):
            card = tk.Frame(
                frame_cards, bg=THEME['bg_subtle'],
                highlightbackground=THEME['border'], highlightthickness=1, padx=14, pady=10
            )
            card.pack(side='left', fill='both', expand=True, padx=6 if idx > 0 else (0, 6))

            # Header do Card com Tag de Desgaste
            topo_card = tk.Frame(card, bg=THEME['bg_subtle'])
            topo_card.pack(fill='x')
            tk.Label(topo_card, text=time_nome, font=FONTS['header'], fg=cor_time, bg=THEME['bg_subtle']).pack(side='left')

            desgaste = ctx.get('desgaste_fisico', 'Normal')
            cor_desg = THEME['tag_rest_warn'] if 'Crítico' in desgaste or 'Alto' in desgaste else THEME['text_muted']
            tk.Label(topo_card, text=f"[{desgaste}]", font=FONTS['badge'], fg=cor_desg, bg=THEME['bg_subtle']).pack(side='right')

            ult = ctx['ultimo_jogo']
            if ult:
                txt_ult = f"• Último em Copas: {ult['competicao']} ({ult['fase']})\n  {ult['adversario']} [{ult['placar']}] — há {ctx['dias_desde_ultimo']} dias"
            else:
                txt_ult = "• Sem jogo recente de Copa registrado"
            tk.Label(card, text=txt_ult, font=FONTS['body'], fg=THEME['text_primary'], bg=THEME['bg_subtle'], justify='left').pack(anchor='w', pady=3)

            prox = ctx['proximo_jogo']
            if prox:
                alerta_cor = THEME['tag_cup_alert'] if (ctx['dias_ate_proximo'] and ctx['dias_ate_proximo'] <= 5) else THEME['text_secondary']
                txt_prox = f"• Próximo em Copas: {prox['competicao']} ({prox['fase']})\n  vs {prox['adversario']} — em {ctx['dias_ate_proximo']} dias!"
            else:
                txt_prox = "• Sem compromisso próximo em Copas"
                alerta_cor = THEME['text_muted']
            tk.Label(card, text=txt_prox, font=FONTS['body_b'], fg=alerta_cor, bg=THEME['bg_subtle'], justify='left').pack(anchor='w', pady=3)

        tk.Label(
            parent, text="📅 Histórico Recente nas Copas (Copa do Brasil, Libertadores, Sudamericana)",
            font=FONTS['header'], fg=THEME['accent_blue'], bg=THEME['bg_card']
        ).pack(anchor='w', pady=(6, 4))

        tabela_frame = tk.Frame(parent, bg=THEME['bg_card'])
        tabela_frame.pack(fill='both', expand=True)

        cols = ('Time', 'Data', 'Competição', 'Fase', 'Mando', 'Adversário', 'Placar', 'Res')
        tree = ttk.Treeview(tabela_frame, columns=cols, show='headings', height=8)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=90 if c not in ['Time', 'Adversário', 'Fase'] else 140, anchor='center')

        vsb = ttk.Scrollbar(tabela_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        for time_nome, _ in [(m, 'mandante'), (v, 'visitante')]:
            jogos = self.gerenciador.timeline_copas_por_time.get(time_nome, [])
            jogos_proximos = [j for j in jogos if data_jogo and abs((j['data'] - data_jogo).days) <= 90]
            for j in sorted(jogos_proximos, key=lambda x: x['data'], reverse=True)[:8]:
                dt_str = j['data'].strftime('%d/%m/%Y') if j['data'] else '-'
                vals = (time_nome, dt_str, j['competicao'], j['fase'], j['local'], j['adversario'], j['placar'], j['resultado'])
                tree.insert('', 'end', values=vals, tags=(j['resultado'],))

        tree.tag_configure('V', foreground=THEME['win'])
        tree.tag_configure('E', foreground=THEME['draw'])
        tree.tag_configure('D', foreground=THEME['loss'])

    # ── TAB 2: RAIO-X & FORÇA (INSPEÇÃO MANUAL DAS 42 FEATURES) ──────────────
    def _render_tab_metricas(self, parent, m: str, v: str):
        data_jogo = self.jogo.get('Data_Datetime')
        ctx_m = self.gerenciador.obter_contexto_copa(m, data_jogo)
        ctx_v = self.gerenciador.obter_contexto_copa(v, data_jogo)
        h2h_info = self.gerenciador.obter_h2h_completo(m, v, data_limite=data_jogo)
        aval = avaliar_features_ia(self.jogo, ctx_m=ctx_m, ctx_v=ctx_v, h2h=h2h_info)
        features_ia = aval['features']
        categorias = aval.get('categorias', [])

        sec = tk.Frame(parent, bg=THEME['bg_card'])
        sec.pack(fill='both', expand=True)

        # Barra de Topo com Filtro por Categoria e Busca de Feature
        top_bar = tk.Frame(sec, bg=THEME['bg_subtle'], pady=8, padx=12, highlightbackground=THEME['border'], highlightthickness=1)
        top_bar.pack(fill='x', pady=(0, 8))

        tk.Label(
            top_bar,
            text=f"📋 INSPEÇÃO MANUAL — TODAS AS {len(features_ia)} FEATURES USADAS (7 CATEGORIAS)",
            font=FONTS['header'], fg=THEME['accent_blue'], bg=THEME['bg_subtle']
        ).pack(side='left')

        box_filtros = tk.Frame(top_bar, bg=THEME['bg_subtle'])
        box_filtros.pack(side='right')

        tk.Label(box_filtros, text="Categoria:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_subtle']).pack(side='left', padx=(0, 4))
        opcoes_cat = ["Todas as 7 Categorias (42 Features)"] + categorias
        var_cat = tk.StringVar(value=opcoes_cat[0])
        cb_cat = ttk.Combobox(box_filtros, textvariable=var_cat, values=opcoes_cat, state='readonly', width=34, font=FONTS['body'])
        cb_cat.pack(side='left', padx=(0, 10))

        tk.Label(box_filtros, text="🔍 Feature:", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_subtle']).pack(side='left', padx=(0, 4))
        var_busca_f = tk.StringVar()
        ent_busca_f = tk.Entry(
            box_filtros, textvariable=var_busca_f, width=16, font=FONTS['body'],
            bg=THEME['bg_card'], fg=THEME['text_primary'], insertbackground='#ffffff', relief='flat'
        )
        ent_busca_f.pack(side='left')

        # Tabela Treeview com todas as 42 Features
        tbl_frame = tk.Frame(sec, bg=THEME['bg_card'], highlightbackground=THEME['border'], highlightthickness=1)
        tbl_frame.pack(fill='both', expand=True)

        cols = ('num', 'codigo', 'valor_bruto', 'val_m', 'val_v', 'descricao')
        tree_m = ttk.Treeview(tbl_frame, columns=cols, show='headings', height=18)

        m_curto = m[:14]
        v_curto = v[:14]
        col_defs = [
            ('num',         '#',                         42,  'center'),
            ('codigo',      'Feature (Nome Exato)',      215, 'w'),
            ('valor_bruto', 'Valor da Feature',          165, 'center'),
            ('val_m',       f'🏠 {m_curto}',             155, 'center'),
            ('val_v',       f'✈️ {v_curto}',             155, 'center'),
            ('descricao',   'Descrição / Significado',   310, 'w'),
        ]
        for cid, cname, cwidth, calign in col_defs:
            tree_m.heading(cid, text=cname)
            tree_m.column(cid, width=cwidth, anchor=calign, stretch=(cid in ('codigo', 'descricao')))

        tree_m.tag_configure('cat_hdr', background=THEME['bg_subtle'], foreground=THEME['accent_blue'], font=FONTS['body_b'])
        tree_m.tag_configure('par',     background=THEME['bg_card'], foreground=THEME['text_primary'])
        tree_m.tag_configure('impar',   background=THEME['bg_card_alt'], foreground=THEME['text_primary'])

        vsb = ttk.Scrollbar(tbl_frame, orient='vertical', command=tree_m.yview)
        tree_m.configure(yscrollcommand=vsb.set)
        tree_m.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        def _popular_metricas(*_):
            tree_m.delete(*tree_m.get_children())
            cat_sel = var_cat.get()
            termo = var_busca_f.get().strip().lower()
            cat_atual = None
            row_counter = 0

            for f in features_ia:
                if cat_sel != opcoes_cat[0] and f['categoria'] != cat_sel:
                    continue
                if termo and (termo not in f['codigo'].lower() and termo not in f['descricao'].lower() and termo not in f['categoria'].lower()):
                    continue

                if f['categoria'] != cat_atual:
                    cat_atual = f['categoria']
                    tree_m.insert('', 'end', values=(
                        "━━",
                        f"📂 {cat_atual.upper()}",
                        "━━━",
                        f"🏠 {m_curto}",
                        f"✈️ {v_curto}",
                        "Categoria de Features da IA"
                    ), tags=('cat_hdr',))

                tag_linha = 'impar' if row_counter % 2 == 1 else 'par'
                row_counter += 1
                tree_m.insert('', 'end', values=(
                    f"{f['num']:02d}",
                    f['codigo'],
                    f['valor_bruto'],
                    f['val_m'],
                    f['val_v'],
                    f['descricao']
                ), tags=(tag_linha,))

        cb_cat.bind('<<ComboboxSelected>>', _popular_metricas)
        var_busca_f.trace_add('write', _popular_metricas)
        _popular_metricas()

        # Rodapé de Sequência Recente
        box_seq = tk.Frame(sec, bg=THEME['bg_subtle'], pady=8, padx=12)
        box_seq.pack(fill='x', pady=(8, 0))
        seq_m_val = self.jogo.get('Sequencia_5_Mandante', self.jogo.get('Seq_5_M', '-'))
        seq_v_val = self.jogo.get('Sequencia_5_Visitante', self.jogo.get('Seq_5_V', '-'))
        seq_text = (
            f"Sequência Últimos 5 Jogos:   🏠 {m}: {seq_m_val}   │   ✈️ {v}: {seq_v_val}   │   "
            f"Total de Features Ativas: {len(features_ia)} variáveis verificadas"
        )
        tk.Label(box_seq, text=seq_text, font=FONTS['body_b'], fg=THEME['accent_blue'], bg=THEME['bg_subtle']).pack(anchor='w')


    # ── TAB 2.5: DESEMPENHO (CASA E FORA) ────────────────────────────────────
    def _render_tab_desempenho(self, parent, m: str, v: str):
        data_jogo = self.jogo.get('Data_Datetime')
        if pd.isna(data_jogo): data_jogo = pd.Timestamp.now()
        
        jogos_m = self.gerenciador.obter_ultimos_jogos(m, 'casa', data_jogo, 5)
        jogos_v = self.gerenciador.obter_ultimos_jogos(v, 'fora', data_jogo, 5)
        
        # Estatísticas de força
        def calc_stats(jogos):
            if not jogos: return 0, 0, 0, 0
            v = sum(1 for j in jogos if j['gols_pro'] > j['gols_contra'])
            e = sum(1 for j in jogos if j['gols_pro'] == j['gols_contra'])
            d = sum(1 for j in jogos if j['gols_pro'] < j['gols_contra'])
            gp = sum(j['gols_pro'] for j in jogos)
            gc = sum(j['gols_contra'] for j in jogos)
            aprov = ((v * 3) + e) / (len(jogos) * 3)
            return v, e, d, gp, gc, aprov

        vm, em, dm, gpm, gcm, aprov_m = calc_stats(jogos_m)
        vv, ev, dv, gpv, gcv, aprov_v = calc_stats(jogos_v)
        
        sec_stats = tk.Frame(parent, bg=THEME['bg_card'])
        sec_stats.pack(fill='x', pady=10)
        
        tk.Label(sec_stats, text="Estatísticas de Força (Últimos 5 jogos)", font=FONTS['header'], fg=THEME['text_primary'], bg=THEME['bg_card']).pack(anchor='center', pady=(0, 10))
        
        f_cols = tk.Frame(sec_stats, bg=THEME['bg_card'])
        f_cols.pack(fill='x')
        
        # Mandante
        f_m = tk.Frame(f_cols, bg=THEME['bg_subtle'], padx=10, pady=10, highlightbackground=THEME['border'], highlightthickness=1)
        f_m.pack(side='left', fill='both', expand=True, padx=5)
        tk.Label(f_m, text=f"🏠 {m} (Em Casa)", font=FONTS['body_b'], fg=THEME['accent_blue'], bg=THEME['bg_subtle']).pack()
        tk.Label(f_m, text=f"{vm}V - {em}E - {dm}D | GP: {gpm} GC: {gcm}", font=FONTS['body'], fg=THEME['text_primary'], bg=THEME['bg_subtle']).pack()
        tk.Label(f_m, text=f"Aproveitamento: {aprov_m:.0%}", font=FONTS['badge'], fg=THEME['win'] if aprov_m >= 0.5 else THEME['loss'], bg=THEME['bg_subtle']).pack()
        
        # Visitante
        f_v = tk.Frame(f_cols, bg=THEME['bg_subtle'], padx=10, pady=10, highlightbackground=THEME['border'], highlightthickness=1)
        f_v.pack(side='right', fill='both', expand=True, padx=5)
        tk.Label(f_v, text=f"✈️ {v} (Fora de Casa)", font=FONTS['body_b'], fg=THEME['accent_indigo'], bg=THEME['bg_subtle']).pack()
        tk.Label(f_v, text=f"{vv}V - {ev}E - {dv}D | GP: {gpv} GC: {gcv}", font=FONTS['body'], fg=THEME['text_primary'], bg=THEME['bg_subtle']).pack()
        tk.Label(f_v, text=f"Aproveitamento: {aprov_v:.0%}", font=FONTS['badge'], fg=THEME['win'] if aprov_v >= 0.5 else THEME['loss'], bg=THEME['bg_subtle']).pack()
        
        # Listas de jogos
        tk.Label(parent, text="Últimos Confrontos (Casa / Fora)", font=FONTS['header'], fg=THEME['text_primary'], bg=THEME['bg_card']).pack(anchor='w', pady=(15, 5))
        
        cols = ('time', 'data', 'comp', 'adv', 'placar', 'res')
        tree = ttk.Treeview(parent, columns=cols, show='headings', height=10)
        tree.heading('time', text='Time (Local)')
        tree.heading('data', text='Data')
        tree.heading('comp', text='Competição')
        tree.heading('adv', text='Adversário')
        tree.heading('placar', text='Placar')
        tree.heading('res', text='R')
        
        tree.column('time', width=120)
        tree.column('data', width=90, anchor='center')
        tree.column('comp', width=120)
        tree.column('adv', width=120)
        tree.column('placar', width=70, anchor='center')
        tree.column('res', width=40, anchor='center')
        
        for j in jogos_m:
            res = 'V' if j['gols_pro'] > j['gols_contra'] else ('E' if j['gols_pro'] == j['gols_contra'] else 'D')
            tree.insert('', 'end', values=(f"🏠 {m}", j['data'].strftime('%d/%m/%Y'), j['competicao'], j['adversario'], j['placar'], res), tags=(res,))
            
        tree.insert('', 'end', values=("---", "---", "---", "---", "---", "---"))
        
        for j in jogos_v:
            res = 'V' if j['gols_pro'] > j['gols_contra'] else ('E' if j['gols_pro'] == j['gols_contra'] else 'D')
            tree.insert('', 'end', values=(f"✈️ {v}", j['data'].strftime('%d/%m/%Y'), j['competicao'], j['adversario'], j['placar'], res), tags=(res,))
            
        tree.tag_configure('V', foreground=THEME['win'])
        tree.tag_configure('E', foreground=THEME['draw'])
        tree.tag_configure('D', foreground=THEME['loss'])
        tree.pack(fill='both', expand=True)

    # ── TAB 2.6: TABELA DO CAMPEONATO ────────────────────────────────────────
    def _render_tab_tabela(self, parent):
        comp = self.jogo.get('Competicao')
        ano = self.jogo.get('Ano')
        data_jogo = self.jogo.get('Data_Datetime')
        
        if pd.isna(ano) or pd.isna(data_jogo) or not comp:
            tk.Label(parent, text="Dados insuficientes para gerar a tabela.", fg=THEME['text_primary'], bg=THEME['bg_card']).pack()
            return
            
        df_tab = self.gerenciador.obter_tabela_campeonato(comp, int(ano), data_jogo)
        if df_tab.empty:
            tk.Label(parent, text="Tabela não disponível para este campeonato/fase.", fg=THEME['text_primary'], bg=THEME['bg_card']).pack()
            return
            
        tk.Label(parent, text=f"📋 Classificação - {comp} (até {data_jogo.strftime('%d/%m/%Y')})", font=FONTS['header'], fg=THEME['text_primary'], bg=THEME['bg_card']).pack(pady=(0, 10))
        
        cols = ('pos', 'time', 'p', 'j', 'v', 'e', 'd', 'gp', 'gc', 'sg')
        tree = ttk.Treeview(parent, columns=cols, show='headings', height=20)
        
        headers = [
            ('pos', 'Pos', 40, 'center'), ('time', 'Time', 180, 'w'),
            ('p', 'Pts', 40, 'center'), ('j', 'J', 40, 'center'),
            ('v', 'V', 40, 'center'), ('e', 'E', 40, 'center'),
            ('d', 'D', 40, 'center'), ('gp', 'GP', 40, 'center'),
            ('gc', 'GC', 40, 'center'), ('sg', 'SG', 40, 'center')
        ]
        
        for c, n, w, a in headers:
            tree.heading(c, text=n)
            tree.column(c, width=w, anchor=a)
            
        for _, r in df_tab.iterrows():
            vals = (r['Pos'], r['Time'], r['P'], r['J'], r['V'], r['E'], r['D'], r['GP'], r['GC'], r['SG'])
            tag = 'destaque' if r['Time'] in (self.jogo.get('Time da Casa'), self.jogo.get('Time Visitante')) else ''
            tree.insert('', 'end', values=vals, tags=(tag,))
            
        tree.tag_configure('destaque', background=THEME['bg_subtle'], foreground=THEME['accent_blue'])
        
        vsb = ttk.Scrollbar(parent, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

    # ── TAB 3: H2H CONFRONTO DIRETO ───────────────────────────────────────────
    def _render_tab_h2h(self, parent, m: str, v: str):
        h2h_geral = self.gerenciador.obter_h2h_completo(m, v)
        tot_geral = h2h_geral['total_geral']

        # Top Frame com Título e Filtro de Competição
        top = tk.Frame(parent, bg=THEME['bg_card'])
        top.pack(fill='x', pady=(0, 6))

        top_left = tk.Frame(top, bg=THEME['bg_card'])
        top_left.pack(side='left', fill='x', expand=True)

        lbl_tot = tk.Label(
            top_left,
            text=f"Histórico Geral Mútuo: {tot_geral} confrontos registrados",
            font=FONTS['header'], fg=THEME['text_primary'], bg=THEME['bg_card']
        )
        lbl_tot.pack(anchor='w')

        # Subtítulo com período histórico
        txt_periodo = "Acumulado de todas as competições desde a 1ª edição"
        p_ini = h2h_geral.get('primeiro_jogo')
        p_fim = h2h_geral.get('ultimo_jogo')
        if p_ini and p_fim and p_ini.get('data') and p_fim.get('data'):
            dt_ini_str = p_ini['data'].strftime('%d/%m/%Y')
            dt_fim_str = p_fim['data'].strftime('%d/%m/%Y')
            txt_periodo = f"Histórico desde {dt_ini_str} até {dt_fim_str} ({tot_geral} jogos registrados)"
        elif tot_geral > 0:
            txt_periodo = f"Total de {tot_geral} partidas registradas em todas as competições"

        lbl_periodo = tk.Label(
            top_left, text=txt_periodo,
            font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_card']
        )
        lbl_periodo.pack(anchor='w')

        # Filtro de Competição à Direita
        top_right = tk.Frame(top, bg=THEME['bg_card'])
        top_right.pack(side='right', padx=(10, 0))

        tk.Label(
            top_right, text="Filtrar Competição:",
            font=FONTS['card_lbl'], fg=THEME['text_secondary'], bg=THEME['bg_card']
        ).pack(anchor='e')

        comps_disponiveis = ['Todas as Competições'] + h2h_geral.get('competicoes', [])
        var_comp_filtro = tk.StringVar(value='Todas as Competições')
        cb_comp_filtro = ttk.Combobox(
            top_right, textvariable=var_comp_filtro, values=comps_disponiveis,
            state='readonly', width=24, font=FONTS['body']
        )
        cb_comp_filtro.pack(anchor='e', pady=(2, 0))

        # Barra H2H
        barra = BarraH2HVisual(
            parent,
            v_m=h2h_geral['vits_m_geral'],
            emp=h2h_geral['empates_geral'],
            v_v=h2h_geral['vits_v_geral'],
            altura=32
        )
        barra.pack(fill='x', pady=6)

        # Legenda com Placar Geral e Gols
        legenda = tk.Frame(parent, bg=THEME['bg_card'])
        legenda.pack(fill='x', pady=(0, 8))

        lbl_leg_m = tk.Label(legenda, text="", fg=THEME['win'], bg=THEME['bg_card'], font=FONTS['body_b'])
        lbl_leg_m.pack(side='left', padx=(0, 14))

        lbl_leg_e = tk.Label(legenda, text="", fg=THEME['draw'], bg=THEME['bg_card'], font=FONTS['body_b'])
        lbl_leg_e.pack(side='left', padx=14)

        lbl_leg_v = tk.Label(legenda, text="", fg=THEME['loss'], bg=THEME['bg_card'], font=FONTS['body_b'])
        lbl_leg_v.pack(side='left', padx=14)

        # Resumo com Mando de Campo
        box_mando = tk.Frame(parent, bg=THEME['bg_subtle'], padx=10, pady=6)
        box_mando.pack(fill='x', pady=(0, 8))
        lbl_mando = tk.Label(box_mando, text="", font=FONTS['body'], fg=THEME['text_secondary'], bg=THEME['bg_subtle'])
        lbl_mando.pack(anchor='w')

        # Título da Tabela
        lbl_tbl_tit = tk.Label(parent, text="", font=FONTS['header'], fg=THEME['text_secondary'], bg=THEME['bg_card'])
        lbl_tbl_tit.pack(anchor='w', pady=(2, 4))

        # Tabela de Confrontos com Scrollbar
        tbl_frame = tk.Frame(parent, bg=THEME['bg_card'])
        tbl_frame.pack(fill='both', expand=True)

        cols = ('Data', 'Competição', 'Fase', 'Mandante', 'Placar', 'Visitante')
        t = ttk.Treeview(tbl_frame, columns=cols, show='headings', height=8)

        t.heading('Data', text='Data')
        t.column('Data', width=95, anchor='center')
        t.heading('Competição', text='Competição')
        t.column('Competição', width=180, anchor='w')
        t.heading('Fase', text='Fase / Rodada')
        t.column('Fase', width=120, anchor='center')
        t.heading('Mandante', text='Mandante')
        t.column('Mandante', width=140, anchor='w')
        t.heading('Placar', text='Placar')
        t.column('Placar', width=75, anchor='center')
        t.heading('Visitante', text='Visitante')
        t.column('Visitante', width=140, anchor='w')

        t.tag_configure('vit_m', background='#0b2219', foreground=THEME['text_primary'])
        t.tag_configure('emp',   background='#1f1c10', foreground=THEME['text_primary'])
        t.tag_configure('vit_v', background='#221115', foreground=THEME['text_primary'])

        vsb = ttk.Scrollbar(tbl_frame, orient='vertical', command=t.yview)
        t.configure(yscrollcommand=vsb.set)
        t.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        m_canon = canonicalizar_nome_time(m)

        def _atualizar_visual(comp_sel: str):
            dados = self.gerenciador.obter_h2h_completo(m, v, competicao=comp_sel)
            tot = dados['total_geral']
            vm = dados['vits_m_geral']
            vv = dados['vits_v_geral']
            emp = dados['empates_geral']

            # Atualiza barra
            barra.atualizar(vm, emp, vv)

            # Atualiza legendas
            lbl_leg_m.config(text=f"■ Vitórias {m}: {vm} ({dados['gols_m_geral']} gols)")
            lbl_leg_e.config(text=f"■ Empates: {emp}")
            lbl_leg_v.config(text=f"■ Vitórias {v}: {vv} ({dados['gols_v_geral']} gols)")

            # Atualiza texto do mando
            if dados['total_mando'] > 0:
                box_mando.pack(fill='x', pady=(0, 8), before=lbl_tbl_tit)
                txt_mando = (
                    f"🏟️ No mando de {m}: {dados['total_mando']} jogos  •  "
                    f"{dados['vits_m_mando']} vitórias ({dados['taxa_m_mando']:.0%}), "
                    f"{dados['empates_mando']} empates, {dados['vits_v_mando']} vitórias de {v}"
                )
                lbl_mando.config(text=txt_mando)
            else:
                box_mando.pack_forget()

            # Título da tabela
            sufixo_comp = f" — {comp_sel}" if comp_sel != 'Todas as Competições' else " — Todas as Competições"
            lbl_tbl_tit.config(text=f"Histórico Completo de Confrontos Diretos ({tot} jogos{sufixo_comp}):")

            # Popula Treeview com TODOS os jogos do confronto (sem truncamento)
            t.delete(*t.get_children())
            for j in dados['jogos']:
                dt_s = j['data'].strftime('%d/%m/%Y') if j.get('data') else '-'
                gm = j.get('gols_m', 0)
                gv = j.get('gols_v', 0)

                # Cor de acordo com o resultado sob a ótica da equipe `m`
                mandante_jogo = canonicalizar_nome_time(j.get('mandante', ''))
                eh_m_mandante = (mandante_jogo == m_canon)
                if gm == gv:
                    tag = 'emp'
                elif (eh_m_mandante and gm > gv) or (not eh_m_mandante and gv > gm):
                    tag = 'vit_m'
                else:
                    tag = 'vit_v'

                t.insert('', 'end', values=(
                    dt_s, j.get('competicao', '-'), j.get('fase', '-'),
                    j.get('mandante', '-'), j.get('placar', '-'), j.get('visitante', '-')
                ), tags=(tag,))

        cb_comp_filtro.bind('<<ComboboxSelected>>', lambda e: _atualizar_visual(var_comp_filtro.get()))
        _atualizar_visual('Todas as Competições')

    # ── TAB 4: IA & DIAGNÓSTICO TÁTICO (TODAS AS 42 FEATURES) ────────────────
    def _render_tab_ia(self, parent, m: str, v: str):
        data_jogo = self.jogo.get('Data_Datetime')
        ctx_m = self.gerenciador.obter_contexto_copa(m, data_jogo)
        ctx_v = self.gerenciador.obter_contexto_copa(v, data_jogo)
        h2h_info = self.gerenciador.obter_h2h_completo(m, v, data_limite=data_jogo)

        aval = avaliar_features_ia(self.jogo, ctx_m=ctx_m, ctx_v=ctx_v, h2h=h2h_info)
        features_ia = aval['features']
        categorias = aval.get('categorias', [])
        resumo_cats = {r['categoria']: r for r in aval.get('resumo_categorias', [])}
        total_features = aval.get('total_features', len(features_ia))
        total_pts_m = aval['total_pts_m']
        total_pts_v = aval['total_pts_v']
        pct_score_m = aval['pct_score_m']
        pct_score_v = aval['pct_score_v']
        diff_total = aval['diff_total']
        vits_feat_m = aval['vits_feat_m']
        vits_feat_v = aval['vits_feat_v']
        emp_feat = aval['emp_feat']

        des_m = float(self.jogo.get('Desespero_Mandante', 0) or 0)
        des_v = float(self.jogo.get('Desespero_Visitante', 0) or 0)
        soberba = float(self.jogo.get('Risco_Soberba', 0) or 0)
        alerta_copa = str(self.jogo.get('Alerta_Copa', '-') or '-')
        prob_m = float(self.jogo.get('Prob_Vit_M', 0.44) or 0.44)
        prob_e = float(self.jogo.get('Prob_Emp', 0.28) or 0.28)
        prob_v = float(self.jogo.get('Prob_Vit_V', 0.28) or 0.28)
        favorito = str(self.jogo.get('Favorito', 'Equilibrado') or 'Equilibrado')
        zebra = str(self.jogo.get('Zebra', 'Normal') or 'Normal')

        # ── 1. Painel Superior: Probabilidades & Placar Geral de Features ──
        box_probs = tk.Frame(parent, bg=THEME['bg_subtle'], padx=14, pady=6, highlightbackground=THEME['border'], highlightthickness=1)
        box_probs.pack(fill='x', pady=(0, 6))

        tk.Label(
            box_probs,
            text=f"PROBABILIDADES ESTIMADAS & PONTUAÇÃO CONSOLIDADA DA IA ({total_features} FEATURES EM 7 CATEGORIAS):",
            font=FONTS['card_lbl'], fg=THEME['accent_blue'], bg=THEME['bg_subtle']
        ).pack(anchor='w')

        barra_prob = tk.Frame(box_probs, bg=THEME['bg_subtle'], pady=2)
        barra_prob.pack(fill='x')

        col_m = tk.Frame(barra_prob, bg=THEME['bg_subtle'])
        col_m.pack(side='left', expand=True, fill='x')
        tk.Label(col_m, text=f"🏠 {m}", font=FONTS['body_b'], fg=THEME['win'], bg=THEME['bg_subtle']).pack()
        tk.Label(col_m, text=f"{prob_m:.1%}", font=FONTS['card_kpi'], fg=THEME['win'], bg=THEME['bg_subtle']).pack()
        tk.Label(col_m, text=f"Score IA: {total_pts_m:.2f} pts ({vits_feat_m}V)", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_subtle']).pack()

        col_e = tk.Frame(barra_prob, bg=THEME['bg_subtle'])
        col_e.pack(side='left', expand=True, fill='x')
        tk.Label(col_e, text="🟡 Empate", font=FONTS['body_b'], fg=THEME['draw'], bg=THEME['bg_subtle']).pack()
        tk.Label(col_e, text=f"{prob_e:.1%}", font=FONTS['card_kpi'], fg=THEME['draw'], bg=THEME['bg_subtle']).pack()
        tk.Label(col_e, text=f"Features Neutras: {emp_feat}", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_subtle']).pack()

        col_v = tk.Frame(barra_prob, bg=THEME['bg_subtle'])
        col_v.pack(side='left', expand=True, fill='x')
        tk.Label(col_v, text=f"✈️ {v}", font=FONTS['body_b'], fg=THEME['loss'], bg=THEME['bg_subtle']).pack()
        tk.Label(col_v, text=f"{prob_v:.1%}", font=FONTS['card_kpi'], fg=THEME['loss'], bg=THEME['bg_subtle']).pack()
        tk.Label(col_v, text=f"Score IA: {total_pts_v:.2f} pts ({vits_feat_v}V)", font=FONTS['badge'], fg=THEME['text_secondary'], bg=THEME['bg_subtle']).pack()

        col_saldo = tk.Frame(barra_prob, bg=THEME['bg_subtle'])
        col_saldo.pack(side='left', expand=True, fill='x')
        cor_saldo = THEME['win'] if diff_total > 0.5 else (THEME['loss'] if diff_total < -0.5 else THEME['draw'])
        lider_nome = m[:14] if diff_total > 0.5 else (v[:14] if diff_total < -0.5 else "Equilíbrio")
        tk.Label(col_saldo, text="⚖️ Saldo Comparativo", font=FONTS['body_b'], fg=THEME['accent_blue'], bg=THEME['bg_subtle']).pack()
        tk.Label(col_saldo, text=f"{diff_total:+.2f} pts", font=FONTS['card_kpi'], fg=cor_saldo, bg=THEME['bg_subtle']).pack()
        tk.Label(col_saldo, text=f"Vantagem: {lider_nome}", font=FONTS['badge'], fg=cor_saldo, bg=THEME['bg_subtle']).pack()

        sub_prob = tk.Frame(box_probs, bg=THEME['bg_subtle'], pady=1)
        sub_prob.pack(fill='x')
        tk.Label(
            sub_prob,
            text=(
                f"Favoritismo: {favorito}   │   Risco de Zebra: {zebra}   │   "
                f"Proporção de Pontos: {m} ({pct_score_m:.1%}) vs {v} ({pct_score_v:.1%})   │   "
                f"Placar de Features: {vits_feat_m} Casa x {emp_feat} Neutras x {vits_feat_v} Fora"
            ),
            font=FONTS['body_b'], fg=THEME['text_primary'], bg=THEME['bg_subtle']
        ).pack(anchor='w')

        # ── 2. Cabeçalho e Filtros da Tabela de 42 Features ───────────────
        hdr_feat = tk.Frame(parent, bg=THEME['bg_card'])
        hdr_feat.pack(fill='x', pady=(0, 4))
        tk.Label(
            hdr_feat,
            text=f"📊 RAIO-X MANUAL DE TODAS AS {total_features} FEATURES USADAS PELA IA:",
            font=FONTS['header'], fg=THEME['accent_blue'], bg=THEME['bg_card']
        ).pack(side='left')

        ctrl_feat = tk.Frame(hdr_feat, bg=THEME['bg_card'])
        ctrl_feat.pack(side='right')

        tk.Label(
            ctrl_feat, text="Filtrar Grupo:", font=FONTS['badge'],
            fg=THEME['text_secondary'], bg=THEME['bg_card']
        ).pack(side='left', padx=(0, 4))

        opcoes_grupo = [f"Todas as 7 Categorias ({total_features} Features)"] + categorias
        var_grupo_ia = tk.StringVar(value=opcoes_grupo[0])
        cb_grupo_ia = ttk.Combobox(
            ctrl_feat, textvariable=var_grupo_ia, values=opcoes_grupo,
            state='readonly', width=34, font=FONTS['body']
        )
        cb_grupo_ia.pack(side='left', padx=(0, 8))

        tk.Label(
            ctrl_feat, text="🔍", font=FONTS['badge'],
            fg=THEME['text_secondary'], bg=THEME['bg_card']
        ).pack(side='left')
        var_busca_ia = tk.StringVar()
        ent_busca_ia = tk.Entry(
            ctrl_feat, textvariable=var_busca_ia, width=14, font=FONTS['body'],
            bg=THEME['bg_subtle'], fg=THEME['text_primary'], insertbackground='#ffffff', relief='flat'
        )
        ent_busca_ia.pack(side='left', padx=(2, 0))

        # ── 3. Tabela Treeview com Todas as 42 Features ───────────────────
        tbl_feat_frame = tk.Frame(parent, bg=THEME['bg_card'], highlightbackground=THEME['border'], highlightthickness=1)
        tbl_feat_frame.pack(fill='both', expand=True, pady=(0, 4))

        cols_ia = ('feature', 'valor_bruto', 'val_m', 'pts_m', 'pts_v', 'val_v', 'comp')
        tree_ia = ttk.Treeview(tbl_feat_frame, columns=cols_ia, show='headings', height=11)

        m_curto = m[:12]
        v_curto = v[:12]
        col_defs = [
            ('feature',     'Feature Usada (42 Variáveis)',    215, 'w'),
            ('valor_bruto', 'Valor da Feature',                145, 'center'),
            ('val_m',       f'🏠 {m_curto}',                   135, 'center'),
            ('pts_m',       f'🏠 Pts ({m[:8]})',                82,  'center'),
            ('pts_v',       f'✈️ Pts ({v[:8]})',                82,  'center'),
            ('val_v',       f'✈️ {v_curto}',                   135, 'center'),
            ('comp',        '⚖️ Comparativo IA / Leitura',     235, 'w'),
        ]
        for cid, cname, cwidth, calign in col_defs:
            tree_ia.heading(cid, text=cname)
            tree_ia.column(cid, width=cwidth, anchor=calign, stretch=(cid in ('feature', 'comp')))

        tree_ia.tag_configure('cat_ia',   background='#16243b', foreground=THEME['accent_blue'], font=FONTS['body_b'])
        tree_ia.tag_configure('vant_m',   background='#0b2219', foreground=THEME['text_primary'])
        tree_ia.tag_configure('vant_v',   background='#221115', foreground=THEME['text_primary'])
        tree_ia.tag_configure('emp_f',    background=THEME['bg_card'], foreground=THEME['text_secondary'])
        tree_ia.tag_configure('total_ia', background=THEME['bg_subtle'], foreground=THEME['accent_blue'], font=FONTS['body_b'])

        vsb_ia = ttk.Scrollbar(tbl_feat_frame, orient='vertical', command=tree_ia.yview)
        tree_ia.configure(yscrollcommand=vsb_ia.set)
        tree_ia.pack(side='left', fill='both', expand=True)
        vsb_ia.pack(side='right', fill='y')

        if diff_total > 0.05:
            comp_tot_str = f"🟢 +{diff_total:.2f} pts {m_curto}"
        elif diff_total < -0.05:
            comp_tot_str = f"🔴 +{abs(diff_total):.2f} pts {v_curto}"
        else:
            comp_tot_str = "🟡 Empate Técnico (0.00)"

        mapa_iid_feature = {}

        def _popular_tabela_ia(*_):
            tree_ia.delete(*tree_ia.get_children())
            mapa_iid_feature.clear()
            grp_sel = var_grupo_ia.get()
            termo = var_busca_ia.get().strip().lower()
            cat_atual = None

            for f in features_ia:
                if grp_sel != opcoes_grupo[0] and f['categoria'] != grp_sel:
                    continue
                if termo and (
                    termo not in f['codigo'].lower()
                    and termo not in f['descricao'].lower()
                    and termo not in f['categoria'].lower()
                    and termo not in f['valor_bruto'].lower()
                ):
                    continue

                if f['categoria'] != cat_atual:
                    cat_atual = f['categoria']
                    rc = resumo_cats.get(cat_atual, {})
                    pm_c = rc.get('pts_m', 0.0)
                    pv_c = rc.get('pts_v', 0.0)
                    df_c = rc.get('diff', 0.0)
                    qtd_c = rc.get('qtd_features', 0)
                    res_cat_str = (
                        f"Subtotal Grupo: 🟢 +{df_c:.2f} {m_curto}" if df_c > 0.05
                        else (f"Subtotal Grupo: 🔴 +{abs(df_c):.2f} {v_curto}" if df_c < -0.05 else "Subtotal Grupo: 🟡 Equilibrado")
                    )
                    tree_ia.insert('', 'end', values=(
                        f"📂 {cat_atual.upper()}",
                        f"{qtd_c} features",
                        f"Subtotal {m_curto}",
                        f"{pm_c:.2f} pts",
                        f"{pv_c:.2f} pts",
                        f"Subtotal {v_curto}",
                        res_cat_str
                    ), tags=('cat_ia',))

                tag = 'vant_m' if f['vencedor'] == 'M' else ('vant_v' if f['vencedor'] == 'V' else 'emp_f')
                iid_f = f"feat_{f['num']}"
                mapa_iid_feature[iid_f] = f
                tree_ia.insert('', 'end', iid=iid_f, values=(
                    f['nome'],
                    f['valor_bruto'],
                    f['val_m'],
                    f"{f['pts_m']:.2f} pts",
                    f"{f['pts_v']:.2f} pts",
                    f['val_v'],
                    f['comparativo_str']
                ), tags=(tag,))

            tree_ia.insert('', 'end', values=(
                f"🏆 PONTUAÇÃO TOTAL ({total_features} FEATURES)",
                f"{vits_feat_m}M / {emp_feat}E / {vits_feat_v}V",
                f"{vits_feat_m} vencidas ({pct_score_m:.1%})",
                f"{total_pts_m:.2f} pts",
                f"{total_pts_v:.2f} pts",
                f"{vits_feat_v} vencidas ({pct_score_v:.1%})",
                comp_tot_str
            ), tags=('total_ia',))

        # Barra interativa de descrição da feature selecionada
        lbl_detalhe_feat = tk.Label(
            parent,
            text="💡 Clique em qualquer uma das 42 features na tabela acima para ver sua definição exata e valor bruto.",
            font=FONTS['subtitle'], fg=THEME['accent_blue'], bg=THEME['bg_subtle'],
            anchor='w', padx=10, pady=4
        )
        lbl_detalhe_feat.pack(fill='x', pady=(0, 4))

        def _ao_selecionar_feat(_=None):
            sel = tree_ia.selection()
            if sel and sel[0] in mapa_iid_feature:
                f = mapa_iid_feature[sel[0]]
                lbl_detalhe_feat.config(
                    text=(
                        f"🔎 [{f['categoria']}]  {f['codigo']}: {f['descricao']}   │   "
                        f"Valor: {f['valor_bruto']}   │   {m_curto}: {f['pts_m']:.2f} pts vs {v_curto}: {f['pts_v']:.2f} pts"
                    )
                )

        tree_ia.bind('<<TreeviewSelect>>', _ao_selecionar_feat)
        cb_grupo_ia.bind('<<ComboboxSelected>>', _popular_tabela_ia)
        var_busca_ia.trace_add('write', _popular_tabela_ia)
        _popular_tabela_ia()

        # ── 4. Caixa de Texto com Relatório Tático & Recomendação ─────────
        box_txt_frame = tk.Frame(parent, bg=THEME['bg_card'])
        box_txt_frame.pack(fill='x', pady=(0, 4))

        texto_box = tk.Text(
            box_txt_frame, bg=THEME['bg_subtle'], fg=THEME['text_primary'], font=FONTS['body'],
            relief='flat', highlightbackground=THEME['border'], highlightthickness=1,
            padx=12, pady=6, height=4
        )
        vsb_txt = ttk.Scrollbar(box_txt_frame, orient='vertical', command=texto_box.yview)
        texto_box.configure(yscrollcommand=vsb_txt.set)
        texto_box.pack(side='left', fill='x', expand=True)
        vsb_txt.pack(side='right', fill='y')

        linhas_features_txt = [
            f"📊 RAIO-X COMPLETO DE TODAS AS {total_features} FEATURES DA IA ({m} x {v}):",
            "=" * 108,
            f"{'FEATURE (42 VARIÁVEIS)'.ljust(33)} | {'VALOR BRUTO'.ljust(20)} | {('🏠 ' + m[:10]).ljust(18)} | {'PTS M'.rjust(6)} | {'PTS V'.rjust(6)} | {('✈️ ' + v[:10]).ljust(18)} | COMPARATIVO",
            "=" * 108,
        ]
        cat_txt_atual = None
        for f in features_ia:
            if f['categoria'] != cat_txt_atual:
                cat_txt_atual = f['categoria']
                linhas_features_txt.append(f"\n--- [{cat_txt_atual.upper()}] ---")
            linhas_features_txt.append(
                f"{f['nome'].ljust(33)} | {f['valor_bruto'][:20].ljust(20)} | {f['val_m'][:18].ljust(18)} | {f['pts_m']:6.2f} | {f['pts_v']:6.2f} | {f['val_v'][:18].ljust(18)} | {f['comparativo_str']}"
            )
        linhas_features_txt.extend([
            "=" * 108,
            f"{f'🏆 TOTAL GERAL ({total_features} FEATURES)'.ljust(33)} | {(f'{vits_feat_m}M/{emp_feat}E/{vits_feat_v}V').ljust(20)} | {(str(vits_feat_m) + ' vencidas').ljust(18)} | {total_pts_m:6.2f} | {total_pts_v:6.2f} | {(str(vits_feat_v) + ' vencidas').ljust(18)} | {comp_tot_str}",
            ""
        ])

        relatorio_sintese = [
            f"🎯 SÍNTESE ANALÍTICA DA PARTIDA: {m.upper()} x {v.upper()} ({total_features} Features Verificadas)",
            f"• Score Total IA: {m} ({total_pts_m:.2f} pts / {pct_score_m:.1%}) x {v} ({total_pts_v:.2f} pts / {pct_score_v:.1%}) — Saldo: {diff_total:+.2f} pts",
            f"• Situação de Copa: {alerta_copa} │ Risco de Soberba/Poupar: {'ALTO ⚠️' if soberba > 0.4 else ('MODERADO ⚡' if soberba > 0.1 else 'BAIXO ✅')} │ Clássico: {'SIM ⚡' if self.jogo.get('É_Clássico', 0) == 1 else 'Não'}",
        ]

        if soberba > 0.3:
            relatorio_sintese.append("• Diagnóstico: ⚠️ Equipe com foco dividido por compromisso decisivo de Copa ou risco de relaxamento. Atenção à escalação.")
        elif des_m > des_v + 0.3:
            relatorio_sintese.append(f"• Diagnóstico: 🔥 Mandante ({m}) sob pressão de tabela. Fator campo potencializado pela necessidade extrema de vitória.")
        elif des_v > des_m + 0.3:
            relatorio_sintese.append(f"• Diagnóstico: 🛡️ Visitante ({v}) entra com urgência de pontuar fora de casa. Tendência de postura competitiva e transições rápidas.")
        else:
            relatorio_sintese.append("• Diagnóstico: ⚖️ Confronto pautado pelo equilíbrio técnico, retrospecto H2H e aproveitamento recente no mando.")

        col_prov = 'Coluna 1 (Mandante)' if prob_m > prob_v and prob_m > 0.45 else ('Coluna 2 (Visitante)' if prob_v > prob_m and prob_v > 0.45 else 'Coluna do Meio (Empate) / Duplo Aberto')
        prot_rec = 'Duplo 1X' if prob_m >= prob_v else 'Duplo X2'
        relatorio_sintese.append(f"• Sugestão Loteca: {col_prov}   │   Proteção Recomendada: {prot_rec}")

        texto_visivel = "\n".join(relatorio_sintese)
        texto_completo_clipboard = "\n".join(linhas_features_txt + relatorio_sintese)

        texto_box.insert('1.0', texto_visivel)
        texto_box.config(state='disabled')

        # ── 5. Barra de Ações Inferior ────────────────────────────────────
        btn_bar = tk.Frame(parent, bg=THEME['bg_card'], pady=4)
        btn_bar.pack(fill='x')

        def _copiar_analise():
            self.clipboard_clear()
            self.clipboard_append(texto_completo_clipboard)
            messagebox.showinfo("Copiado!", f"Relatório completo com todas as {total_features} features e diagnóstico copiado para a área de transferência!")

        btn_copiar = tk.Button(
            btn_bar, text=f"📋 Copiar Análise + {total_features} Features", command=_copiar_analise,
            bg=THEME['accent_indigo'], fg='#ffffff', font=FONTS['body_b'],
            relief='flat', padx=12, pady=4, cursor='hand2', activebackground='#4f46e5'
        )
        btn_copiar.pack(side='left')

        btn_fechar = tk.Button(
            btn_bar, text="Fechar", command=self.destroy,
            bg=THEME['bg_subtle'], fg=THEME['text_primary'], font=FONTS['body'],
            relief='flat', padx=16, pady=4, cursor='hand2'
        )
        btn_fechar.pack(side='right')

