import logging
import math
import statistics
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from django.core.exceptions import MultipleObjectsReturned
from thefuzz import fuzz

logger = logging.getLogger(__name__)


def GBIF_result_match(
    search_string: str, gbif_result: Dict[str, Any]
) -> Dict[str, Optional[Union[int, float]]]:
    """
    Perform fuzzy matching between a search string and a single GBIF API result.

    Args:
        search_string: User input string to search for (e.g., species name).
        gbif_result: A dictionary representing a single species result from GBIF.

    Returns:
        A dictionary containing max scientific and vernacular name scores,
        median score over all name types, and count of scores > 50.
    """
    # Normalize the search string for more robust comparison
    search_string = search_string.lower()
    keys_to_search = ['scientificName', 'canonicalName']

    # Fuzzy match against both scientific and canonical names
    scores = [
        fuzz.ratio(search_string, gbif_result.get(x, "").lower())
        for x in keys_to_search
    ]

    # Fuzzy match against all vernacular (common) names
    vernacular_scores = [
        fuzz.ratio(search_string, x['vernacularName'].lower())
        for x in gbif_result.get('vernacularNames', [])
    ]

    # Find the highest vernacular score, or None if there are no vernaculars
    try:
        max_vernacular_score = max(vernacular_scores)
    except ValueError:
        max_vernacular_score = None

    # Compute the max scientific score
    maximum_score = max(scores)
    # The median across all scores (scientific, canonical, vernacular)
    if vernacular_scores + scores:
        median_score = statistics.median(vernacular_scores + scores)
    else:
        median_score = 0
    # Count how many scores are above the threshold of 50
    n_scores_gt_50 = len([x for x in scores + vernacular_scores if x > 50])

    return {
        "max_scientific_score": maximum_score,
        "max_vernacular_score": max_vernacular_score,
        "median_score": median_score,
        "n_scores_gt_50": n_scores_gt_50
    }


def GBIF_species_search(
    search_string: str
) -> Tuple[List[Dict[str, Any]], List[float]]:
    """
    Query the GBIF API for species matching the search string, scoring and ranking results.

    Args:
        search_string: The string (species name) to search for.

    Returns:
        Tuple containing:
            - List of sorted GBIF result dictionaries (best match first)
            - List of overall scores for each result (matching order)
    """
    gbif_response = requests.get(
        "https://api.gbif.org/v1/species/search",
        params={
            "q": search_string,
            "datasetKey": "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c",
            "limit": 5,
            "verbose": True
        }
    )
    # Parse results or empty list if none
    gbif_data = gbif_response.json().get('results', [])

    # Score each result using the custom fuzzy matcher
    all_scores = [GBIF_result_match(search_string, x) for x in gbif_data]

    # The best score for each result (across all name types)
    scores = [max([y for y in x.values() if y is not None])
              for x in all_scores]

    # Give a huge boost to exact matches
    for i in range(len(all_scores)):
        if all_scores[i]["max_scientific_score"] == 100:
            all_scores[i]["max_scientific_score"] = 1000
        if all_scores[i]["max_vernacular_score"] == 100:
            all_scores[i]["max_vernacular_score"] = 1000

    # Compute a combined score for each result (product of all available scores)
    multi_score = [
        math.prod([y for y in x.values() if y is not None])
        for x in all_scores
    ]

    # Sort results by combined score, descending
    sorted_items = sorted(enumerate(multi_score),
                          key=lambda x: x[1], reverse=True)
    gbif_data = [gbif_data[i[0]] for i in sorted_items]
    scores = [scores[i[0]] for i in sorted_items]

    return gbif_data, scores


def GBIF_taxoncode_from_search(
    search_string: str, threshold: int = 80
) -> List[Tuple[int, int]]:
    """
    Return taxon codes from a search string if match score is above threshold.

    Args:
        search_string: The string to search for (usually a species name).
        threshold: Minimum score for a match to be accepted (default 80).

    Returns:
        List of (taxon code, taxonomic level) tuples for the best match, or empty list.
    """
    gbif_data, gbif_scores = GBIF_species_search(search_string)
    if len(gbif_data) == 0:
        return []
    if gbif_scores[0] >= threshold:
        gbif_data_0 = gbif_data[0]
        all_keys = GBIF_get_taxoncodes(gbif_data_0)
        if len(all_keys) > 0:
            return all_keys
    return []


