from django.db import models


class Owner(models.Model):
    name = models.CharField(max_length=32)
    email = models.EmailField(unique=True)
    organization = models.ForeignKey(
        'tests.Organization', related_name='staff',
        on_delete=models.CASCADE
    )


class Organization(models.Model):
    name = models.CharField(unique=True, max_length=32)


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
