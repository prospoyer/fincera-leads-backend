from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0002_create_pipeline_tables"),
    ]

    operations = [
        migrations.AddField(
            model_name="pipelinerun",
            name="process_pid",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="pipelinerun",
            name="cancel_requested",
            field=models.BooleanField(default=False),
        ),
    ]
