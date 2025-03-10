import math
import statistics

import requests
from thefuzz import fuzz


def GBIF_result_match(search_string, gbif_result):
    # Another lay of fuzzy matching on top of the GBIF API results
    search_string = search_string.lower()
    keys_to_search = ['scientificName', 'canonicalName']
    scores = [fuzz.ratio(search_string, gbif_result.get(x, "").lower())
              for x in keys_to_search]

    vernacular_scores = [fuzz.ratio(search_string, x['vernacularName'].lower(
    )) for x in gbif_result['vernacularNames']]
    try:
        max_vernacular_score = max(vernacular_scores)
    except:
        max_vernacular_score = None

    maximum_score = max(scores)
    median_score = statistics.median(vernacular_scores+scores)
    n_scores_gt_50 = len([x for x in scores+vernacular_scores if x > 50])

    return {"max_scientific_score": maximum_score,
            "max_vernacular_score": max_vernacular_score,
            "median_score": median_score,
            "n_scores_gt_50": n_scores_gt_50}


def GBIF_species_search(search_string):
    gbif_response = requests.get("https://api.gbif.org/v1/species/search",
                                 params={
                                     "q": search_string,
                                     "datasetKey": "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c",
                                     "limit": 5,
                                     "verbose": True})

    gbif_data = gbif_response.json()['results']

    all_scores = [GBIF_result_match(search_string, x) for x in gbif_data]
    scores = [max([y for y in x.values() if y is not None])
              for x in all_scores]
    for i in range(len(all_scores)):
        # Weight exact matches far more highly
        if all_scores[i]["max_scientific_score"] == 100:
            all_scores[i]["max_scientific_score"] = 1000
        if all_scores[i]["max_vernacular_score"] == 100:
            all_scores[i]["max_vernacular_score"] = 1000

    multi_score = [math.prod([y for y in x.values() if y is not None])
                   for x in all_scores]
    # sort GBIF data by scores
    gbif_data = [gbif_data[i[0]] for i in sorted(
        enumerate(multi_score), key=lambda x: x[1], reverse=True)]

    # sort scores by scores
    scores = [scores[i[0]] for i in sorted(
        enumerate(multi_score), key=lambda x: x[1], reverse=True)]

    return gbif_data, scores


def GBIF_taxoncode_from_search(search_string, threshold=80):
    gbif_data, gbif_scores = GBIF_species_search(search_string)
    if len(gbif_data) == 0:
        return []
    if gbif_scores[0] >= threshold:
        gbif_data = gbif_data[0]
        all_keys = GBIF_get_taxoncodes(gbif_data)
        if len(all_keys) > 0:
            return all_keys

    return []


def GBIF_get_taxoncodes(gbif_data):

    rank_keys = ['speciesKey',
                 'genusKey',
                 'familyKey',
                 'orderKey',
                 'classKey',
                 'phylumKey',
                 'kingdomKey']
    all_keys = []
    for taxonomic_level, rank_key in enumerate(rank_keys):
        curr_key = gbif_data.get(rank_key, None)
        if curr_key is not None:
            # check the data for major issues
            species_data = GBIF_get_species(curr_key)
            issues = species_data.get('issues')
            if any([x in issues for x in ['NO_SPECIES']]):
                continue
            all_keys.append((curr_key, taxonomic_level))

    if gbif_data.get('rank') == 'SUBSPECIES':
        all_keys[0] = (gbif_data.get('key'), 0)

    return all_keys


def GBIF_get_species(species_key):
    gbif_response = requests.get(
        f"https://api.gbif.org/v1/species/{species_key}")
    gbif_data = gbif_response.json()
    return gbif_data


def GBIF_to_avibase(species_key):
    gbif_response = requests.get("https://api.gbif.org/v1/occurrence/search",
                                 params={
                                     'taxonKey': species_key,
                                     'limit': 1,
                                     'datasetKey': '4fa7b334-ce0d-4e88-aaae-2e0c138d049e'
                                 }
                                 )
    gbif_data = gbif_response.json()['results']
    if len(gbif_data) > 0:
        avibase = gbif_data[0]['taxonConceptID']
        return avibase
    else:
        return None


def GBIF_get_or_create_taxon_object_from_taxon_code(taxon_code):
    from .models import Taxon
    species_data = GBIF_get_species(taxon_code)
    all_taxon_codes = GBIF_get_taxoncodes(species_data)
    taxon_obj, created = Taxon.objects.get_or_create(
        species_name=species_data.get("canonicalName"),
        species_common_name=species_data.get("vernacularName", ""),
        taxon_source=1,
        taxon_code=all_taxon_codes[0][0],
        taxonomic_level=all_taxon_codes[0][1]
    )
    return taxon_obj, created
