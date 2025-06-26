import mimetypes
import os

from data_models.models import DataFile
from rest_framework import serializers

# Based on https://camtrap-dp.tdwg.org/data/


class DeploymentSerializerCTDP(serializers.Serializer):
    deploymentID = serializers.CharField(
        source='deployment_device_ID',
        help_text="Unique identifier for this deployment (required by Camtrap DP: deploymentID)."
    )
    locationID = serializers.CharField(
        help_text="Identifier for the location where the deployment occurs (required by Camtrap DP: locationID)."
    )
    latitude = serializers.DecimalField(
        max_digits=8, decimal_places=6,
        help_text="Latitude of the deployment in decimal degrees (required by Camtrap DP: latitude)."
    )
    longitude = serializers.DecimalField(
        max_digits=8, decimal_places=6,
        help_text="Longitude of the deployment in decimal degrees (required by Camtrap DP: longitude)."
    )
    deploymentStart = serializers.DateTimeField(
        source="deployment_start", format="%Y-%m-%dT%H:%M:%S%z",
        help_text="Date and time when the deployment started (required by Camtrap DP: deploymentStart, ISO 8601)."
    )
    deploymentEnd = serializers.DateTimeField(
        source="deployment_start", format="%Y-%m-%dT%H:%M:%S%z",
        help_text="Date and time when the deployment ended (required by Camtrap DP: deploymentEnd, ISO 8601)."
    )
    setupBy = serializers.CharField(
        help_text="Person or organization responsible for setting up the deployment (Camtrap DP: setupBy)."
    )
    cameraID = serializers.CharField(
        help_text="Identifier for the camera trap device used in this deployment (Camtrap DP: cameraID)."
    )
    cameraModel = serializers.CharField(
        help_text="Manufacturer's model name or number of the camera trap device (Camtrap DP: cameraModel)."
    )
    coordinateUncertainty = serializers.FloatField(
        help_text="Uncertainty in the spatial coordinates, in meters (Camtrap DP: coordinateUncertainty)."
    )
    cameraHeight = serializers.FloatField(
        help_text="Height of the camera above ground in meters (Camtrap DP: cameraHeight)."
    )
    cameraHeading = serializers.IntegerField(
        help_text="Compass direction the camera is facing in degrees (Camtrap DP: cameraHeading)."
    )
    baitUse = serializers.BooleanField(
        help_text="Whether bait was used at the deployment (Camtrap DP: baitUse)."
    )
    habitatType = serializers.CharField(
        help_text="Type of habitat at the deployment location (Camtrap DP: habitatType)."
    )
    deploymentGroups = serializers.CharField(
        help_text="Group names or categories associated with this deployment (Camtrap DP: deploymentGroups)."
    )
    deploymentTags = serializers.CharField(
        help_text="Tags to annotate this deployment (Camtrap DP: deploymentTags)."
    )
    deploymentComments = serializers.CharField(
        help_text="Free-form comments about the deployment (Camtrap DP: deploymentComments)."
    )


class DataFileSerializerCTDP(serializers.Serializer):
    mediaID = serializers.CharField(
        source='file_name',
        help_text="Unique identifier for the media file (Camtrap DP: mediaID)."
    )
    deploymentID = serializers.CharField(
        help_text="Identifier for the deployment associated with this media (Camtrap DP: deploymentID)."
    )
    captureMethod = serializers.CharField(
        help_text="Method used to capture the media (e.g., motion detection, time lapse) (Camtrap DP: captureMethod)."
    )
    timestamp = serializers.CharField(
        help_text="Date and time when the media was recorded (Camtrap DP: timestamp, ISO 8601)."
    )
    filePath = serializers.CharField(
        help_text="File path to the media file (Camtrap DP: filePath)."
    )
    fileName = serializers.CharField(
        help_text="Name of the media file (Camtrap DP: fileName)."
    )
    filePublic = serializers.CharField(
        help_text="Indicates if the file is publicly accessible (Camtrap DP: filePublic)."
    )
    fileMediatype = serializers.SerializerMethodField(
        help_text="MIME type of the media file, e.g., image/jpeg, video/mp4 (Camtrap DP: fileMediatype)."
    )
    favorite = serializers.BooleanField(
        help_text="Indicates if the file is marked as a favorite (not a standard Camtrap DP field, custom)."
    )
    mediaComments = serializers.CharField(
        help_text="Comments or notes about the media file (Camtrap DP: mediaComments)."
    )

    def get_fileMediatype(self, obj):
        return mimetypes.guess_type(obj.fileName)[0]


