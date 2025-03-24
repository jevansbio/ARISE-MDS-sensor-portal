import psycopg2
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Fix database constraints by dropping NOT NULL constraints on problematic columns'

    def handle(self, *args, **options):
        # Database connection params from Django settings
        db_params = {
            'dbname': settings.DATABASES['default']['NAME'],
            'user': settings.DATABASES['default']['USER'],
            'password': settings.DATABASES['default']['PASSWORD'],
            'host': settings.DATABASES['default']['HOST'] or 'localhost',
            'port': settings.DATABASES['default']['PORT'] or '5432'
        }
        
        # Connect to the database
        try:
            conn = psycopg2.connect(**db_params)
            conn.autocommit = True  # We want each statement to be committed immediately
            cursor = conn.cursor()
            
            # First, list all columns and their constraints for our troublesome tables
            self.stdout.write("Checking current column constraints...")
            
            tables = ['data_models_device', 'data_models_deployment', 'data_models_datafile']
            
            for table in tables:
                cursor.execute(f"""
                    SELECT column_name, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                    ORDER BY column_name
                """)
                columns = cursor.fetchall()
                self.stdout.write(f"\nTable: {table}")
                self.stdout.write("Column | Nullable")
                self.stdout.write("-----------------")
                for col in columns:
                    self.stdout.write(f"{col[0]} | {col[1]}")
            
            # Now let's fix all the known problematic fields
            self.stdout.write("\nDropping NOT NULL constraints...")
            
            # Common fields across tables
            fields_to_fix = [
                ('data_models_device', 'extra_data'),
                ('data_models_deployment', 'extra_data'),
                ('data_models_datafile', 'extra_data'),
                ('data_models_datafile', 'linked_files'),
                ('data_models_deployment', 'time_zone')
            ]
            
            for table, column in fields_to_fix:
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table} 
                        ALTER COLUMN {column} DROP NOT NULL;
                    """)
                    self.stdout.write(f"✓ Fixed {table}.{column}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error fixing {table}.{column}: {e}"))
            
            # Also provide default values for some fields that are likely causing issues
            default_values = [
                ('data_models_deployment', 'time_zone', "'UTC'"),
                ('data_models_device', 'extra_data', "'{}'::jsonb"),
                ('data_models_deployment', 'extra_data', "'{}'::jsonb"),
                ('data_models_datafile', 'extra_data', "'{}'::jsonb"),
                ('data_models_datafile', 'linked_files', "'{}'::jsonb")
            ]
            
            self.stdout.write("\nSetting default values for NULL fields...")
            
            for table, column, default in default_values:
                try:
                    cursor.execute(f"""
                        UPDATE {table} 
                        SET {column} = {default}
                        WHERE {column} IS NULL;
                    """)
                    rows_updated = cursor.rowcount
                    self.stdout.write(f"✓ Updated {rows_updated} rows in {table}.{column} with default value")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error setting default for {table}.{column}: {e}"))
            
            # Print updated constraints
            self.stdout.write("\nUpdated constraints:")
            
            for table in tables:
                cursor.execute(f"""
                    SELECT column_name, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                    ORDER BY column_name
                """)
                columns = cursor.fetchall()
                self.stdout.write(f"\nTable: {table}")
                self.stdout.write("Column | Nullable")
                self.stdout.write("-----------------")
                for col in columns:
                    self.stdout.write(f"{col[0]} | {col[1]}")
                
            self.stdout.write(self.style.SUCCESS("\nConstraints fixed successfully!"))
            self.stdout.write("\nNow you can run the import command again:")
            self.stdout.write("docker compose -f docker-compose-dev.yml exec sensor_portal_django python manage.py direct_audio_import")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Database error: {e}"))
        finally:
            if 'conn' in locals() and conn:
                conn.close() 