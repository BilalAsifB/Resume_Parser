from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_resume, name='upload_resume'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('parse_resume/login/', views.parse_resume_login, name='parse_resume_login'),
    path('parsed_results/', views.parsed_selected_pdfs, name='parsed_results'),
    path('options/', views.admin_options, name='admin_options'),
    path('parsed_resume/', views.parsed_resume, name='parsed_resume'),
]
