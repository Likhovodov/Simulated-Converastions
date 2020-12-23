# Generated by Django 3.1.3 on 2020-12-21 20:14

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('conversation_templates', '0003_auto_20201219_1846'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemplateFolder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=50)),
                ('templates', models.ManyToManyField(related_name='folder', to='conversation_templates.ConversationTemplate')),
            ],
        ),
    ]