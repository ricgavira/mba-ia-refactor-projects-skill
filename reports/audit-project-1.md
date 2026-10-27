# Audit Report — code-smells-project

> Gerado pela skill `refactor-arch` (Fase 2) em 2026-10-26. Linhas referem-se ao código **antes** da refatoração.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.12
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1 (sqlite3 da stdlib)
Domain:        E-commerce API (produtos, pedidos, usuários, relatório de vendas)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed (~780 lines of code)
DB tables:     produtos, usuarios, pedidos, itens_pedido (SQLite, loja.db)
Entry point:   app.py (porta 5000)
Layers found:  app.py → Config + Routes + Controller + Data (SQL em /admin/*)
               controllers.py → Controller + Business rules + Data (health_check)
               models.py → Model + Business rules + Serialização
               database.py → Infra (conexão global) + Schema + Seed
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] AP-01 — Credenciais e segredos hardcoded
File: app.py:7, controllers.py:289, database.py:75-79
Description: `SECRET_KEY = "minha-chave-super-secreta-123"` fixo em app.py:7 e repetido literalmente na resposta de health_check (controllers.py:289); o seed grava as senhas `admin123`, `123456`, `senha123` no código (database.py:76-78).
Impact: O segredo da sessão vai para o Git e para qualquer cliente que chame /health; quem o conhece forja sessões.
Recommendation: Ler SECRET_KEY de variável de ambiente via módulo de config, sem default conhecido (Playbook P1).

### [CRITICAL] AP-02 — SQL Injection (SQL por concatenação)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 149-151, 155, 157-166, 174, 188, 192, 220, 224, 279-281, 289-297
Description: Praticamente todas as queries (get_produto_por_id, criar/atualizar/deletar_produto, login_usuario, criar_usuario, criar_pedido, buscar_produtos com LIKE...) concatenam dados da requisição. Comprovado no baseline: POST /login com `' OR '1'='1` retorna 200 e autentica.
Impact: Bypass de login, leitura, alteração e destruição de qualquer tabela.
Recommendation: Queries parametrizadas (`?`) em todas as consultas; filtros dinâmicos com fragmentos fixos + lista de parâmetros (Playbook P2).

### [CRITICAL] AP-03 — God File / God Class
File: models.py:1-314, controllers.py:1-292, app.py:47-78
Description: models.py mistura SQL, serialização, regra de negócio (desconto, cálculo de pedido) de 4 domínios em um arquivo; controllers.py mistura validação, regra, notificações e acesso direto ao banco (health_check, linhas 264-292); app.py (entry point) define rotas, executa SQL e handlers admin.
Impact: Impossível testar em isolamento; qualquer mudança afeta tudo.
Recommendation: Separar em config/database/models/controllers/views/middlewares com composition root `create_app()` (Playbook P4).

### [CRITICAL] AP-04 — Endpoints perigosos sem autenticação
File: app.py:47-57, 59-78
Description: `POST /admin/reset-db` apaga todas as tabelas e `POST /admin/query` executa SQL arbitrário recebido no corpo (`cursor.execute(query)`), ambos abertos a qualquer cliente.
Impact: Qualquer pessoa na rede destrói ou exfiltra o banco inteiro.
Recommendation: Proteger com token administrativo configurado por env (desabilitado por padrão) e restringir /admin/query a SELECT somente-leitura (Playbook P13).

### [CRITICAL] AP-05 — Senhas em texto puro
File: models.py:105-110, 122-129, database.py:75-84
Description: criar_usuario grava a senha como veio; login_usuario compara `senha = '<texto>'` no SQL; o seed grava senhas em claro.
Impact: Um vazamento do banco expõe todas as credenciais reutilizáveis dos usuários.
Recommendation: `generate_password_hash`/`check_password_hash` (werkzeug), login por e-mail + verificação do hash; seed com hashes (Playbook P3).

### [CRITICAL] AP-06 — Exposição de dados sensíveis
File: controllers.py:276-290, models.py:72-87, 89-103
Description: /health devolve `secret_key`, `db_path` e `debug`; GET /usuarios e /usuarios/<id> devolvem o campo `senha`; erros devolvem `str(e)` (stack/SQL) ao cliente.
Impact: Vazamento de segredo, senhas e detalhes internos para qualquer cliente.
Recommendation: Serializers com allowlist (sem senha/segredo), health mínimo, erro 500 genérico com detalhe só no log (Playbook P13, P8).

### [HIGH] AP-07 — Lógica de negócio em controllers
File: controllers.py:24-62, 64-96, 203-210, 242-250, 264-292
Description: Controllers validam regras de domínio (categorias válidas, limites de nome), disparam notificações (e-mail/SMS/push simulados) e consultam o banco diretamente (health_check).
Impact: Regra espalhada, não reutilizável nem testável sem HTTP.
Recommendation: Validação em funções dedicadas, notificações em NotificationService, consultas em models (Playbook P5, P9).

### [HIGH] AP-08 — Estado global mutável
File: database.py:4-5, 9-10, 86
Description: `db_connection` global, criada sob demanda com `check_same_thread=False` e compartilhada por todas as requests/threads.
Impact: Race conditions, transações de requests distintas se misturam, impossível isolar em testes.
Recommendation: Conexão por request (`flask.g`) fechada em teardown, configurada pelo composition root (Playbook P6).

### [HIGH] AP-09 — Acoplamento forte sem injeção de dependência
File: controllers.py:1-3, 264-270, app.py:3-4, 47-56, 66-69
Description: controllers e app.py importam `get_db` e abrem cursor diretamente; `app.py` importa o módulo `controllers` e registra cada rota manualmente com `add_url_rule`.
Impact: Camadas dependem umas das outras em todas as direções; trocar o banco exige editar controllers e entry point.
Recommendation: Regra de dependência Routes → Controllers → Models → Config; acesso a dados só nos models (Playbook P4, P6).

### [HIGH] AP-10 — Configuração insegura de execução
File: app.py:8, 88, controllers.py:286-288
Description: `DEBUG = True` e `app.run(host="0.0.0.0", debug=True)` fixos (debugger interativo do Werkzeug exposto na rede); ambiente "producao" e `debug: True` escritos no código.
Impact: Execução remota de código via console do debugger; valores de config impossíveis de variar por ambiente.
Recommendation: DEBUG/HOST/PORT lidos de env, default seguro (debug off, host 127.0.0.1) (Playbook P1).

### [HIGH] AP-11 — Operações multi-passo sem atomicidade
File: models.py:133-169, controllers.py:247-250
Description: criar_pedido faz checagem de estoque, INSERT do pedido, INSERTs dos itens e UPDATEs de estoque sem `rollback` em caso de falha e com check-then-act; ao cancelar pedido o controller só imprime "Devolver estoque" e o estoque nunca é devolvido.
Impact: Pedido parcial persistido em falha, estoque inconsistente sob concorrência.
Recommendation: Escrita em transação única com rollback; UPDATE condicional de estoque (Playbook P14).

### [MEDIUM] AP-12 — Queries N+1
File: models.py:154-166, 171-201, 203-233
Description: get_pedidos_usuario e get_todos_pedidos executam 1 query de itens por pedido e 1 query de produto por item (cursor2/cursor3 dentro de loops); criar_pedido relê o preço de cada produto dentro do loop de itens.
Impact: Latência cresce com pedidos × itens.
Recommendation: Uma query com JOIN e agrupamento em memória (Playbook P7).

### [MEDIUM] AP-13 — Código duplicado
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 177-200, 209-232, controllers.py:24-62, 64-96
Description: O dict de produto (8 campos) é repetido 3x, o de usuário 2x, a montagem de pedido+itens 2x; a validação de produto é copiada em criar e atualizar (e já divergiu: atualizar não valida tamanho do nome nem categoria).
Impact: Correção feita em um lugar e esquecida no outro.
Recommendation: Serializer único por entidade e função de validação compartilhada (Playbook P9).

### [MEDIUM] AP-14 — Validação de entrada ausente/inconsistente
File: controllers.py:26-50, 118-121, 169-171, 188-203, 239-245
Description: `preco < 0` com preço string gera TypeError (500); `request.get_json()` nulo em login/atualizar_status levanta AttributeError (500); `float(preco_min)` sem tratamento; itens do pedido sem validar `produto_id`/`quantidade`; atualizar_status não verifica se o pedido existe.
Impact: Entrada malformada vira erro 500 com mensagem interna em vez de 400/404.
Recommendation: Validação centralizada com `isinstance` e erros 400/404 tipados (Playbook P9, P8).

### [MEDIUM] AP-15 — Tratamento de erro inadequado
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292, app.py:77-78
Description: Todo handler repete `try/except Exception` e devolve `str(e)` com 500; não existe handler global de 404/500.
Impact: Duplicação, vazamento de detalhes internos e formato de erro inconsistente.
Recommendation: Exceções de domínio + error handlers centralizados (Playbook P8).

### [LOW] AP-18 — Magic numbers e strings
File: models.py:256-262, controllers.py:47-54, 242, app.py:88, database.py:5
Description: Faixas de desconto (10000/5000/1000 → 0.1/0.05/0.02) soltas no cálculo; tamanhos de nome (2/200), lista de categorias e lista de status repetidas inline; porta 5000 e caminho do banco fixos.
Impact: Regra de negócio escondida em literais; mudar exige caçar o código.
Recommendation: Constantes nomeadas em config/constants (Playbook P12).

### [LOW] AP-19 — Nomenclatura ruim
File: models.py:24, 54, 65, 89, 187, 191, 219, 223, controllers.py:14, 24, 64, 98, 136
Description: Parâmetro `id` sombreia o builtin; `cursor2`/`cursor3`; mistura de nomes `get_todos_*` e `criar_*`/`login_usuario`.
Impact: Legibilidade e risco de bugs sutis.
Recommendation: Nomes consistentes por camada (Playbook P12).

### [LOW] AP-20 — Código morto / imports não usados
File: models.py:2, database.py:2
Description: `import sqlite3` em models.py e `import os` em database.py nunca são usados.
Impact: Ruído.
Recommendation: Remover (Playbook P15).

### [LOW] AP-21 — print como logging
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250, app.py:56, 83-87
Description: `print` espalhado (inclusive "ENVIANDO EMAIL/SMS/PUSH" simulados) sem nível de log.
Impact: Sem controle de verbosidade nem destino de log.
Recommendation: Módulo `logging` e NotificationService (Playbook P15).

Deprecated APIs: none detected (APIs de Flask 3.1.1, flask-cors 5.0.1 e sqlite3/Python 3.12 conferidas contra AP-17)

================================
Total: 19 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Confirmação: y — Fase 3 executada em 2026-10-26.
