from typing import TypeVar

from data_models.models import DataFile, Deployment
from django.conf import settings
from django.db.models import (BooleanField, Case, CharField, Count,
                              ExpressionWrapper, F, FloatField, IntegerField,
                              Max, Min, Q, Subquery, Value, When)
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast, Concat, FirstValue, Replace
from django.db.models.query import QuerySet
from observation_editor.models import Observation

# Move to settings
activity_types = ["wildlifecamera"]
timelapse_types = ["timelapsecamera"]

_QS = TypeVar('_QS', bound=QuerySet)


def get_ctdp_deployment_qs(qs: _QS) -> _QS:
    """
    Annotate a deployment queryset with fields formatted for Camtrap Data Package (CTDP) export.

    Args:
        qs (QuerySet): A Django queryset for Deployment objects.

    Returns:
        QuerySet: Annotated queryset with additional CTDP fields.
    """
    qs = qs.annotate(
        locationID=Case(
            When(extra_data__deploymentLocationID__isnull=False, then=Cast(KeyTextTransform('deploymentLocationID', 'extra_data'),
                 output_field=CharField())),
            When(extra_data__locationID__isnull=False,
                 then=Cast(KeyTextTransform('locationID', 'extra_data'),
                           output_field=CharField())),
            default=F('deployment_ID'), output_field=CharField()
        )
    )

    qs = qs.annotate(setupBy=Case(When(owner__isnull=False,
                                  then=Concat(F('owner__first_name'), Value(
                                      ' '), F('owner__last_name'))),
                                  default=Value(''), output_field=CharField()))

    qs = qs.annotate(
        coordinateUncertainty=Case(
            When(extra_data__coordinateUncertainty__isnull=False, then=Cast(KeyTextTransform('coordinateUncertainty', 'extra_data'),
                 output_field=FloatField())),
            When(extra_data__LatLongInaccuracy_cm__isnull=False, then=Cast(KeyTextTransform('LatLongInaccuracy_cm', 'extra_data'),
                 output_field=FloatField()) / 100),
            default=Value(None), output_field=FloatField()
        )
    )

    qs = qs.annotate(cameraID=F('device__device_ID'))

    qs = qs.annotate(
        cameraModel=Concat(F('device__model__manufacturer'),
                           Value('-'), F('device__model__name'))
    )

    qs = qs.annotate(
        cameraHeight=Case(
            When(extra_data__cameraHeight__isnull=False, then=Cast(KeyTextTransform('cameraHeight', 'extra_data'),
                                                                   output_field=FloatField())),
            When(extra_data__height_cm__isnull=False, then=Cast(KeyTextTransform('height_cm', 'extra_data'),
                                                                output_field=FloatField()) / 100),
            default=Value(None), output_field=FloatField()
        )
    )

    qs = qs.annotate(
        cameraHeading=Case(
            When(extra_data__cameraHeading__isnull=False,
                 then=Cast(KeyTextTransform('cameraHeading', 'extra_data'), output_field=IntegerField())),
            When(extra_data__Direction__isnull=False,
                 then=Case(
                     When(
                         extra_data__Direction="NE", then=Value(45)),
                     When(
                         extra_data__Direction="E", then=Value(90)),
                     When(
                         extra_data__Direction="SE", then=Value(135)),
                     When(
                         extra_data__Direction="S", then=Value(180)),
                     When(
                         extra_data__Direction="SW", then=Value(225)),
                     When(
                         extra_data__Direction="W", then=Value(270)),
                     When(
                         extra_data__Direction="NW", then=Value(315)),
                     default=Value(None), output_field=IntegerField()
                 )
                 ),
            default=Value(None), output_field=IntegerField()
        )
    )

    qs = qs.annotate(
        baitUse=Case(
            When(extra_data__baitUse__isnull=False,
                 extra_data__baitUse="yes", then=Value(True)),
            When(extra_data__Bait__isnull=False,
                 extra_data__Bait="yes", then=Value(True)),
            default=Value(False), output_field=BooleanField()
        )
    )

    qs = qs.annotate(
        habitatType=Case(
            When(extra_data__habitatType__isnull=False,
                 then=F('extra_data__habitatType')),
            default=Value(None), output_field=CharField()
        )
    )

    qs = qs.annotate(
        deploymentTags=Case(
            When(extra_data__deploymentTags__isnull=False,
                 then=F('extra_data__deploymentTags')),
            default=Value(None), output_field=CharField()
        )
    )

    qs = qs.annotate(
        deploymentGroups=Case(
            When(extra_data__deploymentGroups__isnull=False,
                 then=F('extra_data__deploymentGroups')),
            default=Value(None), output_field=CharField()
        )
    )

    qs = qs.annotate(
        deploymentComments=Case(
            When(extra_data__deploymentComments__isnull=False,
                 then=F('extra_data__deploymentComments_')),
            When(extra_data__comments__isnull=False,
                 then=F('extra_data__comments')),
            When(extra_data__Comment__isnull=False,
                 then=F('extra_data__comments')),
            default=Value(None), output_field=CharField()
        )
    )
    return qs


