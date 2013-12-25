from django.contrib import admin
from django.contrib.contenttypes import generic

import models

# Register your models here.

class ParameterAdmin(admin.TabularInline):
    models = models.Parameter

class CommandAdmin(generic.GenericTabularInline):
    model = models.Command
    inlines = [ParameterAdmin]
    extra = 1

class InstrumentAdmin(admin.ModelAdmin):
    inlines = [CommandAdmin]

class BaseInstrumentAdmin(admin.ModelAdmin):
    inlines = [CommandAdmin]


#admin.site.register(models.Command, CommandAdmin)
#admin.site.register(models.Parameter, ParameterAdmin)
admin.site.register(models.Instrument, InstrumentAdmin)
admin.site.register(models.BaseInstrument, BaseInstrumentAdmin)
