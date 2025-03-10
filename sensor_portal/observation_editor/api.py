from rest_framework import routers

from .viewsets import ObservationViewSet, TaxonAutocompleteViewset

router = routers.DefaultRouter()
router.register(r"observation", ObservationViewSet, basename='observation')
router.register(r"taxon", TaxonAutocompleteViewset,
                basename='taxon')
