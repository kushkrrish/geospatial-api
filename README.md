# Geospatial File Measurement API

An asynchronous REST API for uploading KML files and ZIP archives
containing Shapefiles, extracting geographic features, and calculating
polygon areas and line lengths.

**Stack:** FastAPI · Celery · Redis · GeoPandas · Shapely · PyProj ·
PostgreSQL · PostGIS · SQLAlchemy · Alembic

## Features

-   Upload `.kml` files or `.zip` archives containing a Shapefile or
    KML.
-   Store upload metadata and processing status in PostgreSQL.
-   Process files asynchronously with Celery and Redis.
-   Extract feature geometry and arbitrary source attributes.
-   Calculate polygon area in square metres and line length in metres
    using projected coordinates.
-   Store normalized geometries in PostGIS and source attributes in
    PostgreSQL `JSONB`.
-   Query file status and precomputed measurements through REST
    endpoints.
-   Track failures using `FAILED` status and an error message.

## High-level design

```mermaid
flowchart TD
    C[Client / Swagger UI] --> API[FastAPI]
    API --> S[Save uploaded file]
    API --> DB[(PostgreSQL + PostGIS)]
    API --> Q[Redis queue]
    Q --> W[Celery worker]
    W --> G[GeoPandas reads file]
    G --> CRS[PyProj transforms CRS]
    CRS --> M[Shapely calculates measurements]
    M --> DB
    C -->|Check status / results| API
```

## Design decisions — and why

| Decision | Why it makes sense |
|---|---|
| **FastAPI** | Simple API development, request validation, and built-in Swagger documentation. |
| **Celery + Redis** | Geospatial files can take time to parse. Background jobs keep upload requests quick; Redis passes jobs to workers. |
| **PostgreSQL + PostGIS** | Stores file records and feature geometries in a database designed to support spatial data. |
| **JSONB for properties** | Different files can have different attribute columns, so we do not need a database column for every possible attribute. |
| **SQLAlchemy + repositories** | Keeps database queries separate from the business logic and makes the code easier to maintain. |

## Architecture: Layered Application

``` text
app/
├── api/routes/       # HTTP routes
├── controllers/      # Request orchestration
├── services/         # Upload, processing, and measurement logic
├── repositories/     # Database queries
├── models/           # SQLAlchemy/PostGIS models
├── schemas/           # Pydantic request/response schemas
├── db/                # Engine, sessions, Base
├── core/              # Environment-based configuration
├── workers/           # Celery tasks
└── celery_app.py      # Celery configuration
```

**Request path:** Route → Controller → Service → Repository → Database.

The service layer coordinates business logic; repositories encapsulate
database operations; Celery workers run the processing pipeline
separately from API requests.

## Upload and Processing Data Flow

``` mermaid
sequenceDiagram
    participant C as Client
    participant A as FastAPI
    participant S as File Storage
    participant D as PostgreSQL
    participant R as Redis
    participant W as Celery Worker

    C->>A: POST /api/files/ (file)
    A->>S: Save uploaded file
    A->>D: Insert file_info (PENDING)
    A->>R: Enqueue process_geospatial_file(file_id)
    A-->>C: 201 Created + file metadata
    R->>W: Deliver task
    W->>D: Set status PROCESSING
    W->>W: Read, validate, transform, measure
    W->>D: Save features and set COMPLETED
    Note over W,D: On processing failure, record FAILED and error_message
    C->>A: GET /api/files/{file_id}
    A->>D: Read status and metadata
    A-->>C: Current processing status
```

The upload request does not wait for geospatial processing to finish.
Clients can poll the file-info endpoint until the status becomes
`COMPLETED` or `FAILED`.

### File status lifecycle

``` mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> PROCESSING
    PROCESSING --> COMPLETED
    PROCESSING --> FAILED
```

## Measurement and CRS Flow

