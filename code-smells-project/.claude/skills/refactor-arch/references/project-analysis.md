# Análise de Projeto — Heurísticas da Fase 1

Objetivo: descobrir **linguagem, framework, banco, domínio e arquitetura atual** lendo o código, sem assumir nada sobre a stack. Toda conclusão deve ter evidência (arquivo ou linha) — se não houver evidência, escreva `não detectado`.

## 1. Inventário de arquivos

1. Liste os arquivos do projeto ignorando: `.git/`, `node_modules/`, `venv/`, `.venv/`, `__pycache__/`, `dist/`, `build/`, `target/`, `vendor/`, `*.lock`, `*.db`, `*.sqlite*`, binários e `.claude/`.
2. Conte **arquivos-fonte** (extensões de código) e **linhas de código** (`wc -l` ou leitura). Esses números vão para o resumo — nunca estime "de cabeça".
3. Leia **todos** os arquivos-fonte. Projetos-alvo são pequenos; se passar de ~40 arquivos, leia primeiro entry point, rotas, e os 10 maiores arquivos, e amostre o resto.

## 2. Detecção de linguagem

Use a extensão dominante **e** o arquivo de manifesto. O manifesto vence em caso de dúvida.

| Sinal (arquivo) | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `*.py` | Python |
| `package.json`, `*.js`, `*.mjs`, `*.cjs` | JavaScript / Node.js |
| `tsconfig.json`, `*.ts` | TypeScript |
| `pom.xml`, `build.gradle(.kts)`, `*.java`, `*.kt` | Java / Kotlin |
| `go.mod`, `*.go` | Go |
| `composer.json`, `*.php` | PHP |
| `Gemfile`, `*.rb` | Ruby |
| `*.csproj`, `*.sln`, `*.cs` | C# / .NET |
| `Cargo.toml`, `*.rs` | Rust |

Versão da linguagem: `engines` no `package.json`, `python_requires`, `.python-version`, `.nvmrc`, `go.mod`, `<java.version>`. Se ausente, registre a versão do runtime instalado (`python --version`, `node --version`).

## 3. Detecção de framework

Procure primeiro nas **dependências declaradas** (com versão), depois confirme nos **imports** do entry point.

| Linguagem | Dependência / import | Framework | Como confirmar |
|---|---|---|---|
| Python | `flask` / `from flask import Flask` | Flask | `Flask(__name__)`, `@app.route`, `Blueprint`, `add_url_rule` |
| Python | `flask-sqlalchemy` | Flask + SQLAlchemy ORM | `db = SQLAlchemy()`, `db.Model` |
| Python | `django` | Django | `manage.py`, `settings.py`, `urls.py`, `views.py` |
| Python | `fastapi` | FastAPI | `FastAPI()`, `@app.get`, `APIRouter` |
| Node | `express` | Express | `express()`, `app.get/post`, `express.Router()` |
| Node | `@nestjs/core` | NestJS | `@Controller`, `@Injectable`, `@Module` |
| Node | `koa`, `fastify`, `hapi` | respectivo | `new Koa()`, `fastify()` |
| Java | `spring-boot-starter-web` | Spring Boot | `@RestController`, `@SpringBootApplication` |
| PHP | `laravel/framework` | Laravel | `artisan`, `routes/web.php` |
| Ruby | `rails` | Rails | `config/routes.rb`, `app/controllers` |
| Go | `gin-gonic/gin`, `labstack/echo`, `net/http` | Gin / Echo / stdlib | `gin.Default()`, `http.HandleFunc` |
| C# | `Microsoft.AspNetCore` | ASP.NET Core | `[ApiController]`, `MapControllers()` |

Registre também as demais dependências relevantes (CORS, ORM, validação, auth, testes).

## 4. Detecção de banco de dados

