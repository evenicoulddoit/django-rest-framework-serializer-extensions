from __future__ import absolute_import
from collections import OrderedDict

from django.utils import six
from rest_framework import serializers

from rest_framework_serializer_extensions import (
    fields as custom_fields, utils
)


NESTED_DELIMITER = '__'
DEFAULT_MAX_EXPAND_DEPTH = 3


def _get_serializer_hierarchy(serializer):
    """
    Return a string representing the given serializer's hierarchy position.

    We match this hierarchy string against the "nested field names".

    * For a root serializer we return an empty string
    * For a child serializer, we return it's field name (e.g. 'foo')
    * For nested child serializers, we __ delimit (e.g, 'foo__bar')

    Returns:
        (str) - The hierarchy
    """
    name = serializer.field_name or ''
    parent = serializer.parent

    while parent:
        if parent.field_name:
            if name:
                name = '{0}__{1}'.format(parent.field_name, name)
            else:
                name = parent.field_name
        parent = parent.parent

    return name


def _get_nested_field_names(hierarchy, root_field_names):
    """
    Return the collection of field names matching the given hierarchy.

    Arguments:
        hierarchy (str) - The current serializer's hierarchy (see above)
        root_field_names (set) - The nested field names from the root level

    Examples:
        >>> _get_nested_field_names('', {'a', 'b__b1'})
        set({'a', 'b__b1'})

        >>> _get_nested_field_names('a', {'a', 'b__b1'})
        set({'*'})

        >>> _get_nested_field_names('a', {'a__a1', 'a__a2__a3', b__b1'})
        set({'a1', 'a2__a3'})

        >>> _get_nested_field_names('a', {'b', 'c__c1'})
        set({})

    Returns:
        (set)
    """
    matching = set()

    for name in root_field_names:
        # Include all fields on the serializer
        if name == hierarchy:
            matching.add('*')
        elif hierarchy:
            prefix = '{0}{1}'.format(hierarchy, NESTED_DELIMITER)

            if name.startswith(prefix):
                matching.add(name[len(prefix):])
        else:
            matching.add(name)

    return matching


def _field_names_list(field_names):
    return ', '.join(
        '"{0}"'.format(field_name) for field_name in field_names
    )