def get_ctdp_media_qs(qs: _QS) -> _QS:
    """
    Annotate a media file queryset with fields formatted for Camtrap Data Package (CTDP) export.

    Args:
        qs (QuerySet): A Django queryset for DataFile or similar media objects.

    Returns:
        QuerySet: Annotated queryset with additional CTDP media fields.
    """
    qs = qs.annotate(
        favorite=ExpressionWrapper(
            Q(favourite_of__isnull=False),
            output_field=BooleanField()
        )
    )
    qs = qs.annotate(
        captureMethod=Case(
            When(file_type__name__in=timelapse_types, then=Value("timeLapse")),
            When(file_type__name=activity_types,
                 then=Value("activityDetection")),
            default=Value(""), output_field=CharField()
        )
    )

    qs = qs.annotate(
        timestamp=Replace(
            Concat(F('recording_dt'), Value('Z'), output_field=CharField()),
            Value(" "),
            Value("T")
        )
    )

    qs = qs.annotate(
        deploymentID=F('deployment__deployment_device_ID')
    )

    qs = qs.annotate(
        filePath=Case(
            When(local_storage=True, then=Replace(
                'file_url',
                Concat(
                    F('file_name'), F('file_format')),
                Value('')
            )),
            When(local_storage=False,
                 archived=True,
                 then=Concat(
                     Value('ARCHIVE/'),
                     F('tar_file__name'),
                     Value('/'),
                     F('path')
                 )
                 ),
            defaul=Value('')
        )
    )

    qs = qs.annotate(
        fileName=Concat(F('file_name'), F('file_format'))
    )

    qs = qs.annotate(
        mediaComments=Case(
            When(extra_data__mediaComments__isnull=False,
                 then=Cast(KeyTextTransform('mediaComments', 'extra_data'), output_field=CharField())),
            When(extra_data__comments__isnull=False,
                 then=Cast(KeyTextTransform('comments', 'extra_data'), output_field=CharField())),
            default=Value(None), output_field=CharField()
        )
    )

    qs = qs.annotate(
        filePublic=Value(False)
    )

    return qs


