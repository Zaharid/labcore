# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('instruments', '0001_initial')]

    operations = [
        migrations.AlterField(
            field = models.ForeignKey(to=u'instruments.Command', to_field=u'id'),
            name = 'command',
            model_name = 'parameter',
        ),
    ]
