import django_filters.rest_framework


class GenericFilterMixIn(django_filters.FilterSet):
    """
    A mixin for generic filtering of objects based on their ID, creation, and modification dates.
    Also provides functionality to attach help text to filters based on field names and lookup expressions.
    """
    created_after = django_filters.DateFilter(
        field_name='created_on', lookup_expr='gt', help_text="Object was created after this date")
    created_before = django_filters.DateFilter(
        field_name='created_on', lookup_expr='lte', help_text="Object was created before this date")
    modified_after = django_filters.DateFilter(
        field_name='modified_on', lookup_expr='gt', help_text="Object was modified after this date")
    modified_before = django_filters.DateFilter(
        field_name='modified_on', lookup_expr='lte', help_text="Object was modified before this date")

    field_help_dict = {'id': "Unique numeric identifier of the object.", }

    lookup_expr_dict = {"exact": "Exact match",
                        "in": "Match any of the values in the list",
                        "gt": "Greater than",
                        "gte": "Greater than or equal to",
                        "lt": "Less than",
                        "lte": "Less than or equal to",
                        "contains": "Partial match (case-insensitive)"}

    class Meta:
        fields = {
            'id': ['exact', 'in']
        }

    @classmethod
    def filter_for_field(cls, f, name, lookup_expr):
        filter = super(GenericFilterMixIn, cls).filter_for_field(
            f, name, lookup_expr)

        help_text = f.help_text

        if help_text == "":

            help_text = cls.field_help_dict.get(
                name, name.replace("__", " ").replace('_', ' ')+".")

        new_help_text = cls.lookup_expr_dict.get(
            lookup_expr, lookup_expr.replace("__", " ").replace('_', ' '))

        filter.extra['help_text'] = help_text + " " + new_help_text

        return filter


class ExtraDataFilterMixIn(django_filters.FilterSet):
    """
    Implements a method for filtering by extra data JSON fields.
    """
    extra_data = django_filters.CharFilter(
        method='extra_data_filter', help_text="Filter by extra data. Format: extra_data__key__value.")

    def extra_data_filter(self, queryset, name, value):
        # unpack value
        newvalue = value.split("__")[-1]
        newname = "__".join(value.split("__")[:-1])
        newname = name + "__" + newname
        return queryset.filter(**{
            newname: newvalue,
        })
