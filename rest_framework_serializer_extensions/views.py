from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, Http404

from rest_framework_serializer_extensions import utils


class SerializerExtensionsAPIViewMixin(object):
    """
    Mixin to provide support for Serializer Extensions within API views.
    """
    extensions_query_params_enabled = True

    def get_serializer_context(self):
        context = (
            super(SerializerExtensionsAPIViewMixin, self)
            .get_serializer_context()
        )
        context.update(self.get_extensions_mixin_context())
        return context

    def get_extensions_query_params_enabled(self):
        """
        Return whether the serializer context can be set using query params.
        """
        return self.extensions_query_params_enabled

    def get_extensions_mixin_context(self):
        """
        Return the context to be used by an extensions enabled serializer.

        The field names to include, exclude or expand can be set either
        through query parameters, or by the view.
        """
        context = dict()
        params_enabled = self.get_extensions_query_params_enabled()

        for field in ['expand', 'expand_id_only', 'exclude', 'only']:
            field_names = getattr(self, 'extensions_{0}'.format(field), [])

            if params_enabled:
                query_params = self.request.query_params.getlist(field)

                if query_params:
                    if len(query_params) == 1 and ',' in query_params[0]:
                        field_names = query_params[0].split(',')
                    else:
                        field_names = query_params

            context[field] = set(field_names)

        return context


class ExternalIdViewMixin(object):
    """
    Allow external IDs to be used for generic API views.
    """
    def get_object(self):
        """
        Extend the vanilla get_object() method to retrieve by external_id.

        Translate the external ID to the internal one explicitly, rather than
        calling get_by_external_id() in order to allow for additional
        filtering.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        assert self.lookup_field == 'pk', (
            'View %s cannot have a custom lookup_field value, as the '
            'ExternalIdViewMixin expects to retrieve the object by its '
            'primary key.' %
            (self.__class__.__name__)
        )

        try:
            internal_id = utils.internal_id_from_model_and_external_id(
                queryset.model, self.kwargs[lookup_url_kwarg]
            )
        except ObjectDoesNotExist:
            raise Http404

        obj = get_object_or_404(queryset, pk=internal_id)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
