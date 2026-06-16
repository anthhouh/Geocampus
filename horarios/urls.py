from django.urls import path
from . import views

app_name = 'horarios'

urlpatterns = [
    # Públicas / comunes
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('verificar-2fa/', views.verify_2fa_view, name='verify_2fa'),
    path('verificar-registro/', views.verify_registro_view, name='verify_registro'),
    path('configuracion/', views.configuracion_view, name='configuracion'),
    path('api/toggle-modo-oscuro/', views.toggle_modo_oscuro, name='toggle_modo_oscuro'),
    path('api/reset-password/enviar/', views.api_reset_password_enviar, name='api_reset_password_enviar'),
    path('api/reset-password/verificar/', views.api_reset_password_verificar, name='api_reset_password_verificar'),
    path('api/reset-password/cambiar/', views.api_reset_password_cambiar, name='api_reset_password_cambiar'),

    # Docente
    path('dashboard/', views.dashboard_docente, name='dashboard_docente'),
    path('api/cambiar-estado/', views.cambiar_estado, name='cambiar_estado'),
    path('imprimir-horario/', views.imprimir_horario, name='imprimir_horario'),
    path('anadir-horario/', views.añadir_horario, name='anadir_horario'),

    # Horarios de curso (estudiantes)
    path('horarios/', views.horarios_curso, name='horarios_curso'),

    # Horario público de un docente
    path('docentes/<int:docente_id>/horario/', views.horario_docente, name='horario_docente'),

    # ── Panel de gestión (solo admin) ─────────────────────────────────────
    path('gestion/',                                    views.gestion_dashboard,        name='gestion_dashboard'),
    path('gestion/horarios/',                           views.gestion_horarios,         name='gestion_horarios'),
    path('gestion/horarios/preliminar/',                views.gestion_horarios_preliminar, name='gestion_horarios_preliminar'),
    path('gestion/horarios/exportar-excel/',            views.exportar_horarios_excel,  name='exportar_horarios_excel'),
    path('gestion/horarios/docentes/',                  views.gestion_horarios_docentes,name='gestion_horarios_docentes'),
    path('gestion/horarios/cursos/',                    views.gestion_horarios_cursos,  name='gestion_horarios_cursos'),
    path('gestion/horarios/api/guardar/',               views.api_guardar_horario,      name='api_guardar_horario'),
    path('gestion/horarios/crear/',                     views.gestion_crear_horario,    name='gestion_crear_horario'),
    path('gestion/horarios/<int:horario_id>/editar/',   views.gestion_editar_horario,   name='gestion_editar_horario'),
    path('gestion/horarios/<int:horario_id>/eliminar/', views.gestion_eliminar_horario, name='gestion_eliminar_horario'),
    path('gestion/docentes/',                           views.gestion_docentes,         name='gestion_docentes'),
    path('gestion/docentes/crear/',                     views.gestion_crear_docente,    name='gestion_crear_docente'),
    path('gestion/docentes/<int:docente_id>/editar/',   views.gestion_editar_docente,   name='gestion_editar_docente'),
    path('gestion/docentes/<int:docente_id>/eliminar/', views.gestion_eliminar_docente, name='gestion_eliminar_docente'),
    path('gestion/cursos/',                             views.gestion_cursos,           name='gestion_cursos'),
    path('gestion/cursos/crear/',                       views.gestion_crear_curso,      name='gestion_crear_curso'),
    path('gestion/cursos/<int:curso_id>/editar/',       views.gestion_editar_curso,     name='gestion_editar_curso'),
    path('gestion/cursos/<int:curso_id>/eliminar/',     views.gestion_eliminar_curso,   name='gestion_eliminar_curso'),
    path('gestion/paralelos/crear/',                    views.gestion_crear_paralelo,   name='gestion_crear_paralelo'),
    path('gestion/paralelos/<int:paralelo_id>/editar/', views.gestion_editar_paralelo,  name='gestion_editar_paralelo'),
    path('gestion/paralelos/<int:paralelo_id>/eliminar/', views.gestion_eliminar_paralelo, name='gestion_eliminar_paralelo'),
    path('gestion/asignaturas/',                             views.gestion_asignaturas,           name='gestion_asignaturas'),
    path('gestion/asignaturas/crear/',                       views.gestion_crear_asignatura,      name='gestion_crear_asignatura'),
    path('gestion/asignaturas/<int:asignatura_id>/editar/',       views.gestion_editar_asignatura,     name='gestion_editar_asignatura'),
    path('gestion/asignaturas/<int:asignatura_id>/eliminar/',     views.gestion_eliminar_asignatura,   name='gestion_eliminar_asignatura'),
    
    # ── Módulo: Generador Automático (solo admin) ─────────────────────────────
    path('gestion/lecciones/',                               views.gestion_lecciones,        name='gestion_lecciones'),
    path('gestion/lecciones/crear/',                         views.gestion_crear_leccion,    name='gestion_crear_leccion'),
    path('gestion/lecciones/<int:leccion_id>/editar/',       views.gestion_editar_leccion,   name='gestion_editar_leccion'),
    path('gestion/lecciones/<int:leccion_id>/eliminar/',     views.gestion_eliminar_leccion, name='gestion_eliminar_leccion'),
    path('gestion/lecciones/eliminar-masivo/',               views.gestion_eliminar_lecciones_masivo, name='gestion_eliminar_lecciones_masivo'),
    path('gestion/lecciones/eliminar-todas/',                views.gestion_eliminar_todas_lecciones, name='gestion_eliminar_todas_lecciones'),
    path('gestion/disponibilidad/',                          views.gestion_disponibilidad,   name='gestion_disponibilidad'),
    path('gestion/disponibilidad/api/guardar/',              views.api_guardar_disponibilidad, name='api_guardar_disponibilidad'),
    path('gestion/generador/',                               views.gestion_generador,        name='gestion_generador'),
    path('gestion/generador/api/verificar/',                 views.api_verificar_coherencia, name='api_verificar_coherencia'),
    path('gestion/generador/api/ejecutar/',                  views.api_ejecutar_generador,   name='api_ejecutar_generador'),
    path('gestion/generador/api/estado/<str:sesion_id>/',    views.api_estado_generador,     name='api_estado_generador'),
    path('gestion/generador/borrador/<str:sesion_id>/',      views.gestion_borrador,         name='gestion_borrador'),
    path('gestion/generador/api/publicar/<uuid:sesion_id>/', views.api_publicar_borrador, name='api_publicar_borrador'),
    path('gestion/generador/api/descartar/<uuid:sesion_id>/', views.api_descartar_borrador, name='api_descartar_borrador'),

    path('gestion/atencion-padres/', views.gestion_atencion_padres, name='gestion_atencion_padres'),
    path('gestion/atencion-padres/notificar/', views.enviar_notificacion_padres_view, name='notificar_atencion_padres'),
    path('api/cron/notificar-padres/', views.cron_notificar_padres_view, name='cron_notificar_padres'),
    path('atencion-padres/', views.atencion_padres_publico, name='atencion_padres_publico'),
]
