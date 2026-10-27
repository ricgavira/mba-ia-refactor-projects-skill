# Guidelines de Arquitetura — MVC alvo

Estas regras definem o **estado final** da Fase 3. São independentes de linguagem; a seção 5 traduz cada camada para os frameworks mais comuns.

## 1. Camadas e responsabilidades

```
Request ─► View/Routes ─► Controller ─► (Service) ─► Model ─► Banco
                                  │
Response ◄───────────────────────┘          Config / Middlewares transversais
```

| Camada | Responsabilidade | Pode importar | **Não** pode |
|---|---|---|---|
| **Config** | Ler variáveis de ambiente, definir defaults seguros e constantes. Único lugar com valores de configuração. | stdlib | Conter segredos reais; importar models/controllers |
| **Models** | Estrutura dos dados, acesso ao banco (queries parametrizadas/ORM), regras de domínio que dependem só do dado (ex.: `is_overdue`, cálculo de total, transições de estado válidas). Retorna dados puros (objetos/dicts), nunca respostas HTTP. | Config, banco | Importar `request/response`, framework web, controllers; devolver `jsonify` |
| **Views / Routes** | Mapear **método + URL → função do controller**. Registrar blueprints/routers. Nada além disso. | Controllers | Conter validação, regra de negócio ou acesso a dados |
| **Controllers** | Orquestrar o fluxo da requisição: ler/validar entrada, chamar models/services, escolher status HTTP e montar o corpo da resposta. Lançar erros de domínio tipados. | Models, Services, Config | Montar SQL, instanciar conexão de banco, conter regra de negócio pesada |
| **Services** *(opcional)* | Regras que cruzam várias entidades ou falam com o mundo externo (pagamento, e-mail, notificações). Uma classe/módulo por integração, recebida por injeção. | Models, Config | Conhecer HTTP |
| **Middlewares / Error handling** | Tratamento centralizado de erros (404, 500, erros de domínio), CORS, logging de request. | Config | Regra de negócio |
| **Entry point (composition root)** | Criar a aplicação, carregar config, inicializar banco, instanciar e **injetar** dependências, registrar rotas e middlewares, subir o servidor. | Tudo | Conter regra, SQL ou handlers |

### Regra de dependência
`Routes → Controllers → Services → Models → Config`. **Nunca no sentido contrário.** Se um model precisar de algo do controller, a responsabilidade está no lugar errado.

## 2. Estrutura de diretórios alvo

Escolha conforme a situação encontrada na Fase 1:

**A) Projeto sem camadas (monolito/God File)** — crie `src/`:

```
<projeto>/
├── <entry point original>      # mantém o comando de execução do README (python app.py / npm start)
└── src/
    ├── config/        settings.<ext>          # env + constantes
    ├── database/      connection.<ext>        # criação da conexão, schema, seed
    ├── models/        <entidade>_model.<ext>  # um por entidade/agregado
    ├── services/      <integração>_service    # opcional
    ├── controllers/   <entidade>_controller   # um por recurso
    ├── views/         routes.<ext>            # (ou routes/<recurso>_routes) mapeamento URL → controller
    ├── middlewares/   error_handler.<ext>
    └── app.<ext>      # composition root / factory (create_app)
```

**B) Projeto que já tem camadas na raiz (`models/`, `routes/`, `services/`, `utils/`)** — **evolua no lugar**, não recrie. Adicione apenas o que falta:

```
<projeto>/
├── app.py                 # entry point enxuto
├── config/                # NOVO: settings (env) + constants
├── models/                # dados + regras de domínio (sem HTTP)
├── controllers/           # NOVO: fluxo/validação de cada recurso, extraído de routes/
├── routes/                # só mapeamento URL → controller
├── services/              # integrações (injetadas)
├── middlewares/           # NOVO: error handlers
└── utils/                 # helpers puros e realmente usados
```

Em ambos os casos, **o comando de execução e as URLs públicas não mudam**.

## 3. Regras transversais (checklist de qualidade)

1. **Configuração**: nenhum segredo, porta, caminho de banco, flag de debug ou lista de valores válidos no código de negócio. `Config` lê `ENV` com defaults **seguros** (debug desligado, host local, segredo vazio → falha ou valor gerado).
2. **Models** abstraem o dado: nenhuma query fora de `models/` (ou de `database/` para criação do schema).
3. **Routes** só roteiam: 1 linha por rota.
4. **Controllers** são finos: validar → chamar model/service → responder. Validação compartilhada vive em funções reutilizadas por create e update.
5. **Erros centralizados**: controllers/models lançam exceções de domínio (`NotFoundError`, `ValidationError`, `ConflictError`, ...); **um** handler converte em resposta HTTP padronizada. Exceções inesperadas → 500 genérico (a mensagem real vai para o log, **nunca** para o cliente).
6. **Sem estado global mutável**: conexão por request (ou pool) e dependências injetadas pelo composition root.
7. **Segurança**: queries parametrizadas; senhas com hash adequado; respostas sem campos sensíveis; endpoints administrativos protegidos ou removidos.
8. **Logging** com o logger da plataforma (`logging`, `console` encapsulado em `logger`), nunca segredos.
9. **Contrato público preservado**: mesmas rotas, métodos, status codes de sucesso e formato dos payloads. Mudanças deliberadas (remover `senha` da resposta, 404 em vez de 200 falso) são listadas no resumo final da Fase 3.
10. **Entry point claro**: um arquivo, um comando, `create_app()`/`createApp()` para facilitar teste.

## 4. Convenções de nomenclatura

- Arquivos por camada: `<recurso>_model`, `<recurso>_controller`, `<recurso>_routes` (snake_case em Python; camelCase em JS: `userModel.js`, `userController.js`, `userRoutes.js`).
- Funções de controller com verbo do caso de uso (`list_products`, `create_order`). Respeite o idioma do domínio já usado no projeto (se rotas são `/produtos`, mantenha termos de domínio em português nos models).
- Constantes em `UPPER_SNAKE_CASE`.

## 5. Tradução para frameworks

| Conceito | Flask | Express | Django | NestJS | Spring Boot |
|---|---|---|---|---|---|
| Routes/View | `Blueprint` + `add_url_rule` | `express.Router()` | `urls.py` | `@Controller` rotas | `@RequestMapping` |
| Controller | funções em `controllers/` | funções/classe em `controllers/` | `views.py` (fino) | métodos do `@Controller` | `@RestController` |
| Service | módulo `services/` | `services/` | `services.py` | `@Injectable` | `@Service` |
| Model | classe `db.Model` ou módulo de queries | módulo com queries / ORM model | `models.py` | entity + repository | `@Entity` + `Repository` |
| Erro central | `@app.errorhandler` | middleware `(err, req, res, next)` | middleware / `handler404` | `ExceptionFilter` | `@ControllerAdvice` |
| Composition root | `create_app()` | `createApp()` | `settings.py`/`wsgi` | `AppModule` | `@SpringBootApplication` |

Se o framework já impõe uma convenção (Django `views.py`, Nest modules), **siga a convenção do framework** mapeando as responsabilidades acima — o objetivo é a separação de responsabilidades, não os nomes literais das pastas.

## 6. Quando NÃO refatorar

- Não introduza dependências novas pesadas sem necessidade (prefira stdlib/framework: `werkzeug.security`, `crypto.scrypt`).
- Não troque de ORM/banco/framework.
- Não reescreva regras de negócio: **mova**, não reinterprete. Bugs de regra encontrados são reportados; só corrija os que são segurança ou integridade.
