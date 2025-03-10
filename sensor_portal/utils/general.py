import hashlib
import subprocess


def convert_unit(size_in_bytes: int, unit: str) -> float:
    """
    Convert the size from bytes to 
    other units like KB, MB or GB

    Args:
        size_in_bytes (int): Size of file in bytes
        unit (str): Unit to convert to (kb, mb, gb)

    Returns:
        float: Size of file in chosen unit.
    """
    unit = unit.lower()

    if unit == 'kb':
        return size_in_bytes/1024
    elif unit == 'mb':
        return size_in_bytes/(1024*1024)
    elif unit == 'gb':
        return size_in_bytes/(1024*1024*1024)
    else:
        return size_in_bytes


def call_with_output(command: str | list[str], cwd: str = '/', verbose=False) -> tuple[bool, str]:
    """
    Calls a shell command and returns its output.

    Args:
        command (str | list[str]): Command to run, either a string or a list of strings (reccomended)
        cwd (str, optional): Working directory in which to run the command. Defaults to '/'.
        verbose (bool, optional): Print command and output to console. Defaults to False.
    Returns:
        tuple[bool, str]: success, shell output of command
    """
    success = False
    if verbose:
        print(command)
    try:
        output = subprocess.check_output(
            command, stderr=subprocess.STDOUT, cwd=cwd).decode()
        success = True
    except subprocess.CalledProcessError as e:
        output = e.output.decode()
    except Exception as e:
        # check_call can raise other exceptions, such as FileNotFoundError
        output = str(e)
    if verbose:
        print(output)
    return (success, output)


def get_md5(file_path: str) -> str:
    """
    Get md5 hash of file at file path.

    Args:
        file_path (str): Path to file to be hashed.

    Returns:
        str: md5 hash of file.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def divide_chunks(list_to_chunk, chunk_size):
    for i in range(0, len(list_to_chunk), chunk_size):
        yield list_to_chunk[i:i + chunk_size]
