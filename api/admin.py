from django.contrib import admin

from .models import Comic, Video


class ComicAdmin(admin.ModelAdmin):
    pass


class VideoAdmin(admin.ModelAdmin):
    pass


admin.site.register(Comic, ComicAdmin)
admin.site.register(Video, VideoAdmin)