class ObservationSerializerCTDP(serializers.Serializer):
    observationID = serializers.CharField(
        help_text="Unique identifier for this observation (Camtrap DP: observationID)."
    )
    deploymentID = serializers.CharField(
        help_text="Deployment identifier associated with this observation (Camtrap DP: deploymentID)."
    )
    mediaID = serializers.CharField(
        allow_null=True,
        help_text="Media identifier related to this observation, if any (Camtrap DP: mediaID)."
    )
    eventID = serializers.CharField(
        allow_null=True,
        help_text="Identifier for the event grouping observations (Camtrap DP: eventID)."
    )
    eventStart = serializers.CharField(
        allow_null=True,
        help_text="Start time of the event (Camtrap DP: eventStart, ISO 8601)."
    )
    eventEnd = serializers.CharField(
        allow_null=True,
        help_text="End time of the event (Camtrap DP: eventEnd, ISO 8601)."
    )
    observationLevel = serializers.CharField(
        help_text="Level of observation (e.g. image, sequence, deployment) (Camtrap DP: observationLevel)."
    )
    observationType = serializers.CharField(
        help_text="Type of observation (e.g. species, blank, unclassified) (Camtrap DP: observationType)."
    )
    scientificName = serializers.CharField(
        allow_null=True,
        help_text="Scientific name of the observed taxon (Camtrap DP: scientificName)."
    )
    count = serializers.IntegerField(
        help_text="Number of individuals observed (Camtrap DP: count)."
    )
    lifeStage = serializers.CharField(
        allow_null=True, allow_blank=True,
        help_text="Life stage of the observed organism, if known (Camtrap DP: lifeStage)."
    )
    sex = serializers.CharField(
        allow_null=True, allow_blank=True,
        help_text="Sex of the observed organism, if known (Camtrap DP: sex)."
    )
    behavior = serializers.CharField(
        allow_null=True, allow_blank=True,
        help_text="Observed behavior(s) (Camtrap DP: behavior)."
    )
    individualID = serializers.CharField(
        allow_null=True,
        help_text="Identifier for the individual, if known (Camtrap DP: individualID)."
    )
    bboxX = serializers.FloatField(
        allow_null=True,
        help_text="Bounding box X coordinate for detection (Camtrap DP: bboxX)."
    )
    bboxY = serializers.FloatField(
        allow_null=True,
        help_text="Bounding box Y coordinate for detection (Camtrap DP: bboxY)."
    )
    bboxWidth = serializers.FloatField(
        allow_null=True,
        help_text="Bounding box width for detection (Camtrap DP: bboxWidth)."
    )
    bboxHeight = serializers.FloatField(
        allow_null=True,
        help_text="Bounding box height for detection (Camtrap DP: bboxHeight)."
    )
    classificationMethod = serializers.CharField(
        help_text="Method used for classification (Camtrap DP: classificationMethod)."
    )
    classifiedBy = serializers.CharField(
        allow_null=True,
        help_text="Person, software, or device that made the classification (Camtrap DP: classifiedBy)."
    )
    classificationProbability = serializers.FloatField(
        allow_null=True,
        help_text="Probability/score of the classification, if available (Camtrap DP: classificationProbability)."
    )
    observationComments = serializers.CharField(
        allow_null=True,
        help_text="Comments or notes about the observation (Camtrap DP: observationComments)."
    )


class SequenceSerializer(serializers.Serializer):
    eventID = serializers.CharField(
        help_text="Identifier for the sequence event (Camtrap DP: eventID)."
    )
    mediaID = serializers.SerializerMethodField(
        help_text="List of media identifiers associated with this event (Camtrap DP: mediaID)."
    )
    mediaCount = serializers.IntegerField(
        source='nfiles',
        help_text="Total number of media files in this event (Camtrap DP: mediaCount)."
    )
    eventStart = serializers.CharField(
        help_text="Start time of the event/sequence (Camtrap DP: eventStart, ISO 8601)."
    )
    eventEnd = serializers.CharField(
        help_text="End time of the event/sequence (Camtrap DP: eventEnd, ISO 8601)."
    )
    mediaID = serializers.SlugRelatedField(
        queryset=DataFile.objects.all(), many=True, source="data_files", slug_field='file_name',
        help_text="Media files associated with this sequence (Camtrap DP: mediaID)."
    )
