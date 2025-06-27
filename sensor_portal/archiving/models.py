import logging
import os
from posixpath import join as posixjoin

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone as djtimezone
from encrypted_model_fields.fields import EncryptedCharField
from utils.general import try_remove_file_clean_dirs
from utils.models import BaseModel
from utils.ssh_client import SSH_client

logger = logging.getLogger(__name__)


class Archive(BaseModel):
    name = models.CharField(
        max_length=200,
        help_text="A human-readable name for this archive."
    )
    username = models.CharField(
        max_length=50,
        unique=True,
        help_text="Username for SSH login to the archive server."
    )
    password = EncryptedCharField(
        max_length=128,
        help_text="Password for SSH login to the archive server. Stored encrypted."
    )
    address = models.CharField(
        max_length=100,
        unique=True,
        help_text="Network address of the archive server."
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="owned_archives",
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who owns this archive."
    )
    root_folder = models.CharField(
        max_length=100,
        unique=True,
        help_text="Root folder path on the archive server."
    )

    def __str__(self) -> str:
        """Return the name of the archive."""
        return self.name

    def init_ssh_client(self) -> SSH_client:
        """Initialize an SSH client for this archive."""
        return SSH_client(self.username, self.password, self.address, 22)

    def check_projects(self) -> None:
        """Check and update archive projects."""
        from .functions import check_archive_projects
        check_archive_projects(self)

    def check_upload(self) -> None:
        """Check and update archive uploads."""
        from .functions import check_archive_upload
        check_archive_upload(self)


class TarFile(BaseModel):
    name = models.CharField(
        max_length=200,
        help_text="Filename of the TAR archive (without extension)."
    )
    archived_dt = models.DateTimeField(
        default=djtimezone.now,
        help_text="Datetime this TAR was archived."
    )
    uploading = models.BooleanField(
        default=False,
        help_text="True if the TAR is currently uploading."
    )
    local_storage = models.BooleanField(
        default=True,
        help_text="True if the TAR is stored locally."
    )
    archived = models.BooleanField(
        default=False,
        help_text="True if the TAR is archived remotely."
    )
    path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Filesystem path to the TAR archive."
    )
    archive = models.ForeignKey(
        Archive,
        related_name="tar_files",
        on_delete=models.PROTECT,
        null=True,
        help_text="Archive to which this TAR file belongs."
    )

    def __str__(self) -> str:
        """Return the name of the TAR file."""
        return self.name

    def clean_tar(self, delete_obj: bool = False, force_delete: bool = False) -> bool:
        """
        Remove the TAR file from storage and update the database accordingly.

        Args:
            delete_obj (bool): If True, delete the database object.
            force_delete (bool): If True, force deletion even if errors occur.

        Returns:
            bool: True if successful, False otherwise.
        """
        logger.info(
            f"Clean TAR file {self.name} - Delete object: {delete_obj}")
        if not self.local_storage and not self.archived and not self.uploading:
            logger.info(
                f"Clean TAR file {self.name} - object exists only in database")
            return True
        if self.local_storage:
            tar_name = self.name
            if ".tar.gz" not in tar_name:
                tar_name = tar_name + ".tar.gz"
            tar_path = os.path.join(
                settings.FILE_STORAGE_ROOT, self.path, tar_name)
            logger.info(
                f"Clean TAR file {self.name} - try to delete local TAR")

            success = try_remove_file_clean_dirs(tar_path)

            if not success and not force_delete:
                logger.error(
                    f"Clean TAR file {self.name} - failed - could not delete local TAR")
                return False
            elif success:
                logger.info(
                    f"Clean TAR file {self.name} - try to delete local TAR - success")

            if not delete_obj:
                logger.info(
                    f"Clean TAR file {self.name} - Alter database object")
                self.local_storage = False
                self.save()

            return True

        elif not self.local_storage and delete_obj and force_delete:
            if not all(self.files.values_list("local_storage", flat=True)):
                logger.error(
                    f"{self.name}: Some files contained in this TAR are no longer stored locally. The remote TAR cannot be deleted.")
                return False
            self.files.all().update(archived=False)
            ssh_client = self.archive.init_ssh_client()
            ssh_connect_success = ssh_client.connect_to_ssh()
            if not ssh_connect_success:
                return False
            remote_path = posixjoin(self.path, self.name + ".tar.gz")
            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"rm {remote_path}")
            if status_code != 0:
                remote_path = posixjoin(self.path, self.name)
                status_code, stdout, stderr = ssh_client.send_ssh_command(
                    f"rm {remote_path}")
            if status_code != 0:
                logger.info(f"{self.name}: Cannot remove remote TAR. {stdout}")
                return False
            else:
                logger.info(f"{self.name}: Remote TAR removed.")
                status_code, stdout, stderr = ssh_client.send_ssh_command(
                    f"find {self.path} -type d -empty -delete")
                return True
        else:
            return False


@receiver(pre_delete, sender=TarFile)
def pre_remove_tar(sender, instance: "TarFile", **kwargs) -> None:
    """
    Signal handler to clean up TAR file storage before deleting the TarFile instance.

    Raises:
        Exception: If cleanup fails.
    """
    success = instance.clean_tar(True)
    if not success:
        raise Exception(f"Unable to remove TAR file {instance.name}")
