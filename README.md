# VeloCambio Backend

API REST para consulta y almacenamiento histórico de tasas de cambio en Venezuela.

Obtiene cotizaciones de [dolarapi.com](https://ve.dolarapi.com) (dólar oficial, dólar paralelo, euro oficial) y **Binance P2P** (USDT/VES), las almacena en PostgreSQL y las expone a través de endpoints públicos.

---

## Stack

| Capa | Tecnología |
|---|---|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (declarative) |
| Base de datos | PostgreSQL 16 / SQLite (dev) |
| Async HTTP | httpx 0.28 |
| Scheduler | APScheduler 3.10 |
| Autenticación | JWT (python-jose + passlib/bcrypt) |
| Validación | Pydantic 2 + pydantic-settings |
| Servidor ASGI | Uvicorn 0.34 |
| Testing | pytest + httpx |
| Contenedor | Docker + docker-compose |

---

## Estructura

```
velocambio-back/
├── app/
│   ├── core/               # Configuración, seguridad, DB, middlewares
│   │   ├── config.py       # Settings con pydantic-settings
│   │   ├── database.py     # Engine, session, Base declarativa
│   │   ├── dependencies.py # Dependencias FastAPI (auth)
│   │   ├── error_handlers.py
│   │   ├── logger.py
│   │   ├── middleware.py   # CORS + LogMiddleware
│   │   └── security.py     # JWT + bcrypt
│   ├── features/           # Módulos por funcionalidad
│   │   └── rates/          # Tasas de cambio
│   │       ├── datasource/api/   # Fuentes externas (DolarAPI, Binance)
│   │       ├── models/           # Modelo ExchangeRate
│   │       ├── repository/       # Consultas a DB
│   │       ├── routes/           # Endpoints /rates
│   │       ├── schemas/          # Schemas Pydantic
│   │       ├── services/         # Lógica de negocio
│   │       ├── constants.py
│   │       └── dependencies.py
│   ├── routes/             # Routers adicionales (health)
│   ├── main.py             # Punto de entrada FastAPI
├── cron/
│   └── fetch_rates.py      # Fetch periódico con APScheduler
├── .github/
│   └── workflows/
│       └── fetch-rates.yml # Cron vía GitHub Actions
├── tests/
│   ├── conftest.py
│   ├── test_cron_fetch_rates.py
│   └── test_placeholder.py
├── .env.example
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/rates/usd_oficial` | Tasa USD oficial (DolarAPI) |
| `GET` | `/rates/usd_promedio` | Tasa USD paralelo (DolarAPI) |
| `GET` | `/rates/eur` | Tasa EUR oficial (DolarAPI) |
| `GET` | `/rates/usdt` | Tasa USDT P2P (Binance) |
| `GET` | `/rates/today` | Todas las tasas (últimas 24h) |
| `GET` | `/rates/ping` | Healthcheck simple |
| `GET` | `/health` | Healthcheck con DB |
| `GET` | `/` | Root |

---

## Base de datos — Modelo

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│ source_types │     │  exchange_rates  │     │  rate_types  │
├──────────────┤     ├──────────────────┤     ├──────────────┤
│ id (PK)      │────→│ source_type_id   │     │ id (PK)      │
│ code         │     │ currency_from_id │     │ code         │
│ name         │     │ currency_to_id   │     │ name         │
│ is_active    │     │ rate_type_id     │←────│              │
└──────────────┘     │ price            │     └──────────────┘
                     │ rate_buy         │
┌──────────────┐     │ rate_sell        │
│ currency_codes│    │ fetched_at       │
├──────────────┤     └──────────────────┘
│ id (PK)      │←────│ currency_from_id
│ code         │     └──────────────────┘
│ name         │←────│ currency_to_id
│ symbol       │
└──────────────┘
```

Las tablas `source_types`, `currency_codes` y `rate_types` se pueblan automáticamente al primer inicio (seed).

---

## Inicio rápido

### Con venv (desarrollo local)

```bash
git clone <repo-url>
cd velocambio-back

python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

uvicorn app.main:app --reload
```

### Con Docker

```bash
docker compose up --build
```

La API estará disponible en `http://localhost:9000`.

Documentación interactiva en `http://localhost:9000/docs`.

### Cron de fetch

```bash
# Scheduler local (ventana 8am-2pm hora Venezuela, cada 30 min)
python cron/fetch_rates.py

# Un solo fetch y terminar (GitHub Actions / cron externo)
python cron/fetch_rates.py --once
```

Solo inserta un registro cuando la tasa **cambió** respecto al último valor de esa fuente/moneda/tipo (dedup). También se puede ejecutar automáticamente vía GitHub Actions (`.github/workflows/fetch-rates.yml`), el cual corre `--once` en la ventana 9am-2pm VET.

> Para GitHub Actions: configurar los secrets `DATABASE_URL`, `SECRET_KEY_JWT`, `DOLARAPI_BASE_URL` y `BINANCE_P2P_BASE_URL` en Settings → Secrets and variables → Actions.

---

## Tests

```bash
.venv\Scripts\activate
pytest -v
```

---

## Variables de entorno (`.env`)

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/velocambio
DATABASE_TYPE=postgresql
DATABASE_ECHO=False

SECRET_KEY_JWT=<tu-secreto>
ALGORITHIM_HASH_JWT=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=90

FETCH_INTERVAL_MINUTES=10
DOLARAPI_BASE_URL=https://ve.dolarapi.com/v1
BINANCE_P2P_BASE_URL=https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search
HTTP_TIMEOUT_SECONDS=10
HTTP_MAX_RETRIES=3
```
