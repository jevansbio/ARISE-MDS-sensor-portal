from rest_framework import routers

from .viewsets import ObservationViewSet, TaxonAutocompleteViewset, TaxonViewSet

router = routers.DefaultRouter()
router.register(r"observation", ObservationViewSet, basename='observation')
router.register(r"taxon", TaxonViewSet, basename='taxon')
router.register(r"taxon-autocomplete", TaxonAutocompleteViewset, basename='taxon-autocomplete')
