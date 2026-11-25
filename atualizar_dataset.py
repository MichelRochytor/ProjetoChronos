"""
PROJETO CHRONOS — Atualizador Automático de Dataset via Tor (CLI / GitHub Actions)
Executa o Raspador O Gol em modo rápido utilizando a Rede Tor integrada para atualizar
somente os campeonatos ainda em andamento na pasta `dados/` (ignorando automaticamente
campeonatos já finalizados, como os Estaduais encerrados).
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
    usar_tor: bool = True,
    pular_finalizados: bool = True,
    modo: str = 'rapido',
) -> tuple[int, int]:
    """Executa uma rodada completa de raspagem paralela via Tor e aguarda o término das threads."""
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
        pular_finalizados=pular_finalizados,
        callback_log=log_console,
        callback_concluido=_ao_concluir,
    )

    concluido_evt.wait()
    return resultado['atualizados'], resultado['poupados']


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Atualiza os campeonatos em andamento na pasta dados/ via Raspador O Gol com Rede Tor."
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help="Quantidade de conexões/navegadores simultâneos (padrão: 5).",
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
        help="Desativa o uso da rede Tor (por padrão, toda a importação rápida roda pelo Tor).",
    )
    parser.add_argument(
        '--incluir-finalizados',
        action='store_true',
        help="Força a reimportação também de campeonatos já finalizados (ex: Estaduais encerrados).",
    )
    parser.add_argument(
        '--sem-fallback-selenium',
        action='store_true',
        help="Desativa a retentativa automática com Chrome Headless (via Tor) caso algum torneio falhe no modo HTTP.",
    )
    args = parser.parse_args()

    usar_tor = not args.sem_tor
    pular_finalizados = not args.incluir_finalizados

    raspador = RaspadorGol()
    todas_chaves = [k for k, v in raspador.catalogo.items() if not k.startswith('_') and isinstance(v, dict)]

    if not todas_chaves:
        log_console("⚠️ Nenhum campeonato encontrado em campeonatos_links.json.")
        return 1

    chaves_finalizadas = []
    chaves_em_andamento = []

    for k in todas_chaves:
        camp = raspador.catalogo[k]
        if pular_finalizados and raspador.campeonato_finalizado(camp):
            chaves_finalizadas.append(k)
        else:
            chaves_em_andamento.append(k)

    log_console(
        f"📊 Diagnóstico do acervo: {len(todas_chaves)} campeonatos no catálogo | "
        f"🏁 {len(chaves_finalizadas)} já finalizados (poupados) | "
        f"⚽ {len(chaves_em_andamento)} em andamento para atualizar."
    )

    if chaves_finalizadas:
        nomes_fin = ", ".join(raspador.catalogo[k].get('nome', k) for k in chaves_finalizadas)
        log_console(f"⏩ Ignorando campeonatos encerrados: {nomes_fin}")

    if not chaves_em_andamento:
        log_console("✅ Todos os campeonatos da temporada já estão 100% encerrados. Nada a atualizar!")
        return 0

    inicio_execucao = datetime.now()
    log_console(
        f"🧅 Iniciando importação rápida {'via Rede Tor' if usar_tor else 'direta'} "
        f"para {len(chaves_em_andamento)} campeonatos em andamento..."
    )

    try:
        atualizados, _ = executar_lote(
            raspador=raspador,
            chaves=chaves_em_andamento,
            motor=args.motor,
            num_workers=min(args.workers, len(chaves_em_andamento)),
            usar_tor=usar_tor,
            pular_finalizados=pular_finalizados,
            modo='rapido',
        )

        # Identifica campeonatos em andamento cuja última atualização não avançou nesta execução
        pendentes = []
        for k in chaves_em_andamento:
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
                f"Tentando fallback automático com Chrome Headless via Tor..."
            )
            att_fb, _ = executar_lote(
                raspador=raspador,
                chaves=pendentes,
                motor='selenium',
                num_workers=min(3, len(pendentes)),
                usar_tor=usar_tor,
                pular_finalizados=pular_finalizados,
                modo='rapido',
            )
            atualizados += att_fb

        duracao = (datetime.now() - inicio_execucao).total_seconds()
        log_console(
            f"✅ Atualização finalizada em {duracao:.1f}s! "
            f"Campeonatos atualizados: {atualizados}/{len(chaves_em_andamento)} "
            f"(+{len(chaves_finalizadas)} encerrados poupados)."
        )
        return 0
    finally:
        raspador.encerrar_tor()


if __name__ == '__main__':
    sys.exit(main())
