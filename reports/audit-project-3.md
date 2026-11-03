# Audit Report — task-manager-api

> Gerado pela skill `refactor-arch` (Fase 2) em 2026-10-26. Linhas referem-se ao código **antes** da refatoração.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.12
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.x)
Dependencies:  flask-cors 4.0.0, marshmallow 3.20.1 (não usada), requests 2.31.0 (não usada), python-dotenv 1.0.0 (não usada)
Domain:        Task Manager API (tasks, users, categories, relatórios, login)
Architecture:  Parcialmente em camadas (models/routes/services/utils) com lógica de negócio e acesso a dados nas rotas
Source files:  15 files analyzed (~1160 lines of code)
DB tables:     tasks, users, categories (SQLite via SQLAlchemy, tasks.db)
Entry point:   app.py (porta 5000); seed.py popula o banco
Layers found:  app.py → Config (inline) + Entry point + health/index handlers
               database.py → Infra (db = SQLAlchemy())
               models/{task,user,category}.py → Model (+ serialização; regras de domínio não usadas)
               routes/task_routes.py → Routes + Controller + Business rules + Data + Serialização
               routes/user_routes.py → Routes + Controller + Business rules + Data + Serialização
               routes/report_routes.py → Routes + Controller + Business rules + Data (relatórios E CRUD de categorias)
               services/notification_service.py → Service (credenciais hardcoded, nunca usado)
               utils/helpers.py → Utils (quase todo código morto) + constantes não usadas
               seed.py → Infra (dados iniciais)
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask (Flask-SQLAlchemy)
Files:   15 analyzed | ~1160 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] AP-01 — Credenciais e segredos hardcoded
File: app.py:11-13, services/notification_service.py:7-10
Description: `SECRET_KEY = 'super-secret-key-123'` fixo no entry point; `NotificationService` traz usuário e senha SMTP (`taskmanager@gmail.com` / `senha123`) no `__init__`.
Impact: Segredos de sessão e credencial de e-mail versionados no Git.
Recommendation: Ler de variáveis de ambiente em `config/settings.py`; serviço recebe a configuração por injeção (Playbook P1).

### [CRITICAL] AP-04 — Escalonamento de privilégio e autenticação simulada
File: routes/user_routes.py:52, 71-72, 74-78, 119-122, 134-151, 185-211
Description: `POST /users` (anônimo) lê `role` do corpo e grava `admin`/`manager` sem checar quem chama (mass assignment: qualquer cliente se cadastra como admin); `PUT /users/<id>` também aceita `role` e `active` de qualquer chamador; `DELETE /users/<id>` apaga o usuário e todas as suas tasks sem identificar quem pede; `POST /login` devolve `'fake-jwt-token-' + str(user.id)` — token previsível, e nenhuma rota verifica token algum.
Impact: Qualquer pessoa vira administrador com um único `POST`, promove outras contas, apaga usuários e forja o "token".
Recommendation: Aplicar na Fase 3 (não fica como risco residual) — (1) cadastro anônimo **ignora** o `role` enviado e grava o papel padrão; só um admin autenticado pode definir papel; (2) token assinado com expiração **e verificação real** (`Authorization: Bearer`), via `middlewares/auth.py`; (3) `require_admin` em `DELETE /users/<id>` e exigência de admin autenticado para alterar `role`/`active` em `PUT /users/<id>` (401 sem token, 403 sem papel admin) (Playbook P13).

### [CRITICAL] AP-05 — Armazenamento inseguro de senha
File: models/user.py:27-32
Description: `set_password` e `check_password` usam `hashlib.md5(pwd.encode())` sem sal e sem custo.
Impact: MD5 sem sal é quebrado por tabela arco-íris em segundos; um vazamento do banco expõe as senhas.
Recommendation: `werkzeug.security.generate_password_hash` / `check_password_hash` (Playbook P3).

