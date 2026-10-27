"""
LOTECA ANALYTICS PRO — Widget Visual: Barra H2H Segmentada
Canvas personalizado com proporções dinâmicas, percentuais e estética dark moderna.
"""

import tkinter as tk
from config import THEME, FONTS


class BarraH2HVisual(tk.Canvas):
    """
    Barra visual interativa dividida proporcionalmente em 3 blocos:
    - Vitórias do Mandante (Verde)
    - Empates (Âmbar / Laranja)
    - Vitórias do Visitante (Vermelho / Rose)
    """
    def __init__(self, parent, v_m: int = 1, emp: int = 1, v_v: int = 1, altura: int = 30, **kw):
        kw.setdefault('height', altura)
        kw.setdefault('bg', THEME['bg_card'])
        kw.setdefault('highlightthickness', 0)
        kw.setdefault('relief', 'flat')
        super().__init__(parent, **kw)

        self.v_m = max(0, v_m)
        self.emp = max(0, emp)
        self.v_v = max(0, v_v)

        self.bind('<Configure>', lambda e: self.redesenhar())

    def atualizar(self, v_m: int, emp: int, v_v: int):
        """Atualiza os valores e solicita redesenho imediato."""
        self.v_m = max(0, int(v_m))
        self.emp = max(0, int(emp))
        self.v_v = max(0, int(v_v))
        self.redesenhar()

    def redesenhar(self):
        """Desenha a barra proporcional com visual moderno e tags legíveis."""
        self.delete('all')
        W = self.winfo_width()
        H = self.winfo_height()
        if W < 30 or H < 10:
            return

        tot = self.v_m + self.emp + self.v_v
        if tot == 0:
            pct_m, pct_e, pct_v = 0.333, 0.334, 0.333
            tem_dados = False
        else:
            pct_m = self.v_m / tot
            pct_e = self.emp / tot
            pct_v = self.v_v / tot
            tem_dados = True

        wm = int(pct_m * W)
        we = int(pct_e * W)
        wv = W - wm - we

        pad_y = 3
        y1, y2 = pad_y, H - pad_y

        # Segmento Mandante (Verde)
        if wm > 0:
            self.create_rectangle(0, y1, wm, y2, fill=THEME['win'], outline=THEME['bg_main'], width=1)
        # Segmento Empate (Âmbar)
        if we > 0:
            self.create_rectangle(wm, y1, wm + we, y2, fill=THEME['draw'], outline=THEME['bg_main'], width=1)
        # Segmento Visitante (Vermelho)
        if wv > 0:
            self.create_rectangle(wm + we, y1, W, y2, fill=THEME['loss'], outline=THEME['bg_main'], width=1)

        # Textos com porcentagens e quantidades
        font_txt = FONTS['mono_b']
        cor_txt = '#ffffff'

        if tem_dados:
            if wm >= 55:
                txt_m = f"{pct_m:.0%}" + (f" ({self.v_m})" if wm >= 80 else "")
                self.create_text(wm // 2, H // 2, text=txt_m, fill=cor_txt, font=font_txt)
            elif wm >= 35:
                self.create_text(wm // 2, H // 2, text=f"{pct_m:.0%}", fill=cor_txt, font=FONTS['badge'])

            if we >= 55:
                txt_e = f"{pct_e:.0%}" + (f" ({self.emp})" if we >= 80 else "")
                self.create_text(wm + (we // 2), H // 2, text=txt_e, fill=cor_txt, font=font_txt)
            elif we >= 35:
                self.create_text(wm + (we // 2), H // 2, text=f"{pct_e:.0%}", fill=cor_txt, font=FONTS['badge'])

            if wv >= 55:
                txt_v = f"{pct_v:.0%}" + (f" ({self.v_v})" if wv >= 80 else "")
                self.create_text(wm + we + (wv // 2), H // 2, text=txt_v, fill=cor_txt, font=font_txt)
            elif wv >= 35:
                self.create_text(wm + we + (wv // 2), H // 2, text=f"{pct_v:.0%}", fill=cor_txt, font=FONTS['badge'])
        else:
            self.create_text(W // 2, H // 2, text="Sem confrontos diretos anteriores registrados",
                             fill=THEME['text_muted'], font=FONTS['subtitle'])
