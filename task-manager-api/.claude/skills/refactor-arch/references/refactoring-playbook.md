# Playbook de Refatoração

Cada padrão `P<n>` resolve um ou mais anti-patterns do catálogo. Os exemplos usam Python/Flask e JavaScript/Express; **aplique a mesma transformação na sintaxe da stack encontrada**. Sempre preserve o contrato público da API (rotas, métodos, status e formato de payload).

Ordem recomendada de aplicação: P1 → P2/P3 → P4 → P6 → P5 → P9 → P8 → P7/P10/P14 → P11 → P12/P15 (segurança e estrutura primeiro, polimento por último).

| Padrão | Resolve |
|---|---|
| P1 Extrair configuração e segredos | AP-01, AP-10 |
| P2 Parametrizar queries | AP-02 |
| P3 Hash de senha adequado | AP-05 |
| P4 Quebrar God File em camadas MVC | AP-03, AP-09 |
| P5 Mover regra de negócio para Model/Service | AP-07 |
| P6 Eliminar estado global (DI / escopo de request) | AP-08, AP-09 |
| P7 Eliminar N+1 | AP-12 |
| P8 Tratamento de erro centralizado | AP-15 |
| P9 Validação e serialização únicas (DRY) | AP-13, AP-14 |
| P10 Callbacks → async/await | AP-16 |
| P11 Trocar APIs deprecated | AP-17 |
| P12 Constantes e nomes claros | AP-18, AP-19 |
| P13 Proteger endpoints perigosos e dados sensíveis | AP-04, AP-06 |
| P14 Transações e integridade referencial | AP-11 |
| P15 Remover código morto e logging adequado | AP-20, AP-21 |

---

## P1 — Extrair configuração e segredos

**Antes** (Python):
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```

**Depois**:
```python
# src/config/settings.py
import os

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "")           # sem default real
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DB_PATH = os.environ.get("DB_PATH", "loja.db")

# src/app.py
app.config.from_object(Settings)
app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
```

**Antes** (JS):
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123", port: 3000 };
```
**Depois**:
```js
// src/config/settings.js
module.exports = {
  port: Number(process.env.PORT) || 3000,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  dbPath: process.env.DB_PATH || ':memory:',
};
```

Passos: (1) liste todos os literais sensíveis; (2) crie o módulo de config; (3) substitua os usos; (4) documente as variáveis em `.env.example` (sem valores reais); (5) segredo ausente em produção deve falhar no boot ou gerar valor efêmero (`secrets.token_hex(32)`), nunca cair num literal conhecido.

---

## P2 — Parametrizar queries

**Antes**:
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
cursor.execute("SELECT * FROM produtos WHERE nome LIKE '%" + termo + "%'")
```
**Depois**:
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
cursor.execute("SELECT * FROM produtos WHERE nome LIKE ?", (f"%{termo}%",))

# filtros dinâmicos: monte o SQL com fragmentos FIXOS e acumule os parâmetros
clauses, params = ["1=1"], []
if categoria:
    clauses.append("categoria = ?"); params.append(categoria)
cursor.execute("SELECT * FROM produtos WHERE " + " AND ".join(clauses), params)
```
JS: `db.get("SELECT * FROM users WHERE email = ?", [email], cb)`.
ORM: use `filter(Model.col == valor)` / `.like(...)`; nunca `text(f"...")`.

Regras: nomes de tabela/coluna dinâmicos só via *allowlist*; `LIMIT/OFFSET` convertidos com `int()`.

---

## P3 — Hash de senha adequado

