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
# Step 1: Create a new migration file
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py makemigrations data_models

# Step 2: Apply the migration
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py migrate
```

```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py createsuperuser
```

## Populating with dummy data
```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django bash
```

```bash
python manage.py shell
```

```py
from data_models import factories

factories.DeploymentFactory()
```

## Testing
```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django pytest
```

## NINA Audio Files Import

The sensor portal supports importing audio files from the NINA project directory. This functionality allows you to integrate existing audio recordings with the portal's database structure.

### Directory Structure

The audio files should be organized in the following structure:

```
/Users/noahsyrdal/ARISE-MDS-sensor-portal-Pam/proj_tabmon_NINA/
├── bugg_RPiID-10000000d2b4d01e/
│   ├── audio_files/
│   │   ├── bugg_RPiID-10000000d2b4d01e_20240316_123000_16kHz.wav
│   │   └── ...
└── bugg_RPiID-10000000d642707c/
    ├── audio_files/
    │   ├── bugg_RPiID-10000000d642707c_20240317_083000_16kHz.wav
    │   └── ...
```

### Importing Audio Files

There are two ways to import the audio files:

#### 1. Using the Migration

The migration `0020_load_initial_audio_data.py` will automatically import the audio files when you run:

```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py migrate
```

This will create:
- Data types
- Site: "NINA Field Site"
- Device models: "AudioMoth"
- A project: "TABMON_NINA"
- Devices for each device folder
- Deployments for each device
- Data file records for each audio file

#### 2. Using the Management Command

For more control or to refresh the data, use the `import_audio_files` management command:

```bash
# Basic usage - import all files
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py import_audio_files

# Clean existing data before importing
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py import_audio_files --clean

# Specify a different directory
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py import_audio_files --base-dir=/path/to/audio/files

# Specify a different project ID
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py import_audio_files --project-id=MY_PROJECT

# Dry run (doesn't make actual changes)
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py import_audio_files --dry-run
```

### Audio File Information

The system will extract the following information from each audio file:
- File name and size
- Recording date/time (parsed from the filename if possible)
- Configuration (parsed from the filename if possible)
- Sample rate (parsed from the filename if possible)
- Estimated file length

### Accessing Audio Files in the API

The audio files will be available through the standard API endpoints:

- `/api/datafiles/` - List all audio files
- `/api/deployments/` - List deployments with their associated devices
- `/api/devices/` - List devices

### File Naming Convention

For best results, audio files should follow this naming convention:

```
bugg_RPiID-DEVICEID_YYYYMMDD_HHMMSS_CONFIG.wav
```

Example:
```
bugg_RPiID-10000000d2b4d01e_20240316_123000_16kHz.wav
```

This allows the system to extract:
- Device ID: 10000000d2b4d01e
- Recording date: 2024-03-16
- Recording time: 12:30:00
- Configuration: 16kHz (sample rate will be extracted as 16000 Hz)

## Data Flow from Backend to Frontend

The ARISE-MDS sensor portal uses a Django REST Framework backend to serve data to a React frontend. Here's how to ensure data flows correctly:

### API Endpoints

The primary way data gets sent from the backend to the frontend is through RESTful API endpoints:

```bash
# List available API endpoints
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py show_urls
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
   - Navigate to http://localhost:8000/admin/ 
   - Log in with your superuser credentials
   - Browse to various model pages to confirm data exists

2. Testing API endpoints directly:
   - Visit http://localhost:8000/api/ in your browser
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

## Using Fake Google Cloud Storage for Local Development

The sensor portal can use a fake Google Cloud Storage implementation for local development. This allows you to test GCS-dependent features without needing actual GCS credentials or connectivity.

### Setting Up Fake GCS

Initialize the fake GCS environment:

```bash
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py fake_gcs --init
```

This will create a directory structure in your `file_storage` folder that mimics GCS buckets and objects.

### Bucket Organization

The system uses a device-specific bucket organization strategy:

1. Each device has its own bucket (e.g., `audio-files-10000000d642707c`)
2. Audio files are stored directly in these device buckets without additional subdirectory structure
3. This makes it easy to access all files for a specific device

### Working with Fake GCS

You can interact with the fake GCS using the management command:

```bash
# List all buckets
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py fake_gcs --list-buckets

# List device-specific buckets
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py fake_gcs --list-device-buckets

# List device buckets with a specific prefix
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py fake_gcs --list-device-buckets --base-bucket audio-files

# Create a new bucket
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py fake_gcs --create-bucket my-bucket

# List files in a device bucket
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py fake_gcs --list-files audio-files-10000000d642707c

# Upload a file to a device bucket
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py fake_gcs --upload-file path/to/file.mp3 --bucket audio-files-10000000d642707c --destination file.mp3
```

### Importing Audio Files to GCS

To import audio files to device-specific buckets:

```bash
# Import with default settings
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py import_audio_to_gcs

# Initialize fake GCS first and then import
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py import_audio_to_gcs --init-gcs

# Clean existing data before importing
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py import_audio_to_gcs --clean

# Specify a different base bucket name
docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py import_audio_to_gcs --bucket my-custom-bucket
```

The import process will:
1. Create a separate bucket for each device (e.g., `audio-files-10000000d642707c`)
2. Upload audio files directly to the appropriate device bucket
3. Update database records to point to the proper bucket locations

### Using GCS in Your Code

You can access device-specific buckets in your code:

```python
from utils.storage import upload_file, download_file, list_files, get_storage_client

# Get all device buckets
client = get_storage_client()
device_buckets = client.list_device_buckets('audio-files')

# Upload a file to a device bucket
public_url = upload_file('path/to/local/file.mp3', 'audio-files-10000000d642707c', 'file.mp3')

# Download a file from a device bucket
download_file('audio-files-10000000d642707c', 'file.mp3', 'local/download/path.mp3')

# List all files in a device bucket
files = list_files('audio-files-10000000d642707c')
```

The system will automatically use the fake GCS implementation during development and the real GCS in production.

### Switching Between Fake and Real GCS

You can control which implementation to use with the `USE_FAKE_GCS` environment variable:

```bash
# In docker-compose-dev.yml
environment:
  - USE_FAKE_GCS=True  # Use fake GCS

# To use real GCS in development (requires credentials)
environment:
  - USE_FAKE_GCS=False
```

If you switch to using real GCS, make sure you have the Google Cloud credentials properly configured.
