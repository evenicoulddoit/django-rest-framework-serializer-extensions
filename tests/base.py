from django.test import TestCase
from hashids import Hashids

from tests import models


TEST_HASH_IDS = Hashids(salt='testing')


class SerializerMixinTestCase(TestCase):
    """
    Base test case to provide common functionality for serializer mixin tests.
    """
    fixtures = ['test_data.json']

    def setUp(self):
        super(SerializerMixinTestCase, self).setUp()
        self.manufacturer_tesla = models.Manufacturer.objects.get()
        self.carmodel_model_s = models.CarModel.objects.get()
        self.sku_p100d = models.Sku.objects.get(variant='P100D')
        self.sku_70 = models.Sku.objects.get(variant='70')
        self.owner_tyrell = models.Owner.objects.get()
        self.organization_ecorp = models.Organization.objects.get()

    @property
    def expected_complete_data(self):
        """
        Return our expectation of the fully serialized model.
        """
        return dict(
            id=self.carmodel_model_s.pk,
            name=self.carmodel_model_s.name,
            manufacturer=dict(
                id=self.manufacturer_tesla.pk,
                name=self.manufacturer_tesla.name
            ),
            skus=[
                # Model ordering applies
                dict(
                    id=self.sku_p100d.pk,
                    variant=self.sku_p100d.variant,
                    owners=[
                        dict(
                            id=self.owner_tyrell.pk,
                            name=self.owner_tyrell.name,
                            email=self.owner_tyrell.email,
                            organization=dict(
                                id=self.organization_ecorp.id,
                                name=self.organization_ecorp.name
                            )
                        )
                    ]
                ),
                dict(
                    id=self.sku_70.pk,
                    variant=self.sku_70.variant,
                    owners=[]
                )
            ]
        )
