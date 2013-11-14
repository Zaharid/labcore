# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('instruments', '0004_command_command_type')]

    operations = [
        migrations.AlterField(
            field = models.CharField(max_length=1, choices=(('W', 'Write',), ('A', 'Ask',), ('B', 'Ask Raw',),)),
            name = 'command_type',
            model_name = 'command',
        ),
    ]
