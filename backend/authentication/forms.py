from django.contrib.auth.forms import UserCreationForm as StockUserCreationForm


class UserCreationForm(StockUserCreationForm):
    class Meta:
        fields = ("personnel_number",)