def get_ctdp_obs_qs(qs: _QS) -> _QS:
    """
    Annotate an observation queryset with fields formatted for Camtrap Data Package (CTDP) export.

    Args:
        qs (QuerySet): A Django queryset for Observation objects.

    Returns:
        QuerySet: Annotated queryset with additional CTDP observation fields.
    """
    qs = qs.annotate(nfiles=Count('data_files'))

    qs = qs.annotate(
        deploymentID=Min(F('data_files__deployment__deployment_device_ID')))

    qs = qs.annotate(
        observationID=F('label'))

    qs = qs.annotate(
        mediaID=Case(
            When(nfiles=1, then=Min('data_files__file_name')),
            default=Value(None), output_field=CharField()
        )
    )

    qs = qs.annotate(
        eventIDA=Case(
            When(nfiles__gt=1, then=F('label')),
            default=Value(None), output_field=CharField()
        ))

    qs = qs.annotate(
        eventID=Case(
            When(nfiles__gt=1, then=Concat(F('eventIDA'), Value('_EVENT'))),
            default=Value(None), output_field=CharField()
        ))

    qs = qs.annotate(
        observationLevel=Case(
            When(nfiles__gt=1, then=Value('event')),
            default=Value('media'), output_field=CharField()
        ))

    qs = qs.annotate(
        observationType=Case(
            When(taxon__taxon_code=settings.HUMAN_TAXON_CODE, then=Value('human')),
            When(taxon__species_name__in=[
                'car', 'van', 'vehicle', 'plane'], then=Value('vehicle')),
            When(taxon__species_name__in=[
                 'blank', 'empty', 'None', 'No detection'], then=Value('blank')),
            When(taxon__species_name__in=[
                'unknown'], then=Value('unknown')),
            default=Value('animal'), output_field=CharField()))

    qs = qs.annotate(
        scientificName=Case(
            When(taxon__taxon_code="", then=Value(None)),
            default=F('taxon__species_name'), output_field=CharField()
        ))
    qs = qs.annotate(
        classificationMethod=Case(
            When(source='human', then=Value('human')),
            default=Value('machine'), output_field=CharField()
        ))
    qs = qs.annotate(
        individualID=Case(
            When(extra_data__individualID__isnull=False,
                 then=Cast(KeyTextTransform('individualID', 'extra_data'), output_field=CharField())),
            default=Value(None), output_field=CharField()
        ))
    qs = qs.annotate(
        bboxX=Case(
            When(bounding_box__x1__isnull=False, then=Cast(
                Cast(F('bounding_box__x1'), CharField()), FloatField())),
            default=Value(None), output_field=FloatField()
        ),
        bboxY=Case(
            When(bounding_box__x1__isnull=False, then=Cast(
                Cast(F('bounding_box__y1'), CharField()), FloatField())),
            default=Value(None), output_field=FloatField()
        ),
        bboxX2=Case(
            When(bounding_box__x1__isnull=False, then=Cast(
                Cast(F('bounding_box__x2'), CharField()), FloatField())),
            default=Value(None), output_field=FloatField()
        ),
        bboxY2=Case(
            When(bounding_box__x1__isnull=False, then=Cast(
                Cast(F('bounding_box__y2'), CharField()), FloatField())),
            default=Value(None), output_field=FloatField()
        ),
        bboxWidth=Case(
            When(bounding_box__x1__isnull=False, then=F('bboxX2')-F('bboxX')),
            default=Value(None), output_field=FloatField()
        ),
        bboxHeight=Case(
            When(bounding_box__x1__isnull=False, then=F('bboxY2')-F('bboxY')),
            default=Value(None), output_field=FloatField()
        )
    )
    qs = qs.annotate(
        classifiedBy=Case(
            When(owner__isnull=False,
                 then=Concat(F('owner__first_name'), Value(
                     ' '), F('owner__last_name'))),
            default=F('source'), output_field=CharField()
        )
    )
    qs = qs.annotate(
        classificationProbability=Case(
            When(confidence__isnull=False,
                 then=F('confidence')),
            default=Value(None), output_field=FloatField()
        )
    )
    qs = qs.annotate(
        observationComments=Case(
            When(extra_data__observationComments__isnull=False,
                 then=Cast(KeyTextTransform('observationComments', 'extra_data'), output_field=CharField())),
            When(extra_data__comments__isnull=False,
                 then=Cast(KeyTextTransform('comments', 'extra_data'), output_field=CharField())),
            default=Value(None), output_field=CharField()
        ))

    qs = qs.annotate(
        eventStart=Case(

            When(nfiles__gt=1, then=Replace(
                Concat(Min('data_files__recording_dt'),
                       Value('Z'), output_field=CharField()),
                Value(" "),
                Value("T")
            )),
            default=Value(None), output_field=CharField()
        ),
        eventEnd=Case(
            When(nfiles__gt=1, then=Replace(
                Concat(Max('data_files__recording_dt'),
                       Value('Z'), output_field=CharField()),
                Value(" "),
                Value("T")
            )),
            default=Value(None), output_field=CharField()
        )
    )

    qs = qs.annotate(
        lifeStage=F('lifestage'),
        count=F('number')
    )

    return qs


def get_ctdp_seq_qs(qs: _QS) -> _QS:
    """
    Annotate an observation queryset to represent event/sequence records for CTDP export.

    Args:
        qs (QuerySet): A Django queryset for Observation objects.

    Returns:
        QuerySet: Annotated queryset filtered for sequence/event records with additional event fields.
    """
    qs = qs.distinct()

    qs = qs.annotate(nfiles=Count('data_files')).filter(nfiles__gt=1)

    qs = qs.annotate(
        eventIDA=Case(
            When(nfiles__lte=1, then=Value(None)),
            When(nfiles__gt=1, then=F('label'))
        ),
        eventID=Case(
            When(nfiles__lte=1, then=Value(None)),
            When(nfiles__gt=1, then=Concat(F('eventIDA'), Value('_EVENT'))
                 )
        ),
        eventStart=Case(
            When(nfiles__lte=1, then=Value(None)),
            When(nfiles__gt=1, then=Replace(
                Concat(Min('data_files__recording_dt'),
                       Value('Z'), output_field=CharField()),
                Value(" "),
                Value("T")
            )
            )
        ),
        eventEnd=Case(
            When(nfiles__lte=1, then=Value(None)),
            When(nfiles__gt=1, then=Replace(
                Concat(Max('data_files__recording_dt'),
                       Value('Z'), output_field=CharField()),
                Value(" "),
                Value("T")
            )
            )
        ),
    )
    return qs
