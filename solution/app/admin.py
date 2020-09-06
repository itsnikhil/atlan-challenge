from django.contrib import admin
from app.models import DataStore, GameSale

# Show files uploaded in django admin
admin.site.register(DataStore)

# Show record in django admin
admin.site.register(GameSale)