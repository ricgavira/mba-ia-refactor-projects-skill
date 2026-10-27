# Catálogo de Anti-Patterns

Cada entrada tem: **ID**, **severidade**, **o que é**, **sinais de detecção** (acionáveis — algo que se encontra com `grep` ou leitura) e **playbook** (padrão de correção em `refactoring-playbook.md`).

## Escala de severidade

| Severidade | Critério |
|---|---|
| **CRITICAL** | Falha de segurança explorável, exposição de credenciais/dados sensíveis, ou violação total da separação de responsabilidades (God Class/File). |
| **HIGH** | Forte violação de MVC/SOLID que dificulta manutenção e teste: regra de negócio em controller/rota, acoplamento sem injeção de dependência, estado global mutável, operações multi-passo sem atomicidade. |
| **MEDIUM** | Padronização, duplicação, performance moderada (N+1), validação ausente, tratamento de erro inadequado, APIs deprecated. |
| **LOW** | Legibilidade: nomes ruins, magic numbers, imports/código morto, `print`/`console.log` como log. |

Regra de desempate: na dúvida entre duas severidades, escolha a **maior** se houver dado sensível ou execução arbitrária envolvidos; caso contrário, a menor.

---

## CRITICAL

### AP-01 — Credenciais e segredos hardcoded
- **Sinais**: literais atribuídos a nomes como `SECRET_KEY`, `password`, `pass`, `pwd`, `token`, `api_key`, `*_KEY`, `smtpPass`, `dbPass`; prefixos `pk_live_`, `sk_`, `AKIA`; strings de conexão com usuário/senha; `app.config["SECRET_KEY"] = "..."`.
- **Busca**: `grep -rniE "(secret|passw|pwd|api_?key|token)\w*\s*[:=]\s*[\"'][^\"']+[\"']"`.
- **Por que é crítico**: o segredo vai para o Git e para quem tiver acesso ao repositório.
- **Playbook**: P1.

### AP-02 — SQL Injection (SQL montado por concatenação/interpolação)
- **Sinais**: `execute("... " + var)`, `f"SELECT ... {var}"`, `"... %s" % var`, template literal com `${}` dentro de SQL, `LIKE '%" + termo + "%'`, `.format()` em SQL, `text(f"...")` no SQLAlchemy.
- **Busca**: `grep -rnE "(execute|run|get|all|query)\(.*(\+|f\"|f'|\\$\{|%s|\.format)"` nos arquivos de dados.
- **Contra-exemplo**: `execute("... WHERE id = ?", (id,))` e `filter(Model.col == valor)` são seguros.
- **Playbook**: P2.

### AP-03 — God Class / God File
- **Sinais**: um arquivo que mistura **3+ camadas** (rotas + SQL/ORM + regra de negócio + formatação + notificação); arquivo de models com lógica de vários domínios; classe "Manager/Handler" que cria o banco, define rotas e implementa fluxos; função de rota com >60 linhas; arquivo >300 linhas com múltiplos domínios.
- **Como medir**: para cada arquivo, marque quais camadas da seção 7 de `project-analysis.md` ele contém.
- **Playbook**: P4 (e P5 para a regra de negócio).

### AP-04 — Endpoint perigoso sem autenticação/autorização
- **Sinais**: rota que executa SQL recebido do cliente (`/admin/query`), apaga/reseta dados (`/admin/reset-db`), ou expõe operações administrativas sem checar identidade/papel; rota `DELETE`/`PUT` sem qualquer verificação de dono ou role.
- **Busca**: rotas com `admin`, `reset`, `debug`, `query`, `exec`, `eval` no caminho.
- **Playbook**: P13.

### AP-05 — Armazenamento inseguro de senha
- **Sinais**: senha gravada/comparada em texto puro (`WHERE senha = '...'`, `password == pwd`); hash fraco/rápido (`md5`, `sha1`, `sha256` sem sal); "criptografia caseira" (loop de base64, XOR, rot13); senha padrão implícita (`pwd || "123456"`).
- **Busca**: `grep -rniE "md5|sha1|hashlib\.(md5|sha1)|createHash\('(md5|sha1)'|base64"` perto de `pass|senha|pwd`.
- **Playbook**: P3.