### [CRITICAL] AP-06 — Exposição de dados sensíveis nas respostas
File: models/user.py:16-25, routes/user_routes.py:33, 85, 129, 209
Description: `User.to_dict()` inclui `'password': self.password` e é usado em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`; `notification_service.py:21,24` imprime erros SMTP.
Impact: O hash da senha trafega em respostas de API (e facilita o ataque do AP-05).
Recommendation: Serializer com allowlist, sem `password` (Playbook P13).

### [HIGH] AP-07 — Lógica de negócio e acesso a dados nas rotas
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299, routes/user_routes.py:10-25, 153-183, routes/report_routes.py:12-101, 103-155, 157-223
Description: Todas as rotas validam, consultam via `Model.query`, calculam atraso/estatísticas, serializam e montam a resposta no mesmo handler (`get_tasks` tem ~50 linhas); `report_routes.py` mistura relatórios e o CRUD de categorias (domínios distintos); não existe camada de controllers.
Impact: Regra não reutilizável, difícil de testar e de manter.
Recommendation: Extrair `controllers/` por recurso, regras de domínio nos models, `routes/` só mapeando (Playbook P5, P4).

### [HIGH] AP-09 — Acoplamento forte / efeitos colaterais no import
File: app.py:9-31, seed.py:2, services/notification_service.py:12-25, routes/task_routes.py:3-6
Description: `app` é criado como global de módulo e `db.create_all()` executa no import; `seed.py` importa `app` global; rotas importam `db` e models e executam queries direto; `NotificationService` abre `smtplib.SMTP` dentro do próprio método.
Impact: Impossível criar instâncias isoladas para teste; importar o módulo já toca o banco.
Recommendation: `create_app()` factory como composition root, configuração injetada (Playbook P4, P6).

### [HIGH] AP-10 — Configuração insegura de execução
File: app.py:11-13, 34
Description: `app.run(debug=True, host='0.0.0.0')` fixo (debugger interativo exposto à rede) e URI do banco/flags inline.
Impact: Execução remota de código via debugger do Werkzeug.
Recommendation: DEBUG/HOST/PORT/DATABASE_URI por env com defaults seguros (Playbook P1).

### [HIGH] AP-11 — Integridade referencial e perda de dados
File: routes/report_routes.py:211-223, routes/user_routes.py:140-151
Description: `DELETE /categories/<id>` remove a categoria e deixa `tasks.category_id` apontando para um id inexistente; `DELETE /users/<id>` apaga em silêncio todas as tasks do usuário.
Impact: Dados órfãos / perda de dados sem aviso.
Recommendation: Anular `category_id` das tasks na mesma transação; manter a remoção das tasks do usuário de forma explícita no model (Playbook P14).

### [MEDIUM] AP-12 — Queries N+1
File: routes/task_routes.py:42, 51, routes/user_routes.py:22, routes/report_routes.py:56, 163
Description: `get_tasks` faz `User.query.get` e `Category.query.get` por task; `get_users` acessa `len(u.tasks)` (lazy load) por usuário; o resumo executa `Task.query.filter_by(user_id=...)` por usuário e `get_categories` faz um `count()` por categoria.
Impact: Número de queries cresce linearmente com os dados.
Recommendation: `joinedload` e agregações `GROUP BY` (Playbook P7).

### [MEDIUM] AP-13 — Código duplicado
File: routes/task_routes.py:30-39, 71-80, 283-287, routes/user_routes.py:162-181, routes/report_routes.py:33-43, 132-135, models/task.py:50-60
Description: O cálculo de `overdue` está copiado em 6 lugares apesar de existir `Task.is_overdue()` (nunca usado); a serialização de task é reescrita à mão em `get_tasks` e `get_user_tasks`; validação de task duplicada entre create/update e `utils/helpers.process_task_data` (não usado); regex de e-mail em `user_routes.py:61,106` e em `helpers.validate_email`; lista de status repetida em 4 arquivos.
Impact: Correção feita em um ponto e esquecida nos outros.
Recommendation: Regra única em `Task.is_overdue()`/`to_dict()`, validação compartilhada, reuso dos helpers (Playbook P9).

### [MEDIUM] AP-14 — Validação de entrada ausente/inconsistente
File: routes/task_routes.py:113, 166-167, 182, 261, 264, routes/user_routes.py:103, 125, routes/report_routes.py:196-197
Description: `priority < 1` com valor não numérico gera TypeError (500); `len(data['title'])` em título não-string; `int(priority)`/`int(user_id)` no `/tasks/search` sem tratamento; `PUT /categories/<id>` faz `'name' in data` com corpo nulo (TypeError); `name` e `active` do usuário sem validação de tipo.
Impact: Entrada malformada vira HTTP 500 em vez de 400.
Recommendation: Validação centralizada que devolve 400 (Playbook P9).

### [MEDIUM] AP-15 — Tratamento de erro inadequado
File: routes/task_routes.py:62, 137, 236, routes/user_routes.py:130, 149, routes/report_routes.py:186, 207, 221, utils/helpers.py:47-49, 88
Description: `except:` sem classe engole qualquer erro (inclusive KeyboardInterrupt) e devolve mensagem genérica sem registrar; cada rota repete o mesmo try/commit/rollback; não existe handler global de 404/500.
Impact: Falhas silenciosas e impossíveis de diagnosticar.
Recommendation: Erros de domínio + error handlers centralizados com log (Playbook P8).

### [MEDIUM] AP-17 — Deprecated API: datetime.utcnow() e Query.get()
File: models/task.py:15-16, 52, models/user.py:14, models/category.py:11, routes/task_routes.py:31, 72, 285, routes/user_routes.py:172, routes/report_routes.py:35, 45, 71, 133, utils/helpers.py:38, services/notification_service.py:35, seed.py:66-74; Query.get em routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227, routes/user_routes.py:29, 94, 136, 155, routes/report_routes.py:105, 192, 213
Description: `datetime.utcnow()` está deprecated desde o Python 3.12 (DeprecationWarning confirmado ao executar) e `Model.query.get()` é API legada do SQLAlchemy 2.x (LegacyAPIWarning confirmado). `hashlib.md5` para senha está em AP-05.
Impact: Warnings hoje; quebra em versões futuras do Python/SQLAlchemy.
Recommendation: `utc_now()` central (UTC sem tzinfo, preserva as comparações com o banco) e `db.session.get(Model, id)` (Playbook P11).

### [LOW] AP-18 — Magic numbers e strings
File: routes/task_routes.py:96-100, 110, 113, models/task.py:39,46, routes/user_routes.py:64, 71, 120, utils/helpers.py:110-116
Description: Limites de título (3/200), faixa de prioridade (1-5), senha mínima (4), listas de status/roles espalhadas; as constantes existem em `helpers.py:110-116` mas ninguém as usa.
Impact: Regra duplicada e divergente.
Recommendation: `config/constants.py` único consumido pelas camadas (Playbook P12).

### [LOW] AP-19 — Nomenclatura ruim
File: routes/report_routes.py:24-28, 157-223, models/category.py:14, routes/task_routes.py:16
Description: `p1…p5`, `t`, `u`, `d`, `cat`; arquivo `report_routes.py` hospeda as rotas de `/categories`.
Impact: Leitura difícil e arquivo com nome enganoso.
Recommendation: Nomes descritivos e `category_routes.py` próprio (Playbook P12).

### [LOW] AP-20 — Código morto e imports não usados
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, services/notification_service.py:1-48, utils/helpers.py:2-7, 9-55, 57-108
Description: Imports nunca usados (`os, sys, json, time, hashlib, format_date, calculate_percentage`); `NotificationService` inteiro nunca é chamado; quase todas as funções de `helpers.py` (`generate_id`, `log_action`, `sanitize_string`, `process_task_data`...) e `Task.validate_status/validate_priority` não têm uso; `marshmallow`, `requests` e `python-dotenv` estão em `requirements.txt` sem uso.
Impact: Ruído, superfície de manutenção e dependências desnecessárias.
Recommendation: Remover o que é morto e reutilizar o que é a versão correta de lógica duplicada (Playbook P15, P9).

### [LOW] AP-21 — print como logging
File: routes/task_routes.py:149, 153, 219, 234, routes/user_routes.py:83, 89, 147, services/notification_service.py:21, 24, utils/helpers.py:36-41
Description: `print` direto nas rotas e no serviço, sem nível nem destino configurável.
Impact: Sem controle de verbosidade.
Recommendation: Módulo `logging` (Playbook P15).

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Confirmação: y — Fase 3 executada em 2026-10-26.
