# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('instruments', '0003_auto')]

    operations = [
        migrations.AddField(
            field = models.CharField(default='A', max_length=1, choices=(('W', 'Write',), ('A', 'Ask',), ('B', 'Ask Raw',),)),
            name = 'command_type',
            model_name = 'command',
        ),
    ]
