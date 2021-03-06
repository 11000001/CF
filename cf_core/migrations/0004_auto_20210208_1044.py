# Generated by Django 3.1.5 on 2021-02-08 18:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cf_core', '0003_auto_20201209_0941'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='addon',
            options={'ordering': ['name', 'perk']},
        ),
        migrations.AlterModelOptions(
            name='perk',
            options={'ordering': ['name', 'domain']},
        ),
        migrations.AlterModelOptions(
            name='version',
            options={'ordering': ['number']},
        ),
        migrations.RenameField(
            model_name='version',
            old_name='xml',
            new_name='json',
        ),
    ]
