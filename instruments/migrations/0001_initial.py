# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = []

    operations = [
        migrations.CreateModel(
            fields = [(u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True),), ('name', models.CharField(max_length=128),), ('command_string', models.CharField(max_length=1024),), ('command_type', models.CharField(blank=True, max_length=1, choices=(('W', 'Write',), ('A', 'Ask',), ('B', 'Ask Raw',),)),), ('description', models.TextField(default='', blank=True),)],
            bases = (models.Model,),
            options = {},
            name = 'Command',
        ),
        migrations.CreateModel(
            fields = [(u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True),), ('name', models.CharField(max_length=256),), ('device_id', models.CharField(max_length=256, null=True),)],
            bases = (models.Model,),
            options = {},
            name = 'Instrument',
        ),
        migrations.CreateModel(
            fields = [(u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True),), ('name', models.CharField(max_length=128),), ('module', models.CharField(max_length=128),)],
            bases = (models.Model,),
            options = {},
            name = 'Interface',
        ),
        migrations.CreateModel(
            fields = [(u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True),), ('command', models.ForeignKey(to=u'instruments.Command', to_field=u'id'),), ('name', models.CharField(max_length=128),), ('default_value', models.CharField(max_length=128, blank=True),), ('description', models.TextField(default='', blank=True),)],
            bases = (models.Model,),
            options = {},
            name = 'Parameter',
        ),
    ]
