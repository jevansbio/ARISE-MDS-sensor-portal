import os
import datetime
import psycopg2
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
        
        # Connect to the database
        try:
            conn = psycopg2.connect(**db_params)
            conn.autocommit = False  # Start a transaction
            cursor = conn.cursor()
            
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
            
            # Clean existing data if requested
            if options['clean'] and not options['dry_run']:
                self.stdout.write("Cleaning existing data...")
                cursor.execute("""
                    DELETE FROM data_models_datafile 
                    WHERE deployment_id IN (
                        SELECT d.id FROM data_models_deployment d
                        JOIN data_models_deployment_project dp ON d.id = dp.deployment_id
                        JOIN data_models_project p ON dp.project_id = p.id
                        WHERE p."project_ID" = %s
                    )
                """, [project_id])
                
                cursor.execute("""
                    DELETE FROM data_models_deployment_project
                    WHERE project_id IN (
                        SELECT id FROM data_models_project
                        WHERE "project_ID" = %s
                    )
                """, [project_id])
                
                cursor.execute("""
                    DELETE FROM data_models_deployment
                    WHERE id IN (
                        SELECT d.id FROM data_models_deployment d
                        LEFT JOIN data_models_deployment_project dp ON d.id = dp.deployment_id
                        WHERE dp.deployment_id IS NULL
                    )
                """)
            
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
                    self.stdout.write(f"  Would create deployment NINA_{device_id[:5]}")
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
                
                try:
                    # 1. Create device
                    cursor.execute('SELECT id FROM data_models_device WHERE "device_ID" = %s', [device_id])
                    result = cursor.fetchone()
                    
                    if result:
                        device_id_pk = result[0]
                        self.stdout.write(f"  Device {device_id} already exists.")
                    else:
                        # Insert with explicit defaults for problematic fields
                        cursor.execute("""
                            INSERT INTO data_models_device 
                            ("device_ID", name, model_id, type_id, created_on, modified_on, 
                             autoupdate, update_time)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, [
                            device_id, 
                            f'AudioMoth {device_id}',
                            device_model_id,
                            audio_type_id,
                            timezone.now(),
                            timezone.now(),
                            False,  # autoupdate
                            48      # update_time
                        ])
                        device_id_pk = cursor.fetchone()[0]
                        stats['devices'] += 1
                        self.stdout.write(f"  Created device {device_id}")
                    
                    # 2. Create deployment
                    deployment_id = f'NINA_{device_id[:5]}'
                    cursor.execute('SELECT id FROM data_models_deployment WHERE "deployment_ID" = %s', [deployment_id])
                    result = cursor.fetchone()
                    
                    if result:
                        deployment_id_pk = result[0]
                        self.stdout.write(f"  Deployment {deployment_id} already exists.")
                    else:
                        # Create deployment with minimal fields and explicit defaults
                        cursor.execute("""
                            INSERT INTO data_models_deployment 
                            ("deployment_ID", "deployment_device_ID", device_id, site_id, 
                             device_type_id, device_n, deployment_start, is_active, 
                             created_on, modified_on, time_zone)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, [
                            deployment_id,
                            f"{device_id}-{deployment_id}",
                            device_id_pk,
                            site_id, 
                            audio_type_id,
                            1,  # device_n
                            timezone.now() - datetime.timedelta(days=30),
                            True,  # is_active
                            timezone.now(),
                            timezone.now(),
                            'UTC'  # Add default time_zone
                        ])
                        deployment_id_pk = cursor.fetchone()[0]
                        
                        # Add project relationship
                        cursor.execute("""
                            INSERT INTO data_models_deployment_project
                                (deployment_id, project_id)
                            VALUES (%s, %s)
                        """, [deployment_id_pk, project_db_id])
                        
                        stats['deployments'] += 1
                        self.stdout.write(f"  Created deployment {deployment_id}")
                    
                    # 3. Process audio files
                    audio_dir = os.path.join(device_dir, 'conf_20240314_TABMON')
                    if not os.path.exists(audio_dir):
                        audio_dir = device_dir  # Fallback to device directory if conf dir doesn't exist
                    
                    # Check if directory exists and has files
                    if os.path.exists(audio_dir):
                        self.stdout.write(f"  Found audio directory at {audio_dir}")
                        
                        # Find all audio files in this directory (including subdirectories)
                        audio_files = []
                        for root, dirs, files in os.walk(audio_dir):
                            for file in files:
                                if file.lower().endswith(('.wav', '.mp3', '.m4a')):
                                    audio_files.append(os.path.join(root, file))
                        
                        self.stdout.write(f"  Found {len(audio_files)} audio files")
                        
                        for file_path in audio_files:
                            file_size = os.path.getsize(file_path)
                            file_name = os.path.splitext(os.path.basename(file_path))[0]
                            file_ext = os.path.splitext(file_path)[1]
                            
                            # Skip if already exists
                            cursor.execute('SELECT id FROM data_models_datafile WHERE file_name = %s', [file_name])
                            if cursor.fetchone():
                                self.stdout.write(f"  File {file_name} already exists, skipping.")
                                continue
                            
                            # Extract metadata from filename
                            recording_dt = None
                            
                            try:
                                # Our files follow the format: 2024-05-16T17_49_40.549Z.m4a
                                # Extract the date and time from this format
                                dt_part = file_name
                                
                                # Remove the .m4a if it's somehow in the filename
                                if dt_part.endswith('.m4a'):
                                    dt_part = dt_part[:-4]
                                    
                                # Convert from ISO-like format
                                if 'T' in dt_part and 'Z' in dt_part:
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
                                    
                                    # Format date part - replace hyphens with hyphens (already correct)
                                    date_part = date_part.replace('-', '-')
                                    
                                    # Create datetime object
                                    iso_dt = f"{date_part}T{time_part}"
                                    recording_dt = datetime.datetime.fromisoformat(iso_dt)
                                    recording_dt = recording_dt.replace(tzinfo=timezone.get_current_timezone())
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
                                    cursor.execute("""
                                        INSERT INTO data_models_datafile 
                                        (deployment_id, file_name, file_size, file_format, 
                                         path, local_path, created_on, modified_on, recording_dt, file_type_id,
                                         local_storage, archived, do_not_remove, upload_dt)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                                        now    # upload_dt
                                    ])
                                else:
                                    cursor.execute("""
                                        INSERT INTO data_models_datafile 
                                        (deployment_id, file_name, file_size, file_format, 
                                         path, local_path, created_on, modified_on, file_type_id,
                                         local_storage, archived, do_not_remove, upload_dt)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                                        now    # upload_dt
                                    ])
                                    
                                stats['files'] += 1
                                self.stdout.write(f"  Imported file {file_name}")
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"  Error creating data file {file_name}: {e}"))
                                stats['errors'] += 1
                    else:
                        self.stdout.write(self.style.WARNING(f"  No audio directory found at {audio_dir}"))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing device {device_id}: {e}"))
                    stats['errors'] += 1
                    conn.rollback()  # Rollback the transaction for this device
                    
            # Commit all changes
            conn.commit()
            
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