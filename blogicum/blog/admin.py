from django.contrib import admin
from .models import Category, Location, Post, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pub_date',
        'author',
        'category',
        'location',
        'is_published'
    )
    list_editable = ('is_published',)
    list_filter = ('category', 'location', 'is_published', 'pub_date')
    search_fields = ('title', 'text')
    date_hierarchy = 'pub_date'

    fieldsets = (
        (None, {
            'fields': ('title', 'text', 'author')
        }),
        ('Дополнительные параметры', {
            'fields': ('pub_date', 'location', 'category', 'is_published'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published')
    list_editable = ('is_published',)
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published')
    list_editable = ('is_published',)
    search_fields = ('name',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at', 'text')
    list_filter = ('created_at', 'author')
    search_fields = ('text', 'author__username', 'post__title')


admin.site.register(Comment, CommentAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)

admin.site.site_title = 'Админ-панель Блогикума'
admin.site.site_header = 'Админ-панель Блогикума'
