import logging
from typing import Any, Dict, List, Optional, Union

from celery import chain, chord, group, shared_task, signature
from celery.app import Celery
from data_models.job_handling_functions import register_job
from data_models.models import DataFile
from django.conf import settings
from django.db.models import CharField, QuerySet
from django.db.models.functions import Lower
from django.utils import timezone
from observation_editor.models import Observation, Taxon

from sensor_portal.celery import app

logger = logging.getLogger(__name__)

# While we are using django_results as a backend, the ultralytics worker cannot access this to trigger the callback.
# Therefore we set up an app using redis as a backend
ai_app = Celery(broker_url=settings.CELERY_BROKER_URL,
                result_backend=settings.CELERY_BROKER_URL)

CharField.register_lookup(Lower)


@app.task(name="do_ultra_inference")
@register_job("Do Ultralytic AI model inference", "do_ultra_inference", "datafile", True,
              default_args={"model_name": "yolov8s"})
def do_ultra_inference(
    datafile_pks: Union[int, List[int]],
    model_name: str,
    target_labels: Optional[Union[str, List[str]]] = None,
    chunksize: int = 500,
    chunksize2: int = 100,
    exclude_done: bool = False,
    parallel: bool = False,
    **kwargs: Any
) -> None:
    """
    Runs ultralytic AI model inference on batches of DataFiles.

    Args:
        datafile_pks: A single primary key or a list of primary keys of DataFile objects.
        model_name: The name of the ultralytics model to use.
        target_labels: Optional; a label or list of labels to target in inference.
        chunksize: The number of files to process in the outer batch.
        chunksize2: The number of files per job batch.
        exclude_done: If True, skips files which already have observations for this model.
        parallel: If True, runs jobs in parallel; otherwise, chains jobs.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    valid_formats = [".jpg", ".jpeg", ".png"]  # should be setting from env
    target_queue_name = settings.ULTRALYTICS_QUEUE  # should be setting from env
    queue_names = [x[0]['name']
                   for x in ai_app.control.inspect().active_queues().values()]

    if target_queue_name not in queue_names:
        logger.info(f"No {target_queue_name} queue available")
        return

    if type(datafile_pks) is not list:
        datafile_pks = [datafile_pks]
    if target_labels is not None and type(target_labels) is not list:
        target_labels = [target_labels]

    file_objs: QuerySet = DataFile.objects.filter(
        pk__in=datafile_pks, file_format__lower__in=valid_formats)

    if exclude_done or not parallel:
        file_objs = file_objs.exclude(observations__source=model_name)
        datafile_pks = list(file_objs.values_list('pk', flat=True))

    if len(datafile_pks) == 0:
        logger.info("No files to analyse")
        return

    file_pks_chunks: List[List[int]] = [datafile_pks[i:i + chunksize]
                                        for i in range(0, len(datafile_pks), chunksize)]

    for i, file_pks_chunk in enumerate(file_pks_chunks):
        file_objs_chunk = file_objs.filter(pk__in=file_pks_chunk).full_paths()
        file_pks_job_chunks = [file_pks_chunk[i:i + chunksize2]
                               for i in range(0, len(file_pks_chunk), chunksize2)]

        all_tasks = []

        for file_pk_job_chunk in file_pks_job_chunks:
            job_qs = file_objs_chunk.filter(pk__in=file_pk_job_chunk)
            file_paths = list(
                job_qs.values_list("full_path", flat=True))

            all_tasks.append(ai_app.signature('AnalysisTask', [
                file_paths, model_name, target_labels], queue="ultralytics", immutable=True))

        task_chord = chord(all_tasks, handle_ultra_results.s(
            target_labels).set(queue="main_worker"))

        if not parallel:
            task_chain = chain(task_chord,
                               do_ultra_inference.si(datafile_pks,
                                                     model_name,
                                                     target_labels,
                                                     chunksize,
                                                     chunksize2, True, False).set(queue="main_worker"))
            logger.info(task_chain)
            task_chain.apply_async()
            return

        else:
            task_chord.apply_async()


@app.task()
def handle_ultra_results(
    all_results: List[Dict[str, Any]],
    target_labels: Optional[Union[str, List[str]]] = None
) -> None:
    """
    Processes results from ultralytics inference, creates Observation objects, and links them to DataFiles.

    Args:
        all_results: List of dictionaries with inference results.
        target_labels: Optional; label or list of labels to target in result processing.

    Returns:
        None
    """
    through_class = Observation.data_files.through
    if target_labels is not None and type(target_labels) is not list:
        target_labels = [target_labels]

    objs_to_create: List[Observation] = []
    file_objs_pks: List[int] = []
    file_objs_human_pks: List[int] = []

    for results in all_results:
        source = results.get('source')
        for file_name, file_results in results.get('files').items():
            file_obj = DataFile.objects.get(file_name=file_name)
            num_results = 0
            if len(file_results) > 0:
                for result in file_results:
                    prediction = result.get('prediction')
                    if target_labels is None or prediction in target_labels:
                        num_results += 1
                        bounding_box = result.get("bbox")
                        extra_data: Dict[str, Any] = {}

                        if bounding_box is not None:
                            bbox_keys = ["x1", "y1", "x2", "y2"]
                            bounding_box = {k: v for k, v in zip(
                                bbox_keys, bounding_box)}
                        confidence = result.get('confidence')
                        if result.get('orig_shape') is not None:
                            extra_data["orig_shape"] = result.get('orig_shape')

                        taxon_obj = Taxon.objects.get_or_create(
                            species_name=prediction)[0]

                        new_observation_object = Observation(
                            label=f"{prediction}_{file_obj.file_name}",
                            taxon=taxon_obj,
                            obs_dt=file_obj.recording_dt,
                            bounding_box=bounding_box,
                            confidence=confidence,
                            extra_data=extra_data,
                            source=source
                        )

                        objs_to_create.append(new_observation_object)
                        file_objs_pks.append(file_obj.pk)
                        if taxon_obj.taxon_code == settings.HUMAN_TAXON_CODE:
                            file_objs_human_pks.append(file_obj.pk)

            if len(file_results) == 0 or num_results == 0:
                taxon_obj = Taxon.objects.get_or_create(
                    species_name="No detection")[0]
                new_observation_object = Observation(
                    label=f"No_dectection_{file_obj.file_name}",
                    taxon=taxon_obj,
                    obs_dt=file_obj.recording_dt,
                    extra_data={},
                    source=source
                )
                objs_to_create.append(new_observation_object)
                file_objs_pks.append(file_obj.pk)
    new_observations = Observation.objects.bulk_create(
        objs_to_create, batch_size=500)
    new_obervation_pks = [x.pk for x in new_observations]
    all_through_objs = []
    for obs_pk, file_pk in zip(new_obervation_pks, file_objs_pks):
        new_through_obj = through_class.objects.create(
            observation_id=obs_pk, datafile_id=file_pk)
        all_through_objs.append(new_through_obj)
    through_class.objects.bulk_create(
        all_through_objs, batch_size=500, ignore_conflicts=True)
    logger.info(f"Created {len(new_observations)} observations")
    # Update datafiles if human is present
    DataFile.objects.filter(pk__in=file_objs_human_pks).update(
        has_human=True, modified_on=timezone.now())