### AP-06 — Exposição de dados sensíveis (respostas e logs)
- **Sinais**: resposta JSON contendo `password`/`senha`/hash; endpoint de health/debug devolvendo `secret_key`, caminhos, flags de debug; log com número de cartão completo, token ou chave de gateway; `str(e)` de exceção devolvido ao cliente (vaza stack/SQL); `to_dict()` que serializa a senha.
- **Playbook**: P13 (e P8 para erros).

---

## HIGH

### AP-07 — Lógica de negócio em Controllers/Rotas
- **Sinais**: handler que calcula totais/descontos, aplica regras de estado, consulta várias entidades, valida regras de domínio, envia notificações; handler com `if` aninhados de regra (ex.: cálculo de atraso repetido em cada rota); acesso direto a `Model.query`/SQL dentro da rota.
- **Playbook**: P5.

### AP-08 — Estado global mutável
- **Sinais**: `global x`, variável de módulo mutada em funções (`db_connection = None` + `global db_connection`), caches em `let globalCache = {}`, contadores globais (`totalRevenue`), singletons exportados e mutados, conexão única compartilhada entre requests.
- **Playbook**: P6.

### AP-09 — Acoplamento forte sem injeção de dependência
- **Sinais**: classe/função que instancia suas próprias dependências (`new sqlite3.Database(...)` no construtor, `NotificationService()` dentro da rota, `smtplib` dentro do model); controller que importa o driver de banco; models importando `request`; módulos com import circular; rotas definidas dentro da classe que também cria o banco.
- **Playbook**: P6 e P4.

### AP-10 — Configuração insegura de execução
- **Sinais**: `debug=True`/`DEBUG = True` fixo, `host="0.0.0.0"` fixo, CORS aberto sem restrição em API com dados sensíveis, `app.config` definido inline, ambiente ("producao") escrito no código.
- **Playbook**: P1.

### AP-11 — Operações multi-passo sem atomicidade / integridade referencial
- **Sinais**: sequência de `INSERT/UPDATE/DELETE` sem transação (`commit` só no final sem `rollback` em erro, ou commit por passo); efeito colateral antes da validação final (criar usuário antes de o pagamento ser aprovado); `DELETE` do pai sem tratar filhos (matrículas/pagamentos órfãos); mensagem de resposta admitindo inconsistência.
- **Playbook**: P14.

---

## MEDIUM

### AP-12 — Queries N+1
- **Sinais**: `execute`/`query` dentro de `for`/`forEach`/`map`; relacionamento ORM acessado em loop (`len(u.tasks)`, `User.query.get(t.user_id)` por tarefa); `COUNT` por categoria/usuário em loop; callbacks aninhados que fazem uma consulta por linha.
- **Playbook**: P7.

### AP-13 — Código duplicado
- **Sinais**: mesmo bloco de validação em create e update; mesma serialização de entidade (`{"id": row["id"], ...}`) repetida; mesma regra (`is_overdue`) copiada em ≥3 lugares; helpers existentes ignorados pelas rotas.
- **Playbook**: P9.

### AP-14 — Validação de entrada ausente ou inconsistente
- **Sinais**: `request.get_json()` sem checar `None`; acesso a `dados.get(...)` quando `dados` pode ser nulo; conversão `int(x)`/`float(x)` sem tratamento; comparação `preco < 0` sem checar tipo; update que valida menos que create; campos obrigatórios descobertos só no banco.
- **Playbook**: P9.

### AP-15 — Tratamento de erro inadequado
- **Sinais**: `except:` / `except Exception` que engole o erro ou repete try/except idêntico em todo handler; `catch` vazio; callback que ignora `err`; resposta de erro em formatos diferentes (texto vs JSON); falta de handler global de 404/500.
- **Playbook**: P8.

### AP-16 — Callback hell / fluxo assíncrono não gerenciado
- **Sinais**: callbacks aninhados ≥3 níveis; contadores manuais (`pending--`, `if (pending === 0) res.json`) para sincronizar assíncronos; `this`/`self` copiado para escapar de escopo; ausência de `async/await`.
- **Playbook**: P10.

### AP-17 — APIs deprecated / obsoletas
Detectar uso e recomendar o equivalente moderno. Consulte também a documentação oficial da versão **instalada** — esta lista não é exaustiva.

