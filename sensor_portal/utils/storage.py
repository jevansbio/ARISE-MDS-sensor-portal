import os
from django.conf import settings

# Try to import the real GCS libraries, but fall back to our fake implementation if not available
try:
    from google.cloud import storage as google_storage
    from google.cloud.exceptions import NotFound
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    
# Import our fake implementation
from data_models.management.commands.fake_gcs import FakeStorageClient

def get_storage_client():
    """
    Get a storage client - either real GCS or our fake implementation
    based on settings and available libraries.
    """
    if settings.DEBUG and getattr(settings, 'USE_FAKE_GCS', True):
        # Use our fake implementation for local development
        return FakeStorageClient()
    elif GCS_AVAILABLE:
        # Use real GCS in production or if specifically configured
        return google_storage.Client()
    else:
        # Fallback to fake implementation if real one is not available
        return FakeStorageClient()

def get_bucket(bucket_name):
    """Get a bucket by name"""
    client = get_storage_client()
    return client.bucket(bucket_name)

def get_device_bucket(device_id, base_bucket_name=None):
    """
    Get a device-specific bucket
    
    Args:
        device_id: Device ID to get bucket for
        base_bucket_name: Base bucket name to prefix (default from settings)
    
    Returns:
        Device-specific bucket
    """
    if base_bucket_name is None:
        base_bucket_name = settings.GCS_BUCKET_NAME
        
    bucket_name = f"{base_bucket_name}-{device_id}"
    return get_bucket(bucket_name)

def list_device_buckets(base_bucket_name=None):
    """
    List all device buckets
    
    Args:
        base_bucket_name: Base bucket name to filter by
    
    Returns:
        List of device buckets
    """
    client = get_storage_client()
    if hasattr(client, 'list_device_buckets'):
        return client.list_device_buckets(base_bucket_name)
    else:
        # If using real GCS, filter bucket list
        all_buckets = client.list_buckets()
        if base_bucket_name:
            return [b for b in all_buckets if b.name.startswith(f"{base_bucket_name}-")]
        else:
            return all_buckets

def get_blob(bucket_name, blob_name):
    """Get a blob (file) from a bucket"""
    bucket = get_bucket(bucket_name)
    return bucket.blob(blob_name)

def get_device_blob(device_id, blob_name, base_bucket_name=None):
    """
    Get a blob from a device-specific bucket
    
    Args:
        device_id: Device ID
        blob_name: Name of the blob
        base_bucket_name: Base bucket name (default from settings)
    
    Returns:
        Blob object
    """
    device_bucket = get_device_bucket(device_id, base_bucket_name)
    return device_bucket.blob(blob_name)

def upload_file(source_file_path, bucket_name, destination_blob_name=None):
    """
    Upload a file to a GCS bucket
    
    Args:
        source_file_path: Path to the file to upload
        bucket_name: Name of the bucket to upload to
        destination_blob_name: Name to give the file in GCS (default: use source filename)
    
    Returns:
        The public URL of the uploaded file
    """
    if destination_blob_name is None:
        destination_blob_name = os.path.basename(source_file_path)
    
    blob = get_blob(bucket_name, destination_blob_name)
    blob.upload_from_filename(source_file_path)
    
    return blob.public_url

def upload_file_to_device_bucket(source_file_path, device_id, destination_blob_name=None, base_bucket_name=None):
    """
    Upload a file to a device-specific bucket
    
    Args:
        source_file_path: Path to the file to upload
        device_id: Device ID to upload for
        destination_blob_name: Name to give the file in GCS (default: use source filename)
        base_bucket_name: Base bucket name (default from settings)
    
    Returns:
        The public URL of the uploaded file
    """
    device_bucket = get_device_bucket(device_id, base_bucket_name)
    if destination_blob_name is None:
        destination_blob_name = os.path.basename(source_file_path)
    
    blob = device_bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_path)
    
    return blob.public_url

def download_file(bucket_name, source_blob_name, destination_file_path):
    """
    Download a file from a GCS bucket
    
    Args:
        bucket_name: Name of the bucket to download from
        source_blob_name: Name of the file in GCS
        destination_file_path: Path to save the file to
    
    Returns:
        True if successful, False otherwise
    """
    blob = get_blob(bucket_name, source_blob_name)
    
    if not blob.exists():
        return False
    
    blob.download_to_filename(destination_file_path)
    return True

def list_files(bucket_name, prefix=None):
    """
    List all files in a bucket, optionally filtered by prefix
    
    Args:
        bucket_name: Name of the bucket to list files from
        prefix: Optional prefix to filter files by
    
    Returns:
        List of blob objects
    """
    bucket = get_bucket(bucket_name)
    return list(bucket.list_blobs(prefix=prefix))

def delete_file(bucket_name, blob_name):
    """
    Delete a file from a bucket
    
    Args:
        bucket_name: Name of the bucket to delete from
        blob_name: Name of the file to delete
    
    Returns:
        True if successful, False otherwise
    """
    blob = get_blob(bucket_name, blob_name)
    
    if not blob.exists():
        return False
    
    return blob.delete()

def get_signed_url(bucket_name, blob_name, expiration=3600):
    """
    Get a signed URL for a file
    
    Args:
        bucket_name: Name of the bucket
        blob_name: Name of the file
        expiration: Expiration time in seconds (default: 1 hour)
    
    Returns:
        Signed URL for the file
    """
    blob = get_blob(bucket_name, blob_name)
    
    if not blob.exists():
        return None
    
    return blob.generate_signed_url(expiration=expiration) 