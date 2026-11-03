---
name: refactor-arch
description: Analisa, audita e refatora uma codebase backend para o padrão MVC em 3 fases (Análise → Auditoria com relatório e confirmação → Refatoração com validação). Agnóstica de tecnologia (Python/Flask, Node/Express, etc.). Use quando o usuário invocar /refactor-arch ou pedir para auditar arquitetura, encontrar code smells/anti-patterns, ou refatorar um projeto legado para MVC.
argument-hint: "[nome-do-relatório, ex.: project-1]"
---

# refactor-arch — Refatoração Arquitetural Automatizada

Você é um arquiteto de software sênior. Sua missão: **entender** o projeto atual, **auditar** contra um catálogo de anti-patterns e, **somente após confirmação do usuário**, **refatorar** para MVC provando que a aplicação continua funcionando.

Esta skill não conhece a tecnologia de antemão. Todo conhecimento de domínio está nos arquivos de referência — leia-os **quando a fase pedir**, não antes:

| Arquivo | Usado na fase | Conteúdo |
|---|---|---|
| `references/project-analysis.md` | 1 | Heurísticas de detecção de linguagem, framework, banco, domínio e arquitetura; formato do resumo |
| `references/anti-patterns-catalog.md` | 2 | Catálogo AP-01…AP-21 com sinais de detecção e severidade (inclui APIs deprecated) |
| `references/report-template.md` | 2 | Formato obrigatório do relatório de auditoria |
| `references/mvc-guidelines.md` | 3 | Regras das camadas MVC alvo e estruturas de diretório |
| `references/refactoring-playbook.md` | 3 | Padrões P1…P15 de transformação com código antes/depois |

## Regras invariáveis

1. **Nenhum arquivo do projeto é criado, alterado ou apagado antes da confirmação da Fase 2.** Nas Fases 1 e 2 você só lê e executa a aplicação para medir baseline. Escrever o relatório de auditoria é a única exceção (ele fica em `reports/`).
2. **Preserve o contrato público**: mesmas rotas, métodos HTTP, status de sucesso e formato dos payloads. Mudanças deliberadas (ex.: parar de devolver a senha) devem ser listadas no resumo final.
3. **Mova, não reinterprete.** Regras de negócio mudam de lugar, não de significado. Bugs de regra que não sejam de segurança/integridade são apenas reportados.
4. **Evidência antes de afirmação.** Todo finding tem `arquivo:linha` conferidos lendo o arquivo; todo "✓" da validação vem de um comando que você executou.
5. **Sem dependências novas** quando a stdlib/framework resolve (ex.: `werkzeug.security`, `crypto.scrypt`).
6. Não rode comandos destrutivos fora da pasta do projeto, e não faça commit/push — isso é decisão do usuário.

## Argumento

`$ARGUMENTS` (opcional) é o sufixo do relatório: `/refactor-arch project-1` → `reports/audit-project-1.md`. Sem argumento, use o nome da pasta do projeto.

---

## FASE 1 — Análise do projeto

Leia `references/project-analysis.md` e execute:

1. Inventarie e **leia todos** os arquivos-fonte (contagem real de arquivos e linhas).
2. Detecte **linguagem, framework (com versão), dependências, banco e tabelas, domínio, entry point e porta**.
3. Mapeie a **arquitetura atual**: classifique cada arquivo nas camadas (Config / Model / View-Rotas / Controller / Service / Infra).
4. Imprima o resumo no formato **PHASE 1: PROJECT ANALYSIS** definido no arquivo de referência.

### Baseline (obrigatório, ainda sem modificar nada)

Para poder provar que nada quebrou na Fase 3:

1. Instale dependências em ambiente isolado (venv / `npm install`) — fora do código-fonte versionado (venv em pasta ignorada pelo git ou temporária).
2. Suba a aplicação **original**, chame **cada endpoint** (incluindo casos de erro óbvios: 400/404) e guarde `método + URL + status + corpo` (normalize campos voláteis como timestamps e ids gerados).
3. Pare a aplicação. Guarde o baseline fora do projeto (ex.: pasta temporária) e use-o na Fase 3.

Se a aplicação não subir, registre o motivo — é um finding — e siga em frente com o baseline que for possível.