| Stack | API obsoleta (sinal) | Equivalente moderno |
|---|---|---|
| Python | `datetime.utcnow()` / `utcfromtimestamp()` (deprecated 3.12) | `datetime.now(timezone.utc)` (ou helper `utc_now()`) |
| SQLAlchemy 2.x | `Model.query.get(id)` (legacy) | `db.session.get(Model, id)` |
| SQLAlchemy 2.x | `Query` API legada em geral (`session.query`) | `select()` + `session.execute/scalars` |
| Python | `hashlib.md5/sha1` para senha | `werkzeug.security` / `bcrypt` / `argon2` |
| Python | `except:` sem classe | `except SpecificError as e:` |
| Flask | `@app.before_first_request` (removido no 2.3), `flask.json.JSONEncoder` | `with app.app_context()` na fábrica, `app.json` provider |
| Flask | `flask.ext.*`, `app.run(debug=True)` fixo | imports diretos, flag por env |
| Node | `new Buffer()` / `Buffer()` | `Buffer.from()` / `Buffer.alloc()` |
| Node | `var`, `require` de `body-parser` em Express ≥4.16 | `const/let`, `express.json()` |
| Node | callbacks de `fs`/`sqlite3` aninhados | `fs.promises` / wrapper com Promise + `async/await` |
| Node | `url.parse()`, `fs.exists()`, `crypto.createCipher()`, módulo `request` | `new URL()`, `fs.access`, `createCipheriv`, `fetch`/`axios` |
| Node | `res.send(status)` com número, `res.json(obj, status)` | `res.status(n).json(obj)` |
| Java | `new Date()`, `Calendar` | `java.time` |
| Geral | libs sem manutenção ou versões com CVE no manifesto | versão suportada |

- **Severidade**: MEDIUM se o runtime emite warning/removerá a API; LOW se apenas estilo.
- **Playbook**: P11.

---

## LOW

### AP-18 — Magic numbers e strings
- **Sinais**: literais numéricos de regra de negócio sem nome (`> 10000`, `* 0.1`, `len(x) < 3`), listas de valores válidos repetidas (`["pendente","aprovado",...]`), status como string solta, portas/limites inline.
- **Playbook**: P12.

### AP-19 — Nomenclatura ruim
- **Sinais**: variáveis de 1–2 letras fora de loops curtos (`u`, `e`, `p`, `cc`, `cid`), nomes genéricos (`data`, `tmp`, `res2`), chaves de payload crípticas, mistura de idiomas/estilos (`snake_case` e `camelCase`) no mesmo módulo, classes `Manager` sem responsabilidade clara.
- **Observação**: nomes que fazem parte do **contrato público** da API (ex.: `usr`, `c_id`) não podem ser renomeados na borda; mapeie-os para nomes claros internamente.
- **Playbook**: P12.

### AP-20 — Código morto e imports não usados
- **Sinais**: imports nunca referenciados (`json, os, sys, time`), funções/variáveis exportadas e nunca usadas (`totalRevenue`, `generate_id`), classes instanciadas e nunca chamadas, blocos comentados, arquivos utilitários ignorados pelo resto do código.
- **Busca**: para cada import/símbolo, `grep` das ocorrências; 1 ocorrência = não usado.
- **Playbook**: P15.

### AP-21 — `print`/`console.log` como logging
- **Sinais**: `print(...)`/`console.log(...)` espalhados nos handlers, mensagens "ENVIANDO EMAIL" simuladas com print, sem nível de log.
- **Playbook**: P15.

---

## Como usar o catálogo na Fase 2

1. Percorra os IDs **na ordem** (CRITICAL → LOW) e varra todos os arquivos-fonte procurando os sinais.
2. Cada ocorrência vira um *finding* com **arquivo e intervalo de linhas exatos** (`arquivo:inicio-fim`). Várias ocorrências do mesmo anti-pattern no mesmo arquivo podem ser agrupadas em um finding, listando todas as linhas; em arquivos diferentes, gere findings separados.
3. Valide cada sinal lendo o trecho — não reporte por correspondência de `grep` sem ler o contexto.
4. Anti-patterns sem ocorrência não aparecem no relatório.
5. Se um padrão real não está no catálogo, reporte-o com o ID `AP-X` e justifique a severidade pela escala acima.
