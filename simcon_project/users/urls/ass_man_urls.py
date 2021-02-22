from django.urls import path
from users.views import *

app_name = 'ass-management'
urlpatterns = [
    path('', assignment_management_view, name="main"),
    path('view-details/<pk>/', view_settings, name="view-settings"),
    path('view-templates/<pk>/', view_templates, name="view-templates"),
    path('view-students/<pk>/', view_students, name="view-students"),
    path('delete/<pk>', AssignmentDeleteView.as_view(), name="delete-assignment"),
]
