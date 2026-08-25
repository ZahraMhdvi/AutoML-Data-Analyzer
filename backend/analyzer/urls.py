from django.urls import path
from . import views
from .views import upload_dataset

urlpatterns = [
    # path("", views.home, name="home"),
    path("",upload_dataset,name="upload_dataset"),
]