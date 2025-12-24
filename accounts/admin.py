from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, ProfilePhoto, Interest, UserInterest

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'is_online', 'is_verified', 'last_seen', 'created_at']
    list_filter = ['is_online', 'is_verified', 'is_staff', 'created_at']
    search_fields = ['email', 'username']
    ordering = ['-created_at']
    
    # Champs en lecture seule (non éditables)
    readonly_fields = ['last_seen', 'created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('phone', 'is_verified', 'is_online', 'last_seen')  # last_seen reste ici
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('email', 'phone', 'is_verified')
        }),
    )


class ProfilePhotoInline(admin.TabularInline):
    model = ProfilePhoto
    extra = 1
    max_num = 6
    readonly_fields = ['created_at']


class UserInterestInline(admin.TabularInline):
    model = UserInterest
    extra = 1
    readonly_fields = ['created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'gender', 'age', 'city', 'match_count', 'swipe_count']
    list_filter = ['gender', 'looking_for', 'created_at']
    search_fields = ['user__email', 'user__username', 'city']
    readonly_fields = ['created_at', 'updated_at', 'age']
    inlines = [ProfilePhotoInline, UserInterestInline]
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations personnelles', {
            'fields': ('bio', 'birth_date', 'gender', 'looking_for', 'age')
        }),
        ('Localisation', {
            'fields': ('city', 'country', 'latitude', 'longitude', 'max_distance')
        }),
        ('Préférences', {
            'fields': ('min_age_preference', 'max_age_preference')
        }),
        ('Statistiques', {
            'fields': ('swipe_count', 'match_count')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']