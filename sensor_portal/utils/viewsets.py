from django.conf import settings
from rest_framework.viewsets import ModelViewSet


class OptionalPaginationViewSetMixIn(ModelViewSet):
    """By default, paginate_queryset returns None when no paginator is set. This extends
    it to also return None if no 'page' query param is set"""

    def paginate_queryset(self, queryset):
        if self.paginator \
                and self.request.query_params.get(self.paginator.page_query_param, None) is None \
                and queryset.count() < settings.REST_FRAMEWORK['MAX_PAGE_SIZE']:
            return None
        return super().paginate_queryset(queryset)


class AddOwnerViewSetMixIn(ModelViewSet):
    def perform_create(self, serializer):
        print("Add owner")
        serializer.save(owner=self.request.user)
        return super().perform_create(serializer)


class CheckFormViewSetMixIn(ModelViewSet):
    def get_serializer_context(self):
        context = super(CheckFormViewSetMixIn, self).get_serializer_context()

        context.update(
            {'form': 'multipart/form-data' in self.request.content_type})
        return context


class CheckAttachmentViewSetMixIn(ModelViewSet):
    """
        Viewset mixin to call a check_attachment function on create and update.

        check_attachment should be overriden inside the inheriting viewset.

        IMPORTANT: Make sure this is first class inherited, otherwise the object can be created
        before a check is made.
    """

    def perform_create(self, serializer):
        print("check attachment")
        self.check_attachment(serializer)
        return super().perform_create(serializer)

    def perform_update(self, serializer):
        print("check attachment")
        self.check_attachment(serializer)
        return super().perform_update(serializer)

    def check_attachment(self, serializer):
        pass
