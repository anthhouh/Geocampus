from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    ROLES = (
        ('estudiante', 'Estudiante/Representante'),
        ('docente', 'Docente/Personal'),
        ('admin', 'Administrador'),
    )
    rol = models.CharField(max_length=20, choices=ROLES, default='estudiante')

    def is_estudiante(self):
        return self.rol == 'estudiante'

    def is_docente(self):
        return self.rol == 'docente'

    def is_admin(self):
        return self.rol == 'admin'

class Docente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_docente')
    especialidad = models.CharField(max_length=100)
    foto = models.ImageField(upload_to='docentes_fotos/', null=True, blank=True)
    disponible = models.BooleanField(default=True)
    ubicacion_actual = models.CharField(max_length=100, blank=True, null=True, help_text="Ej: Laboratorio 1, Sala de Profesores")

    @property
    def ubicacion_dinamica(self):
        from django.utils import timezone
        ahora = timezone.localtime()
        # Mapeo simple de weekday() a los identificadores usados en la BD
        dias_map = {0: 'lunes', 1: 'martes', 2: 'miercoles', 3: 'jueves', 4: 'viernes', 5: 'sabado', 6: 'domingo'}
        dia_actual = dias_map.get(ahora.weekday())
        hora_actual = ahora.time()
        
        # Buscar si el docente tiene un horario en este momento
        clase_actual = self.horarios.filter(
            dia=dia_actual,
            hora_inicio__lte=hora_actual,
            hora_fin__gte=hora_actual
        ).first()
        
        if clase_actual:
            if clase_actual.curso and clase_actual.paralelo:
                return f"{clase_actual.curso.nombre} \"{clase_actual.paralelo.identificador}\""
            elif clase_actual.curso:
                return f"{clase_actual.curso.nombre}"
                
        return self.ubicacion_actual or "Ubicación no reportada"

    @property
    def estado_disponible(self):
        from django.utils import timezone
        ahora = timezone.localtime()
        dias_map = {0: 'lunes', 1: 'martes', 2: 'miercoles', 3: 'jueves', 4: 'viernes', 5: 'sabado', 6: 'domingo'}
        dia_actual = dias_map.get(ahora.weekday())
        hora_actual = ahora.time()
        
        en_clase = self.horarios.filter(
            dia=dia_actual,
            hora_inicio__lte=hora_actual,
            hora_fin__gte=hora_actual
        ).exists()
        
        if en_clase:
            return False
        return self.disponible

    def __str__(self):
        nombre = self.usuario.get_full_name()
        if not nombre.strip():
            nombre = self.usuario.username
        return nombre

class Curso(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Ej: Octavo, Noveno, Décimo")
    nivel = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.nombre

class Paralelo(models.Model):
    ESPECIALIDADES = (
        ('',             'Ninguna (Básica)'),
        ('bgu',          'Bachillerato General Unificado'),
        ('informatica',  'Bachillerato Técnico en Informática'),
        ('electricidad', 'Bachillerato Técnico en Electricidad'),
    )

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='paralelos')
    identificador = models.CharField(max_length=50, help_text="Ej: A, B, C o nombre completo")
    especialidad_bachillerato = models.CharField(
        max_length=20,
        choices=ESPECIALIDADES,
        blank=True,
        default='',
        help_text="Solo para bachillerato. Dejar vacío para básica."
    )
    tutor = models.ForeignKey('Docente', on_delete=models.SET_NULL, null=True, blank=True, related_name='paralelos_tutorados', help_text="Docente asignado como tutor de este paralelo.")


    class Meta:
        unique_together = ('curso', 'identificador')
        ordering = ['curso__nombre', 'identificador']

    def __str__(self):
        if self.especialidad_bachillerato:
            return f"{self.curso.nombre} - \"{self.identificador}\" ({self.get_especialidad_bachillerato_display()})"
        return f"{self.curso.nombre} - \"{self.identificador}\""

