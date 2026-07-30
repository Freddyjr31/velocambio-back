# AGENTS.md — Contexto para asistentes IA

## Proyecto

VeloCambio backend — API REST para consulta y almacenamiento histórico de tasas de cambio en Venezuela. Obtiene cotizaciones de DolarAPI (USD oficial, USD paralelo, EUR oficial) y Binance P2P (USDT/VES), las almacena en PostgreSQL y las expone vía endpoints.

## Stack técnico

- **Python 3.12**
- **FastAPI** — framework web
- **SQLAlchemy 2.0** — ORM (declarative)
- **PostgreSQL / SQLite** — base de datos
- **httpx** — cliente HTTP
- **APScheduler** — scheduler para fetch periódico
- **slowapi** — rate limiting
- **python-jose + passlib[bcrypt]** — JWT + hashing
- **Pydantic 2 + pydantic-settings** — validación y configuración
- **Uvicorn** — servidor ASGI
- **pytest** — testing
- **Docker + docker-compose** — contenedor

## Estructura

```
velocambio-back/
├── app/
│   ├── core/               # Configuración, seguridad, DB, middlewares
│   │   ├── config.py       # Settings con pydantic-settings
│   │   ├── database.py     # Engine, session, Base declarativa
│   │   ├── dependencies.py # Dependencias FastAPI (auth)
│   │   ├── logger.py       # Logger structurado
│   │   ├── error_handlers.py
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
│   │       ├── constants.py      # IDs de monedas/fuentes/tipos
│   │       └── dependencies.py   # DI del módulo rates
│   ├── routes/             # Routers adicionales
│   ├── main.py             # Punto de entrada FastAPI
├── cron/
│   └── fetch_rates.py      # Script scheduleado con APScheduler
├── tests/
│   ├── conftest.py         # Fixtures (SQLite in-memory, TestClient)
│   ├── test_cron_fetch_rates.py
│   └── test_placeholder.py
├── .env.example
├── opencode.json
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
├── AGENTS.md
└── README.md
```

## Convenciones del código

- Imports orden: estándar → terceros → locales
- Los archivos terminan con una línea en blanco
- Comentarios con `#?` para secciones, `#*` para notas importantes
- Type hints de Python (PEP 484)
- SQLAlchemy 2.0 style (declarative) para modelos
- Rutas con prefijo `/rates` usando APIRouter
- Schemas Pydantic separados del modelo BD
- Servicios separados de rutas (sin lógica en los endpoints)
- Datasources separados por API externa
- El endpoint `GET /rates/today` usa rolling window de 24h (no fecha calendario)

## Endpoints disponibles

| Método | Ruta | Descripción | Auth | Rate limit |
|--------|------|-------------|------|------------|
| `GET` | `/rates/usd_oficial` | Tasa USD oficial (DolarAPI) | No | 30/min |
| `GET` | `/rates/usd_promedio` | Tasa USD paralelo (DolarAPI) | No | 30/min |
| `GET` | `/rates/eur` | Tasa EUR oficial (DolarAPI) | No | 30/min |
| `GET` | `/rates/usdt` | Tasa USDT P2P (Binance) | No | 30/min |
| `GET` | `/rates/today` | Todas las tasas de las últimas 24h | No | 30/min |
| `GET` | `/rates/ping` | Healthcheck simple | No | 30/min |
| `GET` | `/health` | Healthcheck + DB | No | — |
| `GET` | `/` | Root | No | — |

## Datasources externos

- **DolarAPI** (`https://ve.dolarapi.com/v1`): Tasas oficiales y paralelas
  - Endpoints: `/dolares/oficial`, `/dolares/paralelo`, `/euros/oficial`
  - `fechaActualizacion` formato ISO 8601 con offset o `Z` (UTC)
- **Binance P2P** (`https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search`): Anuncios USDT/VES
  - No incluye fecha, se usa `datetime.now(timezone.utc)`

## Comandos útiles

```bash
# Iniciar servidor de desarrollo
uvicorn app.main:app --reload

# Ejecutar cron de fetch de tasas
python cron/fetch_rates.py

# Tests
pytest -v

# Construir y ejecutar con Docker
docker compose up --build

# Instalar dependencias
pip install -r requirements.txt
```

## Reglas al modificar código

1. **No romper** la estructura de carpetas existente
2. **Seguir el patrón** datasource → servicio → repositorio → ruta
3. **No exponer** secretos ni credenciales
4. **No agregar archivos** que no sean necesarios
5. **Mantener** el tipado y los comentarios existentes
6. **Usar** SQLAlchemy 2.0 style declarative para modelos nuevos
7. **Fechas siempre en UTC** — `datetime.now(timezone.utc)` o `astimezone(timezone.utc)`
