import uuid

from django.db import models


class Hello(models.Model):

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    value = models.CharField(max_length=255)


class World(models.Model):

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    value = models.CharField(max_length=255)
    parent = models.ForeignKey(Hello)
