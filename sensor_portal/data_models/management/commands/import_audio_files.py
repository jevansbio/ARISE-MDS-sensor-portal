import os
import glob
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from data_models.models import DataType, Site, DeviceModel, Device, Project, Deployment, DataFile

class Command(BaseCommand):
    help = 'Import audio files from NINA project directory'
    
    def add_arguments(self, parser):
        parser.add_argument('--base-dir', type=str, 
                            default='/Users/noahsyrdal/ARISE-MDS-sensor-portal-Pam/proj_tabmon_NINA',
                            help='Base directory containing the audio files')
        
        parser.add_argument('--project-id', type=str, default='TABMON_NINA',
                            help='Project ID to associate files with')
        
        parser.add_argument('--clean', action='store_true',
                            help='Clean existing data before importing')
        
        parser.add_argument('--dry-run', action='store_true',
                            help='Simulate the import without making changes')
    
    def get_audio_file_info(self, file_path):
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
        
        # Calculate file length estimation (based on WAV format, 16-bit stereo)
        # This is a rough estimation and would need actual audio file parsing for accuracy
        if sample_rate > 0 and file_size > 44:  # 44 bytes is the WAV header size
            # Assuming 16-bit stereo (4 bytes per sample)
            duration_seconds = (file_size - 44) / (sample_rate * 4)
            minutes, seconds = divmod(int(duration_seconds), 60)
            hours, minutes = divmod(minutes, 60)
            file_length = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            file_length = "00:03:00"  # Default fallback
        
        return {
            "file_name": os.path.splitext(file_name)[0],
            "file_format": file_format,
            "file_size": file_size,
            "recording_dt": recording_dt,
            "config": config,
            "sample_rate": sample_rate,
            "file_length": file_length
        }
    
    @transaction.atomic
    def clean_existing_data(self, project_id):
        """Remove existing data for the specified project"""
        self.stdout.write(f"Cleaning existing data for project {project_id}...")
        
        try:
            project = Project.objects.get(project_ID=project_id)
            
            # Get deployments for this project
            deployments = Deployment.objects.filter(project=project)
            
            # Get deployment IDs
            deployment_ids = list(deployments.values_list('id', flat=True))
            
            # Delete data files
            num_files = DataFile.objects.filter(deployment_id__in=deployment_ids).count()
            self.stdout.write(f"  Deleting {num_files} data files...")
            DataFile.objects.filter(deployment_id__in=deployment_ids).delete()
            
            # Get device IDs
            device_ids = list(deployments.values_list('device_id', flat=True).distinct())
            
            # Delete deployments
            self.stdout.write(f"  Deleting {deployments.count()} deployments...")
            deployments.delete()
            
            # Delete devices
            self.stdout.write(f"  Deleting {len(device_ids)} devices...")
            Device.objects.filter(id__in=device_ids).delete()
            
            self.stdout.write(self.style.SUCCESS(f"Cleaned data for project {project_id}"))
            
        except Project.DoesNotExist:
            self.stdout.write(f"Project {project_id} not found, nothing to clean")
    
    def handle(self, *args, **options):
        base_dir = options['base_dir']
        project_id = options['project_id']
        clean = options['clean']
        dry_run = options['dry_run']
        
        if not os.path.isdir(base_dir):
            self.stdout.write(self.style.ERROR(f"Directory not found: {base_dir}"))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Start a transaction if not in dry run mode
        if not dry_run and clean:
            self.clean_existing_data(project_id)
        
        with transaction.atomic():
            # If dry run, roll back all changes at the end
            if dry_run:
                transaction.set_rollback(True)
            
            # Get or create required models
            audio_type, _ = DataType.objects.get_or_create(name="Audio")
            
            site, _ = Site.objects.get_or_create(
                name="NINA Field Site", 
                defaults={"short_name": "NINA"}
            )
            
            device_model, _ = DeviceModel.objects.get_or_create(
                name="AudioMoth",
                defaults={
                    "manufacturer": "Open Acoustic Devices",
                    "type": audio_type
                }
            )
            
            project, _ = Project.objects.get_or_create(
                project_ID=project_id,
                defaults={
                    "name": "Tabmontoring NINA Project",
                    "objectives": "Audio monitoring in field conditions",
                    "principal_investigator": "NINA Research Team",
                    "organisation": "NINA"
                }
            )
            
            self.stdout.write(f"Scanning {base_dir} for audio files...")
            
            # Process each device folder
            device_folders = glob.glob(os.path.join(base_dir, "bugg_RPiID-*"))
            total_files_found = 0
            total_files_imported = 0
            
            for device_folder in device_folders:
                # Extract device ID from folder name
                folder_name = os.path.basename(device_folder)
                parts = folder_name.split('-')
                if len(parts) < 2:
                    self.stdout.write(f"Skipping folder with invalid name: {folder_name}")
                    continue
                    
                device_id = parts[1]
                
                # Create device
                device, device_created = Device.objects.get_or_create(
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
                
                status = "Created" if device_created else "Found"
                self.stdout.write(f"{status} device: {device.name} (ID: {device.device_ID})")
                
                # Create deployment
                deployment, deployment_created = Deployment.objects.get_or_create(
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
                
                status = "Created" if deployment_created else "Found"
                self.stdout.write(f"{status} deployment: {deployment.deployment_ID}")
                
                # Add project to deployment if needed
                if project not in deployment.project.all():
                    deployment.project.add(project)
                    self.stdout.write(f"Added deployment to project {project.project_ID}")
                
                # Find audio files
                audio_files = glob.glob(os.path.join(device_folder, "**/*.wav"), recursive=True)
                total_files_found += len(audio_files)
                
                # Process audio files
                files_imported = 0
                for audio_file in audio_files:
                    file_info = self.get_audio_file_info(audio_file)
                    
                    # Create relative path within storage
                    rel_path = os.path.dirname(os.path.relpath(audio_file, base_dir))
                    
                    # Create or get data file
                    data_file, created = DataFile.objects.get_or_create(
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
                    
                    if created:
                        files_imported += 1
                
                total_files_imported += files_imported
                self.stdout.write(f"Imported {files_imported} out of {len(audio_files)} files from {folder_name}")
            
            status_msg = f"Found {total_files_found} audio files, imported {total_files_imported} new files"
            if dry_run:
                self.stdout.write(self.style.WARNING(f"DRY RUN - {status_msg} (no changes made)"))
            else:
                self.stdout.write(self.style.SUCCESS(status_msg)) 