from django.urls import path
from conversation_templates.views import *

app_name = 'management'
urlpatterns = [
    path('', main_view, name="main"),
    path('folder/<uuid:pk>/', folder_view, name="folder-view"),
    path('folder/new/', FolderCreateView.as_view(), name='create-folder'),
    path('folder/delete/<uuid:pk>/', FolderDeleteView.as_view(), name='delete-folder'),
    path('folder/edit/<uuid:pk>/', FolderEditView.as_view(), name='edit-folder'),
    path('delete/<uuid:pk>/', TemplateDeleteView.as_view(), name="delete-template"),
    path('folder/remove/<uuid:pk>/', remove_template, name="remove-template"),
    path('new/', create_conversation_template_view, name="create-conversation-template-view"),
    path('edit/<uuid:pk>/', edit_conversation_template, name="edit_conversation_template"),
    path('redirect/template/', RedirectToTemplateCreation.as_view(), name="redirect-to-template-creation"),
    path('display/archived/<show_archived>', update_cookie, name="display-archived-templates"),
    path('archived/<uuid:pk>', archive_template, name="archive-template"),
]
