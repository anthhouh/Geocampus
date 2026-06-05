from django import forms
from .models import Leccion, DisponibilidadDocente

_INPUT = 'w-full px-4 py-2 bg-surface border border-outline-variant rounded-lg focus:outline-none focus:border-primary'
_SELECT = _INPUT

class LeccionForm(forms.ModelForm):
    class Meta:
        model = Leccion
        fields = [
            'docente', 'asignatura', 'curso', 'paralelo', 'aula_requerida',
            'horas_semanales', 'max_horas_seguidas', 'permitir_doble', 'dias_separados'
        ]
        widgets = {
            'docente':            forms.Select(attrs={'class': _SELECT}),
            'asignatura':         forms.Select(attrs={'class': _SELECT}),
            'curso':              forms.Select(attrs={'class': _SELECT, 'id': 'id_curso'}),
            'paralelo':           forms.Select(attrs={'class': _SELECT, 'id': 'id_paralelo'}),
            'aula_requerida':     forms.Select(attrs={'class': _SELECT}),
            'horas_semanales':    forms.NumberInput(attrs={'class': _INPUT, 'min': 1, 'max': 20}),
            'max_horas_seguidas': forms.NumberInput(attrs={'class': _INPUT, 'min': 1, 'max': 4}),
            'permitir_doble':     forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded accent-primary cursor-pointer'}),
            'dias_separados':     forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded accent-primary cursor-pointer'}),
        }
