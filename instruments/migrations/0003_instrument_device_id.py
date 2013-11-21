# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('instruments', '0002_remove_instrument_device_id')]

    operations = [
        migrations.AddField(
            field = models.CharField(max_length=256, null=True),
            name = 'device_id',
            model_name = 'instrument',
        ),
    ]
