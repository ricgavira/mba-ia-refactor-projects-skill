# Audit Report — ecommerce-api-legacy

> Gerado pela skill `refactor-arch` (Fase 2) em 2026-10-26. Linhas referem-se ao código **antes** da refatoração.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js v20.19.0)
Framework:     Express 4.x (^4.18.2)
Dependencies:  express, sqlite3 ^5.1.6
Domain:        LMS API com fluxo de checkout (cursos, matrículas, pagamentos, usuários, auditoria)
Architecture:  Monolítica — lógica, rotas e banco concentrados em uma God Class (AppManager)
Source files:  3 files analyzed (~180 lines of code)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite em memória)
Entry point:   src/app.js (porta 3000, `npm start`)
Layers found:  src/app.js → Entry point (composition mínima)
               src/AppManager.js → Infra (banco) + Schema/Seed + Routes + Controller + Business rules + Data
               src/utils.js → Config (com segredos) + Infra (cache global) + Security (hash caseiro)
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Node.js/Express
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] AP-01 — Credenciais e segredos hardcoded
File: src/utils.js:2-6
Description: O objeto `config` contém `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` e `smtpUser` em texto no código-fonte.
Impact: Chave live do gateway de pagamento e senha de banco versionadas no Git; qualquer pessoa com acesso ao repositório pode cobrar/estornar em nome da loja.
Recommendation: Ler tudo de variáveis de ambiente em `src/config/settings.js`, sem default real (Playbook P1).

### [CRITICAL] AP-03 — God Class
File: src/AppManager.js:4-139
Description: `AppManager` cria a conexão SQLite (7), define schema e seeds (10-23), registra as rotas e implementa inline o checkout (28-78), o relatório financeiro (80-129) e a remoção de usuário (131-137).
Impact: Banco, regras, rotas e formatação acoplados; nenhuma parte é testável isolada.
Recommendation: Separar em config/database/models/services/controllers/views/middlewares com `createApp()` (Playbook P4).

### [CRITICAL] AP-04 — Endpoints destrutivos/administrativos sem autenticação
File: src/AppManager.js:80-129, 131-137
Description: `GET /api/admin/financial-report` expõe receita e nomes de alunos e `DELETE /api/users/:id` apaga qualquer usuário, ambos sem qualquer verificação de identidade.
Impact: Qualquer cliente lê dados financeiros e remove contas.
Recommendation: Aplicar na Fase 3 (não fica como risco residual): middleware `requireAdminToken` que **falha fechado** — sem `ADMIN_TOKEN` configurado as duas rotas ficam desabilitadas (403); com ele, header `X-Admin-Token` ausente → 401 e incorreto → 403, comparação em tempo constante (Playbook P13).

### [CRITICAL] AP-05 — Armazenamento inseguro de senha
File: src/utils.js:17-23, src/AppManager.js:18, 68
Description: `badCrypto` concatena base64 em loop de 10.000 iterações e corta em 10 caracteres — não é hash, é determinístico, sem sal e colide; quando `pwd` não vem, a senha vira o default implícito `"123456"` (linha 68); o seed grava a senha `'123'` em claro (linha 18).
Impact: Senhas recuperáveis/colidíveis; contas novas criadas com senha previsível.
Recommendation: `crypto.scrypt` com sal por usuário e comparação em tempo constante; `pwd` obrigatório ao criar usuário (Playbook P3).

