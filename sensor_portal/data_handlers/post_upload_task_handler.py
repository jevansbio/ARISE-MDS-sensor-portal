from data_models.models import DataFile
from typing import Callable, Tuple, List
import traceback


def post_upload_task_handler(file_names: List[str],
                             task_function: Callable[[DataFile], Tuple[DataFile | None, List[str] | None]]) -> None:
    """
Wrapper function to handle applying post upload functions on files. Will lock any files being operated on, return them to their initial lock state when done.

Args:
    file_names (List[str]): list of DataFile file names. These will be the files on which task_function is called.
    task_function (Callable[[DataFile], Tuple[DataFile  |  None, List[str]  |  None]]): Function to carry out on each DataFile.

    task_function Should take the DataFile as arguments and return a modified DataFile and a list of the names of the modified fields.
    """

    # get datafiles
    data_file_objs = DataFile.objects.filter(
        file_name__in=file_names).order_by("created_on")
    # save initial do_not_delete state of files

    print(
        f"Running job {str(task_function)} on {data_file_objs.count()} files")

    do_not_remove_initial = list(data_file_objs.values_list(
        "do_not_remove", flat=True))

    # lock datafiles
    data_file_objs.update(do_not_remove=True)

    updated_data_objs = []
    modified_fields = []
    # loop through datafiles
    for i, data_file in enumerate(data_file_objs):

        file_do_not_remove = do_not_remove_initial[i]
        try:
            data_file, modified_fields = task_function(data_file)

        except Exception as e:
            # One file failing shouldn't lead to the whole job failing
            print(repr(e))
            print(traceback.format_exc())

        data_file.do_not_remove = file_do_not_remove
        updated_data_objs.append(data_file)

    if "do_not_remove" not in modified_fields:
        modified_fields.append("do_not_remove")

    # update objects
    update = DataFile.objects.bulk_update(updated_data_objs, modified_fields)
    print(f"Running job {str(task_function)} updated {update} files")
