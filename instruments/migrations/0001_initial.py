# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = []

    operations = [
        migrations.CreateModel(
            fields = [(u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True),), ('name', models.CharField(max_length=128),), ('command_string', models.CharField(max_length=1024),)],
            bases = (models.Model,),
            options = {},
            name = 'Command',
        ),
        migrations.CreateModel(
            fields = [(u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True),), ('name', models.CharField(max_length=128),), ('module', models.CharField(max_length=128),)],
            bases = (models.Model,),
            options = {},
            name = 'Interface',
        ),
        migrations.CreateModel(
            fields = [(u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True),), ('name', models.CharField(max_length=256),), ('interface', models.ForeignKey(to=u'instruments.Interface', to_field=u'id'),)],
            bases = (models.Model,),
            options = {},
            name = 'Instrument',
        ),
    ]