**Antes**:
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()          # Python
cursor.execute("INSERT ... VALUES (..., '" + senha + "')")     # texto puro
```
```js
function badCrypto(pwd) { /* loop de base64 */ }               // JS
```
**Depois**:
```python
from werkzeug.security import generate_password_hash, check_password_hash
self.password = generate_password_hash(pwd)       # pbkdf2/scrypt com sal
def check_password(self, pwd): return check_password_hash(self.password, pwd)
```
```js
// sem dependência nativa: crypto.scrypt do Node
const crypto = require('crypto');
const hashPassword = (pwd) => new Promise((resolve, reject) => {
  const salt = crypto.randomBytes(16).toString('hex');
  crypto.scrypt(pwd, salt, 64, (err, key) => err ? reject(err) : resolve(`${salt}:${key.toString('hex')}`));
});
const verifyPassword = (pwd, stored) => new Promise((resolve, reject) => {
  const [salt, hash] = stored.split(':');
  crypto.scrypt(pwd, salt, 64, (err, key) =>
    err ? reject(err) : resolve(crypto.timingSafeEqual(Buffer.from(hash, 'hex'), key)));
});
```
Login: busque o usuário **por e-mail** e compare o hash em código (nunca `WHERE senha = ?`). Seeds devem gravar hashes. Senha padrão implícita (`pwd || "123456"`) vira erro 400. Informe no resumo que bancos já populados com senha antiga precisam de migração/reset.

---

## P4 — Quebrar God File em camadas MVC

**Antes** (`AppManager.js`: cria o banco, define schema, rotas e fluxo de checkout num só lugar):
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE ... INSERT seeds */ }
  setupRoutes(app) { app.post('/api/checkout', (req, res) => { /* 50 linhas: valida, consulta, cobra, grava */ }); }
}
```
**Depois**:
```
src/
├── app.js                       # composition root: createApp(), listen
├── config/settings.js
├── database/connection.js       # abre o banco, run/get/all promisificados, schema + seed
├── models/{user,course,enrollment,payment}Model.js
├── services/{paymentGateway,passwordHasher}.js
├── controllers/{checkout,report,user}Controller.js
├── views/routes.js              # router.post('/api/checkout', checkoutController.checkout)
└── middlewares/errorHandler.js
```
```js
// views/routes.js — apenas mapeamento
router.post('/api/checkout', asyncHandler(checkoutController.checkout));
router.get('/api/admin/financial-report', asyncHandler(reportController.financialReport));
router.delete('/api/users/:id', asyncHandler(userController.remove));
```
```js
// app.js — composition root
function createApp() {
  const app = express();
  app.use(express.json());
  app.use(routes);
  app.use(errorHandler);
  return app;
}
```
Método: (1) para cada função do God File decida a camada de destino; (2) mova **sem alterar a lógica**; (3) substitua a ligação direta por imports/injeção; (4) rode o baseline a cada camada extraída; (5) apague o arquivo original só quando vazio. Em Python/Flask use `create_app()` e `Blueprint`s; mantenha o arquivo de entrada original (`app.py`) como wrapper de 5 linhas para não quebrar `python app.py`.

---

## P5 — Mover regra de negócio do Controller para Model/Service

**Antes** (rota calcula atraso, nome do usuário e categoria, e repete isso em 3 rotas):
```python
@task_bp.route('/tasks')
def get_tasks():
    for t in Task.query.all():
        if t.due_date and t.due_date < datetime.utcnow() and t.status not in ('done', 'cancelled'):
            task_data['overdue'] = True
        ...
        user = User.query.get(t.user_id)
```
**Depois**:
```python
# models/task.py — regra de domínio no model
def is_overdue(self):
    return bool(self.due_date and self.due_date < utc_now() and self.status not in FINISHED_STATUSES)

def to_dict(self, include_relations=False):
    data = {..., 'overdue': self.is_overdue()}
    if include_relations:
        data['user_name'] = self.user.name if self.user else None
        data['category_name'] = self.category.name if self.category else None
    return data

# controllers/task_controller.py — só orquestra
def list_tasks():
    tasks = Task.list_with_relations()
    return jsonify([t.to_dict(include_relations=True) for t in tasks]), 200

# routes/task_routes.py — só roteia
task_bp.add_url_rule('/tasks', view_func=task_controller.list_tasks, methods=['GET'])
```
Regra de bolso: se a função tem `if` sobre regras do domínio, cálculo, ou fala com >1 entidade, ela pertence ao Model/Service. O controller só traduz HTTP ⇄ chamada de domínio.

---

## P6 — Eliminar estado global (DI / escopo de request)

