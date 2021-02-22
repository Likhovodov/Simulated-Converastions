from django.urls import path
from users.views import *

app_name = 'assignments'
urlpatterns = [
    path('', create_assignment_view, name="create-assignment"),
    path('add_assignment/', add_assignment, name="add-assignment"),
]
