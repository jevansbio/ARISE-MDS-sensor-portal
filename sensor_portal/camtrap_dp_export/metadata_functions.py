import json
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union

import pandas as pd
from data_models.models import Deployment, Project
from django.conf import settings
from django.contrib.gis.geos import MultiPoint
from django.db.models.query import QuerySet
from observation_editor.models import Observation
from pandas import DataFrame

from .querysets import (get_ctdp_deployment_qs, get_ctdp_media_qs,
                        get_ctdp_obs_qs, get_ctdp_seq_qs)
from .serializers import (DataFileSerializerCTDP, DeploymentSerializerCTDP,
                          ObservationSerializerCTDP, SequenceSerializer)


def create_camtrap_dp_metadata(
    file_qs: QuerySet,
    uuid: str = "",
    title: str = "",
) -> Tuple[DataFrame, DataFrame, DataFrame, DataFrame, Dict[str, Any]]:
    """
    Create Camtrap-DP metadata and table dataframes for export.

    Args:
        file_qs (QuerySet): Queryset of data files to export.
        uuid (str, optional): Unique identifier for the dataset. Defaults to "".
        title (str, optional): Title for the dataset. Defaults to "".

    Returns:
        Tuple[
            DataFrame,  # file_df: DataFrame of media files
            DataFrame,  # observation_df: DataFrame of observations
            DataFrame,  # deploy_df: DataFrame of deployments
            DataFrame,  # event_df: DataFrame of events/sequences
            Dict[str, Any]  # metadata: Metadata dictionary for Camtrap-DP
        ]
    """
    # get files
    file_qs = file_qs.distinct()
    file_qs = get_ctdp_media_qs(file_qs)

    # get deployments
    deployment_qs = Deployment.objects.filter(files__in=file_qs).distinct()
    deployment_qs = get_ctdp_deployment_qs(deployment_qs)

    # get observations
    observation_qs = Observation.objects.filter(
        data_files__in=file_qs).distinct()
    event_qs = get_ctdp_seq_qs(observation_qs)
    observation_qs = get_ctdp_obs_qs(observation_qs)

    project_qs = Project.objects.filter(deployments__in=deployment_qs).exclude(
        project_ID=settings.GLOBAL_PROJECT_ID
    ).distinct()
    principals = list(
        project_qs.values(
            "principal_investigator", "principal_investigator_email", "organisation"
        )
    )
    for x in principals:
        x["title"] = x.pop("principal_investigator")
        x["email"] = x.pop("principal_investigator_email")
        x.update({"role": "principal_investigator"})
        x["organization"] = x.pop("organisation")

    contributors = list(project_qs.values(
        "contact", "contact_email", "organisation"))
    for x in contributors:
        x["title"] = x.pop("contact")
        x["email"] = x.pop("contact_email")
        x.update({"role": "contributor"})
        x["organization"] = x.pop("organisation")

    all_contributors = principals + contributors

    all_contributors_distinct_title: List[Dict[str, Any]] = []
    for x in all_contributors:
        if x["title"] not in [y["title"] for y in all_contributors_distinct_title]:
            all_contributors_distinct_title.append(x)

    # Get 4 dicts
    file_dict = DataFileSerializerCTDP(file_qs, many=True).data
    observation_dict = ObservationSerializerCTDP(
        observation_qs, many=True).data
    deploy_dict = DeploymentSerializerCTDP(deployment_qs, many=True).data
    event_dict = SequenceSerializer(event_qs, many=True).data

    file_df = pd.DataFrame.from_dict(file_dict)
    deploy_df = pd.DataFrame.from_dict(deploy_dict)
    if len(observation_dict) == 0:
        observation_dict = {x: []
                            for x in ObservationSerializerCTDP().get_fields().keys()}
    if len(event_dict) == 0:
        event_dict = {x: [] for x in SequenceSerializer().get_fields().keys()}

    observation_df = pd.DataFrame.from_dict(observation_dict)
    event_df = (
        pd.DataFrame.from_dict(event_dict)
        .explode("mediaID")
        .drop_duplicates(["eventID", "mediaID"])
    )

    project_dict = {
        "title": project_qs.first().name,
        "description": project_qs.first().objectives,
        "samplingDesign": "systematic random",
        "captureMethod": list(file_df.captureMethod.unique()),
        "individualAnimals": any([x is not None for x in observation_df.individualID]),
        "observationLevel": list(file_df.captureMethod.unique()),
    }

    points = deployment_qs.filter(
        point__isnull=False).values_list("point", flat=True)
    all_points = MultiPoint(*points)
    hull = all_points.convex_hull

    spatial_dict = json.loads(hull.geojson)
    spatial_dict.update({"bbox": list(hull.extent)})

    taxon_ids = observation_qs.values(
        "taxon__species_name", "taxon__taxon_code")
    taxon_dict: List[Dict[str, Union[str, None]]] = []

    for x in taxon_ids:
        if x["taxon__taxon_code"] != "":
            taxon_ID = f"https://www.gbif.org/{x['taxon__taxon_code']}"
        else:
            taxon_ID = None
        taxon_dict.append(
            {"scientificName": x["taxon__species_name"], "taxonID": taxon_ID})

    metadata: Dict[str, Any] = {
        "resources": [
            {
                "name": "deployments",
                "path": "deployments.csv",
                "profile": "tabular-data-resource",
                "format": "csv",
                "mediatype": "text/csv",
                "encoding": "utf-8",
                "schema": "https://raw.githubusercontent.com/tdwg/camtrap-dp/1.0/deployments-table-schema.json",
            },
            {
                "name": "media",
                "path": "media.csv",
                "profile": "tabular-data-resource",
                "format": "csv",
                "mediatype": "text/csv",
                "encoding": "utf-8",
                "schema": "https://raw.githubusercontent.com/tdwg/camtrap-dp/1.0/media-table-schema.json",
            },
            {
                "name": "observations",
                "path": "observations.csv",
                "profile": "tabular-data-resource",
                "format": "csv",
                "mediatype": "text/csv",
                "encoding": "utf-8",
                "schema": "https://raw.githubusercontent.com/tdwg/camtrap-dp/1.0/observations-table-schema.json",
            },
            {
                "name": "events",
                "path": "events.csv",
                "profile": "tabular-data-resource",
                "format": "csv",
                "mediatype": "text/csv",
                "encoding": "utf-8",
                "description": "Table of observation events, listing the media items that make up those events",
            },
        ],
        "profile": "https://raw.githubusercontent.com/tdwg/camtrap-dp/1.0/camtrap-dp-profile.json",
        "name": title,
        "id": uuid,
        "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "title": "Camtrap DP dataset",
        "contributors": all_contributors_distinct_title,
        "description": "",
        "version": "1.0",
        "keywords": [""],
        "image": "",
        "homepage": "",
        "sources": [{"title": "ARISE-MDS"}],
        "licenses": [
            {"name": "CC0-1.0", "scope": "data"},
            {"path": "http://creativecommons.org/licenses/by/4.0/", "scope": "media"},
        ],
        "bibliographicCitation": "",
        "project": project_dict,
        "coordinatePrecision": 0.00001,
        "spatial": spatial_dict,
        "temporal": {
            "start": pd.to_datetime(deploy_df["deploymentStart"], format="%Y-%m-%dT%H:%M:%S%z")
            .min()
            .date()
            .strftime("%Y-%m-%d"),
            "end": pd.to_datetime(deploy_df["deploymentEnd"], format="%Y-%m-%dT%H:%M:%S%z")
            .max()
            .date()
            .strftime("%Y-%m-%d"),
        },
        "taxonomic": taxon_dict,
        "relatedIdentifiers": [],
    }

    return file_df, observation_df, deploy_df, event_df, metadata
