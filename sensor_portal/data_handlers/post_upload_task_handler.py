import logging
import traceback
from typing import Callable, List, Tuple

from data_models.models import DataFile

logger = logging.getLogger(__name__)


def post_upload_task_handler(
    file_pks: List[int],
    task_function: Callable[[DataFile],
                            Tuple[DataFile | None, List[str] | None]]
) -> None:
    """
    Executes a post-upload task function on a list of DataFile objects, ensuring each file is locked during processing
    and restored to its initial lock state afterward.

    This function retrieves DataFile objects by their primary keys, temporarily locks them (by setting `do_not_remove=True`),
    applies the provided `task_function` to each file, and then restores each file's original `do_not_remove` state.
    It ensures that one file's failure does not interrupt processing for others.

    Args:
        file_pks (List[int]): 
            A list of primary keys representing DataFile objects to process.
        task_function (Callable[[DataFile], Tuple[DataFile | None, List[str] | None]]): 
            A function to execute on each DataFile. It should accept a DataFile object and return a tuple:
            (possibly modified DataFile, list of modified field names).
            If the function fails, the original DataFile object is left unchanged.

    Notes:
        - Each DataFile is locked before processing by setting `do_not_remove=True`, and unlocked (restored to its original state) after processing.
        - Any exceptions in processing a file are logged, but will not halt the processing of other files.
        - All modified DataFile objects are batch updated at the end, including the `do_not_remove` field if it was changed.

    Returns:
        None
    """

    # get datafiles
    data_file_objs = DataFile.objects.filter(
        pk__in=file_pks).order_by("created_on")
    # save initial do_not_delete state of files

    logger.info(
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
            logger.error(repr(e))
            logger.error(traceback.format_exc())

        data_file.do_not_remove = file_do_not_remove
        updated_data_objs.append(data_file)

    if "do_not_remove" not in modified_fields:
        modified_fields.append("do_not_remove")

    # update objects
    update = DataFile.objects.bulk_update(updated_data_objs, modified_fields)
    logger.info(f"Running job {str(task_function)} updated {update} files")
