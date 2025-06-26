from drf_spectacular.utils import extend_schema, extend_schema_view
from observation_editor.filtersets import ObservationFilter
from observation_editor.models import Observation
from utils.viewsets import OptionalPaginationViewSetMixIn

from .querysets import get_ctdp_seq_qs
from .serializers import SequenceSerializer


@extend_schema(summary="Sequences of observations",
               description="An observation can be linked to multiple files.\
                   A single observation linked to multiple files is considered a sequence",
               tags=["Observations"],
               methods=["get"],
               )
@extend_schema_view(
    retrieve=extend_schema(exclude=True)
)
class SequenceViewsetCTDP(OptionalPaginationViewSetMixIn):
    """
    A ViewSet for listing sequences of observations in Camtrap DP format.
    """
    http_method_names = ['get', 'head']
    queryset = get_ctdp_seq_qs(Observation.objects.all())
    serializer_class = SequenceSerializer
    filterset_class = ObservationFilter