def GBIF_get_taxoncodes(
    gbif_data: Dict[str, Any]
) -> List[Tuple[int, int]]:
    """
    Extract all available taxonomic codes and their levels from a GBIF result.

    Args:
        gbif_data: Dictionary containing GBIF taxon data.

    Returns:
        List of (taxon code, taxonomic level) tuples, ordered from species up to kingdom.
    """
    # List of GBIF taxonomic ranks, ordered from most specific to most general
    rank_keys = [
        'speciesKey', 'genusKey', 'familyKey', 'orderKey',
        'classKey', 'phylumKey', 'kingdomKey'
    ]
    all_keys: List[Tuple[int, int]] = []
    for taxonomic_level, rank_key in enumerate(rank_keys):
        curr_key = gbif_data.get(rank_key, None)
        if curr_key is not None:
            # Validate the key by checking for major issues in GBIF data
            species_data = GBIF_get_species(curr_key)
            issues = species_data.get('issues', [])
            if any([x in issues for x in ['NO_SPECIES']]):
                continue
            all_keys.append((curr_key, taxonomic_level))

    # Handle special case where the result is a subspecies: use its own key
    if gbif_data.get('rank') == 'SUBSPECIES' and all_keys:
        all_keys[0] = (gbif_data.get('key'), 0)

    return all_keys


def GBIF_get_species(
    species_key: int
) -> Dict[str, Any]:
    """
    Retrieve a species' detailed metadata from GBIF by its key.

    Args:
        species_key: Integer GBIF species key.

    Returns:
        Dictionary of species metadata returned by GBIF.
    """
    gbif_response = requests.get(
        f"https://api.gbif.org/v1/species/{species_key}")
    gbif_data = gbif_response.json()
    return gbif_data


def GBIF_to_avibase(
    species_key: int
) -> Optional[str]:
    """
    Map a GBIF species key to an Avibase taxonConceptID using GBIF occurrence API.

    Args:
        species_key: Integer GBIF species key.

    Returns:
        Avibase taxonConceptID string if found, otherwise None.
    """
    gbif_response = requests.get(
        "https://api.gbif.org/v1/occurrence/search",
        params={
            'taxonKey': species_key,
            'limit': 1,
            'datasetKey': '4fa7b334-ce0d-4e88-aaae-2e0c138d049e'
        }
    )
    if gbif_response.status_code != 200:
        logger.error("GBIF to avibase failed: %s %s",
                     gbif_response.status_code, gbif_response.text)
        return None
    gbif_data = gbif_response.json().get('results', [])
    if gbif_data:
        avibase = gbif_data[0].get('taxonConceptID')
        return avibase
    else:
        return None


def GBIF_get_or_create_taxon_object_from_taxon_code(
    taxon_code: int
) -> Tuple[Any, bool]:
    """
    Retrieve or create a Taxon model object from a GBIF taxon code.

    Args:
        taxon_code: Integer GBIF taxon code.

    Returns:
        Tuple of (Taxon object, boolean indicating if it was created).
    """
    from .models import Taxon
    species_data = GBIF_get_species(taxon_code)
    all_taxon_codes = GBIF_get_taxoncodes(species_data)
    try:
        # Try to get or create the Taxon object
        taxon_obj, created = Taxon.objects.get_or_create(
            species_name=species_data.get("canonicalName"),
            species_common_name=species_data.get("vernacularName", ""),
            taxon_source=1,
            taxon_code=all_taxon_codes[0][0],
            taxonomic_level=all_taxon_codes[0][1]
        )
    except MultipleObjectsReturned:
        # If multiple objects exist, just return the first one
        taxon_obj = Taxon.objects.filter(
            species_name=species_data.get("canonicalName"),
            species_common_name=species_data.get("vernacularName", ""),
            taxon_source=1,
            taxon_code=all_taxon_codes[0][0],
            taxonomic_level=all_taxon_codes[0][1]
        ).first()
        created = False

    return taxon_obj, created