**Antes**:
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```
```js
let globalCache = {}; let totalRevenue = 0;          // mutados de qualquer lugar
```
**Depois** (conexão por request + factory):
```python
# src/database/connection.py
from flask import g, current_app
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# src/app.py
def create_app(settings=Settings):
    app = Flask(__name__)
    app.config.from_object(settings)
    app.teardown_appcontext(close_db)
    ...
```
```js
// dependências recebidas, não criadas
function buildCheckoutController({ userModel, courseModel, paymentGateway }) {
  return { checkout: async (req, res) => { /* usa as dependências injetadas */ } };
}
```
Cache/contadores sem leitor são removidos (ver P15); se forem necessários, vire um serviço instanciado no composition root e injetado.

---

## P7 — Eliminar N+1

**Antes** (1 query de pedidos + 1 por pedido + 1 por item):
```python
for row in cursor.execute("SELECT * FROM pedidos"):
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**Depois** (1 query com JOIN, agrupamento em memória):
```python
rows = db.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    ORDER BY p.id, i.id
""").fetchall()
pedidos = {}
for r in rows:
    pedido = pedidos.setdefault(r["id"], {..., "itens": []})
    if r["produto_id"] is not None:
        pedido["itens"].append({"produto_id": r["produto_id"], "produto_nome": r["produto_nome"] or "Desconhecido", ...})
```
ORM: `Task.query.options(joinedload(Task.user), joinedload(Task.category))`; contagens por grupo: `db.session.query(Task.user_id, func.count()).group_by(Task.user_id)`.
Node: um `SELECT ... JOIN` e `reduce` por chave em vez de `forEach` + query por linha.

---

## P8 — Tratamento de erro centralizado

**Antes** (try/except repetido em todo handler, `str(e)` vaza para o cliente):
```python
def listar_produtos():
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```
**Depois**:
```python
# src/middlewares/error_handler.py
class AppError(Exception):
    status_code = 500
    def __init__(self, message): super().__init__(message); self.message = message
class NotFoundError(AppError):   status_code = 404
class ValidationError(AppError): status_code = 400

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(404)
    def handle_404(_):
        return jsonify({"erro": "Rota não encontrada", "sucesso": False}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("Erro não tratado")           # detalhe só no log
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500

# controller: apenas lança
produto = Produto.get(id) or raise_not_found("Produto não encontrado")
```
```js
// Express: handler com 4 argumentos + wrapper para async
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
function errorHandler(err, req, res, next) {
  const status = err.statusCode || 500;
  if (status === 500) logger.error(err);
  res.status(status).json({ error: status === 500 ? 'Erro interno do servidor' : err.message });
}
```
Elimine `except:` sem classe; capture exceções **específicas** onde há ação a tomar (ex.: `IntegrityError` → 409).

---

## P9 — Validação e serialização únicas (DRY)

**Antes**: validação de produto copiada em `criar_produto` e `atualizar_produto` (e já divergindo); o dict de 8 campos repetido em 3 funções.

**Depois**:
```python
# controllers/produto_controller.py
def _validar_produto(dados):
    if not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    for campo in ("nome", "preco", "estoque"):
        if campo not in dados:
            raise ValidationError(f"{campo.capitalize()} é obrigatório")
    if not isinstance(dados["preco"], (int, float)) or dados["preco"] < 0:
        raise ValidationError("Preço inválido")
    ...
    return dados

# create e update chamam _validar_produto(request.get_json(silent=True))

# models/produto_model.py
def row_to_dict(row):               # serializer único
    return {k: row[k] for k in ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")}
```
Use `request.get_json(silent=True)` e `isinstance` antes de comparar. Em JS valide `typeof`/`Number.isInteger` e retorne 400 antes de tocar o banco. Se o projeto já tem um módulo de helpers/validators não utilizado, **reutilize-o** em vez de criar outro.

---

## P10 — Callbacks → async/await

