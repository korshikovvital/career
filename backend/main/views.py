from rest_framework import generics
from rest_framework.response import Response

from .models import (
    Banner,
    CareerTypeCard,
    EmployeeCard,
    InterestingCard,
    Poll,
    PollResult
)
from .serializers import (
    BannerSerializer,
    CareerTypeCardSerializer,
    EmployeeCardSerializer,
    InterestingCardSerializer,
    InvitationSerializer,
    MainSerializer,
    PollAnswerWrapperSerializer,
    PollResultSerializer,
    PollSerializer
)


class MainView(generics.GenericAPIView):

    def get(self, request):
        serialized_data = MainSerializer(data={
            'career_type_cards': CareerTypeCardSerializer(
                CareerTypeCard.objects.order_by('priority'),
                many=True
            ).data,
            'interesting_cards': InterestingCardSerializer(
                InterestingCard.objects.order_by('priority'),
                many=True
            ).data,
            'employee_cards': EmployeeCardSerializer(
                EmployeeCard.objects.select_related('user').order_by('-modified'),
                many=True
            ).data,
            'banner': BannerSerializer(
                Banner.objects.last()
            ).data,
            'poll': PollSerializer(
                Poll.objects.prefetch_related('questions').last(),
            ).data
        })
        serialized_data.is_valid()
        return Response(serialized_data.data)


class PollView(generics.GenericAPIView):

    def post(self, request, *args, **kwargs):
        serialized_data = PollAnswerWrapperSerializer(data=request.data)
        if serialized_data.is_valid(raise_exception=True):
            poll_res = PollResult.calculate_results(
                answers=serialized_data.data['answers']
            )
            serialized_result = PollResultSerializer(poll_res)
            return Response(serialized_result.data)


class InvitationView(generics.CreateAPIView):
    serializer_class = InvitationSerializer
