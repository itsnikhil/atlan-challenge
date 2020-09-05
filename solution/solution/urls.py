"""solution URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('upload/<str:filename>', views.FileUploadView.as_view()),
    path('upload/start/<int:file_id>', views.StartUploadTask.as_view()),
    path('upload/status/<int:file_id>', views.UploadTaskState.as_view()),
    path('upload/pause/<int:file_id>', views.PauseUploadTask.as_view()),
    path('upload/resume/<int:file_id>', views.ResumeUploadTask.as_view()),
    path('upload/stop/<int:file_id>', views.StopUploadTask.as_view())
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