``` mermaid
flowchart TD
    Input[Uploaded KML / ZIP Shapefile] --> Read[GeoPandas reads features]
    Read --> Source[Inspect source CRS]
    Source --> Missing{CRS known?}
    Missing -->|No, KML with standard WGS84 coordinates| Assign[Assign EPSG:4326]
    Missing -->|No, other dataset| Fail[Fail with missing CRS]
    Missing -->|Yes| Normalize[Transform geometry to EPSG:4326]
    Assign --> Normalize
    Normalize --> Project[Transform to suitable projected CRS]
    Project --> Type{Geometry type}
    Type -->|Polygon / MultiPolygon| Area[Calculate area in m²]
    Type -->|LineString / MultiLineString| Length[Calculate length in m]
    Type -->|Point / MultiPoint| None[No area or length]
    Area --> Persist[Persist geometry, properties, and measurements]
    Length --> Persist
    None --> Persist
    Persist --> Done[Set status COMPLETED]
```

### Measurement rules

  Geometry                          Result           Unit
  --------------------------------- ---------------- --------
  `Polygon`, `MultiPolygon`         Area             m²
  `LineString`, `MultiLineString`   Length           m
  `Point`, `MultiPoint`             No measurement   `null`

**CRS matters:** EPSG:4326 uses longitude/latitude degrees, not metres.
Area and length are therefore calculated after transforming geometries
to a suitable projected CRS. The original source CRS is retained as file
metadata; geometries are normalized to EPSG:4326 for storage.

> UTM is appropriate for many local/regional datasets, but it is not
> universally suitable for every dataset. Very large or multi-region
> datasets may need a different projection strategy.

## Database Model

``` mermaid
erDiagram
    FILE_INFO ||--o{ FEATURES : contains
    FILE_INFO {
        int id PK
        string filename
        string file_path
        string status
        string source_crs
        int feature_count
        string error_message
        datetime created_at
        datetime updated_at
    }
    FEATURES {
        int id PK
        int file_id FK
        int feature_index
        string geometry_type
        geometry geometry
        jsonb properties
        float area
        float length
    }
```

-   `file_info` stores upload metadata and processing state.
-   `features` stores one row per supported, non-empty geometry.
-   `properties` is `JSONB` because input files can have different
    attribute fields.
-   Geometry is stored in PostGIS with SRID 4326.
-   Area and length are precomputed, so measurement requests do not need
    to parse the original file again.

## API Reference

The current route prefix in the application is `/api/files`. If you
configure a versioned prefix, use `/api/v1/files` consistently in the
router and this documentation.

### 1. Upload a file

`POST /api/files/`

**Content type:** `multipart/form-data`

**Form field:** `file`

Supported extensions: `.kml`, `.zip` containing a Shapefile or KML.

**Example response --- `201 Created`:**

``` json
{
  "id": 1,
  "filename": "survey_site.kml",
  "status": "PENDING",
  "source_crs": null,
  "feature_count": null,
  "error_message": null,
  "created_at": "2026-10-09T12:00:00",
  "updated_at": "2026-10-09T12:00:00"
}
```

Processing is asynchronous; the status may change shortly after this
response.

### 2. Get file status

`GET /api/files/{file_id}`

Returns file metadata and processing status.

**Example response --- `200 OK`:**

``` json
{
  "id": 1,
  "filename": "survey_site.kml",
  "status": "COMPLETED",
  "source_crs": "EPSG:4326",
  "feature_count": 3,
  "error_message": null,
  "created_at": "2026-10-09T12:00:00",
  "updated_at": "2026-10-09T12:00:02"
}
```

### 3. Get measurements

`GET /api/files/{file_id}/measurements/`

Returns the stored measurements for a file. While processing is pending,
the response may contain no features yet. A failed file returns a
processing error.

**Example response --- `200 OK`:**

``` json
{
  "file_id": 1,
  "status": "COMPLETED",
  "feature_count": 2,
  "measurements": [
    {
      "feature_id": 101,
      "feature_index": 0,
      "geometry_type": "Polygon",
      "area": 12016.97,
      "area_unit": "m²",
      "length": null,
      "length_unit": null,
      "properties": {
        "Name": "Agricultural Zone A",
        "crop_type": "Wheat"
      }
    },
    {
      "feature_id": 102,
      "feature_index": 1,
      "geometry_type": "LineString",
      "area": null,
      "area_unit": null,
      "length": 875.96,
      "length_unit": "m",
      "properties": {
        "Name": "Main Access Road"
      }
    }
  ]
}
```

**Common status codes:** `201` upload accepted, `200` successful query,
`404` unknown file ID, `422` processing failed (for measurements). Exact
error responses depend on the route/service implementation.