class Asignatura(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Aula(models.Model):
    nombre = models.CharField(max_length=50, unique=True, help_text="Ej: Laboratorio de Informática, Aula 101")
    capacidad = models.IntegerField(default=30)
    tipo = models.CharField(max_length=50, default='ordinaria', help_text="Ej: ordinaria, laboratorio, cancha")

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Horario(models.Model):
    DIAS = (
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
    )

    TIPOS = (
        ('docente', 'Horario del Docente'),
        ('clase',   'Horario de Clase'),
    )
    
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name='horarios')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='horarios')
    paralelo = models.ForeignKey(Paralelo, on_delete=models.CASCADE, related_name='horarios')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='horarios', null=True, blank=True)
    aula = models.ForeignKey(Aula, on_delete=models.SET_NULL, related_name='horarios', null=True, blank=True)
    dia = models.CharField(max_length=15, choices=DIAS)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    tipo = models.CharField(max_length=10, choices=TIPOS, default='docente', help_text="'docente' para el panel del profesor; 'clase' para la consulta pública de horarios.")

    class Meta:
        ordering = ['dia', 'hora_inicio']

    def __str__(self):
        nombre_docente = self.docente.usuario.get_full_name()
        if not nombre_docente.strip():
            nombre_docente = self.docente.usuario.username
        return f"{self.asignatura.nombre} - {nombre_docente} ({self.dia} {self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')})"

import uuid

class Leccion(models.Model):
    docente            = models.ForeignKey(Docente, on_delete=models.CASCADE)
    asignatura         = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    curso              = models.ForeignKey(Curso, on_delete=models.CASCADE)
    paralelo           = models.ForeignKey(Paralelo, on_delete=models.CASCADE)
    aula_requerida     = models.ForeignKey(Aula, on_delete=models.SET_NULL, null=True, blank=True, help_text="Si requiere un aula específica (ej. Laboratorio)")
    horas_semanales    = models.PositiveSmallIntegerField()
    max_horas_seguidas = models.PositiveSmallIntegerField(default=2)
    permitir_doble     = models.BooleanField(default=True)
    dias_separados     = models.BooleanField(default=False)

    class Meta:
        unique_together = ('docente', 'asignatura', 'paralelo')

    def __str__(self):
        return f"{self.asignatura.nombre} - {self.docente} ({self.curso} {self.paralelo.identificador})"

class DisponibilidadDocente(models.Model):
    TIPOS = [('bloqueado', 'Bloqueado'), ('preferido', 'Preferido')]
    docente     = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name='disponibilidades')
    dia         = models.CharField(max_length=15, choices=Horario.DIAS)
    hora_inicio = models.TimeField()
    hora_fin    = models.TimeField()
    tipo        = models.CharField(max_length=15, choices=TIPOS, default='bloqueado')

    class Meta:
        unique_together = ('docente', 'dia', 'hora_inicio')

class SesionGenerador(models.Model):
    ESTADOS = [('pendiente','Pendiente'),('corriendo','Corriendo'),
               ('completado','Completado'),('fallido','Fallido')]
    sesion_id   = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creado_en   = models.DateTimeField(auto_now_add=True)
    estado      = models.CharField(max_length=15, choices=ESTADOS, default='pendiente')
    modo        = models.CharField(max_length=15, default='estandar')
    advertencias = models.JSONField(default=list, blank=True)
    sin_asignar  = models.JSONField(default=list, blank=True)
    publicado    = models.BooleanField(default=False)

class BorradorHorario(models.Model):
    sesion      = models.ForeignKey(SesionGenerador, on_delete=models.CASCADE, related_name='borradores')
    leccion     = models.ForeignKey(Leccion, on_delete=models.CASCADE)
    dia         = models.CharField(max_length=15, choices=Horario.DIAS)
    hora_inicio = models.TimeField()
    hora_fin    = models.TimeField()
    aula        = models.ForeignKey(Aula, on_delete=models.SET_NULL, null=True, blank=True)
    
    docente_id_cache    = models.IntegerField()
    curso_id_cache      = models.IntegerField()
    paralelo_id_cache   = models.IntegerField()
    asignatura_id_cache = models.IntegerField()
