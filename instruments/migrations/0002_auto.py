# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('instruments', '0001_initial')]

    operations = [
        migrations.CreateModel(
            fields = [(u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True),), ('name', models.CharField(max_length=128),), ('description', models.TextField(default=''),), ('default_value', models.CharField(max_length=128),)],
            bases = (models.Model,),
            options = {},
            name = 'Parameter',
        ),
        migrations.AddField(
            field = models.TextField(default=''),
            name = 'description',
            model_name = 'command',
        ),
    ]
