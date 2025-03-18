# Generated manually
import os
import glob
import datetime
from django.db import migrations
from django.utils import timezone
from django.conf import settings

def get_audio_file_info(file_path):
    """
    Extract relevant information from audio file path
    """
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_format = os.path.splitext(file_name)[1]
    created_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path), tz=timezone.utc)
    
    # Try to extract information from filename
    # Assuming format like: bugg_RPiID-10000000d2b4d01e_DATE_TIME_config
    parts = os.path.splitext(file_name)[0].split('_')
    
    # Default values
    recording_dt = created_time
    config = "default"
    sample_rate = 44100  # Standard audio sampling rate
    
    # Try to determine more info from filename if possible
    if len(parts) >= 4:
        try:
            date_str = parts[2]
            time_str = parts[3]
            if len(date_str) == 8 and len(time_str) >= 6:  # YYYYMMDD_HHMMSS
                year, month, day = int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8])
                hour, minute, second = int(time_str[:2]), int(time_str[2:4]), int(time_str[4:6])
                recording_dt = datetime.datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
        except (ValueError, IndexError):
            pass
        
        # Try to get config information if available
        if len(parts) > 4:
            config = parts[4]
            # Parse sample rate from config if possible (e.g., "16kHz")
            if "khz" in config.lower():
                try:
                    sample_rate = int(float(config.lower().replace("khz", "")) * 1000)
                except ValueError:
                    pass
    
    return {
        "file_name": os.path.splitext(file_name)[0],
        "file_format": file_format,
        "file_size": file_size,
        "recording_dt": recording_dt,
        "config": config,
        "sample_rate": sample_rate,
        "file_length": "00:03:00"  # Default length, would need audio processing to get actual length
    }

def load_initial_data(apps, schema_editor):
    """
    Load audio files from proj_tabmon_NINA folder and create necessary database records
    """
    # Get the models
    DataType = apps.get_model('data_models', 'DataType')
    Site = apps.get_model('data_models', 'Site')
    DeviceModel = apps.get_model('data_models', 'DeviceModel')
    Device = apps.get_model('data_models', 'Device')
    Project = apps.get_model('data_models', 'Project')
    Deployment = apps.get_model('data_models', 'Deployment')
    DataFile = apps.get_model('data_models', 'DataFile')
    
    # Create data types
    audio_type, _ = DataType.objects.get_or_create(name="Audio")
    
    # Create a site
    site, _ = Site.objects.get_or_create(
        name="NINA Field Site", 
        defaults={"short_name": "NINA"}
    )
    
    # Create device model
    device_model, _ = DeviceModel.objects.get_or_create(
        name="AudioMoth",
        defaults={
            "manufacturer": "Open Acoustic Devices",
            "type": audio_type
        }
    )
    
    # Create project
    project, _ = Project.objects.get_or_create(
        project_ID="TABMON_NINA",
        defaults={
            "name": "Tabmontoring NINA Project",
            "objectives": "Audio monitoring in field conditions",
            "principal_investigator": "NINA Research Team",
            "organisation": "NINA"
        }
    )
    
    # Base directory for audio files
    base_dir = "/Users/noahsyrdal/ARISE-MDS-sensor-portal-Pam/proj_tabmon_NINA"
    
    # Process each device folder
    device_folders = glob.glob(os.path.join(base_dir, "bugg_RPiID-*"))
    
    for device_folder in device_folders:
        # Extract device ID from folder name
        folder_name = os.path.basename(device_folder)
        parts = folder_name.split('-')
        if len(parts) < 2:
            continue
            
        device_id = parts[1]
        
        # Create device
        device, _ = Device.objects.get_or_create(
            device_ID=device_id,
            defaults={
                "name": f"AudioMoth {device_id[-6:]}",
                "model": device_model,
                "type": audio_type,
                "country": "Norway",
                "site_name": "NINA Research Area",
                "habitat": "Forest",
                "extra_data": {"source_folder": folder_name}
            }
        )
        
        # Create deployment
        deployment, _ = Deployment.objects.get_or_create(
            deployment_ID=f"NINA_{device_id[-6:]}",
            device=device,
            defaults={
                "deployment_start": timezone.now() - datetime.timedelta(days=30),
                "site": site,
                "device_type": audio_type,
                "country": "Norway",
                "habitat": "Forest",
                "latitude": 59.9139,
                "longitude": 10.7522,
                "is_active": True
            }
        )
        
        # Add project to deployment
        deployment.project.add(project)
        
        # Find audio files
        audio_files = glob.glob(os.path.join(device_folder, "**/*.wav"), recursive=True)
        
        # Process audio files
        for audio_file in audio_files:
            file_info = get_audio_file_info(audio_file)
            
            # Create relative path within storage
            rel_path = os.path.dirname(os.path.relpath(audio_file, base_dir))
            
            # Create data file
            DataFile.objects.get_or_create(
                file_name=file_info["file_name"],
                defaults={
                    "deployment": deployment,
                    "file_type": audio_type,
                    "file_size": file_info["file_size"],
                    "file_format": file_info["file_format"],
                    "config": file_info["config"],
                    "sample_rate": file_info["sample_rate"],
                    "file_length": file_info["file_length"],
                    "recording_dt": file_info["recording_dt"],
                    "upload_dt": timezone.now(),
                    "path": rel_path,
                    "local_path": base_dir,
                    "local_storage": True
                }
            )

def reverse_migration(apps, schema_editor):
    """
    Reverse the migration by removing data files, deployments, and devices from NINA project
    """
    Project = apps.get_model('data_models', 'Project')
    DataFile = apps.get_model('data_models', 'DataFile')
    Deployment = apps.get_model('data_models', 'Deployment')
    Device = apps.get_model('data_models', 'Device')
    
    # Get NINA project
    try:
        project = Project.objects.get(project_ID="TABMON_NINA")
        
        # Get deployments for this project
        deployments = Deployment.objects.filter(project=project)
        
        # Get deployment IDs
        deployment_ids = list(deployments.values_list('id', flat=True))
        
        # Delete data files
        DataFile.objects.filter(deployment_id__in=deployment_ids).delete()
        
        # Get device IDs
        device_ids = list(deployments.values_list('device_id', flat=True))
        
        # Delete deployments
        deployments.delete()
        
        # Delete devices
        Device.objects.filter(id__in=device_ids).delete()
        
        # Delete project
        project.delete()
    except Project.DoesNotExist:
        pass

class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0019_rename_archives_project_archive_and_more'),
    ]

    operations = [
        migrations.RunPython(load_initial_data, reverse_migration),
    ] 