### [CRITICAL] AP-06 — Exposição de dados sensíveis em log
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` imprime o número completo do cartão e a chave do gateway a cada checkout.
Impact: Dados de cartão e segredo em logs (violação PCI-DSS) acessíveis a quem lê os logs.
Recommendation: Logar apenas o cartão mascarado (últimos 4 dígitos) e nunca a chave (Playbook P13).

### [HIGH] AP-07 — Lógica de negócio em handlers de rota
File: src/AppManager.js:28-78, 80-129
Description: O handler de checkout valida entrada, decide aprovação do pagamento (`cc.startsWith("4")`), cria usuário/matrícula/pagamento/auditoria; o handler de relatório agrega receita por curso.
Impact: Regras não reutilizáveis nem testáveis sem HTTP.
Recommendation: Controllers finos + models/services para pagamento, matrícula e relatório (Playbook P5).

### [HIGH] AP-08 — Estado global mutável
File: src/utils.js:9-15, 25, src/AppManager.js:2, 59
Description: `globalCache` e `totalRevenue` são variáveis de módulo mutáveis exportadas; `logAndCache` escreve no cache global a cada checkout (e nunca é lido).
Impact: Estado compartilhado entre requests, vazamento de memória e acoplamento oculto.
Recommendation: Remover o estado global; se cache for necessário, serviço injetado (Playbook P6, P15).

### [HIGH] AP-09 — Acoplamento forte sem injeção de dependência
File: src/AppManager.js:5-8, 25-28, src/app.js:8-10
Description: O construtor instancia o próprio `sqlite3.Database(':memory:')`; as rotas são registradas por um método da mesma classe que acessa `this.db` diretamente; `app.js` instancia e conecta tudo manualmente.
Impact: Impossível trocar/mocar o banco; a classe conhece HTTP e persistência ao mesmo tempo.
Recommendation: Camada de banco injetada em models; composition root `createApp()` (Playbook P4, P6).

### [HIGH] AP-11 — Operações multi-passo sem atomicidade/integridade
File: src/AppManager.js:43-78, 131-137
Description: O usuário é criado (linha 69) antes de o pagamento ser aprovado — cartão recusado deixa usuário órfão; matrícula, pagamento e auditoria são `INSERT`s independentes sem transação; `DELETE /api/users/:id` não remove matrículas/pagamentos e a própria resposta admite "ficaram sujos no banco".
Impact: Dados órfãos e inconsistentes (relatório mostra "Unknown" com receita).
Recommendation: Decidir pagamento antes de escrever e gravar tudo em transação; remoção em cascata transacional (Playbook P14).

### [MEDIUM] AP-12 — Queries N+1
File: src/AppManager.js:83-125
Description: O relatório financeiro executa 1 query de matrículas por curso e, para cada matrícula, 1 query de usuário e 1 de pagamento.
Impact: Número de queries cresce com cursos × matrículas.
Recommendation: Uma query com JOINs e agrupamento em memória (Playbook P7).

### [MEDIUM] AP-14 — Validação de entrada insuficiente
File: src/AppManager.js:29-35, 131-133
Description: Checkout só testa truthiness de `usr/eml/cid/cc` (sem formato de e-mail, sem tipo, sem exigir `pwd`); `:id` do DELETE não é validado.
Impact: Dados inválidos chegam ao banco; senha opcional gera conta com senha padrão.
Recommendation: Validação explícita no controller com 400 (Playbook P9).

### [MEDIUM] AP-15 — Tratamento de erro inadequado
File: src/AppManager.js:38-41, 57-58, 92-93, 104-106, 133-135, 35-77
Description: Vários callbacks ignoram `err` (auditoria 57, matrículas 92, usuário/pagamento 104-106, delete 133) — se `enrollments` vier `undefined` a linha 93 derruba o processo; erros são strings de texto soltas ("Erro DB", "Bad Request") em formatos distintos; não há middleware de erro.
Impact: Falhas silenciosas, crash do processo e respostas inconsistentes.
Recommendation: `async/await` + `errorHandler` central com erros tipados (Playbook P8).

### [MEDIUM] AP-16 — Callback hell
File: src/AppManager.js:37-78, 83-128
Description: Checkout com 6 níveis de callbacks aninhados e `self = this`; o relatório sincroniza assíncronos com contadores manuais (`coursesPending--`, `enrPending--`).
Impact: Fluxo difícil de ler, ordem do relatório dependente da ordem de conclusão das queries (não determinística).
Recommendation: Promisificar o acesso ao banco e usar `async/await` (Playbook P10).

### [LOW] AP-18 — Magic numbers e strings
File: src/AppManager.js:46, 68, src/utils.js:6, 19-22
Description: Regra de aprovação `cc.startsWith("4")`, status `"PAID"`/`"DENIED"` soltos, senha `"123456"`, porta 3000 e laço de 10000 iterações com `substring(0, 10)` sem nome.
Impact: Regra de negócio escondida em literais.
Recommendation: Constantes nomeadas e serviço de gateway (Playbook P12).

### [LOW] AP-19 — Nomenclatura ruim
File: src/AppManager.js:29-33, 4, 26, 89, 102, src/utils.js:17
Description: Variáveis `u`, `e`, `p`, `cid`, `cc`, `c`, `enr`, `self`; classe genérica `AppManager`; função `badCrypto`. Os nomes `usr/eml/pwd/c_id/card` são contrato público e só podem ser mapeados na borda.
Impact: Leitura difícil.
Recommendation: Mapear o payload para nomes claros na fronteira do controller (Playbook P12).

### [LOW] AP-20 — Código morto e imports não usados
File: src/utils.js:3-5, 10, 25, src/AppManager.js:2
Description: `dbUser`, `dbPass`, `smtpUser` nunca são usados; `totalRevenue` é exportado e importado sem uso; `globalCache` nunca é lido.
Impact: Ruído e superfície de segredos sem função.
Recommendation: Remover (Playbook P15).

### [LOW] AP-21 — console.log como logging
File: src/AppManager.js:45, src/utils.js:13, src/app.js:13
Description: `console.log` direto, sem nível, inclusive com dado sensível.
Impact: Sem controle de verbosidade; vazamento (ver AP-06).
Recommendation: Módulo `logger` simples (Playbook P15).

Deprecated APIs: none detected (conferidas as APIs de Express 4.x, sqlite3 5.x e Node 20 contra AP-17; o estilo callback é tratado em AP-16)

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Confirmação: y — Fase 3 executada em 2026-10-26.
