import django_filters
from .models import Org, Contact


class OrgFilter(django_filters.FilterSet):
    state       = django_filters.CharFilter(lookup_expr="iexact")
    revenue_min = django_filters.NumberFilter(field_name="revenue", lookup_expr="gte")
    revenue_max = django_filters.NumberFilter(field_name="revenue", lookup_expr="lte")
    has_property = django_filters.CharFilter(method="filter_has_property")

    class Meta:
        model = Org
        fields = ["state", "revenue_min", "revenue_max", "has_property"]

    def filter_has_property(self, queryset, name, value):
        # SQLite stores 0/1 — accept "true"/"yes"/"1" as truthy
        truthy = value.lower() in ("true", "yes", "1")
        return queryset.filter(has_property=1 if truthy else 0)


class ContactFilter(django_filters.FilterSet):
    state        = django_filters.CharFilter(field_name="org__state", lookup_expr="iexact")
    email_status = django_filters.CharFilter(lookup_expr="iexact")
    has_email    = django_filters.CharFilter(method="filter_has_email")
    priority_min = django_filters.NumberFilter(field_name="priority", lookup_expr="gte")
    title_like   = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    ein          = django_filters.CharFilter(field_name="org_id", lookup_expr="exact")

    class Meta:
        model = Contact
        fields = ["email_status", "priority_min", "title_like", "state", "ein"]

    def filter_has_email(self, queryset, name, value):
        truthy = value.lower() in ("true", "yes", "1")
        if truthy:
            return queryset.filter(email__isnull=False).exclude(email_status="invalid")
        return queryset.filter(email__isnull=True)
