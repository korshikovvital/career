import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from app.celery import celery
from main.models import Banner, BannerImage

UserModel = get_user_model()
logger = logging.getLogger(__name__)


@celery.task
def update_images_for_banner():
    """
    Корректирует количество фотографий сотрудников в баннере до нужного количества и рандомно меняет их.
    """
    banner = Banner.objects.last()

    new_banner_users = UserModel.objects.filter(
        image_url__isnull=False
    ).order_by('?')[:settings.NUM_OF_BANNER_IMAGES]

    BannerImage.objects.filter(banner=banner).delete()
    BannerImage.objects.bulk_create([
        BannerImage(banner=banner, user=user) for user in new_banner_users
    ])
