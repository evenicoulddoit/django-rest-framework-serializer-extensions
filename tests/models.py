from django.db import models


class Sku(models.Model):
    variant = models.CharField(max_length=32)
    model = models.ForeignKey(
        'tests.CarModel', related_name='skus', on_delete=models.CASCADE
    )
    owners = models.ManyToManyField('tests.Owner', related_name='cars')

    class Meta:
        ordering = ['id']
        unique_together = (('variant', 'model'),)


class CarModel(models.Model):
    name = models.CharField(max_length=32)
    manufacturer = models.ForeignKey(
        'tests.Manufacturer', related_name='models', on_delete=models.CASCADE
    )


class Manufacturer(models.Model):
    name = models.CharField(max_length=32)


class Owner(models.Model):
    name = models.CharField(max_length=32)
    email = models.EmailField(unique=True)
    organization = models.ForeignKey(
        'tests.Organization', related_name='staff', on_delete=models.CASCADE
    )
    preferences = models.OneToOneField(
        'tests.OwnerPreferences', on_delete=models.PROTECT
    )


class OwnerPreferences(models.Model):
    favorite_manufacturer = models.ForeignKey(
        'tests.Manufacturer', related_name='fans', null=True,
        on_delete=models.SET_NULL
    )
    price_limit_dollars = models.IntegerField(null=True)


class Organization(models.Model):
    name = models.CharField(unique=True, max_length=32)

    def cars(self):
        """
        Custom method which can't be auto-optimized.
        """
        return Sku.objects.filter(owners__organization=self)
