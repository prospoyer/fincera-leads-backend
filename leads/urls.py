from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("orgs",     views.OrgViewSet,     basename="org")
router.register("contacts", views.ContactViewSet, basename="contact")

urlpatterns = [
    path("",                        include(router.urls)),
    path("stats/",                  views.stats),
    path("export/",                 views.export_csv),
    path("pipeline/",               views.pipeline_runs),
    path("pipeline/trigger/",       views.pipeline_trigger),
    path("pipeline/status/",        views.pipeline_status),
]