class ExpandableFieldsMixin(object):
    """
    Expands model representations depending on the serializer context.

    This works very well for ForeignKeys and [One/Many]ToMany fields, but can
    also be applied to serializers which just expand upon the additional
    information, but which might not be required in all circumstantances.

    Serializers are expanded by passing `expand` and/or `expand_id_only`
    iterables.

    The expandable fields should be declared within the serializer's
    Meta class, as a dictionary, where:

        * The keys represent the field name to optionally include
        * The values are either references to a serializer, or a dictionary
          providing advanced configuration, including:
            * serializer: The serializer to use when expanded
            * many (Optional[Boolean]): Whether the field is x-to-many
            * source (Optional[str]):
                The source to the full instance(s)

            * id_source (Optional[str|bool]):
                The source to retrieve the field's ID for Foreign relations.
                Defaults to <field>_id.
                Pass the boolean False to omit the field.
            * id_model (Optional[Model]):
                The model, which is combined with an ID to generate a HashId.
                Defaults to the model within the Meta of the child serializer.

    Example:

        class FooSerializer(ExpandableFieldsMixin)
            class Meta:
                model = foo_models.Foo
                expandable_fields = dict(
                    bar=BarSerializer,
                    zulu=dict(
                        serializer='zulu.serializers.ZuluSerializer',
                        many=True,
                        source='zulu.all'
                    )
                    foo_more=dict(
                        serializer'foo.serializers.FooMoreSerializer',
                        id_source=False,
                        source='*'
                    )
                )

    In the above serializer:

        * The ForeignKey bar is conditionally included when 'bar' is present
          within the to_expand iterable passed to the serializer
        * The `bar_id` field will always be present, and represents the
          external ID of bar
        * The x-to-many zulu instances are serialized fully when 'zulu' is
          present within the to_expand iterable, or as a list of external IDs
          when present within the to_expand_id_only iterable
        * The zulu serializer is passed by import-reference-string
        * The foo_more key will be provided if specified in the to_expand
          iterable, and serializes additional information for the existing
          Foo instance
    """
    def __init__(self, *args, **kwargs):
        super(ExpandableFieldsMixin, self).__init__(*args, **kwargs)
        self.expandable_fields = self._standardise_expandable_definitions(
            self.get_expandable_field_definitions()
        )

    def get_expandable_field_definitions(self):
        try:
            return self.Meta.expandable_fields
        except AttributeError:
            return dict()

    def get_max_expand_depth(self):
        try:
            return self.Meta.max_expand_depth
        except AttributeError:
            return utils.get_setting(
                'MAX_EXPAND_DEPTH', DEFAULT_MAX_EXPAND_DEPTH
            )

    def get_validate_expand_instructions(self):
        try:
            return self.Meta.validate_expand_instructions
        except AttributeError:
            return True

    def get_fields(self):
        fields = super(ExpandableFieldsMixin, self).get_fields()
        fields.update(self._get_expand_fields(fields))
        return fields

    def _standardise_expandable_definitions(self, expandable_fields):
        return {
            key: self._standardise_expandable_definition(definition)
            for key, definition in six.iteritems(expandable_fields)
        }

    def _standardise_expandable_definition(self, definition):
        """
        Return a consistent field definition dictionary.
        """
        if not isinstance(definition, dict):
            definition = dict(serializer=definition)

        # Resolve string references to serializers
        if isinstance(definition['serializer'], six.string_types):
            reference = definition['serializer']
            serializer = utils.import_local(reference)
            assert issubclass(serializer, serializers.BaseSerializer), (
                "{0} is not a serializer".format(reference)
            )
            definition['serializer'] = serializer

        # Custom expansion uses no other fields
        if definition['serializer'] == serializers.SerializerMethodField:
            definition['id_source'] = False
            return definition

        # The model used for the HashId (defaults to the serializer's model)
        if 'id_model' not in definition:
            definition['id_model'] = definition['serializer'].Meta.model

        return definition

    def _parse_root_instructions(self):
        expand_full = set(self.context.get('expand', []))
        expand_id_only = set(self.context.get('expand_id_only', []))

        # ID-only fields implicitly require full expansion of their parents
        for nested_field_name in expand_id_only:
            if NESTED_DELIMITER in nested_field_name:
                expand_full.add(
                    NESTED_DELIMITER.join(
                        nested_field_name.split(NESTED_DELIMITER)[:-1]
                    )
                )

        return dict(full=expand_full, id_only=expand_id_only)

    def _validate_max_depth(self, root_instructions):
        max_depth = self.get_max_expand_depth()

        for nested_field_names in six.itervalues(root_instructions):
            for nested_field_name in nested_field_names:
                depth = len(nested_field_name.split(NESTED_DELIMITER))

                if depth > max_depth:
                    raise ValueError(
                        'Expansion of "{0}" exceeds max depth of {1}'.format(
                            nested_field_name, max_depth
                        )
                    )

    def _expand_instructions(self, root_instructions):
        """
        Return the expand instructions for the current serializer.

        Example: Serializer at hierarchy 'a'
            >>> root_instructions = dict(
            ...     full={'a__a1__a11', 'a__a2', 'b__b1'},
            ...     id_only={'a__a2__a21', 'a__a3', 'b__b2'}
            ... )
            >>> _expand_instructions(root_instructions)
            dict(
                full={'a1', 'a2'},
                id_only={'a3'}
            )
        """
        hierarchy = _get_serializer_hierarchy(self)
        instructions = {}

        for method, root_nested_names in six.iteritems(root_instructions):
            instructions[method] = {
                n.split(NESTED_DELIMITER)[0]
                for n in _get_nested_field_names(hierarchy, root_nested_names)
                if n != '*'
            }

        instructions['id_only'] = {
            name for name in instructions['id_only']
            if name not in instructions['full']
        }

        return instructions

    def get_expand_id_field(self, field_name, field_definition):
        """
        Return the Serializer Field instance to represent the ID.

        Arguments:
            field_name (str)
            field_definition (dict)

        Returns:
            (rest_framework.fields.Field)
        """
        if hasattr(self, 'get_{0}_id'.format(field_name)):
            return serializers.SerializerMethodField(source='*')

        kwargs = dict(read_only=True)

        if 'id_source' in field_definition:
            kwargs.update(source=field_definition['id_source'])

        if utils.get_setting('USE_HASH_IDS', False):
            kwargs.update(pk_field=(
                custom_fields.HashIdField(model=field_definition['id_model'])
            ))

        return serializers.PrimaryKeyRelatedField(**kwargs)

    def get_expand_id_list_field(self, field_name, field_definition):
        """
        Return the Serializer Field instance to represent the ID.

        Arguments:
            field_name (str)
            field_definition (dict)

        Returns:
            (rest_framework.fields.Field)
        """
        method_field_name = 'get_{0}_id_only'.format(field_name)

        # A SerializerMethodField can be used for custom ID generation
        if hasattr(self, method_field_name):
            return serializers.SerializerMethodField(
                method_name=method_field_name,
                source='*'
            )

        if not field_definition.get('many'):
            raise ValueError(
                "Can only expand as ID-only on *-to-many fields"
            )

        kwargs = dict(many=True, read_only=True)

        if 'source' in field_definition:
            kwargs.update(source=field_definition['source'])

        if utils.get_setting('USE_HASH_IDS', False):
            kwargs.update(pk_field=(
                custom_fields.HashIdField(model=field_definition['id_model'])
            ))

        return serializers.PrimaryKeyRelatedField(**kwargs)

    def _validate_instructions(self, instructions, standard_fields):
        if (
            self.get_validate_expand_instructions() is False or
            self.context.get('validate_expand_instructions') is False
        ):
            return

        for method, field_names in six.iteritems(instructions):
            valid_field_names = set(self.expandable_fields)

            # Allow unmatched full expand instructions provided that the
            # field name matches a standard field. This allows
            if method == 'full':
                valid_field_names.update(set(standard_fields))

            unmatched_names = field_names.difference(valid_field_names)

            if unmatched_names:
                raise ValueError(
                    '{0} fields not expandable for serializer "{1}"'.format(
                        _field_names_list(unmatched_names),
                        self.__class__.__name__
                    )
                )

    def _get_expand_fields(self, standard_fields):
        """
        Return a collection of expand fields which match the instructions.
        """
        root_instructions = self._parse_root_instructions()

        if not self.parent:
            self._validate_max_depth(root_instructions)

        expanded_fields = OrderedDict()
        instructions = self._expand_instructions(root_instructions)
        self._validate_instructions(instructions, standard_fields)

        field_iterator = six.iteritems(self.expandable_fields)

        # Expand fields according to their definition and instructions
        for field_name, field_definition in field_iterator:
            # Always provide an ID reference for ForeignKeys
            if (
                not field_definition.get('many') and
                field_definition.get('id_source') is not False
            ):
                expanded_fields['{0}_id'.format(field_name)] = (
                    self.get_expand_id_field(field_name, field_definition)
                )

            # Serialize the full instance(s) if required
            if field_name in instructions['full']:
                kwargs = dict()

                if 'source' in field_definition:
                    kwargs.update(source=field_definition['source'])
                if field_definition.get('many'):
                    kwargs.update(many=True)

                expanded_fields[field_name] = (
                    field_definition['serializer'](**kwargs)
                )

            # Serialize the IDs only for *-to-many fields if required
            elif field_name in instructions['id_only']:
                expanded_fields[field_name] = self.get_expand_id_list_field(
                    field_name, field_definition
                )

        return expanded_fields


