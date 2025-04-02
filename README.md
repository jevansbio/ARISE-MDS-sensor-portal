# ARISE-MDS Sensor Portal
 
This is a shareable version of the ARISE-MDS sensor portal. It is currently a work in progress. This documentation will be updated when the code approaches a release. Please note this branch is very much a WIP, and there may be a risk of breaking changes occasionally.

## Starting the project for the first time
```bash
docker compose -f docker-compose-dev.yml build
```

```bash
docker compose -f docker-compose-dev.yml up
```

### Init database & super user:

```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py migrate


## if you have changes which have not yet been applied. 
# open the database
docker compose -f docker-compose-dev.yml exec sensor_portal_db psql -U postgres
# enter the correct database
\c postgres

DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = current_schema()
        AND tablename != 'spatial_ref_sys'
    )
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;

-- Drop the PostGIS extension
DROP EXTENSION IF EXISTS postgis CASCADE;
-- Then drop all other tables
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema())
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;
-- Recreate PostGIS extension if needed
CREATE EXTENSION postgis;
```

```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py createsuperuser
```



## Testing
```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django pytest
```

## Audio Data Management

The sensor portal uses Google Cloud Storage (GCS) to store and manage audio files. For local development, we provide a fake GCS implementation that works without real GCS credentials.

### Directory Structure

This system expects audio files from the NINA project directory with the following structure:

```
proj_tabmon_NINA/
├── bugg_RPiID-10000000d2b4d01e/
│   ├── audio_files/
│   │   ├── bugg_RPiID-10000000d2b4d01e_20240316_123000_16kHz.wav
│   │   └── ...
└── bugg_RPiID-10000000d642707c/
    ├── audio_files/
    │   ├── bugg_RPiID-10000000d642707c_20240317_083000_16kHz.wav
    │   └── ...
```

### Importing Audio Files with Fake GCS

Initialize the fake GCS environment and import audio files in two steps:

```bash
# Step 1: Initialize fake GCS environment
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py fake_gcs --init

# Step 2: Import audio files (cleans existing data first)
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py direct_audio_import --clean
```

This will:
- Create device-specific buckets in fake GCS
- Copy audio files into these buckets
- Create database records for devices, deployments, and files
- Import all deployment details from config files (location, dates, settings, etc.)
- Link everything together properly

### Resulting Storage Structure

After import, files are organized in device-specific buckets:

```
/file_storage/fake_gcs/
├── audio-files-10000000d642707c/      # Device bucket
│   ├── 2024-06-19T23_51_04.502Z.mp3   # Audio files
│   └── ...
├── audio-files-10000000d2b4d01e/      # Another device bucket
│   ├── 2024-06-14T23_43_06.117Z.mp3
│   └── ...
```

### Data Relationships

```
Device (10000000d642707c)
  │
  └── Deployment (NINA_10000000d642707c-Audio-1)
        │
        └── DataFiles (audio recordings in the device bucket)
```

### Accessing Audio Files

1. **API (recommended)**:
   ```
   GET /api/deployments/{deployment_id}/files/
   ```

2. **Command line**:
   ```bash
   # List files in a device bucket
   docker compose -f docker-compose-dev.yml exec sensor_portal_django \
     python manage.py fake_gcs --list-files audio-files-10000000d642707c
   ```

### Working with Audio Files

```bash
# List all device buckets
docker compose -f docker-compose-dev.yml exec sensor_portal_django \
  python manage.py fake_gcs --list-device-buckets

# Upload a new audio file to a device bucket
docker compose -f docker-compose-dev.yml exec sensor_portal_django \
  python manage.py fake_gcs --upload-file path/to/file.mp3 \
  --bucket audio-files-10000000d642707c --destination file.mp3
```

### File Format Support

The system supports various audio formats:
- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)

### Filename Parsing

For best metadata extraction, audio files should follow this naming convention:
```
bugg_RPiID-DEVICEID_YYYYMMDD_HHMMSS_CONFIG.wav
```

The system will extract:
- Device ID from the filename
- Recording date and time
- Configuration information (e.g., sample rate)

## Data Flow from Backend to Frontend

The ARISE-MDS sensor portal uses a Django REST Framework backend to serve data to a React frontend. Here's how to ensure data flows correctly:

### API Endpoints

The primary way data gets sent from the backend to the frontend is through RESTful API endpoints:

```bash
# List available API endpoints

```

Common endpoints include:
- `/api/datafiles/` - Access audio and sensor data files
- `/api/deployments/` - Access deployment information
- `/api/devices/` - Access device information
- `/api/sites/` - Access site information
- `/api/projects/` - Access project information

### Checking API Responses

To verify data is being sent correctly:

1. Using the Django Admin Interface:
   - Navigate to http://localhost:8080/admin/ 
   - Log in with your superuser credentials
   - Browse to various model pages to confirm data exists

2. Testing API endpoints directly:
   - Visit http://localhost:8080/api/ in your browser
   - Use the browsable API to explore endpoints and verify data

3. Using curl from command line:
   ```bash
   # Example to fetch all devices
   curl -H "Accept: application/json" -H "Content-Type: application/json" http://localhost:8000/api/devices/
   ```

### Debugging Data Flow Issues

If data isn't appearing in the frontend:

1. Check Django logs for errors:
   ```bash
   docker compose -f docker-compose-dev.yml logs sensor_portal_django
   ```

2. Verify the API is returning expected data:
   ```bash
   # Using httpie (if installed)
   http GET http://localhost:8000/api/devices/
   ```

3. Check for CORS issues in browser developer console (F12)

4. Ensure frontend API calls include proper authentication if required:
   ```javascript
   // Example React fetch with authentication
   fetch('/api/devices/', {
     headers: {
       'Authorization': `Token ${authToken}`,
       'Content-Type': 'application/json'
     }
   })
   .then(response => response.json())
   .then(data => console.log(data));
   ```

### Creating Custom API Endpoints

If you need to create new endpoints to expose data:

1. Add a serializer in `sensor_portal/serializers.py`
2. Add a viewset in `sensor_portal/views.py`
3. Register the viewset in `sensor_portal/urls.py`
4. Restart the Django container:
   ```bash
   docker compose -f docker-compose-dev.yml restart sensor_portal_django
   ```
