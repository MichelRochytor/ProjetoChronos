"""
PROJETO CHRONOS — Atualizador Automático de Dataset (CLI / GitHub Actions)
Executa o Raspador O Gol (modo headless / sem GUI) para atualizar toda a pasta `dados/`
nos horários programados (18h e 00h BRT via GitHub Actions).
"""

import argparse
import sys
import threading
from datetime import datetime

from raspador_gol import RaspadorGol


def log_console(msg: str):
    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{agora}] {msg}", flush=True)


def executar_lote(
    raspador: RaspadorGol,
    chaves: list[str],
    motor: str,
    num_workers: int,
    usar_tor: bool,
    modo: str = 'rapido',
) -> tuple[int, int]:
    """Executa uma rodada completa de raspagem paralela e aguarda o término das threads."""
    concluido_evt = threading.Event()
    resultado = {'atualizados': 0, 'poupados': 0}

    def _ao_concluir(atualizados: int, poupados: int):
        resultado['atualizados'] = atualizados
        resultado['poupados'] = poupados
        concluido_evt.set()

    raspador.executar_raspagem_paralela(
        chaves_selecionadas=chaves,
        num_navegadores=num_workers,
        modo=modo,
        motor=motor,
        forcar=True,
        usar_tor=usar_tor,
        callback_log=log_console,
        callback_concluido=_ao_concluir,
    )

    concluido_evt.wait()
    return resultado['atualizados'], resultado['poupados']


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Atualiza todos os campeonatos da pasta dados/ via Raspador O Gol."
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=6,
        help="Quantidade de conexões/navegadores simultâneos (padrão: 6).",
    )
    parser.add_argument(
        '--motor',
        choices=['turbo', 'selenium'],
        default='turbo',
        help="Motor principal de raspagem ('turbo' HTTP ou 'selenium' Chrome Headless).",
    )
    parser.add_argument(
        '--sem-tor',
        action='store_true',
        help="Desativa o uso da rede Tor durante a execução.",
    )
    parser.add_argument(
        '--sem-fallback-selenium',
        action='store_true',
        help="Desativa a retentativa automática com Chrome Headless caso algum torneio falhe no modo HTTP.",
    )
    args = parser.parse_args()

    raspador = RaspadorGol()
    todas_chaves = [k for k, v in raspador.catalogo.items() if not k.startswith('_') and isinstance(v, dict)]

    if not todas_chaves:
        log_console("⚠️ Nenhum campeonato encontrado em campeonatos_links.json.")
        return 1

    inicio_execucao = datetime.now()
    log_console(f"🚀 Iniciando atualização agendada O Gol para {len(todas_chaves)} campeonatos...")

    try:
        atualizados, _ = executar_lote(
            raspador=raspador,
            chaves=todas_chaves,
            motor=args.motor,
            num_workers=args.workers,
            usar_tor=not args.sem_tor,
            modo='rapido',
        )

        # Identifica campeonatos cuja última atualização não avançou nesta execução
        pendentes = []
        for k in todas_chaves:
            ult_str = raspador.catalogo.get(k, {}).get('ultima_atualizacao')
            if not ult_str:
                pendentes.append(k)
                continue
            try:
                if datetime.fromisoformat(ult_str) < inicio_execucao:
                    pendentes.append(k)
            except Exception:
                pendentes.append(k)

        if pendentes and args.motor == 'turbo' and not args.sem_fallback_selenium:
            log_console(
                f"🔄 {len(pendentes)} campeonato(s) não retornaram via HTTP Turbo. "
                f"Tentando fallback automático com Chrome Headless..."
            )
            att_fb, _ = executar_lote(
                raspador=raspador,
                chaves=pendentes,
                motor='selenium',
                num_workers=min(3, len(pendentes)),
                usar_tor=False,
                modo='rapido',
            )
            atualizados += att_fb

        duracao = (datetime.now() - inicio_execucao).total_seconds()
        log_console(
            f"✅ Atualização finalizada em {duracao:.1f}s! "
            f"Total de campeonatos atualizados com sucesso: {atualizados}/{len(todas_chaves)}."
        )
        return 0
    finally:
        raspador.encerrar_tor()


if __name__ == '__main__':
    sys.exit(main())
