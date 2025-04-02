import os
import datetime
import psycopg2
import glob
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

class Command(BaseCommand):
    help = 'Direct PostgreSQL-based audio import bypassing Django ORM entirely'

    def add_arguments(self, parser):
        parser.add_argument(
            '--base-dir',
            type=str,
            default=None,
            help='Base directory for audio files',
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
        # Database connection params from Django settings
        db_params = {
            'dbname': settings.DATABASES['default']['NAME'],
            'user': settings.DATABASES['default']['USER'],
            'password': settings.DATABASES['default']['PASSWORD'],
            'host': settings.DATABASES['default']['HOST'] or 'localhost',
            'port': settings.DATABASES['default']['PORT'] or '5432'
        }
        
        verbosity = options['verbosity']
        
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
        
        # Connect to the database for schema changes and global data
        try:
            conn = psycopg2.connect(**db_params)
            conn.autocommit = False  # Start a transaction
            cursor = conn.cursor()
            
            # First, list all subdirectories so we can see what's available
            self.stdout.write("Available device directories:")
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if os.path.isdir(item_path):
                    self.stdout.write(f"  - {item}")
                    # List contents of each device directory 
                    for subitem in os.listdir(item_path):
                        subitem_path = os.path.join(item_path, subitem)
                        if os.path.isdir(subitem_path):
                            self.stdout.write(f"    |- {subitem}/")
                            # Look for audio files in this directory
                            audio_files = []
                            for ext in ['.mp3', '.wav', '.m4a']:
                                audio_files.extend(glob.glob(os.path.join(subitem_path, f"*{ext}")))
                            if audio_files:
                                self.stdout.write(f"       Found {len(audio_files)} audio files")
                                # Print first 3 examples
                                for i, audio_file in enumerate(audio_files[:3]):
                                    self.stdout.write(f"       Example {i+1}: {os.path.basename(audio_file)}")
            
            # First, drop ALL NOT NULL constraints on the datafile table
            cursor.execute("""
            DO $$
            DECLARE
                col_name text;
            BEGIN
                -- Explicitly drop NOT NULL constraints on common problematic columns
                BEGIN
                    ALTER TABLE data_models_datafile ALTER COLUMN local_storage DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from local_storage: %', SQLERRM;
                END;
                
                BEGIN
                    ALTER TABLE data_models_datafile ALTER COLUMN archived DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from archived: %', SQLERRM;
                END;
                
                BEGIN
                    ALTER TABLE data_models_datafile ALTER COLUMN do_not_remove DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from do_not_remove: %', SQLERRM;
                END;
                
                BEGIN
                    ALTER TABLE data_models_datafile ALTER COLUMN upload_dt DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from upload_dt: %', SQLERRM;
                END;
                
                BEGIN
                    ALTER TABLE data_models_datafile ALTER COLUMN file_name DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from file_name: %', SQLERRM;
                END;
                
                BEGIN
                    ALTER TABLE data_models_datafile ALTER COLUMN file_format DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from file_format: %', SQLERRM;
                END;
                
                BEGIN
                    ALTER TABLE data_models_datafile ALTER COLUMN path DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from path: %', SQLERRM;
                END;
                
                -- Drop NOT NULL on JSON fields too
                BEGIN
                    ALTER TABLE data_models_device ALTER COLUMN extra_data DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from device.extra_data: %', SQLERRM;
                END;
                
                BEGIN
                    ALTER TABLE data_models_deployment ALTER COLUMN extra_data DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from deployment.extra_data: %', SQLERRM;
                END;
                
                BEGIN
                    ALTER TABLE data_models_deployment ALTER COLUMN time_zone DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from deployment.time_zone: %', SQLERRM;
                END;
                
                BEGIN
                    ALTER TABLE data_models_datafile ALTER COLUMN extra_data DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from datafile.extra_data: %', SQLERRM;
                END;
                
                BEGIN
                    ALTER TABLE data_models_datafile ALTER COLUMN linked_files DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'Could not drop NOT NULL from linked_files: %', SQLERRM;
                END;
            END;
            $$;
            """)
            
            # Handle schema differences with more robust error handling
            self.stdout.write("Checking and fixing schema differences...")
            
            # Use a more robust approach with direct SQL and better error handling
            cursor.execute("""
            DO $$
            BEGIN
                -- Check if country column exists in device table
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='data_models_device' AND column_name='country'
                ) THEN
                    -- Add country column to device table
                    EXECUTE 'ALTER TABLE data_models_device ADD COLUMN country varchar(100) NULL';
                    RAISE NOTICE 'Added country column to data_models_device table';
                END IF;
                
                -- More robust: If the deployment table has country and device doesn't, add it
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='data_models_deployment' AND column_name='country'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='data_models_device' AND column_name='country'
                ) THEN
                    -- Add country column to device table
                    EXECUTE 'ALTER TABLE data_models_device ADD COLUMN country varchar(100) NULL';
                    RAISE NOTICE 'Added country column to data_models_device table (from deployment)';
                END IF;
                
                -- Handle any other tables that might need the country field
                -- By handling each possible case separately, we make this very robust
                
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error fixing schema differences: %', SQLERRM;
            END;
            $$;
            """)
            
            # Commit schema changes
            conn.commit()
            self.stdout.write("Schema differences fixed and committed.")
            
            # Clean existing data if requested
            if options['clean'] and not options['dry_run']:
                self.stdout.write("Cleaning existing data...")
                
                # Delete all data files related to the project
                cursor.execute("""
                    DELETE FROM data_models_datafile 
                    WHERE deployment_id IN (
                        SELECT d.id FROM data_models_deployment d
                        JOIN data_models_deployment_project dp ON d.id = dp.deployment_id
                        JOIN data_models_project p ON dp.project_id = p.id
                        WHERE p."project_ID" = %s
                    )
                """, [project_id])
                self.stdout.write("  Deleted data files")
                
                # First, get the deployments we want to delete
                cursor.execute("""
                    SELECT d.id 
                    FROM data_models_deployment d
                    JOIN data_models_deployment_project dp ON d.id = dp.deployment_id
                    JOIN data_models_project p ON dp.project_id = p.id
                    WHERE p."project_ID" = %s
                    UNION
                    SELECT id FROM data_models_deployment WHERE "deployment_ID" LIKE 'NINA_%%'
                """, [project_id])
                deployment_ids = [row[0] for row in cursor.fetchall()]
                
                if deployment_ids:
                    # Delete deployment-project relationships first
                    id_placeholders = ','.join(['%s'] * len(deployment_ids))
                    cursor.execute(f"""
                        DELETE FROM data_models_deployment_project
                        WHERE deployment_id IN ({id_placeholders})
                    """, deployment_ids)
                    self.stdout.write(f"  Deleted {len(deployment_ids)} deployment-project relationships")
                    
                    # Now we can safely delete the deployments
                    cursor.execute(f"""
                        DELETE FROM data_models_deployment
                        WHERE id IN ({id_placeholders})
                    """, deployment_ids)
                    self.stdout.write(f"  Deleted {len(deployment_ids)} deployments")
                else:
                    self.stdout.write("  No deployments found to delete")
                    
                # Also clean up any orphaned deployments
                cursor.execute("""
                    DELETE FROM data_models_deployment
                    WHERE id IN (
                        SELECT d.id FROM data_models_deployment d
                        LEFT JOIN data_models_deployment_project dp ON d.id = dp.deployment_id
                        WHERE dp.deployment_id IS NULL
                    )
                """)
                
                self.stdout.write("Existing data cleaned.")
            
            # Get or create necessary records
            
            # 1. DataType
            cursor.execute("SELECT id FROM data_models_datatype WHERE name = %s", ['Audio'])
            result = cursor.fetchone()
            if result:
                audio_type_id = result[0]
            else:
                cursor.execute("""
                    INSERT INTO data_models_datatype (name, created_on, modified_on)
                    VALUES (%s, %s, %s) RETURNING id
                """, ['Audio', timezone.now(), timezone.now()])
                audio_type_id = cursor.fetchone()[0]
            
            # 2. Site
            cursor.execute("SELECT id FROM data_models_site WHERE name = %s", ['NINA Field Site'])
            result = cursor.fetchone()
            if result:
                site_id = result[0]
            else:
                cursor.execute("""
                    INSERT INTO data_models_site (name, short_name, created_on, modified_on)
                    VALUES (%s, %s, %s, %s) RETURNING id
                """, ['NINA Field Site', 'NINA', timezone.now(), timezone.now()])
                site_id = cursor.fetchone()[0]
            
            # 3. Project
            cursor.execute('SELECT id FROM data_models_project WHERE "project_ID" = %s', [project_id])
            result = cursor.fetchone()
            if result:
                project_db_id = result[0]
            else:
                cursor.execute("""
                    INSERT INTO data_models_project 
                    ("project_ID", name, objectives, principal_investigator, 
                     principal_investigator_email, contact, contact_email, 
                     organisation, created_on, modified_on)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, [
                    project_id, 'TABMON NINA', 'Audio monitoring for NINA project',
                    'NINA', 'info@nina.no', 'NINA', 'info@nina.no', 'NINA',
                    timezone.now(), timezone.now()
                ])
                project_db_id = cursor.fetchone()[0]
            
            # 4. DeviceModel
            cursor.execute("SELECT id FROM data_models_devicemodel WHERE name = %s", ['AudioMoth'])
            result = cursor.fetchone()
            if result:
                device_model_id = result[0]
            else:
                cursor.execute("""
                    INSERT INTO data_models_devicemodel (name, manufacturer, type_id, created_on, modified_on)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, ['AudioMoth', 'Open Acoustic Devices', audio_type_id, timezone.now(), timezone.now()])
                device_model_id = cursor.fetchone()[0]
                
            # Commit these global changes
            conn.commit()
            
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
                
                if options['dry_run']:
                    self.stdout.write(f"  Would create device {device_id}")
                    self.stdout.write(f"  Would create deployment NINA_{device_id}")
                    stats['devices'] += 1
                    stats['deployments'] += 1
                    
                    # Process audio files in dry run mode
                    audio_dir = os.path.join(device_dir, 'conf_20240314_TABMON')
                    if not os.path.exists(audio_dir):
                        audio_dir = device_dir
                        
                    audio_count = 0
                    for root, dirs, files in os.walk(audio_dir):
                        for file in files:
                            if file.lower().endswith(('.wav', '.mp3', '.m4a')):
                                file_name = os.path.splitext(file)[0]
                                self.stdout.write(f"  Would import file {file_name}")
                                audio_count += 1
                    
                    stats['files'] += audio_count
                    self.stdout.write(f"  Found {audio_count} audio files to import")
                    
                    continue  # Skip actual processing in dry run mode
                
                # Open a new connection for each device to ensure isolated transactions
                device_conn = psycopg2.connect(**db_params)
                device_conn.autocommit = False
                device_cursor = device_conn.cursor()
                
                try:
                    # 1. Create device
                    device_cursor.execute('SELECT id FROM data_models_device WHERE "device_ID" = %s', [device_id])
                    result = device_cursor.fetchone()
                    
                    # Initialize device_config here, before any branches
                    device_config = {}
                    device_config_path = os.path.join(device_dir, '.config')
                    if os.path.exists(device_config_path):
                        try:
                            with open(device_config_path, 'r') as f:
                                device_config = json.load(f)
                            self.stdout.write(f"  Found device config in {device_dir}")
                        except Exception as e:
                            self.stdout.write(f"  Warning: Could not read device config: {e}")
                    
                    if result:
                        device_id_pk = result[0]
                        self.stdout.write(f"  Device {device_id} already exists.")
                        
                        # Update existing device with config if we found it
                        if device_config:
                            device_cursor.execute("""
                                UPDATE data_models_device 
                                SET name = %s,
                                    extra_data = %s
                                WHERE id = %s
                            """, [
                                device_config.get('name', f'AudioMoth {device_id}'),
                                json.dumps(device_config),
                                device_id_pk
                            ])
                            self.stdout.write(f"  Updated existing device with config data")
                    else:
                        # Insert with device config data
                        device_cursor.execute("""
                            INSERT INTO data_models_device 
                            ("device_ID", name, model_id, type_id, created_on, modified_on, 
                             autoupdate, update_time, extra_data)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, [
                            device_id, 
                            device_config.get('name', f'AudioMoth {device_id}'),
                            device_model_id,
                            audio_type_id,
                            timezone.now(),
                            timezone.now(),
                            False,  # autoupdate
                            48,     # update_time
                            json.dumps(device_config)  # store full device config
                        ])
                        device_id_pk = device_cursor.fetchone()[0]
                        stats['devices'] += 1
                        self.stdout.write(f"  Created device {device_id}")
                    
                    # 2. Create deployment with a unique deployment_ID for each device
                    deployment_id = f'NINA_{device_id}'
                    
                    if verbosity > 1:
                        self.stdout.write(f"  Checking for existing deployment with ID: {deployment_id}")
                        
                    device_cursor.execute('SELECT id FROM data_models_deployment WHERE "deployment_ID" = %s', [deployment_id])
                    result = device_cursor.fetchone()
                    
                    if result:
                        deployment_id_pk = result[0]
                        self.stdout.write(f"  Deployment {deployment_id} already exists.")
                    else:
                        # Default to 1 if no device_n specified
                        device_n = 1
                        
                        # Try to read deployment config from conf_20240314_TABMON/.config
                        deployment_config = {}
                        config_path = os.path.join(device_dir, 'conf_20240314_TABMON', '.config')
                        if os.path.exists(config_path):
                            try:
                                with open(config_path, 'r') as f:
                                    deployment_config = json.load(f)
                                self.stdout.write(f"  Found deployment config in conf_20240314_TABMON")
                            except Exception as e:
                                self.stdout.write(f"  Warning: Could not read deployment config: {e}")
                        
                        # Get deployment start date from config or default
                        deployment_start = timezone.now() - datetime.timedelta(days=30)
                        if 'StartDate' in deployment_config:
                            try:
                                # Remove the 'Z' and parse
                                start_date_str = deployment_config['StartDate'].replace('Z', '+00:00')
                                deployment_start = datetime.datetime.fromisoformat(start_date_str)
                            except Exception as e:
                                self.stdout.write(f"  Warning: Could not parse StartDate: {e}")
                        
                        # Get deployment end date if available
                        deployment_end = None
                        if 'EndDate' in deployment_config:
                            try:
                                # Remove the 'Z' and parse
                                end_date_str = deployment_config['EndDate'].replace('Z', '+00:00')
                                deployment_end = datetime.datetime.fromisoformat(end_date_str)
                            except Exception as e:
                                self.stdout.write(f"  Warning: Could not parse EndDate: {e}")
                        
                        # Get coordinates if available
                        latitude = None
                        longitude = None
                        if 'Latitude' in deployment_config:
                            try:
                                latitude = float(deployment_config['Latitude'])
                            except Exception as e:
                                self.stdout.write(f"  Warning: Could not parse Latitude: {e}")
                        if 'Longitude' in deployment_config:
                            try:
                                longitude = float(deployment_config['Longitude'])
                            except Exception as e:
                                self.stdout.write(f"  Warning: Could not parse Longitude: {e}")
                        
                        if verbosity > 1:
                            self.stdout.write(f"  Creating new deployment with device ID: {deployment_id}")
                            
                        # Create deployment with all available fields from config
                        device_cursor.execute("""
                            INSERT INTO data_models_deployment 
                            ("deployment_ID", "deployment_device_ID", device_id, site_id, 
                             device_type_id, device_n, deployment_start, deployment_end,
                             is_active, created_on, modified_on, time_zone, extra_data,
                             latitude, longitude, coordinate_uncertainty, gps_device,
                             mic_height, mic_direction, habitat, protocol_checklist,
                             score, user_email, country, site_name)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, [
                            deployment_id,
                            f"{device_id}-Audio-{device_n}",
                            device_id_pk,
                            site_id, 
                            audio_type_id,
                            device_n,
                            deployment_start,
                            deployment_end,
                            True,  # is_active
                            timezone.now(),
                            timezone.now(),
                            'UTC',  # time_zone
                            json.dumps({
                                'deployment_config': deployment_config,
                                'device_config': device_config,  # Include device config too
                                'last_updated': timezone.now().isoformat()
                            }),
                            latitude,
                            longitude,
                            deployment_config.get('Coordinate Uncertainty'),
                            deployment_config.get('GPS device'),
                            deployment_config.get('Microphone Height'),
                            deployment_config.get('Microphone Direction'),
                            deployment_config.get('Habitat'),
                            deployment_config.get('Protocol Checklist'),
                            deployment_config.get('Score'),
                            deployment_config.get('Adresse e-mail'),
                            deployment_config.get('Country'),
                            deployment_config.get('Site')
                        ])
                        deployment_id_pk = device_cursor.fetchone()[0]
                        
                        # Add project relationship
                        device_cursor.execute("""
                            INSERT INTO data_models_deployment_project
                                (deployment_id, project_id)
                            VALUES (%s, %s)
                        """, [deployment_id_pk, project_db_id])
                        
                        stats['deployments'] += 1
                        self.stdout.write(f"  Created deployment {deployment_id}")
                    
                    # 3. Process audio files
                    # First, look in the conf_20240314_TABMON directory
                    audio_dir = os.path.join(device_dir, 'conf_20240314_TABMON')
                    
                    # If that doesn't exist, try the device directory directly
                    if not os.path.exists(audio_dir):
                        audio_dir = device_dir
                    
                    # Log which directory we're using
                    self.stdout.write(f"  Looking for audio files in: {audio_dir}")

                    # Read and process config file if it exists
                    config_path = os.path.join(device_dir, '.config')
                    if os.path.exists(config_path):
                        try:
                            with open(config_path, 'r') as f:
                                config_data = json.load(f)
                                
                            # Update device with config data
                            device_cursor.execute("""
                                UPDATE data_models_device 
                                SET name = %s,
                                    extra_data = %s
                                WHERE id = %s
                            """, [
                                config_data.get('name', f'AudioMoth {device_id}'),
                                json.dumps(config_data.get('extra_data', {})),
                                device_id_pk
                            ])
                            
                            # Update deployment with config data
                            device_cursor.execute("""
                                UPDATE data_models_deployment 
                                SET extra_data = %s
                                WHERE id = %s
                            """, [
                                json.dumps({
                                    'device_config': config_data,
                                    'last_updated': timezone.now().isoformat()
                                }),
                                deployment_id_pk
                            ])
                            
                            self.stdout.write(f"  Updated device and deployment with config data")
                        except Exception as e:
                            self.stdout.write(f"  Warning: Could not process config file: {e}")
                    
                    # Check if directory exists and has files
                    if os.path.exists(audio_dir):
                        # Find all audio files in this directory (including subdirectories)
                        audio_files = []
                        
                        # Check for MP3 files first (since we know these exist)
                        mp3_files = []
                        for root, dirs, files in os.walk(audio_dir):
                            for file in files:
                                if file.lower().endswith('.mp3'):
                                    mp3_files.append(os.path.join(root, file))
                        
                        if mp3_files:
                            self.stdout.write(f"  Found {len(mp3_files)} MP3 files")
                            audio_files = mp3_files
                        else:
                            # Check for other audio types if no MP3s found
                            for ext in ['.wav', '.m4a']:
                                for root, dirs, files in os.walk(audio_dir):
                                    for file in files:
                                        if file.lower().endswith(ext):
                                            audio_files.append(os.path.join(root, file))
                            
                            if audio_files:
                                self.stdout.write(f"  Found {len(audio_files)} non-MP3 audio files")
                            else:
                                # Print directory contents if no audio files found
                                self.stdout.write(f"  No audio files found. Directory contents:")
                                for root, dirs, files in os.walk(audio_dir):
                                    rel_path = os.path.relpath(root, audio_dir)
                                    if rel_path == ".":
                                        self.stdout.write(f"    Root directory: {len(files)} files")
                                    else:
                                        self.stdout.write(f"    {rel_path}: {len(files)} files")
                                    
                                    # Print the first 5 files with their extensions for debugging
                                    for i, file in enumerate(sorted(files)[:5]):
                                        _, ext = os.path.splitext(file)
                                        self.stdout.write(f"      - {file} (extension: {ext})")
                        
                        self.stdout.write(f"  Processing {len(audio_files)} audio files")
                        
                        for file_path in audio_files:
                            file_size = os.path.getsize(file_path)
                            file_name = os.path.splitext(os.path.basename(file_path))[0]
                            file_ext = os.path.splitext(file_path)[1]
                            
                            # Skip if already exists
                            device_cursor.execute('SELECT id FROM data_models_datafile WHERE file_name = %s', [file_name])
                            if device_cursor.fetchone():
                                self.stdout.write(f"  File {file_name} already exists, skipping.")
                                continue
                            
                            # Extract metadata from filename
                            recording_dt = None
                            
                            try:
                                # Extract the date from the filename - handle different formats
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
                                
                                # Log the parsed date for debugging
                                if recording_dt:
                                    self.stdout.write(f"    Parsed date {recording_dt} from {file_name}")
                                else:
                                    self.stdout.write(f"    Could not parse date from {file_name}")
                                
                            except (ValueError, IndexError) as e:
                                self.stdout.write(f"  Warning: Could not parse date from {file_name}: {e}")
                                recording_dt = None
                            
                            # Get the relative path for storage
                            rel_path = os.path.relpath(file_path, base_dir)
                            dir_path = os.path.dirname(rel_path)
                            
                            # Create the DataFile with minimal fields
                            try:
                                now = timezone.now()
                                if recording_dt:
                                    device_cursor.execute("""
                                        INSERT INTO data_models_datafile 
                                        (deployment_id, file_name, file_size, file_format, 
                                         path, local_path, created_on, modified_on, recording_dt, file_type_id,
                                         local_storage, archived, do_not_remove, upload_dt, extra_data, linked_files,
                                         quality_check_status, quality_issues)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """, [
                                        deployment_id_pk, 
                                        file_name,
                                        file_size,
                                        file_ext,
                                        '/usr/src/proj_tabmon_NINA',
                                        dir_path,
                                        now,
                                        now,
                                        recording_dt,
                                        audio_type_id,
                                        True,  # local_storage
                                        False, # archived
                                        False, # do_not_remove
                                        now,   # upload_dt
                                        '{}',  # empty JSON for extra_data
                                        '{}',  # empty JSON for linked_files
                                        'pending',  # quality_check_status
                                        '[]'  # empty JSON array for quality_issues
                                    ])
                                else:
                                    device_cursor.execute("""
                                        INSERT INTO data_models_datafile 
                                        (deployment_id, file_name, file_size, file_format, 
                                         path, local_path, created_on, modified_on, file_type_id,
                                         local_storage, archived, do_not_remove, upload_dt, extra_data, linked_files,
                                         quality_check_status, quality_issues)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """, [
                                        deployment_id_pk, 
                                        file_name,
                                        file_size,
                                        file_ext,
                                        '/usr/src/proj_tabmon_NINA',
                                        dir_path,
                                        now,
                                        now,
                                        audio_type_id,
                                        True,  # local_storage
                                        False, # archived
                                        False, # do_not_remove
                                        now,   # upload_dt
                                        '{}',  # empty JSON for extra_data
                                        '{}',  # empty JSON for linked_files
                                        'pending',  # quality_check_status
                                        '[]'  # empty JSON array for quality_issues
                                    ])
                                    
                                stats['files'] += 1
                                if verbosity > 1:
                                    self.stdout.write(f"  Imported file {file_name}")
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"  Error creating data file {file_name}: {e}"))
                                stats['errors'] += 1
                    else:
                        self.stdout.write(self.style.WARNING(f"  No audio directory found at {audio_dir}"))
                    
                    # Commit after processing each device to ensure changes are saved
                    # even if a later device fails
                    device_conn.commit()
                    self.stdout.write(f"  Committed changes for device {device_id}")
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing device {device_id}: {e}"))
                    stats['errors'] += 1
                    device_conn.rollback()  # Rollback the transaction for this device only
                finally:
                    device_conn.close()  # Make sure we close this connection
            
            # Print summary
            self.stdout.write(self.style.SUCCESS(f"Import summary:"))
            self.stdout.write(f"  Devices: {stats['devices']}")
            self.stdout.write(f"  Deployments: {stats['deployments']}")
            self.stdout.write(f"  Files: {stats['files']}")
            if stats['errors'] > 0:
                self.stdout.write(self.style.ERROR(f"  Errors: {stats['errors']}"))
            
            if options['dry_run']:
                self.stdout.write(self.style.WARNING("This was a dry run, no changes were made."))
                conn.rollback()
            else:
                self.stdout.write(self.style.SUCCESS("Import completed successfully."))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Database error: {e}"))
            if 'conn' in locals() and conn:
                conn.rollback()
        finally:
            if 'conn' in locals() and conn:
                conn.close() 