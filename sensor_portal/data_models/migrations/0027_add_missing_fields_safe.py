# Generated manually to fix schema issues
from django.db import migrations, models

def check_and_add_columns(apps, schema_editor):
    # Get the database connection
    connection = schema_editor.connection
    
    # Helper function to check if column exists
    def column_exists(table, column):
        with connection.cursor() as cursor:
            cursor.execute(f'''
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table}' 
            AND column_name = '{column}';
            ''')
            return cursor.fetchone() is not None
    
    # Helper function to add column if it doesn't exist
    def add_column_if_missing(table, column, definition):
        if not column_exists(table, column):
            with connection.cursor() as cursor:
                cursor.execute(f'''
                ALTER TABLE {table} 
                ADD COLUMN {column} {definition};
                ''')
                print(f'Added column {column} to {table}')
        else:
            print(f'Column {column} already exists in {table}')
    
    # Add missing columns to device table
    add_column_if_missing('data_models_device', 'start_date', 'timestamp with time zone NULL')
    add_column_if_missing('data_models_device', 'end_date', 'timestamp with time zone NULL')
    add_column_if_missing('data_models_device', 'battery_level', 'float NULL')
    add_column_if_missing('data_models_device', 'autoupdate', 'boolean NULL')
    add_column_if_missing('data_models_device', 'update_time', 'integer NULL')
    add_column_if_missing('data_models_device', 'coordinate_uncertainty', 'varchar(100) NULL')
    add_column_if_missing('data_models_device', 'gps_device', 'varchar(100) NULL')
    add_column_if_missing('data_models_device', 'mic_height', 'float NULL')
    add_column_if_missing('data_models_device', 'mic_direction', 'varchar(100) NULL')
    add_column_if_missing('data_models_device', 'habitat', 'varchar(100) NULL')
    add_column_if_missing('data_models_device', 'protocol_checklist', 'varchar(255) NULL')
    add_column_if_missing('data_models_device', 'score', 'float NULL')
    add_column_if_missing('data_models_device', 'comment', 'text NULL')
    add_column_if_missing('data_models_device', 'user_email', 'varchar(254) NULL')
    add_column_if_missing('data_models_device', 'country', 'varchar(100) NULL')
    add_column_if_missing('data_models_device', 'site_name', 'varchar(100) NULL')
    add_column_if_missing('data_models_device', 'username', 'varchar(100) NULL')
    add_column_if_missing('data_models_device', 'extra_data', 'jsonb NULL DEFAULT \'{}\' ')
    
    # Add missing columns to deployment table
    add_column_if_missing('data_models_deployment', 'battery_level', 'float NULL')
    add_column_if_missing('data_models_deployment', 'autoupdate', 'boolean NULL')
    add_column_if_missing('data_models_deployment', 'update_time', 'integer NULL')
    add_column_if_missing('data_models_deployment', 'coordinate_uncertainty', 'varchar(100) NULL')
    add_column_if_missing('data_models_deployment', 'gps_device', 'varchar(100) NULL')
    add_column_if_missing('data_models_deployment', 'mic_height', 'float NULL')
    add_column_if_missing('data_models_deployment', 'mic_direction', 'varchar(100) NULL')
    add_column_if_missing('data_models_deployment', 'habitat', 'varchar(100) NULL')
    add_column_if_missing('data_models_deployment', 'protocol_checklist', 'varchar(255) NULL')
    add_column_if_missing('data_models_deployment', 'score', 'float NULL')
    add_column_if_missing('data_models_deployment', 'comment', 'text NULL')
    add_column_if_missing('data_models_deployment', 'user_email', 'varchar(254) NULL')
    add_column_if_missing('data_models_deployment', 'country', 'varchar(100) NULL')
    add_column_if_missing('data_models_deployment', 'site_name', 'varchar(100) NULL')
    add_column_if_missing('data_models_deployment', 'username', 'varchar(100) NULL')
    add_column_if_missing('data_models_deployment', 'extra_data', 'jsonb NULL DEFAULT \'{}\' ')


class Migration(migrations.Migration):
    dependencies = [
        ('data_models', '0026_auto_20250325_0945'),
    ]

    operations = [
        migrations.RunPython(check_and_add_columns),
    ]
