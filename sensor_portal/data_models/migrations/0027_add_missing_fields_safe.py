from django.db import migrations, models

def check_and_add_columns(apps, schema_editor):
    connection = schema_editor.connection

    def column_exists(table, column):
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s;
            ''', [table, column])
            return cursor.fetchone() is not None

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

    # Device table columns
    device_columns = [
        ('start_date', 'timestamp with time zone NULL'),
        ('end_date', 'timestamp with time zone NULL'),
        ('battery_level', 'float NULL'),
        ('autoupdate', 'boolean NULL'),
        ('update_time', 'integer NULL'),
        ('coordinate_uncertainty', 'varchar(100) NULL'),
        ('gps_device', 'varchar(100) NULL'),
        ('mic_height', 'float NULL'),
        ('mic_direction', 'varchar(100) NULL'),
        ('habitat', 'varchar(100) NULL'),
        ('protocol_checklist', 'varchar(255) NULL'),
        ('score', 'float NULL'),
        ('comment', 'text NULL'),
        ('user_email', 'varchar(254) NULL'),
        ('country', 'varchar(100) NULL'),
        ('site_name', 'varchar(100) NULL'),
        ('username', 'varchar(100) NULL'),
        ('extra_data', "jsonb NULL DEFAULT '{}'"),
    ]

    # Deployment table columns (same as device)
    deployment_columns = device_columns.copy()

    # DataFile table columns
    datafile_columns = [
        ('config', 'varchar(100) NULL'),
        ('sample_rate', 'integer NULL'),
        ('file_length', 'varchar(50) NULL'),
        ('extra_data', "jsonb NULL DEFAULT '{}'"),
        ('linked_files', "jsonb NULL DEFAULT '{}'"),
        ('thumb_url', 'varchar(500) NULL'),
        ('local_storage', 'boolean NULL DEFAULT true'),
        ('archived', 'boolean NULL DEFAULT false'),
        ('do_not_remove', 'boolean NULL DEFAULT false'),
        ('original_name', 'varchar(100) NULL'),
        ('file_url', 'varchar(500) NULL'),
        ('tag', 'varchar(250) NULL'),
    ]

    for column, definition in device_columns:
        add_column_if_missing('data_models_device', column, definition)

    for column, definition in deployment_columns:
        add_column_if_missing('data_models_deployment', column, definition)

    for column, definition in datafile_columns:
        add_column_if_missing('data_models_datafile', column, definition)


class Migration(migrations.Migration):
    dependencies = [
        ('data_models', '0026_auto_20250325_0945'),
    ]

    operations = [
        migrations.RunPython(check_and_add_columns),
    ]
