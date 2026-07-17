from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0005_roadmapprogress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quizsubmission',
            name='career_plan',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]