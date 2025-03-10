import os
from data_models.models import DataFile
from utils.general import get_md5


def bag_info_from_files(file_objs: DataFile, output_path: str) -> list[str]:
    """
    This should generate neccesary files for a bagit object.
    The bagit python implementation requires files to be moved.
    With this script, these text files can be generated an appended straight to a TAR.

    Args:
        file_objs (DataFile): queryset of DataFile objects
        output_folder (str): output folder for generated files

    Returns:
        list[str] : list of paths of the generated bag files
    """
    os.makedirs(output_path, exist_ok=True)

    # bag.txt
    bagit_txt_lines = ["BagIt-Version: 0.97\n",
                       "Tag-File-Character-Encoding: UTF-8\n"]

    bag_path = os.path.join(output_path, "bagit.txt")
    # export file
    with open(bag_path, "w") as f:
        f.writelines(bagit_txt_lines)

    # manifest-md5.txt

    all_full_paths = file_objs.full_paths()
    all_relative_paths = file_objs.relative_paths()

    manifest_lines = [f"{get_md5(x)}  {os.path.join('data',y)}\n" for x, y in zip(
        all_full_paths, all_relative_paths)]

    manifest_path = os.path.join(output_path, "manifest-md5.txt")
    with open(manifest_path, "w") as f:
        f.writelines(manifest_lines)

    # tagmanifest-md5.txt
    # run checksums on previously exported bag txt files

    all_paths = [bag_path, manifest_path]
    tag_manifest_lines = [
        f"{get_md5(x)}  {os.path.split(x)[1]}\n" for x in all_paths]

    tag_manifest_path = os.path.join(output_path, "tagmanifest-md5.txt")

    with open(tag_manifest_path, "w") as f:
        f.writelines(tag_manifest_lines)

    all_paths.append(tag_manifest_path)

    # return paths to these files
    return all_paths
