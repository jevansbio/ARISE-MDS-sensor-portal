import os
import shutil
import json
from django.core.management.base import BaseCommand
from django.conf import settings

class FakeGCSBucket:
    """Mimics a GCS bucket using the local filesystem"""
    
    def __init__(self, bucket_name, base_dir=None):
        # Use a directory in file_storage by default
        if base_dir is None:
            base_dir = os.path.join(settings.MEDIA_ROOT, 'fake_gcs')
        
        self.bucket_name = bucket_name
        self.base_dir = os.path.join(base_dir, bucket_name)
        
        # Ensure the bucket directory exists
        os.makedirs(self.base_dir, exist_ok=True)
    
    def blob(self, path):
        """Get a blob (file) from the bucket"""
        return FakeGCSBlob(self, path)
    
    def list_blobs(self, prefix=None):
        """List all blobs in the bucket, optionally filtered by prefix"""
        blobs = []
        
        # Walk through the directory structure
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                # Get the full path and convert to GCS-style path
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, self.base_dir)
                
                # Filter by prefix if specified
                if prefix and not relative_path.startswith(prefix):
                    continue
                
                blobs.append(self.blob(relative_path))
        
        return blobs

class FakeGCSBlob:
    """Mimics a GCS blob (file) using the local filesystem"""
    
    def __init__(self, bucket, name):
        self.bucket = bucket
        self.name = name
        self.full_path = os.path.join(bucket.base_dir, name)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.full_path), exist_ok=True)
    
    def upload_from_filename(self, filename):
        """Upload a file to the blob"""
        shutil.copy2(filename, self.full_path)
        return True
    
    def download_to_filename(self, filename):
        """Download the blob to a file"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        shutil.copy2(self.full_path, filename)
        return True
    
    def delete(self):
        """Delete the blob"""
        if os.path.exists(self.full_path):
            os.remove(self.full_path)
            return True
        return False
    
    def exists(self):
        """Check if the blob exists"""
        return os.path.exists(self.full_path)
    
    def generate_signed_url(self, expiration=None, method='GET'):
        """Generate a fake signed URL (just a path to the file)"""
        # For local dev, we'll just return a URL to the static file
        return f"/file_storage/fake_gcs/{self.bucket.bucket_name}/{self.name}"
    
    @property
    def public_url(self):
        """Return a public URL for the blob"""
        return f"/file_storage/fake_gcs/{self.bucket.bucket_name}/{self.name}"
    
    @property
    def metadata(self):
        """Return fake metadata for the blob"""
        if not os.path.exists(self.full_path):
            return {}
            
        stats = os.stat(self.full_path)
        return {
            'size': stats.st_size,
            'updated': stats.st_mtime,
            'contentType': 'application/octet-stream'
        }

class FakeStorageClient:
    """Mimics the Google Cloud Storage client"""
    
    def __init__(self, base_dir=None):
        # Use a directory in file_storage by default
        if base_dir is None:
            base_dir = os.path.join(settings.MEDIA_ROOT, 'fake_gcs')
        
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Cache for buckets
        self._buckets = {}
    
    def bucket(self, bucket_name):
        """Get a bucket by name"""
        if bucket_name not in self._buckets:
            self._buckets[bucket_name] = FakeGCSBucket(bucket_name, self.base_dir)
        return self._buckets[bucket_name]
    
    def list_buckets(self):
        """List all buckets"""
        buckets = []
        
        # List directories in the base directory
        for item in os.listdir(self.base_dir):
            if os.path.isdir(os.path.join(self.base_dir, item)):
                buckets.append(self.bucket(item))
        
        return buckets
        
    def list_device_buckets(self, base_bucket_name=None):
        """List all device buckets (buckets that start with a prefix)"""
        buckets = []
        
        # List directories in the base directory
        for item in os.listdir(self.base_dir):
            if os.path.isdir(os.path.join(self.base_dir, item)):
                if base_bucket_name is None or item.startswith(f"{base_bucket_name}-"):
                    buckets.append(self.bucket(item))
        
        return buckets

class Command(BaseCommand):
    help = 'Set up fake Google Cloud Storage for local development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--init',
            action='store_true',
            help='Initialize the fake GCS environment',
        )
        parser.add_argument(
            '--list-buckets',
            action='store_true',
            help='List all buckets in the fake GCS environment',
        )
        parser.add_argument(
            '--list-device-buckets',
            action='store_true',
            help='List all device buckets in the fake GCS environment',
        )
        parser.add_argument(
            '--base-bucket',
            type=str,
            help='Base bucket name for device buckets (e.g. "audio-files")',
        )
        parser.add_argument(
            '--create-bucket',
            type=str,
            help='Create a new bucket in the fake GCS environment',
        )
        parser.add_argument(
            '--list-files',
            type=str,
            help='List all files in a bucket',
        )
        parser.add_argument(
            '--upload-file',
            type=str,
            help='Upload a file to a bucket',
        )
        parser.add_argument(
            '--bucket',
            type=str,
            help='Bucket name for operations',
        )
        parser.add_argument(
            '--destination',
            type=str,
            help='Destination path in bucket',
        )

    def handle(self, *args, **options):
        # Create storage client
        client = FakeStorageClient()
        
        if options['init']:
            # Set up fake GCS environment
            self.stdout.write('Initializing fake GCS environment...')
            
            # Create a config file to store settings
            config = {
                'base_dir': client.base_dir,
                'initialized': True
            }
            
            config_path = os.path.join(client.base_dir, 'config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.stdout.write(self.style.SUCCESS(f'Fake GCS initialized at {client.base_dir}'))
            
            # Create some default buckets
            default_buckets = ['audio-files', 'sensor-data', 'user-uploads']
            for bucket_name in default_buckets:
                client.bucket(bucket_name)
                self.stdout.write(f'Created bucket: {bucket_name}')
            
            self.stdout.write(self.style.SUCCESS('Done!'))
        
        elif options['list_buckets']:
            # List all buckets
            buckets = client.list_buckets()
            
            if not buckets:
                self.stdout.write('No buckets found')
                return
            
            self.stdout.write('Buckets:')
            for bucket in buckets:
                self.stdout.write(f'  - {bucket.bucket_name}')
                
        elif options['list_device_buckets']:
            # List all device buckets
            base_bucket = options['base_bucket']
            buckets = client.list_device_buckets(base_bucket)
            
            if not buckets:
                if base_bucket:
                    self.stdout.write(f'No device buckets found with prefix {base_bucket}-')
                else:
                    self.stdout.write('No device buckets found')
                return
            
            self.stdout.write('Device Buckets:')
            for bucket in buckets:
                self.stdout.write(f'  - {bucket.bucket_name}')
                
                # Count files in each bucket
                blobs = bucket.list_blobs()
                file_count = len(list(blobs))
                self.stdout.write(f'    ({file_count} files)')
        
        elif options['create_bucket']:
            # Create a new bucket
            bucket_name = options['create_bucket']
            bucket = client.bucket(bucket_name)
            self.stdout.write(self.style.SUCCESS(f'Created bucket: {bucket_name}'))
        
        elif options['list_files']:
            # List all files in a bucket
            bucket_name = options['list_files']
            bucket = client.bucket(bucket_name)
            blobs = bucket.list_blobs()
            
            if not blobs:
                self.stdout.write(f'No files found in bucket: {bucket_name}')
                return
            
            self.stdout.write(f'Files in bucket {bucket_name}:')
            for blob in blobs:
                self.stdout.write(f'  - {blob.name} ({blob.metadata.get("size", "unknown")} bytes)')
        
        elif options['upload_file']:
            # Upload a file to a bucket
            file_path = options['upload_file']
            
            if not os.path.exists(file_path):
                self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
                return
            
            bucket_name = options['bucket']
            if not bucket_name:
                self.stdout.write(self.style.ERROR('Bucket name required'))
                return
            
            destination = options['destination']
            if not destination:
                destination = os.path.basename(file_path)
            
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(destination)
            blob.upload_from_filename(file_path)
            
            self.stdout.write(self.style.SUCCESS(
                f'Uploaded {file_path} to {bucket_name}/{destination}'
            ))
        
        else:
            self.stdout.write('Use --help to see available commands') 