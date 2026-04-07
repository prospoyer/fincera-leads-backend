from rest_framework import serializers
from .models import Org, Contact, PipelineRun


class OrgSerializer(serializers.ModelSerializer):
    contact_count       = serializers.SerializerMethodField()
    contacts_with_email = serializers.SerializerMethodField()

    class Meta:
        model = Org
        fields = [
            "ein", "name", "city", "state", "revenue", "assets",
            "ntee_code", "website", "mission", "has_property",
            "fiscal_year_end", "source", "created_at",
            "contact_count", "contacts_with_email",
        ]

    def get_contact_count(self, obj):
        return obj.contacts.count()

    def get_contacts_with_email(self, obj):
        return obj.contacts.filter(email__isnull=False).exclude(email_status="invalid").count()


class OrgListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""
    contact_count = serializers.SerializerMethodField()

    class Meta:
        model = Org
        fields = [
            "ein", "name", "city", "state", "revenue",
            "website", "has_property", "contact_count",
        ]

    def get_contact_count(self, obj):
        return obj.contacts.count()


class ContactSerializer(serializers.ModelSerializer):
    ein         = serializers.CharField(source="org_id")  # org_id == ein value
    org_name    = serializers.CharField(source="org.name",    default=None)
    org_state   = serializers.CharField(source="org.state",   default=None)
    org_revenue = serializers.IntegerField(source="org.revenue", default=None)

    class Meta:
        model = Contact
        fields = [
            "id", "ein", "full_name", "first_name", "last_name",
            "title", "compensation", "email", "email_status",
            "email_source", "priority", "created_at",
            "org_name", "org_state", "org_revenue",
        ]


class PipelineRunSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = PipelineRun
        fields = [
            "id", "stage", "status", "started_at", "ended_at",
            "log", "orgs_found", "duration_seconds",
        ]

    def get_duration_seconds(self, obj):
        if obj.ended_at and obj.started_at:
            return int((obj.ended_at - obj.started_at).total_seconds())
        return None
