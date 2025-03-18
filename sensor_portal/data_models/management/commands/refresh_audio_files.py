import os
import glob
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from data_models.models import DataType, Device, Deployment, DataFile, Project, Site, DeviceModel


class Command(BaseCommand):
    help = 'Discover and import audio files from the NINA project folders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--base-dir',
            dest='base_dir',
            default="/Users/noahsyrdal/ARISE-MDS-sensor-portal-Pam/proj_tabmon_NINA",
            help='Base directory where audio files are stored'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing records that no longer have corresponding files'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        base_dir = options['base_dir']
        clean_missing = options['clean']

        if not os.path.exists(base_dir):
            self.stderr.write(self.style.ERROR(f"Base directory not found: {base_dir}"))
            return

        # Get or create audio type
        audio_type, _ = DataType.objects.get_or_create(name='Audio')
        
        # Get or create device model
        audio_recorder_model, _ = DeviceModel.objects.get_or_create(
            name='AudioMoth',
            defaults={
                'manufacturer': 'Open Acoustic Devices',
                'type': audio_type
            }
        )
        
        # Get or create default site
        default_site, _ = Site.objects.get_or_create(
            name='NINA Default Site',
            defaults={'short_name': 'NINA'}
        )
        
        # Get or create default project
        nina_project, _ = Project.objects.get_or_create(
            project_ID='NINA_PROJ',
            defaults={
                'name': 'NINA Acoustic Monitoring Project',
                'objectives': 'Audio monitoring for wildlife research'
            }
        )
        
        # Process each device folder
        device_folders = []
        # Discover device folders automatically
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path) and item.startswith('bugg_RPiID-'):
                device_id = item.split('-')[1]
                device_folders.append((item, device_id))
        
        if not device_folders:
            self.stderr.write(self.style.WARNING("No device folders found."))
            return
        
        # Track imported files
        imported_files = 0
        existing_files = 0
        
        for folder_name, device_id in device_folders:
            folder_path = os.path.join(base_dir, folder_name)
            self.stdout.write(f"Processing folder: {folder_path}")
            
            # Create or get device
            device, created = Device.objects.get_or_create(
                device_ID=device_id,
                defaults={
                    'name': f'AudioMoth {device_id[-6:]}',
                    'model': audio_recorder_model,
                    'type': audio_type,
                    'country': 'Norway',
                    'habitat': 'Forest'
                }
            )
            
            # Create or get deployment
            deployment_id = f"NINA_{device_id[-6:]}"
            deployment, created = Deployment.objects.get_or_create(
                deployment_ID=deployment_id,
                device=device,
                defaults={
                    'device_type': audio_type,
                    'deployment_start': timezone.now() - datetime.timedelta(days=30),
                    'site': default_site,
                    'is_active': True
                }
            )
            
            # Make sure project is associated with deployment
            if nina_project not in deployment.project.all():
                deployment.project.add(nina_project)
            
            # Find all audio files in this device folder
            audio_extensions = ['.wav', '.mp3', '.aac', '.flac']
            audio_files = []
            for ext in audio_extensions:
                pattern = os.path.join(folder_path, f"**/*{ext}")
                audio_files.extend(glob.glob(pattern, recursive=True))
            
            self.stdout.write(f"Found {len(audio_files)} audio files in {folder_name}")
            
            # Import each audio file
            for file_path in audio_files:
                file_name = os.path.basename(file_path)
                file_base, file_ext = os.path.splitext(file_name)
                rel_path = os.path.relpath(os.path.dirname(file_path), base_dir)
                
                # Get file size and creation time
                try:
                    file_size = os.path.getsize(file_path)
                    create_time = datetime.datetime.fromtimestamp(
                        os.path.getctime(file_path),
                        tz=timezone.get_current_timezone()
                    )
                except (FileNotFoundError, OSError):
                    self.stderr.write(f"Error accessing file: {file_path}")
                    continue
                
                # Check if file already exists in database
                if not DataFile.objects.filter(file_name=file_base).exists():
                    # Create data file record
                    data_file = DataFile(
                        deployment=deployment,
                        file_type=audio_type,
                        file_name=file_base,
                        file_size=file_size,
                        file_format=file_ext,
                        upload_dt=timezone.now(),
                        recording_dt=create_time,
                        path=rel_path,
                        local_path=base_dir,
                        local_storage=True,
                        # Set appropriate audio properties if available
                        sample_rate=44100,  # Default sample rate
                        file_length='00:01:00',  # Default length
                        config='DEFAULT'
                    )
                    try:
                        data_file.save()
                        imported_files += 1
                    except Exception as e:
                        self.stderr.write(f"Error saving file {file_base}: {str(e)}")
                else:
                    existing_files += 1
        
        self.stdout.write(self.style.SUCCESS(f"Imported {imported_files} new files"))
        self.stdout.write(f"Found {existing_files} existing files")
        
        # Clean up missing files if requested
        if clean_missing:
            cleaned = self._clean_missing_files(base_dir)
            self.stdout.write(self.style.SUCCESS(f"Cleaned {cleaned} records for missing files"))
    
    def _clean_missing_files(self, base_dir):
        """Remove database records for files that no longer exist"""
        cleaned_count = 0
        
        # Get all files from our target directory
        files = DataFile.objects.filter(local_path=base_dir)
        
        for file in files:
            full_path = file.full_path()
            if not os.path.exists(full_path):
                self.stdout.write(f"Removing record for missing file: {full_path}")
                file.delete()
                cleaned_count += 1
        
        return cleaned_count 