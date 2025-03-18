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
