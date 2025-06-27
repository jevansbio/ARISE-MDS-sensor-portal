import os

from data_models.models import DataFile
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from utils.general import try_remove_file_clean_dirs
from utils.models import BaseModel

from .create_zip_functions import create_zip

# Create your models here.

status = (
    (0, 'Started'),
    (1, 'Unarchiving'),
    (2, 'Creating bundle'),
    (3, 'Ready'),
    (4, 'Failed'),
)

metadata_type = (
    (0, 'base'),
    (1, 'Camera trap DP'),
    (2, 'COCO'),
)


class DataPackage(BaseModel):
    """
    Model representing a data package, containing files and metadata for download or processing.
    """
    name = models.CharField(
        max_length=200,
        help_text="The name of the data package."
    )
    data_files = models.ManyToManyField(
        DataFile,
        related_name="data_bundles",
        help_text="The data files included in this package."
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="data_bundles",
        on_delete=models.SET_NULL,
        null=True,
        help_text="The user who owns this data package."
    )
    status = models.IntegerField(
        choices=status,
        default=0,
        help_text="The current status of the data package."
    )
    metadata_type = models.IntegerField(
        choices=metadata_type,
        default=0,
        help_text="The type of metadata associated with this package."
    )
    includes_files = models.BooleanField(
        default=True,
        help_text="Whether the package includes files."
    )
    file_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL to download the zipped data package."
    )

    def set_file_url(self) -> None:
        """
        Set the file URL if the data package is ready.
        """
        if self.status == 3:
            zip_name = self.name
            if "zip" not in zip_name:
                zip_name += ".zip"
            self.file_url = os.path.normpath(
                os.path.join(
                    settings.FILE_STORAGE_URL,
                    settings.PACKAGE_PATH,
                    zip_name
                )
            ).replace("\\", "/")
        else:
            self.file_url = None

    def __str__(self) -> str:
        """
        Return the name of the data package.
        """
        return self.name

    def make_zip(self) -> None:
        """
        Create a zip archive of the data files and update status.
        """
        create_zip(self.name, self.data_files,
                   self.metadata_type, self.includes_files)
        self.status = 3
        self.save()

    def save(self, *args, **kwargs) -> None:
        """
        Override save to always update the file URL before saving.
        """
        self.set_file_url()
        super().save(*args, **kwargs)

    def clean_data_package(self) -> bool:
        """
        Remove the data package file from storage if ready or failed.

        Returns:
            bool: True if deletion was successful or unnecessary, False otherwise.
        """
        if self.status == 3:
            package_path = os.path.join(
                settings.FILE_STORAGE_ROOT, settings.PACKAGE_PATH)
            try_remove_file_clean_dirs(
                os.path.join(package_path, self.name+"zip"))
            return True
        elif self.status == 4:
            return True
        else:
            return False


@receiver(pre_delete, sender=DataPackage)
def pre_remove_bundle(sender, instance: DataPackage, **kwargs) -> None:
    """
    Signal handler to remove related files when a DataPackage is deleted.

    Raises:
        Exception: If the data package could not be removed.
    """
    success = instance.clean_data_package()
    if not success:
        raise Exception(f"Could not remove data package {instance.name}")
