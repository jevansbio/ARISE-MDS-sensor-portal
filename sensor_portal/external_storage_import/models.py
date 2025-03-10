import io
from posixpath import join, splitext

from data_models.file_handling_functions import create_file_objects
from django.conf import settings
from django.core.files import File
from django.db import models
from encrypted_model_fields.fields import EncryptedCharField
from utils.models import BaseModel
from utils.ssh_client import SSH_client


class DataStorageInput(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    username = models.CharField(
        max_length=50, unique=True)
    password = EncryptedCharField(max_length=128)
    address = models.CharField(
        max_length=100, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_inputstorages",
                              on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    def init_ssh_client(self):
        return SSH_client(self.username, self.password, self.address, 22)

    def check_users_input(self):
        self.setup_users()
        self.check_input()

    def setup_users(self):
        connection_success, ssh_client = self.check_connection()
        if not connection_success:
            print(f"{self.name} - unable to connect")
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

            print(f"{self.name} - add user {username}")
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
            print(f"{self.name} - check user {username} permissions")

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

    def check_connection(self):
        try:
            ssh_client = self.init_ssh_client()
            return True, ssh_client
        except Exception as e:
            print(f"{self.name} - error")
            print(repr(e))
            return False, None

    def check_input(self):
        connection_success, ssh_client = self.check_connection()
        if not connection_success:
            print(f"{self.name} - unable to connect")
            return

        ssh_client.connect_to_ftp()
        all_devices = self.linked_devices.all()
        all_dirs_attributes = ssh_client.ftp_sftp.listdir_attr()
        file_names = [x.filename for x in all_dirs_attributes]
        for device in all_devices:
            print(f"{self.name} - {device.device_ID} - checking storage")
            if device.username is None:
                print(f"{self.name} - {device.device_ID} - configured incorrectly")
                continue
            # check for folder of this device
            if device.username not in file_names:
                print(
                    f"{self.name} - {device.device_ID} - not found on external storage")
                continue

            # check for files
            device_dir_attribute = ssh_client.ftp_sftp.listdir_attr(
                device.username)
            device_file_names = [
                x.filename for x in device_dir_attribute if all([y != ''for y in splitext(x.filename)])]
            if len(device_file_names) == 0:
                print(
                    f"{self.name} - {device.device_ID} - no files on external storage")
                continue

            files = []
            for filename in device_file_names:
                with ssh_client.ftp_sftp.open(join(device.username, filename), bufsize=32768) as f:
                    f.set_pipelined
                    f.prefetch()
                    f_bytes = io.BytesIO(f.read())
                    file_object = File(f_bytes, name=filename)
                    files.append(file_object)

            print(files)

            # import files
            downloaded_files, invalid_files, existing_files, status = create_file_objects(
                files, device_object=device)
            print(f"{self.name} - {device.device_ID} - {status}")

            # delete files that are succesfully downloaded
            for filename in downloaded_files:
                print(
                    f"{self.name} - {device.device_ID} -{filename} succesfully downloaded")
                if not settings.DEVMODE:
                    ssh_client.ftp_sftp.remove(join(device.username, filename))
                    print(f"{self.name} - {device.device_ID} -{filename} removed")

            for problem_file in invalid_files:
                print(
                    f"{self.name} - {device.device_ID} - {problem_file}")
        ssh_client.close_connection_to_ftp()
