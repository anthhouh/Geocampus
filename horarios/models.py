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
    identificador = models.CharField(max_length=10, help_text="Ej: A, B, C")
    especialidad_bachillerato = models.CharField(
        max_length=20,
        choices=ESPECIALIDADES,
        blank=True,
        default='',
        help_text="Solo para bachillerato. Dejar vacío para básica."
    )

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
