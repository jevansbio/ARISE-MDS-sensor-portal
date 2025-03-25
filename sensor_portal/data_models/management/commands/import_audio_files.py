import os
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from data_models.models import DataType, Site, Device, Deployment, Project, DataFile, DeviceModel
from django.db import connection

class Command(BaseCommand):
    help = 'Import audio files from NINA project directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--base-dir',
            type=str,
            default=None,
            help='Base directory for audio files (defaults to /usr/src/proj_tabmon_NINA in Docker)',
        )
        parser.add_argument(
            '--project-id',
            type=str,
            default='TABMON_NIN',
            help='Project ID to use for the imported files',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing data before importing',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without making changes',
        )

    def handle(self, *args, **options):
        # Set base directory - check both Docker and local paths
        base_dir = options['base_dir']
        if base_dir is None:
            # First try Docker path
            docker_path = '/usr/src/proj_tabmon_NINA'
            if os.path.exists(docker_path):
                base_dir = docker_path
                self.stdout.write(f"Using Docker path: {base_dir}")
            else:
                # Try relative path from Django project
                relative_path = os.path.join(settings.BASE_DIR, '..', 'proj_tabmon_NINA')
                if os.path.exists(relative_path):
                    base_dir = relative_path
                    self.stdout.write(f"Using relative path: {base_dir}")
                else:
                    self.stdout.write(self.style.ERROR(f"Audio directory not found at {docker_path} or {relative_path}"))
                    return
        
        # Check if directory exists
        if not os.path.exists(base_dir):
            self.stdout.write(self.style.ERROR(f"Directory {base_dir} not found"))
            return
        
        # Get project ID
        project_id = options['project_id']
        
        # Clean existing data if requested
        if options['clean'] and not options['dry_run']:
            self.stdout.write("Cleaning existing data...")
            DataFile.objects.filter(deployment__project__project_ID=project_id).delete()
            Deployment.objects.filter(project__project_ID=project_id).delete()
            # Don't delete devices as they might be used by other projects
        
        # Create data type
        audio_type, _ = DataType.objects.get_or_create(name='Audio')
        
        # Create site
        site, _ = Site.objects.get_or_create(
            name='NINA Field Site',
            short_name='NINA'
        )
        
        # Create project
        project, _ = Project.objects.get_or_create(
            project_ID=project_id,
            defaults={
                'name': 'TABMON NINA',
                'objectives': 'Audio monitoring for NINA project',
                'principal_investigator': 'NINA',
                'principal_investigator_email': 'info@nina.no',
                'contact': 'NINA',
                'contact_email': 'info@nina.no',
                'organisation': 'NINA'
            }
        )
        
        # Create or get the AudioMoth device model
        device_model, _ = DeviceModel.objects.get_or_create(
            name='AudioMoth',
            defaults={
                'manufacturer': 'Open Acoustic Devices',
                'type': audio_type
            }
        )
        
        # Track stats
        stats = {
            'devices': 0,
            'deployments': 0,
            'files': 0,
            'errors': 0
        }
        
        # Walk through the directory structure
        for item in os.listdir(base_dir):
            device_dir = os.path.join(base_dir, item)
            
            # Skip non-directories and hidden files
            if not os.path.isdir(device_dir) or item.startswith('.'):
                continue
                
            # Extract the device ID from the directory name
            if item.startswith('bugg_RPiID-'):
                device_id = item.split('-')[1]
            else:
                device_id = item
            
            self.stdout.write(f"Processing device {device_id}...")
            
            # Create device if it doesn't exist
            if not options['dry_run']:
                # Check which fields are available in the Device model
                available_fields = {}
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name='data_models_device'
                    """)
                    columns = [row[0] for row in cursor.fetchall()]
                
                # Build defaults dict with only fields that exist in the database
                device_defaults = {
                    'name': f'AudioMoth {device_id}',
                    'model': device_model,
                    'type': audio_type
                }
                
                # Only add these fields if they exist in the database
                if 'country' in columns:
                    device_defaults['country'] = 'Unknown'  # Safe default
                
                # Get or create device with only valid fields
                device, created = Device.objects.get_or_create(
                    device_ID=device_id,
                    defaults=device_defaults
                )
                if created:
                    stats['devices'] += 1
            else:
                device = None
                self.stdout.write(f"  Would create device {device_id}")
                stats['devices'] += 1
            
            # Create deployment if it doesn't exist
            if not options['dry_run']:
                # Use the full device_id to ensure uniqueness - matching direct_audio_import
                deployment, created = Deployment.objects.get_or_create(
                    deployment_ID=f'NINA_{device_id}',  # Use full device_id instead of just the first 5 chars
                    device=device,
                    defaults={
                        'site': site,
                        'device_type': audio_type,
                        'deployment_start': timezone.now() - datetime.timedelta(days=30),
                        'time_zone': 'UTC',
                    }
                )
                
                if created:
                    deployment.project.add(project)
                    stats['deployments'] += 1
            else:
                deployment = None
                self.stdout.write(f"  Would create deployment NINA_{device_id}")  # Update log message too
                stats['deployments'] += 1
            
            # Check for audio_files directory
            audio_dir = os.path.join(device_dir, 'audio_files')
            if not os.path.exists(audio_dir):
                audio_dir = device_dir  # Use the device directory if audio_files doesn't exist
            
            # Process audio files
            for audio_file in os.listdir(audio_dir):
                # Skip non-audio files
                if not audio_file.endswith(('.wav', '.WAV')):
                    continue
                    
                file_path = os.path.join(audio_dir, audio_file)
                file_size = os.path.getsize(file_path)
                file_name = os.path.splitext(audio_file)[0]
                file_ext = os.path.splitext(audio_file)[1]
                
                # Try to extract date from filename (format: bugg_RPiID-DEVICEID_YYYYMMDD_HHMMSS)
                try:
                    parts = file_name.split('_')
                    if len(parts) >= 3:
                        date_part = parts[-2]  # YYYYMMDD
                        time_part = parts[-1].split('_')[0]  # HHMMSS
                        
                        # Handle config part (e.g., 16kHz)
                        config = None
                        if len(parts) >= 4:
                            config = parts[-1]
                        elif '_' in parts[-1]:
                            config = parts[-1].split('_')[1]
                        
                        # Extract sample rate if available
                        sample_rate = None
                        if config and 'kHz' in config:
                            try:
                                # Convert something like "16kHz" to 16000
                                sample_rate = int(float(config.replace('kHz', '')) * 1000)
                            except (ValueError, TypeError):
                                pass
                        
                        # Parse date and time
                        if len(date_part) == 8 and len(time_part) >= 6:
                            year = int(date_part[0:4])
                            month = int(date_part[4:6])
                            day = int(date_part[6:8])
                            
                            hour = int(time_part[0:2])
                            minute = int(time_part[2:4])
                            second = int(time_part[4:6])
                            
                            recording_dt = datetime.datetime(
                                year, month, day, hour, minute, second,
                                tzinfo=timezone.get_current_timezone()
                            )
                        else:
                            recording_dt = None
                    else:
                        recording_dt = None
                        config = None
                        sample_rate = None
                except (ValueError, IndexError):
                    recording_dt = None
                    config = None
                    sample_rate = None
                
                # Store paths in a way that works in Docker environment
                # Store paths relative to where Django can find them in the container
                container_path = '/usr/src/proj_tabmon_NINA'
                
                # Create the data file if it doesn't exist and not in dry run mode
                if not options['dry_run']:
                    if not DataFile.objects.filter(file_name=file_name).exists():
                        try:
                            # Only include fields that are guaranteed to exist in the database
                            file_data = {
                                'deployment': deployment,
                                'file_type': audio_type,
                                'file_name': file_name,
                                'file_size': file_size,
                                'file_format': file_ext,
                                'recording_dt': recording_dt,
                                'path': container_path,
                                'local_path': os.path.dirname(os.path.relpath(file_path, base_dir)),
                            }
                            
                            # Only add these fields if the model supports them
                            if hasattr(DataFile, 'config'):
                                file_data['config'] = config
                            if hasattr(DataFile, 'sample_rate'):
                                file_data['sample_rate'] = sample_rate
                            if hasattr(DataFile, 'file_length') and sample_rate and sample_rate > 0:
                                file_data['file_length'] = f"{(file_size/2/sample_rate)/60:.2f} min"
                            
                            # Create the data file
                            DataFile.objects.create(**file_data)
                            stats['files'] += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"  Error creating data file {file_name}: {e}"))
                            stats['errors'] += 1
                else:
                    self.stdout.write(f"  Would import file {file_name}")
                    stats['files'] += 1
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f"Import summary:"))
        self.stdout.write(f"  Devices: {stats['devices']}")
        self.stdout.write(f"  Deployments: {stats['deployments']}")
        self.stdout.write(f"  Files: {stats['files']}")
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f"  Errors: {stats['errors']}"))
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("This was a dry run, no changes were made."))
        else:
            self.stdout.write(self.style.SUCCESS("Import completed successfully.")) 