1. **Driver/ORM** nas dependências ou imports: `sqlite3`, `psycopg2`, `pymysql`, `sqlalchemy`, `pg`, `mysql2`, `mongoose`, `sequelize`, `typeorm`, `prisma`, `gorm`, `JpaRepository`, `ActiveRecord`...
2. **String de conexão / arquivo**: `sqlite:///x.db`, `new sqlite3.Database(':memory:')`, `postgres://`, `mongodb://`, `DATABASE_URL`.
3. **Tabelas/entidades**: `CREATE TABLE`, `db.Model`/`@Entity`/`Schema(...)`. Liste os nomes — vão para `DB tables:` no resumo.
4. **Estilo de acesso**: SQL cru (`cursor.execute`, `db.run`) vs ORM (`Model.query`, `repository.find`). Isso define o playbook (parametrização vs. uso correto do ORM).
5. **Seed/migrations**: dados iniciais no boot, `seed.py`, `migrations/`. Se há seed, o baseline de endpoints depende dele.
6. Banco em memória (`:memory:`) → dados somem a cada boot; o baseline precisa criar os dados que usa.

## 5. Detecção de domínio

O domínio sai de **nomes de tabelas, entidades e rotas**, não do nome da pasta.

- Reúna rotas (`/produtos`, `/pedidos`, `/api/checkout`, `/tasks`, `/users`) e entidades.
- Descreva em uma linha: `<tipo de sistema> (<entidades principais>)`. Ex.: `E-commerce API (produtos, pedidos, usuários)`, `LMS API com fluxo de checkout (cursos, matrículas, pagamentos)`, `Task Manager API (tasks, users, categories, relatórios)`.

## 6. Entry point e como executar

- Python: arquivo com `app.run(...)`/`if __name__ == "__main__"`, ou `manage.py`, `uvicorn module:app`.
- Node: campo `main` e `scripts.start` do `package.json`.
- Java/Go/etc.: classe `main`, `main.go`.
- Descubra **porta**, **host** e **comandos de instalação/execução** (README, scripts). Você os usará na Fase 3 para validar o boot.

## 7. Mapeamento da arquitetura atual

Classifique **cada arquivo-fonte** em uma ou mais camadas pelos sinais abaixo.

| Camada | Sinais no código |
|---|---|
| **Config** | leitura de env, constantes de conexão, `app.config[...]`, objeto `config = {...}` |
| **Model / Dados** | `class X(db.Model)`, `CREATE TABLE`, `SELECT/INSERT/UPDATE`, repositórios, DAOs, schemas |
| **View / Rotas** | `@app.route`, `add_url_rule`, `app.get(...)`, `Router`, `Blueprint`, `@RestController` |
| **Controller** | funções que lêem `request`/`req`, validam entrada e montam `jsonify`/`res.json` |
| **Service / Regra de negócio** | cálculo de total, desconto, estado de pedido, notificações, integração externa |
| **Infra / Util** | helpers, logger, cache, formatação |

Um arquivo que aparece em **3 ou mais** camadas é candidato a God Class/God File.

Classifique a arquitetura em um dos rótulos:

- `Monolítica — tudo em N arquivos, sem separação de camadas` (rotas + SQL + regra no mesmo lugar)
- `Parcialmente em camadas (models/routes/services/utils) com lógica de negócio nas rotas`
- `MVC` / `MVC com services` (só se as responsabilidades de fato estiverem separadas)
- `Em camadas, mas com acoplamento circular / global state`

Não confie nos nomes das pastas: abra os arquivos. Uma pasta `models/` pode conter apenas dados enquanto toda a regra está em `routes/`.

## 8. Formato do resumo da Fase 1

Imprima exatamente (preenchendo os valores reais):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão do runtime>
Framework:     <framework + versão>
Dependencies:  <deps relevantes>
Domain:        <domínio em uma linha>
Architecture:  <rótulo da seção 7 + 1 frase de justificativa>
Source files:  <N> files analyzed (~<LOC> lines of code)
DB tables:     <tabelas/entidades>
Entry point:   <arquivo> (porta <porta>)
Layers found:  <arquivo → camada(s), uma linha por arquivo>
================================
```

Depois do resumo, **registre o baseline** (ver SKILL.md, seção "Baseline"): inicie a aplicação original, chame cada endpoint e guarde status + corpo. Sem baseline não é possível provar que a refatoração preservou o comportamento.
