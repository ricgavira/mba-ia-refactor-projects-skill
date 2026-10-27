# Template do Relatório de Auditoria (Fase 2)

O relatório é impresso no terminal **e** salvo em `reports/audit-<nome-do-projeto>.md` (ver SKILL.md). Use exatamente este formato.

## Regras de preenchimento

1. **Ordenação**: findings por severidade `CRITICAL → HIGH → MEDIUM → LOW`. Dentro da mesma severidade, ordene pelo ID do catálogo.
2. **Localização exata**: `File: caminho/relativo.ext:linha-inicio-linha-fim` (ou `:linha` para uma única linha). Linhas devem ser conferidas no arquivo — nunca aproximadas. Várias ocorrências: `File: a.py:10-12, 40, 77-80`.
3. **Description**: o que está errado **neste código** (cite nomes reais de função/variável), não a definição genérica do catálogo.
4. **Impact**: consequência concreta (o que um atacante/mantenedor/usuário sofre).
5. **Recommendation**: a transformação do playbook que será aplicada (cite o `P<n>`).
6. **Summary** deve bater com a lista de findings (contagem por severidade e total).
7. **APIs deprecated** entram como findings `[MEDIUM]`/`[LOW]` com o título `Deprecated API: <nome>` e a API moderna na Recommendation. Se não houver nenhuma, escreva a linha `Deprecated APIs: none detected` antes do total.
8. Idioma: descrições em português; cabeçalhos e rótulos em inglês, como abaixo.
9. Termine **sempre** com a pergunta de confirmação. Não altere nenhum arquivo do projeto antes da resposta afirmativa.

## Template

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <AP-ID> — <título curto do anti-pattern>
File: <caminho>:<linhas>
Description: <o que acontece neste código>
Impact: <consequência>
Recommendation: <correção planejada> (Playbook P<n>)

### [HIGH] <AP-ID> — <título>
File: <caminho>:<linhas>
Description: ...
Impact: ...
Recommendation: ...

### [MEDIUM] ...
### [LOW] ...

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Exemplo preenchido (trecho)

```
### [CRITICAL] AP-02 — SQL Injection
File: models.py:28, 48-49, 110, 290-297
Description: Queries montadas com concatenação de strings usando dados da requisição
(get_produto_por_id, criar_produto, login_usuario, buscar_produtos).
Impact: Um atacante autentica sem senha (' OR '1'='1) e lê/altera/apaga qualquer tabela.
Recommendation: Usar queries parametrizadas (?) em todas as consultas (Playbook P2).
```

## Variante para o arquivo salvo

O arquivo `reports/audit-*.md` é o mesmo conteúdo, com duas adições no topo, antes do bloco `ARCHITECTURE AUDIT REPORT`:

```
# Audit Report — <projeto>

> Gerado pela skill `refactor-arch` (Fase 2) em <AAAA-MM-DD>. Linhas referem-se ao código **antes** da refatoração.
```

e, após a confirmação do usuário, uma linha final `Confirmação: y — Fase 3 executada em <AAAA-MM-DD>`.
