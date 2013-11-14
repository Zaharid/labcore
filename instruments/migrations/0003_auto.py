# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('instruments', '0002_auto')]

    operations = [
        migrations.AlterField(
            field = models.CharField(max_length=128, blank=True),
            name = 'default_value',
            model_name = 'parameter',
        ),
        migrations.AlterField(
            field = models.TextField(default='', blank=True),
            name = 'description',
            model_name = 'parameter',
        ),
        migrations.AlterField(
            field = models.TextField(default='', blank=True),
            name = 'description',
            model_name = 'command',
        ),
    ]
