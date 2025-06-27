from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiParameter, extend_schema_serializer,
                                   inline_serializer)
from rest_framework import serializers
from utils.serializers import DummyJSONField

from .serializers import (DataFileSerializer, DataFileUploadSerializer,
                          DeploymentSerializer, DeviceSerializer)

ctdp_parameter = OpenApiParameter("ctdp",
                                  OpenApiTypes.BOOL,
                                  OpenApiParameter.QUERY,
                                  description='Set True to return in camtrap DP format')
geoJSON_parameter = OpenApiParameter("geojson",
                                     OpenApiTypes.BOOL,
                                     OpenApiParameter.QUERY,
                                     description='Set True to return in geoJSON format')

inline_id_serializer = inline_serializer("IDserializer",
                                         {"ids":
                                          serializers.ListField(child=serializers.IntegerField(), required=True)})
inline_id_serializer_optional = inline_serializer("IDserializer",
                                                  {"ids":
                                                   serializers.ListField(child=serializers.IntegerField(), required=False)})
inline_count_serializer = inline_serializer("InlineCountSerializer",
                                            {"object_n":
                                             serializers.ListField(child=serializers.IntegerField(), required=True)})
inline_metric_serialiser = inline_serializer(
    "MetricSerializer",
    {"metric_name":
     inline_serializer("NestedMetricSerializer",
                       {"name": serializers.CharField(default="metric_name"),
                        "x_label": serializers.CharField(default="Date"),
                        "y_label": serializers.CharField(default="Metric"),
                        "x_values": serializers.ListField(child=serializers.IntegerField()),
                        "y_values": serializers.ListField(child=serializers.IntegerField()),
                        "plot_type": serializers.ListField(child=serializers.CharField(), default=["bar", "scatter"])
                        })
     })


inline_job_start_serializer = inline_serializer("StartJobSerializer",
                                                {"detail": serializers.CharField(default="Job started")})


@extend_schema_serializer(component_name="DeploymentSerializer",
                          )
class DummyDeploymentSerializer(DeploymentSerializer):

    user_is_owner = serializers.BooleanField(
        read_only=True, default=False, required=False)

    user_is_manager = serializers.BooleanField(
        read_only=True, default=False, required=False)

    colour = serializers.CharField(
        read_only=True, default="blue", required=False)
    symbol = serializers.CharField(
        read_only=True, default="camera", required=False)

    extra_data = DummyJSONField(
        required=False, help_text="Extra taxon data that the standard fields do not cover.")


@extend_schema_serializer(component_name="DeviceSerializer",
                          )
class DummyDeviceSerializer(DeviceSerializer):

    user_is_owner = serializers.BooleanField(
        read_only=True, default=False, required=False)

    user_is_manager = serializers.BooleanField(
        read_only=True, default=False, required=False)

    colour = serializers.CharField(
        read_only=True, default="blue", required=False)
    symbol = serializers.CharField(
        read_only=True, default="camera", required=False)

    extra_data = DummyJSONField(
        required=False, help_text="Extra taxon data that the standard fields do not cover.")

    data_handler = serializers.CharField(
        read_only=True, default="Default image handler", required=False)
    data_handler_ID = serializers.IntegerField(
        read_only=True, default=0, required=False)


@extend_schema_serializer(component_name="DataFileSerializer",
                          )
class DummyDataFileSerializer(DataFileSerializer):
    favourite = serializers.BooleanField(
        read_only=True, default=False, required=False)
    can_annotate = serializers.BooleanField(
        read_only=True, default=False, required=False)
    path = None


@extend_schema_serializer(component_name="DataFileUploadSerializer",
                          )
class DummyDataFileUploadSerializer(DataFileUploadSerializer):

    files = serializers.ListField(child=serializers.FileField())

    extra_data = serializers.ListField(required=False,
                                       child=DummyJSONField(),
                                       help_text="Extra taxon data that the standard fields do not cover.")

    file_names = None


inline_upload_response_serializer = inline_serializer(
    "UploadResponseSerializer",
    {"uploaded_files": serializers.ListField(child=DummyDataFileSerializer()),
     "invalid_files": inline_serializer("InvalidSerializer",
                                        {"originalfilename2":
                                         inline_serializer("InvalidFileSerializer",
                                                           {"message": serializers.CharField(default="File upload failed for this reason."),
                                                            "status": serializers.IntegerField(default=400)})}),
     "existing_files": inline_serializer("ExistingSerializer",
                                         {"originalfilename3":
                                          inline_serializer("ExistingFileSerializer",
                                                            {"message": serializers.CharField(default="Already in database."),
                                                             "status": serializers.IntegerField(default=200)})}), })
