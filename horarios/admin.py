from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Docente, Curso, Paralelo, Horario, Asignatura

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Roles y Seguridad', {'fields': ('rol', 'two_factor_enabled')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'two_factor_enabled', 'is_staff')
    list_filter = ('rol', 'two_factor_enabled', 'is_staff', 'is_superuser')

class HorarioInline(admin.TabularInline):
    model = Horario
    extra = 1

class ParaleloInline(admin.TabularInline):
    model = Paralelo
    extra = 1
    fields = ('identificador', 'especialidad_bachillerato', 'tutor')

@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ('get_nombre', 'especialidad', 'disponible', 'ubicacion_actual')
    list_filter = ('disponible', 'especialidad')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'especialidad')
    
    def get_nombre(self, obj):
        return obj.usuario.get_full_name()
    get_nombre.short_description = 'Nombre'

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nivel')
    inlines = [ParaleloInline]

@admin.register(Paralelo)
class ParaleloAdmin(admin.ModelAdmin):
    list_display = ('identificador', 'curso', 'especialidad_bachillerato', 'tutor')
    list_filter = ('curso', 'especialidad_bachillerato')
    search_fields = ('identificador', 'curso__nombre')

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('asignatura', 'docente', 'curso', 'paralelo', 'dia', 'hora_inicio', 'hora_fin', 'tipo')
    list_filter = ('tipo', 'dia', 'curso', 'docente')
    list_editable = ('tipo',)
    search_fields = ('asignatura__nombre', 'docente__usuario__first_name', 'docente__usuario__last_name')

@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

admin.site.register(Usuario, CustomUserAdmin)
