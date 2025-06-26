import logging
from posixpath import join, split, splitext

import paramiko
import paramiko.ssh_exception
from scp import SCPClient

from .general import convert_unit

logger = logging.getLogger(__name__)


class SSH_client:
    def __init__(
        self,
        username: str,
        password: str,
        address: str,
        port: int,
    ) -> None:
        """
        Initialize the SSH_client instance.

        Args:
            username (str): SSH username.
            password (str): SSH password.
            address (str): SSH server address.
            port (int): SSH port number.
        """
        self.username = username
        self.password = password
        self.address = address
        self.port = port

    def check_connection(self) -> None:
        """
        Checks if the FTP connection is active, and attempts to reconnect if not.
        """
        while not self.ftp_t.is_active():
            logger.info("Try to reestablish connection")
            self.connect_to_ftp()

    def connect_to_ftp(self) -> bool:
        """
        Establishes an SFTP connection.

        Returns:
            bool: True if connection succeeded, False otherwise.
        """
        try:
            self.ftp_t = paramiko.Transport((self.address, self.port))
            self.ftp_t.connect(username=self.username, password=self.password)
            self.ftp_sftp = paramiko.SFTPClient.from_transport(self.ftp_t)
            sftp_channel = self.ftp_sftp.get_channel()
            sftp_channel.settimeout(60 * 10)
            return True
        except Exception as e:
            logger.info(repr(e))
            return False

    def close_connection_to_ftp(self) -> None:
        """
        Closes the SFTP connection.
        """
        try:
            self.ftp_t.close()
            logger.info("FTP connection closed")
        except Exception as e:
            logger.info(repr(e))

    def connect_to_ssh(self, port: int = None) -> bool:
        """
        Establishes an SSH connection.

        Args:
            port (int, optional): SSH port. Defaults to self.port.

        Returns:
            bool: True if connection succeeded, False otherwise.
        """
        try:
            self.ssh_c.exec_command('ls')
            logger.info("SSH already connected")
            return True
        except AttributeError:
            pass

        if port is None:
            port = self.port

        try:
            self.ssh_c = paramiko.SSHClient()
            self.ssh_c.set_missing_host_key_policy(
                paramiko.client.AutoAddPolicy)
            self.ssh_c.connect(self.address, port,
                               username=self.username, password=self.password)
            return True
        except Exception as e:
            logger.info(repr(e))
            logger.info("Unable to start SSH connection")
            return False

    def close_connection(self) -> None:
        """
        Closes the SSH connection.
        """
        try:
            self.ssh_c.close()
        except Exception as e:
            logger.info(repr(e))
            logger.info("Unable to close SSH connection")

    def connect_to_scp(self) -> bool:
        """
        Establishes an SCP connection.

        Returns:
            bool: True if connection succeeded, False otherwise.
        """
        self.connect_to_ssh()
        try:
            self.scp_c = SCPClient(
                self.ssh_c.get_transport(),
                progress=lambda file_name, size, sent: self.scp_progress_function(
                    file_name, size, sent)
            )
            return True
        except Exception as e:
            logger.info(repr(e))
            logger.info("Unable to start SCP connection")
            return False

    def close_scp_connection(self) -> None:
        """
        Closes the SCP connection.
        """
        try:
            self.scp_c.close()
        except Exception as e:
            logger.info(repr(e))
            logger.info("Unable to close SCP connection")

    def scp_progress_function(self, file_name: str, size: int, sent: int) -> None:
        """
        Callback to report progress during SCP file transfers.

        Args:
            file_name (str): The name of the file being transferred.
            size (int): The total file size in bytes.
            sent (int): The number of bytes sent so far.
        """
        sent_mb = convert_unit(sent, 'MB')
        size_mb = convert_unit(size, 'MB')

        if sent_mb % 50 != 0:
            return
        logger.info(
            f"{file_name} progress: {sent_mb}/{size_mb} {float(sent)/float(size)*100}% \r"
        )

    def send_ssh_command(
        self,
        command: str,
        sudo: bool = False,
        max_tries: int = 100,
        return_strings: bool = True,
        debug: bool = False,
    ) -> tuple[int, list[str], str] | tuple[int, any, any]:
        """
        Executes a command over SSH, optionally with sudo, and returns result.

        Args:
            command (str): The command to execute.
            sudo (bool, optional): Whether to run the command with sudo. Defaults to False.
            max_tries (int, optional): Maximum number of retry attempts. Defaults to 100.
            return_strings (bool, optional): If True, returns result as strings. Otherwise, returns raw objects. Defaults to True.
            debug (bool, optional): Whether to log debug info. Defaults to False.

        Returns:
            tuple: (exit_status, stdout_lines, stderr_str) if return_strings is True,
                   otherwise (-1, stdout, stderr)
        """
        success = False
        currtries = 0
        while (not success) and (currtries < max_tries):
            try:
                if sudo:
                    command = "sudo -S -p '' " + command
                stdin, stdout, stderr = self.ssh_c.exec_command(command)
                if sudo:
                    stdin.write(self.password + "\n")
                    stdin.flush()

                success = True
            except Exception as e:
                logger.info(repr(e))
                currtries += 1
                self.connect_to_ssh()
            if debug:
                logger.info(f"{command} SUDO {sudo} SUCCESS {success}")

        if not success:
            raise paramiko.ssh_exception.SSHException

        stdout.channel.set_combine_stderr(True)

        if return_strings:
            stdout_lines = stdout.readlines()
            stdout_lines = [x.strip("\n") for x in stdout_lines]
            stderr_str = stderr.read().decode()
            exit_status = stdout.channel.recv_exit_status()

            return exit_status, stdout_lines, stderr_str
        else:
            return -1, stdout, stderr

    def mkdir_p(self, remote_path: str, is_dir: bool = True) -> None:
        """
        Emulates 'mkdir -p' on the remote server via SFTP.

        Args:
            remote_path (str): The remote directory path to create.
            is_dir (bool, optional): Whether the path is a directory. Defaults to True.
        """
        dirs_: list[str] = []
        if is_dir:
            dir_ = remote_path
        else:
            dir_, basename = split(remote_path)
        while len(dir_) > 1:
            dirs_.append(dir_)
            dir_, _ = split(dir_)
        if len(dir_) == 1 and not dir_.startswith("/"):
            dirs_.append(dir_)  # For a remote path like y/x.txt
        while len(dirs_):
            dir_ = dirs_.pop()
            logger.info(dir_)
            try:
                self.ftp_sftp.stat(dir_)
            except FileNotFoundError:
                logger.info(f"making {dir_}")
                self.ftp_sftp.mkdir(dir_)
