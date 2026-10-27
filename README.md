# Projeto Chronos — Loteca Analytics Pro & Importador O Gol 2.0

Interface Gráfica Avançada de Análise Esportiva, Estatística Multicompetições (1971 a 2026) e Motor de Raspagem Concorrente em Segundo Plano.

---

## 🏗️ Estrutura Modular do Projeto

O projeto é 100% desacoplado e modular, com cada classe em seu próprio arquivo:

| Arquivo | Componente / Classe | Descrição |
| :--- | :--- | :--- |
| [`gui_analise.py`](file:///home/michelrochytor/Documentos/ProjetoChronos/gui_analise.py) | **Ponto de Entrada** | Inicia a aplicação e reexporta todas as classes para retrocompatibilidade. |
| [`config.py`](file:///home/michelrochytor/Documentos/ProjetoChronos/config.py) | Configurações Globais | Cores do Dark Theme, fontes, caminhos resilientes (`_caminho`) e metadados de torneios. |
| [`utils.py`](file:///home/michelrochytor/Documentos/ProjetoChronos/utils.py) | Utilitários & IA | Busca sem acentos, parsing de datas históricas, extração de placares e estimativa de probabilidades. |
| [`campeonatos_links.json`](file:///home/michelrochytor/Documentos/ProjetoChronos/campeonatos_links.json) | **Catálogo de Links & CSVs** | JSON com 36+ campeonatos configurados (todos os estaduais, nacionais e copas), URLs e pastas. |
| [`raspador_gol.py`](file:///home/michelrochytor/Documentos/ProjetoChronos/raspador_gol.py) | **Classe `RaspadorGol`** | Motor de raspagem concorrente com múltiplos navegadores headless, verificação incremental e descarte de jogos já atualizados. |
| [`janela_importacao.py`](file:///home/michelrochytor/Documentos/ProjetoChronos/janela_importacao.py) | **Classe `JanelaGerenciadorImportacao`** | Interface visual para editar links, pastas de destino, selecionar navegadores (1 a 4) e acompanhar logs em tempo real. |
| [`gerenciador_dados.py`](file:///home/michelrochytor/Documentos/ProjetoChronos/gerenciador_dados.py) | **Classe `GerenciadorDados`** | Cache em memória, indexação de nacionais e estaduais, histórico H2H bilateral e impacto de copas. |
| [`barra_h2h.py`](file:///home/michelrochytor/Documentos/ProjetoChronos/barra_h2h.py) | **Classe `BarraH2HVisual`** | Widget Canvas para visualização proporcional de vitórias do mandante, empates e visitante. |
| [`janela_raio_x.py`](file:///home/michelrochytor/Documentos/ProjetoChronos/janela_raio_x.py) | **Classe `JanelaRaioXJogo`** | Modal de diagnóstico com 4 abas: Copas, Raio-X de Força, H2H e IA Tática. |
| [`app_analise_loteca.py`](file:///home/michelrochytor/Documentos/ProjetoChronos/app_analise_loteca.py) | **Classe `AppAnaliseLoteca`** | Janela principal com KPIs, filtros dinâmicos, auto-atualização em segundo plano no startup e barra de progresso. |

---

## 🌐 Novidades do Importador O Gol 2.0 Unificado

1. **Múltiplos Navegadores em Segundo Plano (Headless Chrome)**:
   - Permite executar 1, 2, 3 ou 4 instâncias simultâneas do Google Chrome de forma invisível (`--headless=new`), sem abrir janelas incômodas na tela.
2. **Catálogo Completo com Todos os Estaduais**:
   - Arquivo [`campeonatos_links.json`](file:///home/michelrochytor/Documentos/ProjetoChronos/campeonatos_links.json) pré-configurado com os 27 estados do Brasil (Paulista, Carioca, Mineiro, Gaúcho, Goiano, Capixaba, etc.), além do Brasileirão (A, B, C, D), Copa do Brasil, Libertadores e Sul-Americana.
   - Pela interface, é possível adicionar, editar URLs de temporadas, alterar anos iniciais e pastas de destino.
3. **Otimização Inteligente (Ignora Jogos Já Atualizados)**:
   - Se os jogos da temporada já foram importados hoje ou se o arquivo CSV já possui os dados recentes, o motor ignora a raspagem automaticamente, poupando tempo, processamento e conexões de rede.
4. **Auto-Atualização ao Abrir o Aplicativo**:
   - Ao iniciar o sistema, uma thread não-bloqueante verifica se há torneios ativos pendentes de atualização hoje e roda os navegadores em segundo plano, exibindo a barra de progresso no rodapé.
5. **Barra de Carregamento em Tempo Real**:
   - Acompanhamento percentual do progresso tanto na janela principal quanto na modal do importador, com console detalhado de logs por trabalhador (Worker 1, Worker 2, etc.).

---

## 🚀 Como Executar

Para iniciar a aplicação:

```bash
python gui_analise.py
```