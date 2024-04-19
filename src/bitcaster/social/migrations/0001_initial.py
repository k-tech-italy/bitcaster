# Generated by Django 5.0.4 on 2024-04-19 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SocialProvider",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("AZUREAD_OAUTH2", "Azure"),
                            ("AZUREAD_TENANT_OAUTH2", "Azure Tenant"),
                            ("FACEBOOK", "Facebook"),
                            ("GITHUB", "Github"),
                            ("GITHUB_ENTERPRISE", "Github Enterprise"),
                            ("GITHUB_ORG", "Github Organization"),
                            ("GITLAB", "Gitlab"),
                            ("GITHUB_TEAM", "Github Team"),
                            ("GOOGLE_OAUTH2", "Google"),
                            ("LINKEDIN_OAUTH2", "Linkedin"),
                            ("TWITTER", "Twitter"),
                        ],
                        help_text="Social Login provider",
                        max_length=30,
                        unique=True,
                    ),
                ),
                (
                    "configuration",
                    models.JSONField(blank=True, default=dict, help_text="Configuration as per Python Social Auth"),
                ),
                ("enabled", models.BooleanField(default=True)),
            ],
        ),
    ]
