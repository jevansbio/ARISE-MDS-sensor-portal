import os
from typing import List

from data_models.models import DataFile
from utils.general import get_md5


def bag_info_from_files(file_objs: DataFile, output_path: str) -> List[str]:
    """
    Generate the necessary BagIt metadata files for a set of data files, writing them to the specified output directory.

    This function creates 'bagit.txt', 'manifest-md5.txt', and 'tagmanifest-md5.txt' directly in the output directory.
    The files are generated based on the provided `file_objs` (which should be a queryset or collection of DataFile instances).
    Each generated file's full path is returned in a list.

    Args:
        file_objs (DataFile): Queryset or iterable of DataFile objects representing files to be included in the bag.
        output_path (str): Directory path where the BagIt files should be created.

    Returns:
        List[str]: List of absolute paths to the generated BagIt files.
    """
    os.makedirs(output_path, exist_ok=True)

    # Write bagit.txt
    bagit_txt_lines = [
        "BagIt-Version: 0.97\n",
        "Tag-File-Character-Encoding: UTF-8\n"
    ]
    bag_path = os.path.join(output_path, "bagit.txt")
    with open(bag_path, "w") as f:
        f.writelines(bagit_txt_lines)

    # Write manifest-md5.txt
    file_objs = file_objs.full_paths()
    all_full_paths = file_objs.values_list("full_path", flat=True)
    all_relative_paths = file_objs.values_list("relative_path", flat=True)
    manifest_lines = [
        f"{get_md5(full_path)}  {os.path.join('data', relative_path)}\n"
        for full_path, relative_path in zip(all_full_paths, all_relative_paths)
    ]
    manifest_path = os.path.join(output_path, "manifest-md5.txt")
    with open(manifest_path, "w") as f:
        f.writelines(manifest_lines)

    # Write tagmanifest-md5.txt
    all_paths = [bag_path, manifest_path]
    tag_manifest_lines = [
        f"{get_md5(path)}  {os.path.basename(path)}\n"
        for path in all_paths
    ]
    tag_manifest_path = os.path.join(output_path, "tagmanifest-md5.txt")
    with open(tag_manifest_path, "w") as f:
        f.writelines(tag_manifest_lines)

    all_paths.append(tag_manifest_path)

    return all_paths
