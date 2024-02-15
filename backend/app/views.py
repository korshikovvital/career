from app import responses


def health_check_view(request):
    return responses.HealthcheckResponse
