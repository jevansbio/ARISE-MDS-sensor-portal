import django_filters.rest_framework

from .models import User


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class UserFilter(django_filters.FilterSet):
    """
    FilterSet for filtering User objects.
    This filter allows filtering by user ID, with an option to exclude certain IDs.
    """

    id__not_in = NumberInFilter(
        field_name="id",
        lookup_expr="in",
        exclude=True
    )

    class Meta:
        model = User
        fields = {'id': ['exact', 'in']}
