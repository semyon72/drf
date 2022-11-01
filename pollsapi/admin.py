from django.contrib import admin

# Register your models here.
from pollsapi import models

admin.site.register(models.Poll)
admin.site.register(models.Choice)
admin.site.register(models.Vote)
