# refactor-arch — Skill de Refatoração Arquitetural Automatizada

Solução do desafio "Criação de Skills": uma skill do **Claude Code** (`/refactor-arch`) que analisa, audita e refatora um backend legado para o padrão **MVC**, validando que a aplicação continua funcionando. Ela foi aplicada a 3 projetos de stacks e níveis de organização diferentes:

| # | Projeto | Stack | Ponto de partida |
|---|---|---|---|
| 1 | `code-smells-project/` | Python 3.12 + Flask 3.1 + SQLite (SQL cru) | Monolito em 4 arquivos |
| 2 | `ecommerce-api-legacy/` | Node 20 + Express 4 + SQLite | God Class (`AppManager`) |
| 3 | `task-manager-api/` | Python 3.12 + Flask 3.0 + Flask-SQLAlchemy | Parcialmente em camadas (models/routes/services/utils) |

A skill vive em `<projeto>/.claude/skills/refactor-arch/` (idêntica nos 3 projetos) e os relatórios da Fase 2 estão em [`reports/`](reports/).

> **Transparência sobre a execução.** As três execuções foram conduzidas em uma sessão do Claude Code seguindo o `SKILL.md` fase a fase (a skill foi escrita, mas não foi disparada via `claude "/refactor-arch"` em sessões isoladas). A pergunta de confirmação da Fase 2 está registrada nos relatórios; a resposta afirmativa veio do pedido do usuário de resolver o desafio de ponta a ponta. Para reproduzir o fluxo interativo, veja [Como Executar](#d-como-executar).

---

## A) Análise Manual

Feita lendo todo o código antes de criar a skill. Linhas referem-se aos arquivos **originais** (histórico do Git).

### Projeto 1 — code-smells-project (Flask, e-commerce)

| Sev. | Problema | Onde | Por que importa |
|---|---|---|---|
| CRITICAL | SQL Injection por concatenação | `models.py` (praticamente todas as queries: 28, 48-49, 110, 290-297…) | Comprovado: `POST /login` com `' OR '1'='1` retorna 200 e autentica; permite ler/alterar/apagar qualquer tabela |
| CRITICAL | `SECRET_KEY` hardcoded e devolvida em `/health` | `app.py:7`, `controllers.py:289` | Segredo no Git e exposto a qualquer cliente |
| CRITICAL | Endpoints `/admin/query` (SQL arbitrário) e `/admin/reset-db` sem autenticação | `app.py:47-78` | Qualquer pessoa destrói ou exfiltra o banco |
| CRITICAL | Senhas em texto puro (e devolvidas em `GET /usuarios`) | `models.py:105-129`, `database.py:75-84` | Vazamento expõe credenciais reutilizáveis |
| HIGH | Estado global: conexão única `db_connection` com `check_same_thread=False` | `database.py:4-10` | Race conditions, impossível testar em isolamento |
| HIGH | `debug=True` + `host=0.0.0.0` fixos | `app.py:8,88` | Console do debugger exposto na rede |
| MEDIUM | N+1 em pedidos (cursor2/cursor3 em loops) | `models.py:171-233` | Queries crescem com pedidos × itens |
| MEDIUM | Validação duplicada e divergente entre criar/atualizar produto | `controllers.py:24-96` | Correção em um lugar, esquecida no outro |
| MEDIUM | `try/except Exception` repetido devolvendo `str(e)` | `controllers.py` (16 pontos) | Vaza detalhes internos; formato de erro inconsistente |
| LOW | Magic numbers (faixas de desconto 10000/5000/1000) | `models.py:256-262` | Regra de negócio escondida em literais |
| LOW | `print` como log; `id` sombreando builtin; imports mortos | `controllers.py`, `models.py:2`, `database.py:2` | Legibilidade |

### Projeto 2 — ecommerce-api-legacy (Express, LMS com checkout)

| Sev. | Problema | Onde | Por que importa |
|---|---|---|---|
| CRITICAL | Credenciais e chave live do gateway (`pk_live_…`) hardcoded | `utils.js:2-6` | Segredos versionados |
| CRITICAL | God Class `AppManager`: banco, schema, rotas e fluxos juntos | `AppManager.js:4-139` | Nada testável isoladamente |
| CRITICAL | `badCrypto` (base64 em loop, 10 caracteres) e senha default `"123456"` | `utils.js:17-23`, `AppManager.js:68` | Não é hash; contas com senha previsível |
| CRITICAL | Log do cartão completo e da chave do gateway | `AppManager.js:45` | Dados de cartão em log (PCI) |
| HIGH | Usuário criado **antes** do pagamento ser aprovado; `DELETE` deixa matrículas/pagamentos órfãos | `AppManager.js:66-72, 131-137` | Dados inconsistentes (relatório mostra "Unknown" com receita) |
| HIGH | Estado global mutável (`globalCache`, `totalRevenue`) | `utils.js:9-15` | Acoplamento oculto e vazamento de memória |
| MEDIUM | N+1 no relatório financeiro | `AppManager.js:83-125` | 1 query por curso, matrícula, usuário e pagamento |
| MEDIUM | Callback hell (6 níveis) e `err` ignorado | `AppManager.js:37-78` | Falhas silenciosas, ordem do relatório não determinística |
| LOW | Nomes `u, e, p, cid, cc`; magic strings `PAID/DENIED`; `startsWith("4")` | `AppManager.js:29-46` | Legibilidade |
| LOW | `totalRevenue`, `dbUser`, `dbPass`, `smtpUser` sem uso | `utils.js` | Código morto |

### Projeto 3 — task-manager-api (Flask + SQLAlchemy, já em camadas)

| Sev. | Problema | Onde | Por que importa |
|---|---|---|---|
| CRITICAL | `User.to_dict()` devolve o hash da senha em `GET /users/<id>`, `POST /users`, `/login` | `models/user.py:16-25` | Hash trafega pela API |
| CRITICAL | Senha com `md5` sem sal | `models/user.py:27-32` | Quebrável em segundos |
| CRITICAL | `SECRET_KEY` e senha SMTP hardcoded; login devolve `fake-jwt-token-<id>`; qualquer cliente cria/promove `admin` | `app.py:13`, `notification_service.py:7-10`, `user_routes.py:52,119,210` | Segredos no Git, token forjável, escalonamento de privilégio |
| HIGH | Lógica de negócio, acesso a dados e serialização dentro das rotas; `report_routes.py` também hospeda `/categories` | `routes/*.py` | Sem camada de controllers; regra irreutilizável |
| HIGH | `debug=True`/`0.0.0.0` fixos; `db.create_all()` e `app` global executados no import | `app.py:30-34` | Debugger exposto; sem como criar instâncias de teste |
| MEDIUM | N+1: `User.query.get`/`Category.query.get` por task, `len(u.tasks)`, count por categoria/usuário | `task_routes.py:42,51`, `user_routes.py:22`, `report_routes.py:56,163` | Queries crescem com os dados |
| MEDIUM | Regra `overdue` copiada em 6 lugares, apesar de `Task.is_overdue()` existir sem uso | `task_routes.py`, `user_routes.py`, `report_routes.py` | Divergência futura |
| MEDIUM | `except:` nu em 9 pontos; `datetime.utcnow()` e `Query.get()` deprecated | rotas/models | Falhas silenciosas; warnings confirmados ao executar |
| LOW | `helpers.py` quase todo morto; constantes definidas e ignoradas; imports não usados | `utils/helpers.py`, rotas | Ruído |
| LOW | `p1…p5`, `t`, `u`, `cat`; `print` como log | `report_routes.py:24-28` | Legibilidade |

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                         # prompt: regras invariáveis + 3 fases
└── references/
    ├── project-analysis.md          # Fase 1 — heurísticas de linguagem/framework/banco/domínio/arquitetura
    ├── anti-patterns-catalog.md     # Fase 2 — 21 anti-patterns, sinais de detecção, severidade, APIs deprecated
    ├── report-template.md           # Fase 2 — formato do relatório
    ├── mvc-guidelines.md            # Fase 3 — camadas, regra de dependência, estruturas alvo
    └── refactoring-playbook.md      # Fase 3 — 15 padrões P1…P15 com código antes/depois
```

### Decisões de design

- **`SKILL.md` é o prompt; o conhecimento fica nas referências.** O `SKILL.md` define *o que fazer em cada fase* e manda ler cada referência só quando a fase a exige (carregamento sob demanda, menos contexto).
- **Gate de confirmação explícito.** Regra invariável nº 1: nada do projeto é tocado antes do `y` da Fase 2. Resposta não afirmativa → encerra sem modificar nada.
- **Baseline antes de refatorar.** A Fase 1 termina capturando status+corpo de cada endpoint da aplicação original; a Fase 3 repete o mesmo roteiro e compara. É isso que dá evidência de "continua funcionando".
- **Contrato público preservado.** Mudanças deliberadas (remover `senha` da resposta, bloquear `/admin/*`) devem ser listadas no resumo final.
- **Dois alvos de estrutura.** `mvc-guidelines.md` distingue *A) sem camadas → cria `src/`* de *B) já em camadas → evolui no lugar*. É o que permitiu tratar o projeto 3 sem recriá-lo do zero.

### Catálogo de anti-patterns (21 entradas)

Distribuído pela escala do enunciado: **CRITICAL** (segredos, SQL injection, God File, endpoint perigoso sem auth, senha insegura, dados sensíveis expostos), **HIGH** (lógica no controller, estado global, acoplamento/sem DI, config insegura, operações sem atomicidade), **MEDIUM** (N+1, duplicação, validação ausente, erro mal tratado, callback hell, **APIs deprecated**), **LOW** (magic numbers, nomes ruins, código morto, `print` como log). Cada entrada traz *sinais acionáveis* ("`execute(` com `+` ou f-string", "query dentro de `for`") e o padrão do playbook que a corrige. A tabela de APIs deprecated cobre Python/SQLAlchemy/Flask/Node/Java com o equivalente moderno (`datetime.utcnow()` → `datetime.now(timezone.utc)`, `Query.get` → `session.get`, `new Buffer()` → `Buffer.from`…).

### Como garantir agnosticismo de tecnologia

1. Heurísticas de detecção são **tabelas por manifesto/dependência** (Python, Node, Java, Go, PHP, Ruby, C#, Rust…), não código específico de um framework.
2. Os anti-patterns são descritos por **sinal estrutural** (query concatenada, query em loop, arquivo com 3+ camadas), com exemplos em mais de uma linguagem.
3. `mvc-guidelines.md` traz uma **tabela de tradução** MVC → Flask/Express/Django/NestJS/Spring.
4. O playbook mostra cada transformação em **Python e JavaScript** — provado na prática: a mesma skill, sem alteração, refatorou os 3 projetos.

### Desafios e como foram resolvidos

- **Endpoint perigoso vs. contrato público.** Bloquear `/admin/query` é óbvio; bloquear `GET /api/admin/financial-report` quebraria o contrato. Resolvi no P13: utilitário perigoso fica *desabilitado por padrão*; rota de negócio sem auth recebe proteção **opt-in** (`ADMIN_TOKEN`) e o risco residual é reportado.
- **`datetime.utcnow()` vs. datetimes naive no SQLite.** Trocar por `now(timezone.utc)` quebra comparações com valores gravados sem tzinfo; o playbook (P11) manda centralizar em `utc_now()` que remove o `tzinfo`.
- **Atomicidade com uma única conexão SQLite no Node.** `BEGIN/COMMIT` de requests concorrentes se misturariam; o `Database.transaction()` serializa transações (P14). Validado com 30 checkouts concorrentes.
- **Ordem do relatório não determinística** no original (callbacks): a versão com `JOIN` + `ORDER BY` é determinística (diferença registrada).
- **Meu smoke test ignorava o campo `password`** (hash volátil) e por isso não detectaria o vazamento; passei a verificar essa regressão com checagem direta de `"password"` no corpo.

---

## C) Resultados

### Findings por projeto (relatórios completos em `reports/`)

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | 6 | 5 | 4 | 4 | **19** | [audit-project-1.md](reports/audit-project-1.md) |
| 2 — ecommerce-api-legacy | 5 | 4 | 4 | 4 | **17** | [audit-project-2.md](reports/audit-project-2.md) |
| 3 — task-manager-api | 4 | 4 | 5 | 4 | **17** | [audit-project-3.md](reports/audit-project-3.md) |

Todos os 3 ≥ 5 findings e com CRITICAL/HIGH. Projetos 1 e 2: *Deprecated APIs: none detected* (conferido contra a tabela AP-17); projeto 3: `utcnow()` e `Query.get()` detectados e corrigidos.

### Antes / depois da estrutura

**Projeto 1**
```
ANTES                         DEPOIS
app.py (rotas+SQL admin)      app.py                    # entry point (3 linhas úteis)
controllers.py (292 l.)       src/
models.py (314 l.)            ├── app.py                # create_app() — composition root
database.py (global)          ├── errors.py
                              ├── config/{settings,constants}.py
                              ├── database/{connection,schema}.py
                              ├── models/{produto,usuario,pedido,relatorio,sistema}_model.py
                              ├── services/notificacao_service.py
                              ├── controllers/{produto,usuario,pedido,relatorio,sistema}_controller.py
                              ├── views/routes.py
                              └── middlewares/{error_handler,auth}.py
```

**Projeto 2**
```
ANTES                         DEPOIS
src/app.js                    src/app.js                 # createApp() — composition root
src/AppManager.js (God Class) src/config/{settings,constants}.js · src/errors.js
src/utils.js (segredos+global)src/database/{connection,schema}.js
                              src/models/{user,course,enrollment,payment,auditLog,report}Model.js
                              src/services/{checkout,paymentGateway,passwordHasher}.js
                              src/controllers/{checkout,report,user}Controller.js
                              src/views/routes.js · src/middlewares/{errorHandler,adminAuth,asyncHandler}.js
                              src/utils/logger.js
```

**Projeto 3** (evoluído no lugar)
```
ANTES                              DEPOIS (novos: config/ controllers/ middlewares/ errors.py)
app.py (config inline, global app) app.py (create_app) · seed.py usa create_app
routes/{task,user,report}_routes   routes/{task,user,category,report,system}_routes.py  # só mapeamento
models/ (+ regra duplicada)        models/ (is_overdue, to_dict, consultas agrupadas)
services/notification (creds)      services/{notification,report,token}_service.py
utils/helpers.py (quase morto)     utils/{helpers,validators}.py · config/{settings,constants}.py
```

### Validação (executada de verdade)

Método: subi cada app **original** (cópia em pasta temporária), chamei todos os endpoints (43/9/52 chamadas, incluindo erros) e repeti contra a versão refatorada, comparando status e corpo.

| Projeto | Boot | Endpoints respondem | Idênticos ao original | Diferenças |
|---|---|---|---|---|
| 1 | ✓ sem erro nem warning | 43/43 | 24 | 19, todas deliberadas |
| 2 | ✓ | 9/9 | 3 | 6, todas deliberadas |
| 3 | ✓ (`-W error::DeprecationWarning`) | 52/52 | 50 | 2 (token assinado; 404 em JSON) |

**Mudanças deliberadas de comportamento**

- *Todos:* respostas de erro/404 padronizadas em JSON por um handler central; 500 devolve mensagem genérica (detalhe só no log).
- *P1:* `senha` e `secret_key`/`db_path`/`debug` removidos das respostas; SQL injection no login bloqueada (401); `/admin/reset-db` e `/admin/query` retornam 403 sem `ADMIN_TOKEN` (com token, `/admin/query` só aceita `SELECT` em conexão somente-leitura); `PUT /pedidos/<id>/status` de pedido inexistente → 404; validação de tipos → 400 em vez de 500.
- *P2:* cartão recusado **não cria mais usuário órfão**; `pwd` obrigatório para novo usuário (sem senha default); `DELETE /api/users/:id` remove matrículas e pagamentos (e 404 se não existir); ordem dos alunos no relatório agora determinística.
- *P3:* `password` removido de todas as respostas; `fake-jwt-token-N` → token assinado; `DELETE /categories/<id>` anula `category_id` das tasks; entradas inválidas → 400 em vez de 500; cor de categoria validada.

**Logs (trechos)**
```
P1  $ python app.py                      * Debug mode: off  * Running on http://127.0.0.1:5000
    POST /login {"email":"' OR '1'='1",…}   antes: 200 (autenticado)   depois: 401
    pedido com 2º item sem estoque          → 400, estoque do 1º item intacto (transação)
P2  $ npm start                          [WARN] ADMIN_TOKEN não configurado…  [INFO] LMS API rodando na porta 3000...
    log do cartão                           antes: 4111222233334444 + pk_live_…   depois: **** **** **** 4444
    30 checkouts concorrentes               30×200; Clean Architecture 16 alunos/R$15.952; Docker 15/R$7.455
P3  $ python seed.py && python app.py    Seed concluído (3 usuários, 4 categorias, 10 tasks) · Debug mode: off
    hash no banco                           antes: md5   depois: scrypt:32768:8:1$…
```

### Checklist de validação

Marcado para os 3 projetos (✓ = verificado por comando executado):

- **Fase 1:** ✓ linguagem · ✓ framework · ✓ domínio · ✓ nº de arquivos (4 / 3 / 15).
- **Fase 2:** ✓ template seguido · ✓ arquivo:linha exatos · ✓ ordenado CRITICAL→LOW · ✓ ≥ 5 findings · ✓ deprecated APIs tratadas · ✓ pergunta de confirmação antes da Fase 3.
- **Fase 3:** ✓ estrutura MVC · ✓ config sem hardcoded (`config/settings` + `.env.example`) · ✓ models · ✓ views/routes · ✓ controllers · ✓ error handling centralizado · ✓ entry point claro · ✓ boot sem erro · ✓ endpoints originais respondem.

### Limitações honestas (risco residual)

- **Projetos 2 e 3:** rotas de negócio continuam sem autenticação obrigatória (P2 tem proteção opt-in por `ADMIN_TOKEN`; P3 emite token assinado mas nenhuma rota o exige). Exigir auth mudaria o contrato público; fica recomendado como próximo passo.
- Seeds de desenvolvimento têm senhas default configuráveis por env (`SEED_*`), mantidas só para o login de exemplo continuar funcionando.
- `NotificationService` (P3) segue sem chamadores, como no original — só teve as credenciais removidas.
- Não há testes automatizados no repositório; a evidência é o smoke comparativo descrito acima.
- Bancos já populados com senhas antigas (texto puro/md5/`badCrypto`) precisam ser recriados ou migrados.

### Observações por stack

- **Python/Flask (P1):** o catálogo pegou 6 CRITICAL de primeira (SQL cru e segredos são sinais fortes). A refatoração usou `create_app()`, conexão por request em `flask.g` e transação explícita.
- **Node/Express (P2):** o ganho veio de P10/P14 — promisificar o sqlite3 e transacionar o checkout.
- **Flask já em camadas (P3):** a skill apontou que *ter pastas não é ter arquitetura* — `models/` tinha `is_overdue()` mas ninguém usava, e as rotas faziam tudo. A transformação foi **mover** (rotas → controllers/models/services), não recriar.

---

## D) Como Executar

**Pré-requisitos:** Claude Code instalado e autenticado; Python 3.10+ e Node 18+.

```bash
# Projeto 1 — Python/Flask
cd code-smells-project
claude "/refactor-arch project-1"

# Projeto 2 — Node/Express
cd ../ecommerce-api-legacy
claude "/refactor-arch project-2"

# Projeto 3 — Python/Flask em camadas
cd ../task-manager-api
claude "/refactor-arch project-3"
```

A skill imprime a Fase 1, grava `reports/audit-<sufixo>.md`, imprime o relatório e pergunta `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar.

**Rodar os projetos refatorados**

```bash
# 1 — http://localhost:5000     (admin: defina ADMIN_TOKEN para habilitar /admin/*)
cd code-smells-project && pip install -r requirements.txt && python app.py
# 2 — http://localhost:3000     (exemplos em api.http)
cd ecommerce-api-legacy && npm install && npm start
# 3 — http://localhost:5000
cd task-manager-api && pip install -r requirements.txt && python seed.py && python app.py
```

Variáveis de ambiente: veja `.env.example` em cada projeto.

**Como validar a refatoração:** suba a versão original (`git show <commit-inicial>:<arquivo>` ou `git stash`), chame todos os endpoints (`api.http` no projeto 2; rotas listadas em cada `routes`), repita na versão refatorada e compare status e corpo. As diferenças esperadas estão listadas em *Mudanças deliberadas de comportamento*.
