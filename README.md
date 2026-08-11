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
│   │       ├── datasource/api/   # Fuentes externas (DolarAPI, Binance, histórico BCV)
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
│   ├── fetch_rates.py           # Fetch periódico con APScheduler
│   └── backfill_bcv_history.py  # Backfill manual del histórico BCV (2023+)
├── .github/
│   └── workflows/
│       ├── fetch-rates.yml # Cron vía GitHub Actions
│       └── fetch_health.yml# Keep-alive cada 10 min vía GitHub Actions
├── tests/
│   ├── conftest.py
│   ├── test_cron_fetch_rates.py
│   ├── test_rates_brecha_variaciones_historico.py
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
| `GET` | `/rates/brecha` | Brecha cambiaria de paralelo/EUR/USDT vs USD oficial |
| `GET` | `/rates/variaciones` | Variación % a 24h y 7 días de cada tasa |
| `GET` | `/rates/historico/bcv` | Histórico del USD oficial (BCV) — filtro `desde`/`hasta` |
| `GET` | `/rates/ping` | Healthcheck simple |
| `GET` | `/health` | Healthcheck con DB |
| `GET` | `/` | Root |

---

## Brecha cambiaria, variaciones e histórico BCV

### `GET /rates/brecha` — Brecha cambiaria

Diferencia porcentual entre el **USD oficial (BCV)** y las demás tasas:

```
brecha = ((tasa_x - usd_oficial) / usd_oficial) * 100
```

para `x ∈ {usd_paralelo, eur, usdt}`. Si alguna tasa no tiene registro disponible su valor es `null`.

```json
{
  "usd_oficial_price": 74.65,
  "usd_oficial_fetched_at": "2026-07-29T04:00:00Z",
  "brechas": {
    "usd_paralelo": { "rate": 80.85, "brecha": 8.30 },
    "eur": { "rate": 80.50, "brecha": 7.83 },
    "usdt": { "rate": 75.20, "brecha": 0.73 }
  }
}
```

### `GET /rates/variaciones` — Variación diaria y semanal

Cambio porcentual de cada tasa contra la más reciente a **24h** (`variacion_24h`) y a **7 días** (`variacion_7d`):

```
variacion = ((tasa_actual - tasa_base) / tasa_base) * 100
```

La tasa base es el último registro con `fetched_at <= (ahora - 24h/7d)`: si no existe uno exacto se usa el más reciente anterior al corte, lo que maneja correctamente findes de semana y el dedup del cron. Si no hay línea base el campo es `null`.

```json
{
  "rates": {
    "usd_oficial": { "price": 74.65, "variacion_24h": 0.12, "variacion_7d": -1.30, "fetched_at": "2026-07-29T04:00:00Z" },
    "usd_paralelo": { "price": 80.85, "variacion_24h": 0.55, "variacion_7d": null, "fetched_at": "2026-07-29T04:00:00Z" }
  }
}
```

### `GET /rates/historico/bcv` — Histórico del USD oficial (BCV)

Devuelve el histórico del dólar oficial de la tabla local `exchange_rates` (poblada con el backfill, ver abajo). Parámetros opcionales `desde` y `hasta` en formato `YYYY-MM-DD` (asumidos UTC); sin filtros devuelve todo el rango.

```json
{
  "currency": "USD",
  "rate_type": "oficial",
  "source": "dolar_api",
  "history": [
    { "fecha": "2024-01-02T00:00:00Z", "price": 35.96, "rate_buy": 35.96, "rate_sell": 35.96 }
  ]
}
```

### Backfill del histórico (`cron/backfill_bcv_history.py`)

DolarAPI solo publica histórico desde **2023-01-03**. Para poblar la tabla local por primera vez:

```bash
python cron/backfill_bcv_history.py
```

- Trae todo el histórico de `GET /v1/historicos/dolares/oficial` (~864 registros) e inserta en `exchange_rates` con `fetched_at` a medianoche UTC.
- Es idempotente: **solo inserta fechas que no existen** (dedup por fuente/moneda/tipo + fecha), por lo que puede re-ejecutarse sin duplicar.
- No crea columnas ni tablas nuevas; usa el mismo modelo `ExchangeRate`. Requiere las mismas variables de entorno que el cron (`DATABASE_URL`, `SECRET_KEY_JWT`, `DOLARAPI_BASE_URL`, etc.).
- Es un script manual (una sola ejecución y termina; exit 0 si tuvo éxito, 1 si falló).

> El histórico anterior a 2023 no está disponible en DolarAPI; para 2018-2022 habría que cargar la serie publicada por el BCV por otro medio.

Todas las consultas de estas tres features se calculan al vuelo sobre `exchange_rates` (índice en `fetched_at`), sin nuevos campos de BD y sin afectar el rendimiento de los endpoints existentes.

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
