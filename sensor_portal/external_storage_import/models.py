import io
import logging
from datetime import datetime, timedelta
from posixpath import join, splitext

from data_models.file_handling_functions import create_file_objects
from django.conf import settings
from django.core.files import File
from django.db import models
from encrypted_model_fields.fields import EncryptedCharField
from utils.models import BaseModel
from utils.ssh_client import SSH_client

logger = logging.getLogger(__name__)


class DataStorageInput(BaseModel):
    """
    Model representing an external data storage input for sensor data import.
    Manages connection credentials and provides utilities for user and file management.
    """
    name = models.CharField(
        max_length=20,
        unique=True,
        help_text="A unique name for this data storage input."
    )
    username = models.CharField(
        max_length=50,
        unique=True,
        help_text="Username for accessing the external storage."
    )
    password = EncryptedCharField(
        max_length=128,
        help_text="Encrypted password for the storage username."
    )
    address = models.CharField(
        max_length=100,
        unique=True,
        help_text="Network address (IP or hostname) of the external storage."
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="owned_inputstorages",
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who owns this data storage input."
    )

    def __str__(self) -> str:
        """
        Return the string representation of the storage input.
        """
        return self.name

    def init_ssh_client(self) -> 'SSH_client':
        """
        Initialize and return an SSH client for the storage input.
        """
        return SSH_client(self.username, self.password, self.address, 22)

    def check_users_input(self, remove_bad: bool = False) -> None:
        """
        Set up users and check input storage for the linked devices.
        """
        self.setup_users()
        self.check_input(remove_bad)

    def setup_users(self) -> None:
        """
        Ensure all required users for devices exist on the external storage.
        Set up necessary user accounts and permissions.
        """
        connection_success, ssh_client = self.check_connection()
        if not connection_success:
            logger.info(f"{self.name} - unable to connect")
            return

        ssh_client.connect_to_ssh()

        # Get list of all current users
        status_code, stdout, stderr = ssh_client.send_ssh_command(
            'cut -d: -f1 /etc/passwd')
        existing_users = stdout

        all_devices = self.linked_devices.all()
        required_users = all_devices.exclude(
            username="", username__isnull=True).values('username', 'password')
        missing_users = [x for x in required_users if x['username']
                         not in existing_users]

        user_group_name = "ftpuser"

        # check main user group exists
        status_code, stdout, stderr = ssh_client.send_ssh_command(
            f"grep {user_group_name} /etc/group")

        group_users = stdout

        if len(group_users) == 0:
            # If group does not exist, create it
            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"groupadd {user_group_name}", True)

        for user in missing_users:
            username = user["username"]
            user_password = user["password"]

            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"perl -e 'print crypt('{user_password}', 'password')'")
            encrypted_user_password = stdout[0]

            logger.info(f"{self.name} - add user {username}")
            # Add new user, add to ftpuser group
            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"useradd -m -p {encrypted_user_password}-N -g {user_group_name} {username}", True)

            # Create a group for this user
            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"groupadd g{username}", True)

            # Add service account to the user group
            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"usermod -a -G g{username} {self.username}", True)

            # Allow user and service account to own it
            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"chown {username}:g{username} /home/{username}", True)

            # allow user and service account to own it
            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"chmod -R g+srwx /home/{username}", True)

            # Prevent other users viewing the contents
            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"chmod -R o-rwx /home/{username}", True)

        for user in required_users:
            username = user["username"]
            logger.info(f"{self.name} - check user {username} permissions")

            # Check that service account is in user's group
            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"id {self.username} | grep -c g{username}")
            grep_result = int(stdout[0])

            if grep_result == 0:
                # check if group exists
                status_code, stdout, stderr = ssh_client.send_ssh_command(
                    f"grep g{username} /etc/group")
                group_users = stdout

                if len(group_users) == 0:
                    # If group does not exist, create it
                    status_code, stdout, stderr = ssh_client.send_ssh_command(
                        f"groupadd g{username}", True)

                if not (self.username in group_users):
                    # If service account is not in the group, add it.
                    status_code, stdout, stderr = ssh_client.send_ssh_command(
                        f"usermod -a -G g{username} {self.username}", True)

                # Try to list user home directory
                status_code, stdout, stderr = ssh_client.send_ssh_command(
                    f"ls -ld /home/{username} | grep -c g{username}")
                grep_result = int(stdout[0])

                if grep_result == 0:
                    # If unable to list directory, make sure group permissions are correct
                    stdin, stdout, stderr = ssh_client.send_ssh_command(
                        f"chown {username}:g{username} /home/{username}", True)

                # allow user and main user to own it
                stdin, stdout, stderr = ssh_client.send_ssh_command(
                    f"chmod -R g+srwx /home/{username}", True)
                # prevent other users viewing the contents
                stdin, stdout, stderr = ssh_client.send_ssh_command(
                    f"chmod -R o-rwx /home/{username}", True)

        ssh_client.close_connection_to_ftp()

    def check_connection(self) -> tuple[bool, 'SSH_client | None']:
        """
        Attempt to initialize an SSH client for this storage input.
        Returns a tuple: (success, SSH_client or None)
        """
        try:
            ssh_client = self.init_ssh_client()
            return True, ssh_client
        except Exception as e:
            logger.info(f"{self.name} - error")
            logger.info(repr(e))
            return False, None

    def check_input(self, remove_bad: bool = False) -> None:
        """
        Check input files and folders for all linked devices.
        Optionally remove invalid files.
        """
        connection_success, ssh_client = self.check_connection()
        if not connection_success:
            logger.info(f"{self.name} - unable to connect")
            return

        ssh_client.connect_to_ftp()
        all_devices = self.linked_devices.all()
        all_dirs_attributes = ssh_client.ftp_sftp.listdir_attr()
        file_names = [x.filename for x in all_dirs_attributes]
        for device in all_devices:
            logger.info(f"{self.name} - {device.device_ID} - checking storage")
            if device.username is None:
                logger.info(
                    f"{self.name} - {device.device_ID} - configured incorrectly")
                continue
            # check for folder of this device
            if device.username not in file_names:
                logger.info(
                    f"{self.name} - {device.device_ID} - not found on external storage")
                continue

            # check for files
            device_dir_attribute = ssh_client.ftp_sftp.listdir_attr(
                device.username)
            device_file_names = [
                x.filename for x in device_dir_attribute if all([y != '' for y in splitext(x.filename)])]
            if len(device_file_names) == 0:
                logger.info(
                    f"{self.name} - {device.device_ID} - no files on external storage")
                continue

            files = []
            for filename in device_file_names:
                try:
                    with ssh_client.ftp_sftp.open(join(device.username, filename), bufsize=32768) as f:
                        f.set_pipelined
                        f.prefetch()
                        f_bytes = io.BytesIO(f.read())
                        file_object = File(f_bytes, name=filename)
                        files.append(file_object)
                except Exception as e:
                    logger.error(e)

            # import files
            downloaded_files, invalid_files, existing_files, status = create_file_objects(
                files, device_object=device)
            logger.info(f"{self.name} - {device.device_ID} - {status}")

            # delete files that are succesfully downloaded
            for file_obj in downloaded_files:
                logger.info(
                    f"{self.name} - {device.device_ID} - {file_obj.original_name} succesfully downloaded")
                if not settings.DEVMODE:
                    ssh_client.ftp_sftp.remove(
                        join(device.username, file_obj.original_name))
                    logger.info(
                        f"{self.name} - {device.device_ID} - {file_obj.original_name} removed")

            for problem_file in invalid_files:
                logger.info(
                    f"{self.name} - {device.device_ID} - {problem_file}")
                if remove_bad:
                    mtime = ssh_client.ftp_sftp.stat(
                        join(device.username, problem_file)).st_mtime
                    last_modified = datetime.fromtimestamp(mtime)
                    if (datetime.now() - last_modified) <= timedelta(days=7):
                        ssh_client.ftp_sftp.remove(
                            join(device.username, problem_file))
                        logger.info(
                            f"{self.name} - {device.device_ID} - {problem_file} removed")

        ssh_client.close_connection_to_ftp()
