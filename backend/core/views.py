from rest_framework import generics
from rest_framework.exceptions import ValidationError

from app import errors
from core.enums import CareerInfoChoices
from core.models import Info
from core.serializers import InfoSerializer


class InfoView(generics.ListAPIView):
    serializer_class = InfoSerializer

    def get_queryset(self):
        slug_req = self.request.query_params.get('slug')
        if not slug_req or slug_req not in CareerInfoChoices.values:
            raise ValidationError(detail=errors.INCORRECT_INFO_SLUG)

        return Info.objects.filter(sections__slug=slug_req).order_by('priority')