**Antes**:
```js
this.db.all("SELECT * FROM courses", [], (err, courses) => {
  let pending = courses.length;
  courses.forEach(c => {
    this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrs) => {
      enrs.forEach(enr => this.db.get("SELECT ...", [enr.user_id], (err, user) => { if (--pending === 0) res.json(report); }));
    });
  });
});
```
**Depois**:
```js
// database/connection.js — promisifica uma vez
const run = (sql, params = []) => new Promise((resolve, reject) =>
  db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); }));
const get = (sql, params = []) => new Promise((resolve, reject) => db.get(sql, params, (e, r) => e ? reject(e) : resolve(r)));
const all = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r)));

// controller
async function financialReport(req, res) {
  const rows = await reportModel.revenueByCourse();   // 1 query com JOIN (P7)
  res.json(groupByCourse(rows));
}
```
Regras: nenhum contador manual de pendências; erros propagam via `throw` até o `errorHandler` (P8); use `Promise.all` apenas para operações independentes.

---

## P11 — Trocar APIs deprecated

| Antes | Depois |
|---|---|
| `datetime.utcnow()` | `datetime.now(timezone.utc)`; se o banco guarda datetimes *naive*, centralize em `utc_now()` que remove `tzinfo` para manter as comparações |
| `User.query.get(id)` | `db.session.get(User, id)` |
| `new Buffer(x)` | `Buffer.from(x)` |
| `hashlib.md5` p/ senha | `generate_password_hash` (P3) |
| `except:` | `except (ValueError, TypeError):` |
| `body-parser` / `var` | `express.json()` / `const`/`let` |

```python
# utils/helpers.py
from datetime import datetime, timezone
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)     # mesmo valor de utcnow(), sem warning

# models: created_at = db.Column(db.DateTime, default=utc_now)
# controllers: user = db.session.get(User, user_id)
```
Confirme a versão instalada antes de trocar (`pip show sqlalchemy`) e rode o app depois — a troca não pode introduzir `DeprecationWarning` novo.

---

## P12 — Constantes e nomes claros

**Antes**:
```python
if faturamento > 10000: desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
if novo_status not in ["pendente", "aprovado", "enviado", "entregue", "cancelado"]: ...
```
```js
let u = req.body.usr, e = req.body.eml, cid = req.body.c_id, cc = req.body.card;
```
**Depois**:
```python
# config/constants.py
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))   # (faturamento mínimo, percentual)
STATUS_PEDIDO = ("pendente", "aprovado", "enviado", "entregue", "cancelado")

def calcular_desconto(faturamento):
    for minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * percentual
    return 0
```
```js
// o contrato HTTP mantém usr/eml/pwd/c_id/card; internamente nomes claros
const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;
```
Nunca renomeie campos do contrato público; renomeie só na fronteira.

---

## P13 — Proteger endpoints perigosos e dados sensíveis

