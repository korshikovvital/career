from django.db import models


class DefaultQueryset(models.QuerySet):
    pass


class DefaultManager(models.Manager):
    pass


class DefaultModel(models.Model):
    objects = DefaultManager()

    class Meta:
        abstract = True


class TimestampedModel(DefaultModel):

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class IsActiveMixin(models.Model):
    is_active = models.BooleanField('Активно', default=True)

    class Meta:
        abstract = True
