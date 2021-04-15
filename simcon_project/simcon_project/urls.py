"""simcon_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from conversation_templates.views import *
from users.views import *
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib.auth import views
from django.conf import settings

urlpatterns = [
    # Redirects and such
    path('', views.LoginView.as_view(), name="login"),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('redirect-from-login/', redirect_from_login, name="redirect-from-login"),
    path('password-reset/', views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name="password-reset"),
    path('password-reset/done/', views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),name="password-reset-done"),
    path('password-reset-confirm/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),name="password-reset-confirm"),
    path('password-reset-complete/', views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),name="password-reset-complete"),


    # Stuff students can see
    path('student/', student_view, name="student-view"),
    path('student/settings/', student_settings_view, name="student-settings-view"),
    path('student/register/<uidb64>/', student_registration, name="student-registration"),
    path('student/conversation/', include('conversation_templates.urls.conv_urls'), name='conversation'),
    path('student/feedback/', include('conversation_templates.urls.feedback_urls'), name='view-feedback'),

    # Stuff researchers can see
    path('researcher/', researcher_view, name="researcher-view"),
    path('researcher/register/<uidb64>/', researcher_registration, name="researcher-registration"),
    path('researcher/templates/', include('conversation_templates.urls.templates_urls'), name="template-management-view"),
    path('researcher/settings/', include('users.urls.researcher_settings_urls'), name="researcher-settings-view"),
    path('researcher/view-all-responses/<uuid:pk>/', TemplateResponsesView.as_view(), name="view-all-responses"),
    path('researcher/students/<str:name>/', student_management, name="student-management"),
    path('researcher/students/', student_management, name="student-management"),
    path('researcher/assignments/', include('users.urls.ass_man_urls'), name="assignment-management"),
    path('researcher/create-assignment/', include('users.urls.create_assignment_urls'), name="create-assignment-view"),
    path('researcher/response/<uuid:pk>/', view_response, name="view-response"),
    path('researcher/response/delete/<uuid:pk>/', ResponseDeleteView.as_view(), name="delete-response"),
    path('researcher/students/delete/<int:pk>/', delete_students_modal, name="delete-student"),
    path('researcher/students/remove/<int:pk>/', student_remove_view, name="remove-student"),
    path('researcher/labels/delete/<uuid:pk>/', delete_label_view, name="delete-label"),
    path('researcher/create-students/', create_students_modal, name="create-students"),
    path('researcher/create-students/validate/', validate_student_email, name="validate-student-email"),
    path('researcher/create-students/final/', register_students, name="register-students"),

    # Stuff researcher who is an admin can see
    path('admin/researchers/researcher-management/', researcher_management, name="researcher-management"),
    path('admin/researchers/delete/<pk>/', ResearcherDeleteView.as_view(), name="delete-researcher"),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