class OnlyFieldsMixin(object):
    """
    Reduce a serializer's fields to only the ones specified.
    """
    def get_fields(self):
        """
        Restrict the fields based on a set of names if provided.
        """
        fields = super(OnlyFieldsMixin, self).get_fields()

        try:
            only = self.context['only']
        except KeyError:
            return fields

        hierarchy = _get_serializer_hierarchy(self)
        only_nested_names = _get_nested_field_names(hierarchy, only)

        # Flatten the nested names to return a list of field names at the
        # current hierarchy to whitelist
        only_names = {n.split(NESTED_DELIMITER)[0] for n in only_nested_names}

        # Include all fields if either explicitly told to, or no fields were
        # matched (which can only occur if a parent had been whitelisted).
        if only_names == set() or only_names == {'*'}:
            return fields

        if '*' in only_names:
            raise ValueError(
                'Cannot serialize {0} fields for serializer "{1}". '
                'Either serialize some fields, or all'.format(
                    _field_names_list(only_names),
                    self.__class__.__name__
                )
            )

        unmatched_names = only_names.difference(set(fields))

        if unmatched_names:
            raise ValueError(
                '{0} fields not found on serializer "{1}"'.format(
                    _field_names_list(unmatched_names),
                    self.__class__.__name__
                )
            )

        return {
            name: field
            for name, field in six.iteritems(fields)
            if name in only_names
        }


class ExcludeFieldsMixin(object):
    """
    Reduce a serializer's fields by removing the specified fields.
    """
    def get_fields(self):
        """
        Exclude the fields based on a set of names if provided.
        """
        fields = super(ExcludeFieldsMixin, self).get_fields()

        try:
            exclude = self.context['exclude']
        except KeyError:
            return fields

        hierarchy = _get_serializer_hierarchy(self)
        exclude_nested_names = _get_nested_field_names(hierarchy, exclude)

        # Only exclude a field if it exactly matching the current hierarchy
        exclude_names = {
            n for n in exclude_nested_names if NESTED_DELIMITER not in n
        }

        unmatched_names = exclude_names.difference(set(fields))

        if unmatched_names:
            raise ValueError(
                '{0} fields not found on serializer "{1}"'.format(
                    _field_names_list(unmatched_names),
                    self.__class__.__name__
                )
            )

        return {
            name: field
            for name, field in six.iteritems(fields)
            if name not in exclude_names
        }


class SerializerHelpersMixin(object):
    @property
    def hierarchy(self):
        return _get_serializer_hierarchy(self)

    def represent_child(self, name, serializer, instance, **kwargs):
        """
        Shortcut to allow a SerializerMethodField to represent a child.

        The child serializer is invoked with the same context as the parent,
        and is bound to the parent.
        """
        serializer_kwargs = dict(instance=instance, context=self.context)
        serializer_kwargs.update(kwargs)
        serializer = serializer(**serializer_kwargs)
        serializer.bind(name, self)
        return serializer.data


class SerializerExtensionsMixin(
    OnlyFieldsMixin, ExcludeFieldsMixin, ExpandableFieldsMixin,
    SerializerHelpersMixin
):
    """
    A collection of serializer extensions, which allow for:

    * Blacklisting fields through an "exclude" context variable
    * Whitelisting fields through an "only" context variable
    * Expanding related fields through an "expand" context variable
    * Other helper methods

    Blacklisting and whitelisting takes precedence over expanding, and can
    be used in combination with one another.
    """
