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
from users.views import RedirectFromLogin, StudentView, ResearcherView, ViewResponse, UpdateOverallResponseFeedback, UpdateNodeResponseFeedback, ResearcherSettingsView, ResearcherUserView, StudentSettingsView,StudentUserView
from django.conf.urls import include
from django.contrib.auth import views

urlpatterns = [
    path('', views.LoginView.as_view(), name="Login"),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('redirect-from-login/', RedirectFromLogin, name="RedirectFromLogin"),
    path('student-view/', StudentView, name="StudentView"),
    path('researcher-view/', ResearcherView, name="ResearcherView"),
    path('user-view/', ResearcherUserView, name="ResearcherUserView"),
    path('studentuser-view/', StudentUserView, name="StudentUserView"),
    path('settings/', ResearcherSettingsView, name="ResearcherSettingsView"),
    path('student-settings/', StudentSettingsView, name="StudentSettingsView"),
    path('researcher-view/template-management/', include('conversation_templates.urls.templates_urls'), name="TemplateManagementView"),
    path('view-response/', ViewResponse, name="ViewResponse"),
    path('view-response/<uuid:pk>/update/', UpdateOverallResponseFeedback, name='UpdateOverallResponseFeedback'),
    path('view-response/<uuid:pk>/updatenode/', UpdateNodeResponseFeedback, name='UpdateNodeResponseFeedback'),
    path('conversation/', include('conversation_templates.urls.conv_urls'), name='conversation'),
]
