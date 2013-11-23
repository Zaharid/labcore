from django.contrib import admin

import models

# Register your models here.

class ParameterAdmin(admin.ModelAdmin):
    pass

class CommandAdmin(admin.ModelAdmin):
    pass

class InstrumentAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Command, CommandAdmin)
admin.site.register(models.Parameter, ParameterAdmin)
admin.site.register(models.Instrument, InstrumentAdmin)
