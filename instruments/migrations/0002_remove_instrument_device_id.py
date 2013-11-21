# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('instruments', '0001_initial')]

    operations = [
        migrations.RemoveField(
            name = 'device_id',
            model_name = 'instrument',
        ),
    ]