## Local Setup

### Prerequisites

-   Python 3.11+
-   Docker Desktop with Docker Compose
-   Git

### 1. Clone the repository

``` bash
git clone https://github.com/kushkrrish/geospatial-api.git
cd geospatial-api
```

### 2. Create and activate a virtual environment

**Windows PowerShell**

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS**

``` bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

If you have not generated `requirements.txt` yet, install the main
packages:

``` bash
pip install fastapi uvicorn sqlalchemy "psycopg[binary]" alembic \
  pydantic-settings python-multipart "celery[redis]" \
  geopandas shapely pyproj pyogrio fiona geoalchemy2
pip freeze > requirements.txt
```

### 4. Configure environment variables

Create `.env` in the project root. Match these values to your
`docker-compose.yml`:

``` dotenv
APP_NAME="Geospatial File Measurement API"
APP_VERSION="1.0.0"
DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/geospatial_db"
REDIS_URL="redis://localhost:6379/0"
UPLOAD_DIR="storage/uploads"
```


### 5. Start PostgreSQL/PostGIS and Redis

``` bash
docker compose up -d
docker compose ps
```

The Compose configuration should expose PostgreSQL on `localhost:5432`
and Redis on `localhost:6379`.

Confirm PostGIS is enabled. If necessary, connect to `geospatial_db` and
run:

``` sql
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT PostGIS_Version();
```

### 6. Apply database migrations

``` bash
alembic upgrade head
```

If this is a fresh database, ensure the repository contains the
migration files in `alembic/versions/`.

### 7. Start the Celery worker

Open a separate terminal, activate the same virtual environment, and
run:

**Windows**

``` powershell
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo
```

**Linux/macOS**

``` bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

Keep this terminal running so queued tasks can be processed.

### 8. Start FastAPI

Open another terminal and run:

``` bash
uvicorn app.main:app --reload
```

### 9. Open Swagger UI

Visit:

-   **Swagger UI:** http://127.0.0.1:8000/docs
-   **ReDoc:** http://127.0.0.1:8000/redoc
-   **Health/root endpoint:** http://127.0.0.1:8000/

In Swagger UI, expand `POST /api/files/`, select **Try it out**, choose
a `.kml` or `.zip` file, and execute. Then poll
`GET /api/files/{file_id}` and call the measurements endpoint after
processing completes.

## Testing Checklist

1.  Upload a valid KML containing points, lines, or polygons.
2.  Upload a ZIP with a complete Shapefile set (`.shp`, `.shx`, `.dbf`,
    and, when available, `.prj`).
3.  Confirm status transitions from `PENDING` to `PROCESSING` and then
    `COMPLETED`.
4.  Verify polygon area is in m² and line length is in metres.
5.  Verify point measurements are `null`.
6.  Try an unsupported extension, corrupt ZIP, missing Shapefile
    components, and a Shapefile with missing CRS.
7.  Confirm unknown file IDs return `404` and processing failures expose
    a useful error without returning a traceback.

## Design Notes 

-   **Asynchronous processing:** keeps expensive work outside the upload
    request. Redis/Celery are separate processes and must be running.
-   **Atomic persistence:** persist feature rows and mark the file
    completed in one transaction. On failure, roll back feature writes
    and record `FAILED` separately.
-   **Archive safety:** enforce upload size limits, validate ZIP
    contents, guard against path traversal and decompression bombs, and
    avoid trusting client-provided filenames for storage paths.
-   **CRS assumptions:** do not silently assume a missing CRS for
    Shapefiles. KML is normally WGS84, but validate data and driver
    behavior.


## Learnings and Future Scope

### Key learnings

-   Transform geographic coordinates before calculating metric
    measurements.
-   Keep upload requests fast by dispatching long-running work to
    Celery.
-   Use PostGIS for spatial data, `JSONB` for flexible attributes, and
    migrations for schema evolution.
-   Separate HTTP handling, business logic, database operations, and
    background processing.

### Possible future improvements

1.  Store uploaded files in S3/GCS instead of local disk.
2.  Add SSE/WebSocket notifications instead of status polling.
3.  Add spatial filters, spatial indexes, and geometry validation
    policies.
4.  Add richer CRS selection for global and multi-zone datasets.

