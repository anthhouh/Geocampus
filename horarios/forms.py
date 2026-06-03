from django import forms
from .models import Horario, Docente, Curso, Paralelo, Asignatura

_INPUT = 'w-full px-4 py-2 bg-surface border border-outline-variant rounded-lg focus:outline-none focus:border-primary'
_SELECT = _INPUT

class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['curso', 'paralelo', 'asignatura', 'dia', 'hora_inicio', 'hora_fin']
        widgets = {
            'curso':       forms.Select(attrs={'class': _SELECT}),
            'paralelo':    forms.Select(attrs={'class': _SELECT}),
            'asignatura':  forms.Select(attrs={'class': _SELECT}),
            'dia':         forms.Select(attrs={'class': _SELECT}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': _INPUT}),
            'hora_fin':    forms.TimeInput(attrs={'type': 'time', 'class': _INPUT}),
        }

class HorarioAdminForm(forms.ModelForm):
    """Form completo para el panel de administración (incluye docente y tipo)."""
    class Meta:
        model = Horario
        fields = ['docente', 'curso', 'paralelo', 'asignatura', 'dia', 'hora_inicio', 'hora_fin', 'tipo']
        widgets = {
            'docente':     forms.Select(attrs={'class': _SELECT}),
            'curso':       forms.Select(attrs={'class': _SELECT, 'id': 'id_curso'}),
            'paralelo':    forms.Select(attrs={'class': _SELECT, 'id': 'id_paralelo'}),
            'asignatura':  forms.Select(attrs={'class': _SELECT}),
            'dia':         forms.Select(attrs={'class': _SELECT}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': _INPUT}),
            'hora_fin':    forms.TimeInput(attrs={'type': 'time', 'class': _INPUT}),
            'tipo':        forms.Select(attrs={'class': _SELECT}),
        }

class DocenteEditForm(forms.ModelForm):
    class Meta:
        model = Docente
        fields = ['especialidad', 'disponible', 'ubicacion_actual']
        widgets = {
            'especialidad':     forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: Matemáticas'}),
            'disponible':       forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded accent-primary cursor-pointer'}),
            'ubicacion_actual': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: Laboratorio 1'}),
        }

class DocenteCreateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: Juan'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: Pérez'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: jperez'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'Ej: jperez@ladolorosa-loja.edu.ec'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': 'Contraseña temporal'}))

    class Meta:
        model = Docente
        fields = ['especialidad', 'disponible', 'ubicacion_actual']
        widgets = {
            'especialidad':     forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: Matemáticas'}),
            'disponible':       forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded accent-primary cursor-pointer'}),
            'ubicacion_actual': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: Laboratorio 1'}),
        }

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombre', 'nivel']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: Décimo'}),
            'nivel':  forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: Básica Superior'}),
        }

class ParaleloForm(forms.ModelForm):
    class Meta:
        model = Paralelo
        fields = ['curso', 'identificador', 'especialidad_bachillerato', 'tutor']
        widgets = {
            'curso':                   forms.Select(attrs={'class': _SELECT}),
            'identificador':           forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: A, B, Diurno...', 'maxlength': '50'}),

            'especialidad_bachillerato': forms.Select(attrs={'class': _SELECT}),
            'tutor':                   forms.Select(attrs={'class': _SELECT}),
        }

class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ej: Matemáticas'}),
        }

class DocenteFotoForm(forms.ModelForm):
    class Meta:
        model = Docente
        fields = ['foto']

