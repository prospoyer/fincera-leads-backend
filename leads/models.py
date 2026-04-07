from django.db import models


class Org(models.Model):
    """
    Nonprofit organization — populated by pipeline Stage 1 (ProPublica)
    and enriched by Stage 2 (IRS 990 XML).
    managed=False: the pipeline creates this table via db.py, Django only reads/writes it.
    """
    ein             = models.CharField(max_length=20, primary_key=True)  # PK in SQLite
    name            = models.TextField()
    city            = models.TextField(blank=True, null=True)
    state           = models.CharField(max_length=5, blank=True, null=True)
    zipcode         = models.CharField(max_length=20, blank=True, null=True)
    revenue         = models.BigIntegerField(default=0)
    assets          = models.BigIntegerField(default=0)
    ntee_code       = models.CharField(max_length=20, blank=True, null=True)
    website         = models.TextField(blank=True, null=True)
    mission         = models.TextField(blank=True, null=True)
    has_property    = models.IntegerField(default=0)
    fiscal_year_end = models.CharField(max_length=20, blank=True, null=True)
    source          = models.CharField(max_length=50, blank=True, null=True)
    created_at      = models.TextField(blank=True, null=True)

    class Meta:
        managed = False   # pipeline owns schema via db.py
        db_table = "orgs"

    def __str__(self):
        return f"{self.name} ({self.state})"


class Contact(models.Model):
    """
    Officer / key person at an org — populated by pipeline Stage 2 (IRS 990 XML).
    Email filled by Stage 3 (website scrape) and Stage 4 (SMTP pattern guess).
    managed=False: pipeline owns schema.

    Note: db_column='ein' on the FK maps the FK to the same 'ein' column in the
    contacts table. Access ein value via contact.org_id, org object via contact.org.
    """
    org          = models.ForeignKey(
        Org,
        on_delete=models.DO_NOTHING,
        db_column="ein",       # maps FK to the 'ein' column in contacts table
        related_name="contacts",
        null=True,
        blank=True,
    )
    full_name    = models.TextField()
    first_name   = models.TextField(blank=True, null=True)
    last_name    = models.TextField(blank=True, null=True)
    title        = models.TextField(blank=True, null=True)
    compensation = models.IntegerField(default=0)
    email        = models.TextField(blank=True, null=True)
    email_status = models.CharField(max_length=30, blank=True, null=True)
    email_source = models.CharField(max_length=30, blank=True, null=True)
    priority     = models.IntegerField(default=0)
    created_at   = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "contacts"

    def __str__(self):
        return f"{self.full_name} — {self.title}"


class PipelineRun(models.Model):
    """Tracks pipeline stage executions. Managed by Django."""
    STAGES = [
        ("discover", "Stage 1 — Discover"),
        ("enrich",   "Stage 2 — Enrich"),
        ("scrape",   "Stage 3 — Scrape"),
        ("emails",   "Stage 4 — Emails"),
        ("export",   "Stage 5 — Export"),
        ("all",      "Full Pipeline"),
    ]
    STATUS = [
        ("running",   "Running"),
        ("completed", "Completed"),
        ("failed",    "Failed"),
        ("cancelled", "Cancelled"),
    ]

    stage      = models.CharField(max_length=20, choices=STAGES)
    status     = models.CharField(max_length=20, choices=STATUS, default="running")
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at   = models.DateTimeField(null=True, blank=True)
    log        = models.TextField(blank=True, default="")
    orgs_found = models.IntegerField(default=0)

    class Meta:
        db_table = "pipeline_runs"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.stage} — {self.status} ({self.started_at})"