**Antes**:
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"])           # SQL arbitrário, sem auth
...
return jsonify({"status": "ok", "secret_key": "...", "debug": True, "db_path": "loja.db"})
return {'password': self.password, ...}                  # hash na resposta
```
**Depois**:
```python
# middlewares/auth.py
def require_admin_token(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        if not expected or not hmac.compare_digest(request.headers.get("X-Admin-Token", ""), expected):
            raise ForbiddenError("Acesso negado")        # desabilitado se ADMIN_TOKEN não estiver configurado
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.post("/admin/reset-db")
@require_admin_token
def reset_db(): ...
```
- **Utilitário perigoso** (executa SQL/código arbitrário, reseta/apaga dados em massa): desabilitado por padrão — só responde com token configurado; SQL arbitrário restrito a `SELECT` em conexão somente-leitura (ou removido).
- **Escalonamento de privilégio (mass assignment)** — **obrigatório, nunca deixar como risco residual**: campos de privilégio (`role`, `is_admin`, `permissions`, `active`) enviados em cadastro/atualização **não são confiáveis**. Em cadastro anônimo, ignore o valor enviado e grave o papel padrão; só honre o campo se o chamador estiver autenticado **e** for admin. Alterar papel/status de outro usuário exige admin autenticado (403 caso contrário).
  ```python
  # Antes: qualquer cliente anônimo se cadastra como admin
  role = data.get('role', 'user')

  # Depois
  role = data.get('role', DEFAULT_ROLE) if is_admin_request() else DEFAULT_ROLE   # ignora o role do anônimo
  ```
- **Autenticação que existe mas não é verificada** (login emite token e nenhuma rota o valida): implemente a **verificação** do token (assinatura + expiração) e um decorator `require_admin` (header `Authorization: Bearer <token>`; 401 sem token/token inválido, 403 se não for admin), e aplique-o às operações destrutivas/administrativas (remover usuário, mudar role, endpoints `/admin/*`).
  ```python
  def require_admin(view):
      @wraps(view)
      def wrapper(*a, **kw):
          user = current_user()                 # verifica assinatura/expiração do token
          if user is None: raise UnauthorizedError('Autenticação necessária')
          if user.role != 'admin': raise ForbiddenError('Acesso restrito a administradores')
          return view(*a, **kw)
      return wrapper
  ```
- **Rota de negócio de leitura sem autenticação** (ex.: relatório financeiro): se não existir sistema de autenticação, exigir login em todas as rotas mudaria o contrato público; aplique proteção **opt-in** (`ADMIN_TOKEN` configurado ⇒ header exigido; senão segue aberta e o boot registra *warning*). Só este caso — leitura sem sistema de auth prévio — pode ser listado como risco residual no resumo da Fase 3. Operações de escrita/privilégio **não** se enquadram aqui.
- Respostas: serializers com *allowlist* de campos — remova `password/senha/hash`, `secret_key`, caminhos, flags de debug.
- Logs: mascare dados sensíveis (`**** **** **** 4444`), nunca registre segredo/chave.
- Se a rota for parte do contrato, ela continua existindo (responde 403 sem token) — registre a mudança no resumo.

---

## P14 — Transações e integridade referencial

**Antes**:
```js
// cria o usuário ANTES de saber se o pagamento passa → usuário órfão se recusado
this.db.run("INSERT INTO users ...", ..., function () { processPaymentAndEnroll(this.lastID); });
...
this.db.run("DELETE FROM users WHERE id = ?", [id], () => res.send("...matrículas e pagamentos ficaram sujos no banco."));
```
**Depois**:
```js
// decisão de negócio primeiro (pagamento), escrita depois, tudo em uma transação
const payment = paymentGateway.charge(cardNumber, course.price);
if (payment.status === 'DENIED') throw new AppError('Pagamento recusado', 400);

await db.transaction(async (tx) => {
  const userId = existing ? existing.id : (await userModel.create(tx, { name, email, passwordHash })).lastID;
  const enrollment = await enrollmentModel.create(tx, userId, courseId);
  await paymentModel.create(tx, enrollment.lastID, course.price, payment.status);
  await auditLogModel.create(tx, `Checkout curso ${courseId} por ${userId}`);
});
```
```js
// remoção em cascata, atômica
await db.transaction(async (tx) => {
  await tx.run('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)', [id]);
  await tx.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
  await tx.run('DELETE FROM users WHERE id = ?', [id]);
});
```
```python
try:
    ...                       # várias escritas
    db.commit()
except Exception:
    db.rollback()
    raise
```
Conexão SQLite única compartilhada: serialize as transações (fila/mutex de Promise) para que `BEGIN/COMMIT` de requests concorrentes não se misturem. Alternativa: `ON DELETE CASCADE` + `PRAGMA foreign_keys = ON`.

---

## P15 — Remover código morto e usar logging adequado

**Antes**:
```python
import os, sys, json, datetime            # nada disso é usado
print("ENVIANDO EMAIL: Pedido " + str(id))
```
```js
let totalRevenue = 0;                      // exportado, nunca lido
function logAndCache(key, data) { globalCache[key] = data; }   // cache escrito, nunca lido
```
**Depois**:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Notificação de pedido %s enviada ao usuário %s", pedido_id, usuario_id)
```
```js
// utils/logger.js
const logger = { info: (...a) => console.log('[INFO]', ...a), error: (...a) => console.error('[ERROR]', ...a) };
```
Método: para cada import e símbolo exportado, conte referências (`grep -rn nome`); 0 usos → remover. Antes de apagar um helper "não usado", verifique se não é a versão **correta** que deveria substituir lógica duplicada (nesse caso, reutilize-o — P9). Integrações simuladas (e-mail/SMS/push por `print`) viram um `NotificationService` injetável cujo comportamento atual (log) é mantido.
