from django.contrib import admin
from .models import Feature, Plans, Subscription, History

# Register your models here.
admin.site.register(Feature)
admin.site.register(Plans)
admin.site.register(Subscription)
admin.site.register(History)