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
            
            # Use direct SQL rather than ORM to avoid schema issues
            with connection.cursor() as cursor:
                # First, find project ID
                cursor.execute(
                    'SELECT id FROM data_models_project WHERE "project_ID" = %s', 
                    [project_id]
                )
                result = cursor.fetchone()
                if result:
                    project_db_id = result[0]
                    
                    # Delete files for deployments related to this project
                    cursor.execute("""
                        DELETE FROM data_models_datafile 
                        WHERE deployment_id IN (
                            SELECT d.id FROM data_models_deployment d
                            JOIN data_models_deployment_project dp ON d.id = dp.deployment_id
                            WHERE dp.project_id = %s
                        )
                    """, [project_db_id])
                    
                    # Delete deployment-project relationships
                    cursor.execute("""
                        DELETE FROM data_models_deployment_project
                        WHERE project_id = %s
                    """, [project_db_id])
                    
                    # Delete deployments that don't have any projects
                    cursor.execute("""
                        DELETE FROM data_models_deployment
                        WHERE id NOT IN (
                            SELECT deployment_id FROM data_models_deployment_project
                        )
                    """)
                    
                    self.stdout.write("Data cleaned successfully using direct SQL")
                else:
                    self.stdout.write(f"Project with ID {project_id} not found. Nothing to clean.")
        
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
        
        # Get available database columns for each model
        device_columns = []
        deployment_columns = []
        datafile_columns = []
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='data_models_device'
            """)
            device_columns = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='data_models_deployment'
            """)
            deployment_columns = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='data_models_datafile'
            """)
            datafile_columns = [row[0] for row in cursor.fetchall()]
            
        self.stdout.write(f"Found {len(device_columns)} columns in device table")
        self.stdout.write(f"Found {len(deployment_columns)} columns in deployment table")
        self.stdout.write(f"Found {len(datafile_columns)} columns in datafile table")
        
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
                with connection.cursor() as cursor:
                    # Check if device exists
                    cursor.execute('SELECT id FROM data_models_device WHERE "device_ID" = %s', [device_id])
                    device_result = cursor.fetchone()
                    
                    if device_result:
                        device_id_pk = device_result[0]
                        self.stdout.write(f"  Device {device_id} already exists.")
                    else:
                        # Create device using direct SQL without referencing country field
                        cursor.execute("""
                            INSERT INTO data_models_device 
                            ("device_ID", name, model_id, type_id, created_on, modified_on)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, [
                            device_id,
                            f'AudioMoth {device_id}',
                            device_model.id,
                            audio_type.id,
                            timezone.now(),
                            timezone.now()
                        ])
                        device_id_pk = cursor.fetchone()[0]
                        
                        # If country column exists, set it (optional)
                        if 'country' in device_columns:
                            try:
                                cursor.execute("""
                                    UPDATE data_models_device 
                                    SET country = %s
                                    WHERE id = %s
                                """, ['Unknown', device_id_pk])
                            except Exception as e:
                                self.stdout.write(f"  Warning: Could not set country: {e}")
                        
                        stats['devices'] += 1
                        self.stdout.write(f"  Created device {device_id}")
                    
                    # Create deployment if it doesn't exist
                    # Use the full device_id to ensure uniqueness
                    deployment_id = f'NINA_{device_id}'
                    
                    cursor.execute('SELECT id FROM data_models_deployment WHERE "deployment_ID" = %s', [deployment_id])
                    deployment_result = cursor.fetchone()
                    
                    if deployment_result:
                        deployment_id_pk = deployment_result[0]
                        self.stdout.write(f"  Deployment {deployment_id} already exists.")
                    else:
                        # Create basic deployment with minimal fields using direct SQL
                        now = timezone.now()
                        start_date = now - datetime.timedelta(days=30)
                        
                        # Generate a deployment_device_ID (a mandatory field)
                        deployment_device_id = f"{deployment_id}-Audio-1"
                        
                        cursor.execute("""
                            INSERT INTO data_models_deployment 
                            ("deployment_ID", "deployment_device_ID", device_id, site_id, device_type_id, 
                            deployment_start, is_active, created_on, modified_on, device_n, time_zone)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, [
                            deployment_id,
                            deployment_device_id,  # Include deployment_device_ID in the initial insert
                            device_id_pk,
                            site.id,
                            audio_type.id,
                            start_date,
                            True,
                            now,
                            now,
                            1,  # Default value for device_n field
                            'UTC'  # Default value for time_zone field
                        ])
                        deployment_id_pk = cursor.fetchone()[0]
                        
                        # Link to project
                        cursor.execute("""
                            INSERT INTO data_models_deployment_project 
                            (deployment_id, project_id)
                            VALUES (%s, %s)
                        """, [deployment_id_pk, project.id])
                        
                        stats['deployments'] += 1
                        self.stdout.write(f"  Created deployment {deployment_id}")
                
                # Load Django model instances for use with DataFile creation
                # (we need these for the foreign key relationships)
                try:
                    # We'll just use the IDs directly instead of loading models
                    # to avoid ORM issues with missing columns
                    device_id_pk = device_id_pk  # We already have this
                    deployment_id_pk = deployment_id_pk  # We already have this
                    self.stdout.write(f"  Using deployment ID {deployment_id_pk} for files")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error accessing IDs: {e}"))
                    continue
            else:
                device_id_pk = None
                deployment_id_pk = None
                self.stdout.write(f"  Would create device {device_id}")
                self.stdout.write(f"  Would create deployment NINA_{device_id}")
                stats['devices'] += 1
                stats['deployments'] += 1
            
            # Check for audio files
            audio_dir = os.path.join(device_dir, 'conf_20240314_TABMON')
            if not os.path.exists(audio_dir):
                audio_dir = device_dir  # Use device directory if conf_20240314_TABMON doesn't exist
                
            self.stdout.write(f"  Looking for audio files in: {audio_dir}")
            
            # Process audio files
            if os.path.exists(audio_dir):
                # Find all audio files (MP3, WAV, or M4A)
                audio_files = []
                for root, dirs, files in os.walk(audio_dir):
                    for file in files:
                        if file.lower().endswith(('.mp3', '.wav', '.m4a')):
                            audio_files.append(os.path.join(root, file))
                
                if audio_files:
                    self.stdout.write(f"  Found {len(audio_files)} audio files")
                    
                    # Show a few examples
                    for i, file_path in enumerate(audio_files[:3]):
                        self.stdout.write(f"    Example {i+1}: {os.path.basename(file_path)}")
                else:
                    self.stdout.write("  No audio files found")
                    continue
                
                for file_path in audio_files:
                    file_size = os.path.getsize(file_path)
                    file_name = os.path.splitext(os.path.basename(file_path))[0]
                    file_ext = os.path.splitext(file_path)[1]
                    
                    # Skip if file already exists and not in dry run mode
                    if not options['dry_run']:
                        # Check if file exists using SQL instead of ORM
                        with connection.cursor() as cursor:
                            cursor.execute('SELECT id FROM data_models_datafile WHERE file_name = %s', [file_name])
                            if cursor.fetchone():
                                self.stdout.write(f"  File {file_name} already exists, skipping.")
                                continue
                        
                        # Try to extract date from filename
                        recording_dt = None
                        try:
                            # Extract date using the patterns established in direct_audio_import.py
                            dt_part = file_name
                            
                            # First try ISO format with T separator (2024-05-16T17_49_40)
                            if 'T' in dt_part:
                                # Split date and time
                                date_part, time_part = dt_part.split('T')
                                
                                # Remove Z and milliseconds if present
                                if 'Z' in time_part:
                                    time_part = time_part.split('Z')[0]
                                    
                                # Handle milliseconds
                                if '.' in time_part:
                                    time_part = time_part.split('.')[0]
                                
                                # Format time part - replace underscores with colons
                                time_part = time_part.replace('_', ':')
                                
                                # Create datetime object
                                iso_dt = f"{date_part}T{time_part}"
                                recording_dt = datetime.datetime.fromisoformat(iso_dt)
                                recording_dt = recording_dt.replace(tzinfo=timezone.get_current_timezone())
                            
                            # Try format with underscores (YYYYMMDD_HHMMSS)
                            elif '_' in dt_part:
                                parts = dt_part.split('_')
                                # Look for a part that matches the date format YYYYMMDD
                                for part in parts:
                                    if len(part) == 8 and part.isdigit():
                                        date_part = part
                                        # Look for a part that might be the time
                                        for time_part in parts:
                                            if len(time_part) >= 6 and time_part.isdigit():
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
                                                break
                                        break
                        except (ValueError, IndexError) as e:
                            self.stdout.write(f"  Warning: Could not parse date from {file_name}: {e}")
                            recording_dt = None
                        
                        try:
                            # Extract config and sample rate from filename
                            config = None
                            sample_rate = None
                            parts = file_name.split('_')
                            if len(parts) > 3 and 'kHz' in parts[-1]:
                                config = parts[-1]
                                try:
                                    if 'kHz' in config:
                                        # Convert something like "16kHz" to 16000
                                        sample_rate = int(float(config.replace('kHz', '')) * 1000)
                                except (ValueError, TypeError):
                                    pass
                            
                            # Estimate file length if sample rate is available
                            file_length = None
                            if sample_rate:
                                file_length_mins = (file_size/2/sample_rate)/60
                                file_length = f"{file_length_mins:.2f} min"
                            
                            # Get relative path
                            local_path = os.path.dirname(os.path.relpath(file_path, base_dir))
                            
                            # Create DataFile using direct SQL
                            with connection.cursor() as cursor:
                                now = timezone.now()
                                
                                # Create basic DataFile with required fields
                                cursor.execute("""
                                    INSERT INTO data_models_datafile
                                    (deployment_id, file_type_id, file_name, file_size, file_format,
                                     path, local_path, created_on, modified_on,
                                     upload_dt, recording_dt)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, [
                                    deployment_id_pk,
                                    audio_type.id,
                                    file_name,
                                    file_size,
                                    file_ext,
                                    '/usr/src/proj_tabmon_NINA',
                                    local_path,
                                    now,
                                    now,
                                    now,
                                    recording_dt
                                ])
                                
                                # Add optional fields if they exist
                                if config and 'config' in datafile_columns:
                                    cursor.execute("""
                                        UPDATE data_models_datafile
                                        SET config = %s
                                        WHERE file_name = %s
                                    """, [config, file_name])
                                
                                if sample_rate and 'sample_rate' in datafile_columns:
                                    cursor.execute("""
                                        UPDATE data_models_datafile
                                        SET sample_rate = %s
                                        WHERE file_name = %s
                                    """, [sample_rate, file_name])
                                
                                if file_length and 'file_length' in datafile_columns:
                                    cursor.execute("""
                                        UPDATE data_models_datafile
                                        SET file_length = %s
                                        WHERE file_name = %s
                                    """, [file_length, file_name])
                                
                                # Set boolean fields
                                if 'local_storage' in datafile_columns:
                                    cursor.execute("""
                                        UPDATE data_models_datafile
                                        SET local_storage = %s
                                        WHERE file_name = %s
                                    """, [True, file_name])
                                
                                if 'archived' in datafile_columns:
                                    cursor.execute("""
                                        UPDATE data_models_datafile
                                        SET archived = %s
                                        WHERE file_name = %s
                                    """, [False, file_name])
                                
                                if 'do_not_remove' in datafile_columns:
                                    cursor.execute("""
                                        UPDATE data_models_datafile
                                        SET do_not_remove = %s
                                        WHERE file_name = %s
                                    """, [False, file_name])
                                
                                # Set JSON fields if they exist
                                if 'extra_data' in datafile_columns:
                                    cursor.execute("""
                                        UPDATE data_models_datafile
                                        SET extra_data = %s
                                        WHERE file_name = %s
                                    """, ['{}', file_name])
                                
                                if 'linked_files' in datafile_columns:
                                    cursor.execute("""
                                        UPDATE data_models_datafile
                                        SET linked_files = %s
                                        WHERE file_name = %s
                                    """, ['{}', file_name])
                            
                            stats['files'] += 1
                            self.stdout.write(f"  Created file record for {file_name}")
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"  Error creating data file {file_name}: {e}"))
                            stats['errors'] += 1
                    else:
                        self.stdout.write(f"  Would import file {file_name}")
                        stats['files'] += 1
            else:
                self.stdout.write(self.style.WARNING(f"  No directory found at {audio_dir}"))
        
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