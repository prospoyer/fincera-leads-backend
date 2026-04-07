import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from django.db.models import Count, Q
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .filters import OrgFilter, ContactFilter
from .models import Org, Contact, PipelineRun
from .serializers import (
    OrgSerializer, OrgListSerializer,
    ContactSerializer, PipelineRunSerializer,
)


# ─── Orgs ────────────────────────────────────────────────────────────────────

class OrgViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Org.objects.all().order_by("-revenue")
    filterset_class = OrgFilter
    search_fields = ["name", "city", "ein"]
    ordering_fields = ["revenue", "name", "state", "created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return OrgListSerializer
        return OrgSerializer


# ─── Contacts ────────────────────────────────────────────────────────────────

class ContactViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ContactSerializer
    filterset_class = ContactFilter
    search_fields = ["full_name", "org_id", "title", "email"]
    ordering_fields = ["priority", "full_name", "compensation", "created_at"]

    def get_queryset(self):
        return (
            Contact.objects.select_related("org")
            .order_by("-priority", "-org__revenue")
        )


# ─── Stats ───────────────────────────────────────────────────────────────────

@api_view(["GET"])
def stats(request):
    total_orgs     = Org.objects.count()
    total_contacts = Contact.objects.count()

    contacts_with_email = Contact.objects.filter(
        email__isnull=False
    ).exclude(email_status="invalid").count()

    verified_emails = Contact.objects.filter(email_status="verified").count()
    found_emails    = Contact.objects.filter(email_status="found").count()
    guessed_emails  = Contact.objects.filter(email_status="guessed").count()

    has_property_orgs = Org.objects.filter(has_property=1).count()

    orgs_by_state = list(
        Org.objects.values("state")
        .annotate(count=Count("ein"))
        .order_by("-count")[:15]
    )

    top_titles = list(
        Contact.objects.values("title")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    email_coverage = round(contacts_with_email / total_contacts * 100, 1) if total_contacts else 0

    return Response({
        "total_orgs":           total_orgs,
        "total_contacts":       total_contacts,
        "contacts_with_email":  contacts_with_email,
        "email_coverage_pct":   email_coverage,
        "verified_emails":      verified_emails,
        "found_emails":         found_emails,
        "guessed_emails":       guessed_emails,
        "has_property_orgs":    has_property_orgs,
        "orgs_by_state":        orgs_by_state,
        "top_titles":           top_titles,
    })


# ─── Export ──────────────────────────────────────────────────────────────────

@api_view(["GET"])
def export_csv(request):
    contacts = (
        Contact.objects.select_related("org")
        .filter(email__isnull=False)
        .exclude(email_status="invalid")
        .order_by("-priority", "-org__revenue")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="fincera_leads.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "org_name", "ein", "city", "state", "revenue", "website",
        "mission", "has_property", "contact_name", "contact_title",
        "contact_email", "email_status", "priority",
    ])

    for c in contacts:
        try:
            org = c.org
            writer.writerow([
                org.name, org.ein, org.city, org.state, org.revenue,
                org.website, (org.mission or "")[:200], org.has_property,
                c.full_name, c.title, c.email, c.email_status, c.priority,
            ])
        except Exception:
            continue

    return response


# ─── Pipeline ────────────────────────────────────────────────────────────────

VALID_STAGES = ["discover", "enrich", "scrape", "emails", "export", "all"]

PIPELINE_ROOT = Path(__file__).resolve().parents[2]  # /home/wmstf/fincera-leads


@api_view(["GET"])
def pipeline_runs(request):
    runs = PipelineRun.objects.all()[:20]
    return Response(PipelineRunSerializer(runs, many=True).data)


@api_view(["POST"])
def pipeline_trigger(request):
    stage = request.data.get("stage", "all")
    if stage not in VALID_STAGES:
        return Response(
            {"error": f"Invalid stage. Choose from: {VALID_STAGES}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if a run is already in progress
    if PipelineRun.objects.filter(status="running").exists():
        return Response(
            {"error": "A pipeline run is already in progress."},
            status=status.HTTP_409_CONFLICT,
        )

    run = PipelineRun.objects.create(stage=stage, status="running")

    # Use manage.py run_pipeline so it updates PipelineRun status when done/failed
    manage_py = PIPELINE_ROOT / "backend" / "manage.py"
    cmd = [sys.executable, str(manage_py), "run_pipeline", "--stage", stage]
    try:
        subprocess.Popen(
            cmd,
            cwd=str(PIPELINE_ROOT / "backend"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**__import__("os").environ, "DJANGO_SETTINGS_MODULE": "fincera_project.settings"},
        )
    except Exception as e:
        run.status = "failed"
        run.log = str(e)
        run.ended_at = datetime.now()
        run.save()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(PipelineRunSerializer(run).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def pipeline_status(request):
    """Return the most recent run's status, auto-expire stale 'running' runs."""
    from datetime import timedelta
    run = PipelineRun.objects.first()
    if not run:
        return Response({"status": "idle"})

    # Mark as failed if stuck running for more than 6 hours with no update
    if run.status == "running" and run.started_at:
        age = datetime.now() - run.started_at
        if age > timedelta(hours=6):
            run.status = "failed"
            run.log = "Timed out — process may have crashed."
            run.ended_at = datetime.now()
            run.save()

    return Response(PipelineRunSerializer(run).data)