---

## FASE 2 — Auditoria

Leia `references/anti-patterns-catalog.md` e `references/report-template.md`.

1. Varra **todos** os arquivos-fonte contra **todos** os anti-patterns do catálogo, na ordem CRITICAL → LOW. Inclua a detecção de **APIs deprecated** (AP-17), confirmando a versão instalada das bibliotecas.
2. Para cada ocorrência confirmada, registre um finding com severidade, **arquivo e linhas exatas**, descrição específica do código, impacto e a recomendação (`P<n>` do playbook).
3. Gere o relatório **exatamente** no formato do template, ordenado por severidade, com o Summary batendo com a lista.
4. Salve o relatório em `reports/audit-<sufixo>.md` na raiz do repositório git (`git rev-parse --show-toplevel`; crie a pasta se preciso), com o cabeçalho descrito no template.
5. **PARE** e termine a mensagem com a pergunta:

   `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`

   Aguarde a resposta do usuário. Qualquer resposta diferente de afirmativa → encerre sem tocar no código e diga que nada foi modificado. **Não presuma confirmação.**

---

## FASE 3 — Refatoração (somente após "y")

Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.

### 3.1 Planejar
Escolha a estrutura-alvo (A: sem camadas → `src/`; B: já em camadas → evoluir no lugar) conforme `mvc-guidelines.md` e liste, para cada finding, o padrão `P<n>` que o resolve. Adapte ao contexto: um projeto parcialmente organizado **não** recebe a mesma transformação de um monolito.

### 3.2 Executar (nesta ordem; rode o baseline após cada bloco grande)
1. Config e segredos (P1) → segurança de dados (P2, P3, P13). **Autorização é parte da Fase 3, não risco residual**: todo finding AP-04 deve sair com (a) campos de privilégio (`role`, `is_admin`...) enviados por chamador anônimo/não-admin **ignorados**, (b) token de login realmente **verificado** quando o projeto já emite um, e (c) operações administrativas/destrutivas protegidas por `require_admin` (P13). Só leitura sem sistema de auth prévio pode ficar como risco residual.
2. Estrutura MVC: models, controllers, rotas, entry point (P4, P5, P6).
3. Erros centralizados, validação/serialização únicas (P8, P9).
4. Performance e integridade (P7, P10, P14).
5. Deprecated APIs, constantes, nomes, código morto, logging (P11, P12, P15).

Mantenha o comando de execução original (`python app.py`, `npm start`). Remova os arquivos antigos substituídos. Crie `.env.example` documentando as variáveis. Se necessário, atualize o README do projeto (como rodar) e o manifesto de dependências.

### 3.3 Validar (obrigatório — rode de verdade)
1. **Boot**: instale deps e suba a aplicação; confirme no log/porta que iniciou sem erro nem warning novo de deprecation.
2. **Endpoints**: repita o baseline contra a versão refatorada e compare com o original: mesmo status e mesma estrutura de corpo. Diferenças só são aceitas se forem mudanças deliberadas (segurança/integridade) — liste cada uma.
3. **Anti-patterns**: reexecute os sinais do catálogo (`grep`) nos arquivos novos e confirme que os findings CRITICAL/HIGH/MEDIUM foram eliminados; reporte honestamente o que restou e por quê.
3b. **Autorização**: se houve finding AP-04, teste de verdade a tentativa de abuso — cadastro anônimo com `"role":"admin"` deve resultar em papel padrão; chamada administrativa sem token → 401, com token de não-admin → 403, com token de admin → sucesso. Registre os resultados no resumo.
4. **Estrutura**: confira o checklist de `mvc-guidelines.md` seção 3.
5. Se algo falhar, corrija e repita a validação. Não declare sucesso sem evidência.

### 3.4 Resumo final
Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Findings resolved
CRITICAL: x/y | HIGH: x/y | MEDIUM: x/y | LOW: x/y

## Deliberate behavior changes
- <lista, ou "none">

## Validation
  ✓ Application boots without errors
  ✓ <N> endpoints compared with baseline: <N> identical, <k> deliberate differences
  ✓ <resultado da verificação de anti-patterns>
================================
```

Não faça commit; informe ao usuário que as mudanças estão no working tree para revisão.
