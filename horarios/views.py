import json
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.contrib import messages
from .models import Docente, Curso, Paralelo, Horario, Usuario, Asignatura
from .forms import HorarioForm, HorarioAdminForm, DocenteEditForm, DocenteCreateForm, CursoForm, ParaleloForm, AsignaturaForm, DocenteFotoForm


def admin_required(view_func):
    """Decorator: solo administradores. Redirige a index con mensaje si no es admin."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('horarios:login')
        if not (request.user.is_admin() or request.user.is_superuser):
            messages.warning(request, 'Solo se permite acceso a administradores')
            return redirect('horarios:index')
        return view_func(request, *args, **kwargs)
    return wrapper

TIME_TO_ROW = {
    "07:00:00": 2,
    "07:45:00": 3,
    "08:30:00": 4,
    "09:15:00": 5,
    "10:00:00": 6,
    "10:25:00": 7,
    "11:05:00": 8,
    "11:45:00": 9,
    "12:25:00": 10,
    "13:05:00": 11,
    "13:45:00": 12,
}

DAY_TO_COL = {
    "lunes": 2, "martes": 3, "miercoles": 4, "jueves": 5, "viernes": 6,
}

PERIODOS_ROWS = [
    (2, "07:00:00", "07:45:00"),
    (3, "07:45:00", "08:30:00"),
    (4, "08:30:00", "09:15:00"),
    (5, "09:15:00", "10:00:00"),
    (7, "10:25:00", "11:05:00"),
    (8, "11:05:00", "11:45:00"),
    (9, "11:45:00", "12:25:00"),
    (10, "12:25:00", "13:05:00"),
    (11, "13:05:00", "13:45:00"),
]


# Paleta intercalada: cada posición adyacente es de una familia opuesta
# (cálido ↔ frío ↔ neutro) para que índices cercanos nunca se parezcan.
_PALETA = [
    # 0 — Rojo coral (cálido intenso)
    {'bg': 'hsl(4,   90%, 82%)', 'border': 'hsl(4,   85%, 38%)', 'text': 'hsl(4,   80%, 20%)'},
    # 1 — Cian brillante (frío intenso)
    {'bg': 'hsl(192, 88%, 72%)', 'border': 'hsl(192, 80%, 24%)', 'text': 'hsl(192, 75%, 13%)'},
    # 2 — Amarillo dorado (cálido saturado)
    {'bg': 'hsl(46,  96%, 70%)', 'border': 'hsl(46,  88%, 28%)', 'text': 'hsl(46,  82%, 16%)'},
    # 3 — Violeta púrpura (frío vivo)
    {'bg': 'hsl(268, 72%, 76%)', 'border': 'hsl(268, 66%, 32%)', 'text': 'hsl(268, 62%, 17%)'},
    # 4 — Naranja quemado (cálido vibrante)
    {'bg': 'hsl(28,  96%, 76%)', 'border': 'hsl(28,  90%, 33%)', 'text': 'hsl(28,  85%, 17%)'},
    # 5 — Verde esmeralda (frío profundo)
    {'bg': 'hsl(152, 62%, 70%)', 'border': 'hsl(152, 56%, 22%)', 'text': 'hsl(152, 52%, 13%)'},
    # 6 — Rosa frambuesa (cálido suave)
    {'bg': 'hsl(328, 82%, 78%)', 'border': 'hsl(328, 75%, 33%)', 'text': 'hsl(328, 70%, 17%)'},
    # 7 — Azul zafiro (frío medio)
    {'bg': 'hsl(218, 80%, 76%)', 'border': 'hsl(218, 72%, 30%)', 'text': 'hsl(218, 68%, 16%)'},
    # 8 — Fucsia intenso (cálido-frío límite)
    {'bg': 'hsl(294, 74%, 76%)', 'border': 'hsl(294, 68%, 31%)', 'text': 'hsl(294, 62%, 16%)'},
    # 9 — Verde lima eléctrico (neutro vivo)
    {'bg': 'hsl(82,  74%, 70%)', 'border': 'hsl(82,  66%, 26%)', 'text': 'hsl(82,  60%, 14%)'},
    # 10 — Marrón terracota (neutro cálido)
    {'bg': 'hsl(16,  60%, 74%)', 'border': 'hsl(16,  54%, 28%)', 'text': 'hsl(16,  48%, 15%)'},
    # 11 — Turquesa vivo (frío vivo)
    {'bg': 'hsl(174, 76%, 68%)', 'border': 'hsl(174, 68%, 21%)', 'text': 'hsl(174, 64%, 12%)'},
    # 12 — Índigo oscuro (frío intenso)
    {'bg': 'hsl(244, 64%, 74%)', 'border': 'hsl(244, 58%, 33%)', 'text': 'hsl(244, 54%, 18%)'},
    # 13 — Azul cielo claro (frío suave)
    {'bg': 'hsl(206, 82%, 78%)', 'border': 'hsl(206, 74%, 30%)', 'text': 'hsl(206, 70%, 16%)'},
    # 14 — Verde salvia apagado (neutro frío)
    {'bg': 'hsl(120, 34%, 72%)', 'border': 'hsl(120, 28%, 25%)', 'text': 'hsl(120, 26%, 13%)'},
]

def get_color_for_materia(clave):
    """
    Devuelve un color de la paleta según la clave dada.
    La clave debe ser materia|curso_id|paralelo_id para que
    el mismo grupo siempre tenga el mismo color.
    Usa avalanche mixing para dispersar mejor strings similares.
    """
    hash_val = 5381
    for c in str(clave).lower().strip():
        # djb2 con avalanche: mejor dispersión para strings parecidos
        hash_val = ((hash_val << 5) + hash_val + ord(c)) & 0xFFFFFFFF
    # Segunda pasada para mejorar la dispersión de bits
    hash_val ^= (hash_val >> 16)
    hash_val = (hash_val * 0x45d9f3b) & 0xFFFFFFFF
    hash_val ^= (hash_val >> 16)
    return _PALETA[hash_val % len(_PALETA)]



def preparar_horarios_grid(horarios_qs, incluir_vacios=False, fusionar_bloques=False):
    base_items = []
    filled_map = {}
    
    for h in horarios_qs:
        start_str = h.hora_inicio.strftime("%H:%M:%S")
        end_str = h.hora_fin.strftime("%H:%M:%S")
        
        row_start = TIME_TO_ROW.get(start_str, 2)
        row_end = TIME_TO_ROW.get(end_str, row_start + 1)
        col = DAY_TO_COL.get(h.dia.lower(), 2)

        # Color único por combinación materia + curso + paralelo
        clave_color = f"{h.asignatura.nombre if h.asignatura else ''}|{h.curso_id}|{h.paralelo_id}"
        colors = get_color_for_materia(clave_color)
        
        base_items.append({
            'horario': h,
            'grid_row_start': row_start,
            'grid_row_end': row_end,
            'grid_col': col,
            'color_bg':     colors['bg'],
            'color_border': colors['border'],
            'color_text':   colors['text'],
        })
        
        for r in range(row_start, row_end):
            filled_map[(col, r)] = True

    if fusionar_bloques:
        base_items.sort(key=lambda x: (x['grid_col'], x['grid_row_start']))
        merged_items = []
        for item in base_items:
            if not merged_items:
                merged_items.append(item)
                continue
            last = merged_items[-1]
            can_merge = (
                last['grid_col'] == item['grid_col'] and
                last['grid_row_end'] == item['grid_row_start'] and
                last['horario'].asignatura_id == item['horario'].asignatura_id and
                last['horario'].docente_id == item['horario'].docente_id and
                last['horario'].curso_id == item['horario'].curso_id and
                last['horario'].paralelo_id == item['horario'].paralelo_id
            )
            if can_merge:
                last['grid_row_end'] = item['grid_row_end']
            else:
                merged_items.append(item)
        horarios_list = merged_items
    else:
        horarios_list = base_items

    if incluir_vacios:
        celdas_vacias = []
        for dia, col in DAY_TO_COL.items():
            for row, h_inicio, h_fin in PERIODOS_ROWS:
                celdas_vacias.append({
                    'dia': dia,
                    'hora_inicio': h_inicio,
                    'hora_fin': h_fin,
                    'grid_col': col,
                    'grid_row': row
                })
        return horarios_list, celdas_vacias
        
    return horarios_list

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_docente():
            return redirect('horarios:dashboard_docente')
        elif request.user.is_admin() or request.user.is_superuser:
            return redirect('horarios:gestion_dashboard')
        else:
            return redirect('horarios:index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_superuser and not user.email.endswith('@ladolorosa-loja.edu.ec'):
                messages.warning(request, 'El correo asociado a esta cuenta no pertenece a la institución (@ladolorosa-loja.edu.ec). Acceso denegado.')
                return render(request, 'horarios/login.html')
                
            login(request, user)
            if user.is_docente():
                return redirect('horarios:dashboard_docente')
            elif user.is_admin() or user.is_superuser:
                return redirect('horarios:gestion_dashboard')
            else:
                return redirect('horarios:index')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'horarios/login.html')

def registro_view(request):
    if request.user.is_authenticated:
        return redirect('horarios:index')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        rol = request.POST.get('rol')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validaciones
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'horarios/registro.html')

        if not email.endswith('@ladolorosa-loja.edu.ec'):
            messages.warning(request, 'El correo debe pertenecer a la institución (@ladolorosa-loja.edu.ec).')
            return render(request, 'horarios/registro.html')

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'Este nombre de usuario ya está en uso.')
            return render(request, 'horarios/registro.html')

        # Crear Usuario
        try:
            user = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                rol=rol
            )
            
            # Si es docente, crear su perfil automáticamente
            if rol == 'docente':
                Docente.objects.create(usuario=user)
                
            messages.success(request, '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.')
            return redirect('horarios:login')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al crear la cuenta: {str(e)}')

    return render(request, 'horarios/registro.html')

def logout_view(request):
    logout(request)
    return redirect('horarios:login')

@login_required
def index(request):
    # Directorio de Docentes y Disponibilidad
    # Mostrar todos los perfiles docentes (incluyendo admins que dan clases),
    # excepto la cuenta base del sistema 'admin'
    docentes = Docente.objects.exclude(
        usuario__username='admin'
    ).order_by('usuario__first_name')
    # Excluir el propio perfil si el usuario autenticado es docente
    if request.user.is_docente():
        docentes = docentes.exclude(usuario=request.user)
    context = {
        'docentes': docentes
    }
    return render(request, 'horarios/index.html', context)

@login_required
def dashboard_docente(request):
    if not (request.user.is_docente() or request.user.is_admin() or request.user.is_superuser):
        return redirect('horarios:index')
    
    # Crear un perfil de Docente temporal o permanente para el administrador si no lo tiene
    if not hasattr(request.user, 'perfil_docente'):
        Docente.objects.create(usuario=request.user, especialidad="Administrador")
    
    docente = request.user.perfil_docente

    if request.method == 'POST':
        form = DocenteFotoForm(request.POST, request.FILES, instance=docente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Foto de perfil actualizada exitosamente.')
            return redirect('horarios:dashboard_docente')
        else:
            messages.error(request, 'Error al subir la foto de perfil.')

    horarios = Horario.objects.filter(docente=docente).order_by('dia', 'hora_inicio')
    
    # Para el grid interactivo, fusionamos bloques y necesitamos celdas vacías
    horarios_grid, celdas_vacias = preparar_horarios_grid(horarios, incluir_vacios=True, fusionar_bloques=True)
    
    context = {
        'docente': docente,
        'horarios': horarios,
        'horarios_grid': horarios_grid,
        'celdas_vacias': celdas_vacias,
        'cursos': Curso.objects.all(),
        'asignaturas': Asignatura.objects.all(),
        'dias': Horario.DIAS,
        'es_docentes': True,
        'paralelos_json': _paralelos_json(),
    }
    return render(request, 'horarios/dashboard_docente.html', context)

@login_required
def imprimir_horario(request):
    if not hasattr(request.user, 'perfil_docente'):
        return redirect('horarios:index')
    
    docente = request.user.perfil_docente
    horarios = Horario.objects.filter(docente=docente).select_related('asignatura', 'curso', 'paralelo').order_by('dia', 'hora_inicio')

    PERIODOS = [
        {'num': '1',  'inicio': '07:00', 'fin': '07:45', 'key': '07:00:00'},
        {'num': '2',  'inicio': '07:45', 'fin': '08:30', 'key': '07:45:00'},
        {'num': '3',  'inicio': '08:30', 'fin': '09:15', 'key': '08:30:00'},
        {'num': '4',  'inicio': '09:15', 'fin': '10:00', 'key': '09:15:00'},
        {'num': 'R',  'inicio': '10:00', 'fin': '10:25', 'key': '10:00:00', 'recreo': True},
        {'num': '5',  'inicio': '10:25', 'fin': '11:05', 'key': '10:25:00'},
        {'num': '6',  'inicio': '11:05', 'fin': '11:45', 'key': '11:05:00'},
        {'num': '7',  'inicio': '11:45', 'fin': '12:25', 'key': '11:45:00'},
        {'num': '8',  'inicio': '12:25', 'fin': '13:05', 'key': '12:25:00'},
        {'num': '9',  'inicio': '13:05', 'fin': '13:45', 'key': '13:05:00'},
    ]
    DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']

    # Organizar horarios en un dict {dia: {hora_inicio_str: horario_obj}}
    horario_map = {}
    for h in horarios:
        key_dia = h.dia.lower()
        key_hora = h.hora_inicio.strftime("%H:%M:%S")
        horario_map[(key_dia, key_hora)] = h

    # Calcular color por clase
    def color_para(h):
        clave = f"{h.asignatura.nombre if h.asignatura else ''}|{h.curso_id}|{h.paralelo_id}"
        return get_color_for_materia(clave)

    # Construir tabla: lista de filas, cada fila tiene celdas por día
    tabla = []
    skip_map = {}
    for row_idx, periodo in enumerate(PERIODOS):
        if periodo.get('recreo'):
            tabla.append({'periodo': periodo, 'recreo': True})
            continue
            
        fila = {'periodo': periodo, 'recreo': False, 'dias': []}
        for dia_idx, dia in enumerate(DIAS):
            if skip_map.get((dia_idx, row_idx)):
                continue
                
            h = horario_map.get((dia, periodo['key']))
            if h:
                rowspan = 1
                for next_row_idx in range(row_idx + 1, len(PERIODOS)):
                    next_periodo = PERIODOS[next_row_idx]
                    if next_periodo.get('recreo'):
                        break
                    next_h = horario_map.get((dia, next_periodo['key']))
                    if next_h and \
                       next_h.asignatura_id == h.asignatura_id and \
                       next_h.curso_id == h.curso_id and \
                       next_h.paralelo_id == h.paralelo_id:
                        rowspan += 1
                        skip_map[(dia_idx, next_row_idx)] = True
                    else:
                        break
                        
                colors = color_para(h)
                fila['dias'].append({
                    'horario': h,
                    'color_bg': colors['bg'],
                    'color_border': colors['border'],
                    'color_text': colors['text'],
                    'rowspan': rowspan,
                })
            else:
                fila['dias'].append(None)
        tabla.append(fila)

    from django.utils import timezone
    fecha_hoy = timezone.localdate()

    context = {
        'docente': docente,
        'tabla': tabla,
        'fecha_hoy': fecha_hoy,
    }
    return render(request, 'horarios/imprimir_horario.html', context)

@login_required
@require_POST
def cambiar_estado(request):
    if not hasattr(request.user, 'perfil_docente'):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        data = json.loads(request.body)
        docente = request.user.perfil_docente
        docente.disponible = data.get('disponible', docente.disponible)
        docente.ubicacion_actual = data.get('ubicacion_actual', docente.ubicacion_actual)
        docente.save()
        return JsonResponse({'status': 'ok', 'disponible': docente.estado_disponible, 'ubicacion': docente.ubicacion_dinamica})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def horarios_curso(request):
    cursos = Curso.objects.all()
    # Identificadores únicos de paralelos (A, B, C...) en lugar de cada paralelo
    identificadores = Paralelo.objects.values_list('identificador', flat=True).distinct().order_by('identificador')
    
    curso_id = request.GET.get('curso')
    paralelo_ident = request.GET.get('paralelo')
    
    grupos = []
    
    if curso_id or paralelo_ident:
        paralelos = Paralelo.objects.select_related('curso').all()
        if curso_id:
            paralelos = paralelos.filter(curso_id=curso_id)
        if paralelo_ident:
            paralelos = paralelos.filter(identificador=paralelo_ident)
            
        # Mostrar todos los horarios (docente y clase) en la vista del curso,
        # ya que la validación de choques previene duplicados.
        horarios_qs = Horario.objects.select_related('docente__usuario', 'asignatura')
        
        for p in paralelos:
            hs = horarios_qs.filter(curso=p.curso, paralelo=p).order_by('dia', 'hora_inicio')
            horarios_grid = preparar_horarios_grid(hs, fusionar_bloques=True)
            
            grupos.append({
                'id': f"curso_{p.curso_id}_paralelo_{p.id}",
                'titulo': f"{p.curso.nombre} '{p.identificador}'",
                'horarios_grid': horarios_grid,
            })
                
        grupos.sort(key=lambda x: (_get_curso_order(x['titulo']), x['titulo']))
        
    context = {
        'cursos': cursos,
        'identificadores': identificadores,
        'grupos': grupos,
    }
    return render(request, 'horarios/horarios_curso.html', context)

@login_required
def horario_docente(request, docente_id):
    """Vista pública (para docentes y estudiantes) del horario de un docente específico."""
    docente = get_object_or_404(Docente, pk=docente_id)
    horarios = Horario.objects.filter(
        docente=docente, tipo='docente'
    ).order_by('dia', 'hora_inicio')
    
    asignaturas_count = horarios.values('asignatura').distinct().count()
    cursos_count = horarios.values('curso', 'paralelo').distinct().count()
    
    horarios_grid = preparar_horarios_grid(horarios, fusionar_bloques=True)

    context = {
        'docente': docente,
        'horarios': horarios,
        'horarios_grid': horarios_grid,
        'asignaturas_count': asignaturas_count,
        'cursos_count': cursos_count,
        'es_propio': request.user.is_docente() and hasattr(request.user, 'perfil_docente') and request.user.perfil_docente == docente,
    }
    return render(request, 'horarios/horario_docente.html', context)

@login_required
def añadir_horario(request):
    if not request.user.is_docente() and not request.user.is_admin():
        messages.error(request, 'No tienes permisos para añadir horarios.')
        return redirect('horarios:index')

    if request.method == 'POST':
        form = HorarioForm(request.POST)
        if form.is_valid():
            horario = form.save(commit=False)
            horario.docente = request.user.perfil_docente
            horario.save()
            messages.success(request, 'Horario añadido exitosamente.')
            return redirect('horarios:dashboard_docente')
    else:
        form = HorarioForm()

    # Construir mapa curso_id -> lista de paralelos para filtrado en JS
    paralelos_por_curso = {}
    for p in Paralelo.objects.select_related('curso').all():
        cid = str(p.curso_id)
        if cid not in paralelos_por_curso:
            paralelos_por_curso[cid] = []
        label = p.identificador
        if p.especialidad_bachillerato:
            label = f"{p.identificador} ({p.get_especialidad_bachillerato_display()})"
        paralelos_por_curso[cid].append({'id': p.id, 'nombre': label})

    return render(request, 'horarios/anadir_horario.html', {
        'form': form,
        'paralelos_json': json.dumps(paralelos_por_curso),
    })


# ──────────────────────────────────────────────────────────────────────────────
# PANEL DE GESTIÓN (solo administradores)
# ──────────────────────────────────────────────────────────────────────────────

def _paralelos_json():
    """Construye el mapa curso_id → paralelos para el JS de cascada."""
    mapa = {}
    for p in Paralelo.objects.select_related('curso').all():
        cid = str(p.curso_id)
        if cid not in mapa:
            mapa[cid] = []
        label = p.identificador
        if p.especialidad_bachillerato:
            label = f"{p.identificador} ({p.get_especialidad_bachillerato_display()})"
        mapa[cid].append({'id': p.id, 'nombre': label})
    return json.dumps(mapa)


@admin_required
def gestion_dashboard(request):
    context = {
        'total_docentes':        Docente.objects.count(),
        'total_cursos':          Curso.objects.count(),
        'total_paralelos':       Paralelo.objects.count(),
        'total_h_docente':       Horario.objects.filter(tipo='docente').count(),
        'total_h_clase':         Horario.objects.filter(tipo='clase').count(),
        'docentes_disponibles':  Docente.objects.filter(disponible=True).count(),
        'ultimos_horarios':      Horario.objects.select_related(
                                    'docente__usuario', 'curso', 'paralelo'
                                 ).order_by('-id')[:8],
    }
    return render(request, 'horarios/gestion/dashboard.html', context)


@admin_required
def gestion_horarios(request):
    return redirect('horarios:gestion_horarios_docentes')

@admin_required
def gestion_horarios_docentes(request):
    return _render_horarios_list(request, 'docente', 'Horarios de Docentes')

@admin_required
def gestion_horarios_cursos(request):
    return _render_horarios_list(request, 'clase', 'Horarios de Cursos')

def _get_curso_order(titulo):
    t = titulo.lower()
    if 'octavo' in t: return 1
    if 'noveno' in t: return 2
    if 'décimo' in t or 'decimo' in t: return 3
    if 'primero' in t: return 4
    if 'segundo' in t: return 5
    if 'tercero' in t: return 6
    return 99

def _render_horarios_list(request, tipo_agrupacion, titulo):
    horarios_qs = Horario.objects.select_related('docente__usuario', 'curso', 'paralelo').all()
    docente_id = request.GET.get('docente')
    curso_id   = request.GET.get('curso')
    dia        = request.GET.get('dia')

    if docente_id: horarios_qs = horarios_qs.filter(docente_id=docente_id)
    if curso_id:   horarios_qs = horarios_qs.filter(curso_id=curso_id)
    if dia:        horarios_qs = horarios_qs.filter(dia=dia)

    grupos = []
    
    if tipo_agrupacion == 'clase':
        paralelos = Paralelo.objects.select_related('curso').all()
        if curso_id:
            paralelos = paralelos.filter(curso_id=curso_id)
        
        for p in paralelos:
            hs = horarios_qs.filter(curso=p.curso, paralelo=p).order_by('dia', 'hora_inicio')
            filled, empty = preparar_horarios_grid(hs, incluir_vacios=True, fusionar_bloques=True)
            grupos.append({
                'id': f"curso_{p.curso_id}_paralelo_{p.id}",
                'titulo': f"{p.curso.nombre} '{p.identificador}'",
                'curso_id': p.curso_id,
                'paralelo_id': p.id,
                'horarios_grid': filled,
                'celdas_vacias': empty
            })
        # Ordenar cronológicamente (Octavo -> Tercero) y luego por identificador
        grupos.sort(key=lambda x: (_get_curso_order(x['titulo']), x['titulo']))
    else:
        docentes_qs = Docente.objects.select_related('usuario').all().order_by('usuario__first_name')
        if docente_id:
            docentes_qs = docentes_qs.filter(id=docente_id)
            
        for d in docentes_qs:
            hs = horarios_qs.filter(docente=d).order_by('dia', 'hora_inicio')
            filled, empty = preparar_horarios_grid(hs, incluir_vacios=True, fusionar_bloques=True)
            grupos.append({
                'id': f"docente_{d.id}",
                'titulo': d.usuario.get_full_name() or d.usuario.username,
                'docente_id': d.id,
                'horarios_grid': filled,
                'celdas_vacias': empty
            })

    context = {
        'grupos':    grupos,
        'docentes':  Docente.objects.select_related('usuario').order_by('usuario__first_name'),
        'cursos':    Curso.objects.all(),
        'dias':      Horario.DIAS,
        'filtros':   {'docente': docente_id, 'curso': curso_id, 'dia': dia},
        'titulo_seccion': titulo,
        'es_docentes': tipo_agrupacion == 'docente',
        'hay_resultados': len(grupos) > 0,
        'paralelos_json': _paralelos_json(),
        'asignaturas': Asignatura.objects.all(),
    }
    return render(request, 'horarios/gestion/horarios.html', context)

@login_required
@require_POST
def api_guardar_horario(request):
    horario_id = request.POST.get('horario_id')
    dia = request.POST.get('dia')
    hora_inicio = request.POST.get('hora_inicio')
    hora_fin = request.POST.get('hora_fin')
    asignatura_id = request.POST.get('asignatura_id')
    docente_id = request.POST.get('docente_id')
    curso_id = request.POST.get('curso_id')
    paralelo_id = request.POST.get('paralelo_id')

    if not all([dia, hora_inicio, hora_fin, asignatura_id, docente_id, curso_id, paralelo_id]):
        return JsonResponse({'status': 'error', 'message': "Faltan datos requeridos para guardar el horario."})

    # Permisos
    if not (request.user.is_admin() or request.user.is_superuser):
        if not request.user.is_docente():
            return JsonResponse({'status': 'error', 'message': "No tienes permisos."}, status=403)
        if str(request.user.perfil_docente.id) != str(docente_id):
            return JsonResponse({'status': 'error', 'message': "Solo puedes editar tus propios horarios."}, status=403)

    try:
        docente = Docente.objects.get(id=docente_id)
        curso = Curso.objects.get(id=curso_id)
        paralelo = Paralelo.objects.get(id=paralelo_id)
        asignatura = Asignatura.objects.get(id=asignatura_id)
        
        cantidad_periodos = int(request.POST.get('cantidad_periodos', 1))
        
        periodos_a_guardar = []
        hora_inicio_str = str(hora_inicio)
        if len(hora_inicio_str) == 5:
            hora_inicio_str += ":00"
            
        start_idx = -1
        for i, row in enumerate(PERIODOS_ROWS):
            if row[1] == hora_inicio_str:
                start_idx = i
                break
                
        if start_idx != -1:
            for i in range(cantidad_periodos):
                if start_idx + i < len(PERIODOS_ROWS):
                    periodos_a_guardar.append((PERIODOS_ROWS[start_idx + i][1], PERIODOS_ROWS[start_idx + i][2]))
                else:
                    break
                    
        if not periodos_a_guardar:
            periodos_a_guardar = [(hora_inicio, hora_fin)]

        # Validación de cruce de horarios para todos los periodos
        for p_inicio, p_fin in periodos_a_guardar:
            # Check docente
            choques_docente = Horario.objects.filter(
                docente=docente,
                dia=dia,
                hora_inicio__lt=p_fin,
                hora_fin__gt=p_inicio
            )
            if horario_id and p_inicio == periodos_a_guardar[0][0]:
                choques_docente = choques_docente.exclude(id=horario_id)
                
            if choques_docente.exists():
                choque = choques_docente.first()
                docente_nombre = docente.usuario.get_full_name() or docente.usuario.username
                hora_i = choque.hora_inicio.strftime('%H:%M')
                hora_f = choque.hora_fin.strftime('%H:%M')
                return JsonResponse({'status': 'error', 'message': f"¡Choque de Horario! El docente {docente_nombre} ya dicta '{choque.asignatura.nombre}' el {dia} de {hora_i} a {hora_f}."})

            # Check curso/paralelo
            choques_curso = Horario.objects.filter(
                curso=curso,
                paralelo=paralelo,
                dia=dia,
                hora_inicio__lt=p_fin,
                hora_fin__gt=p_inicio
            )
            if horario_id and p_inicio == periodos_a_guardar[0][0]:
                choques_curso = choques_curso.exclude(id=horario_id)
                
            if choques_curso.exists():
                choque = choques_curso.first()
                doc_choque_nombre = choque.docente.usuario.get_full_name() or choque.docente.usuario.username
                hora_i = choque.hora_inicio.strftime('%H:%M')
                hora_f = choque.hora_fin.strftime('%H:%M')
                return JsonResponse({'status': 'error', 'message': f"¡Choque de Horario! El curso {curso.nombre} '{paralelo.identificador}' ya tiene la clase '{choque.asignatura.nombre}' con el docente {doc_choque_nombre} el {dia} de {hora_i} a {hora_f}."})
        
        first_h = None
        tipo = 'docente' if request.POST.get('es_docentes') == '1' else 'clase'
        
        saved_horarios = []
        for idx, (p_inicio, p_fin) in enumerate(periodos_a_guardar):
            if idx == 0 and horario_id:
                h = Horario.objects.get(id=horario_id)
                
                # Verificación de seguridad adicional
                if not (request.user.is_admin() or request.user.is_superuser):
                    if h.docente_id != request.user.perfil_docente.id:
                        return JsonResponse({'status': 'error', 'message': "No autorizado para editar este horario."}, status=403)
                        
                h.dia = dia
                h.hora_inicio = p_inicio
                h.hora_fin = p_fin
                h.asignatura = asignatura
                h.docente = docente
                h.curso = curso
                h.paralelo = paralelo
                h.save()
                saved_horarios.append(h)
            else:
                h = Horario.objects.create(
                    dia=dia,
                    hora_inicio=p_inicio,
                    hora_fin=p_fin,
                    asignatura=asignatura,
                    docente=docente,
                    curso=curso,
                    paralelo=paralelo,
                    tipo=tipo
                )
                saved_horarios.append(h)

        msg = f"Se guardaron {len(periodos_a_guardar)} periodos exitosamente." if len(periodos_a_guardar) > 1 else ("Horario actualizado exitosamente." if horario_id else "Horario guardado exitosamente.")
            
        # Preparar los datos de los items para renderizar el HTML fusionado
        # Extraemos los IDs y hacemos un fetch de la BD para asegurar que los campos de hora sean objetos datetime.time
        saved_ids = [h.id for h in saved_horarios]
        fresh_horarios = Horario.objects.filter(id__in=saved_ids).select_related('docente__usuario', 'curso', 'paralelo', 'asignatura').order_by('dia', 'hora_inicio')
        
        from .views import preparar_horarios_grid
        merged_items = preparar_horarios_grid(fresh_horarios, fusionar_bloques=True)
        
        es_docentes = request.POST.get('es_docentes') == '1'
        html_parts = []
        for item_data in merged_items:
            html_parts.append(render_to_string('horarios/gestion/schedule_item.html', {'item': item_data, 'es_docentes': es_docentes}))
            
        html = "\n".join(html_parts)
        
        if es_docentes:
            grupo_id = f"docente_{docente.id}"
        else:
            grupo_id = f"curso_{curso.id}_paralelo_{paralelo.id}"
            
        return JsonResponse({
            'status': 'success', 
            'message': msg,
            'html': html,
            'horario_id': saved_horarios[0].id,
            'grupo_id': grupo_id
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f"Error al guardar horario: {str(e)}"})


@admin_required
def gestion_crear_horario(request):
    if request.method == 'POST':
        form = HorarioAdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Horario creado exitosamente.')
            return redirect('horarios:gestion_horarios')
    else:
        form = HorarioAdminForm()
    return render(request, 'horarios/gestion/horario_form.html', {
        'form': form,
        'paralelos_json': _paralelos_json(),
        'titulo': 'Crear Horario',
        'accion': 'Crear',
    })


@admin_required
def gestion_editar_horario(request, horario_id):
    horario = get_object_or_404(Horario, pk=horario_id)
    if request.method == 'POST':
        form = HorarioAdminForm(request.POST, instance=horario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Horario actualizado exitosamente.')
            return redirect('horarios:gestion_horarios')
    else:
        form = HorarioAdminForm(instance=horario)
    return render(request, 'horarios/gestion/horario_form.html', {
        'form': form,
        'paralelos_json': _paralelos_json(),
        'titulo': f'Editar — {horario.asignatura.nombre if horario.asignatura else "Horario"}',
        'accion': 'Guardar cambios',
        'horario': horario,
    })


@login_required
@require_POST
def gestion_eliminar_horario(request, horario_id):
    horario = get_object_or_404(Horario, pk=horario_id)
    
    # Permisos
    if not (request.user.is_admin() or request.user.is_superuser):
        if not request.user.is_docente() or horario.docente_id != request.user.perfil_docente.id:
            return JsonResponse({'status': 'error', 'message': "No autorizado para eliminar este horario."}, status=403)
            
    nombre = horario.asignatura.nombre if horario.asignatura else 'Horario'
    
    # Para eliminar el bloque completo (que visualmente estaba fusionado)
    horarios_to_delete = [horario]
    current_h = horario
    
    while True:
        # Buscamos el siguiente periodo que empiece exactamente donde termina este
        # y tenga exactamente los mismos atributos
        next_h = Horario.objects.filter(
            docente_id=current_h.docente_id,
            curso_id=current_h.curso_id,
            paralelo_id=current_h.paralelo_id,
            asignatura_id=current_h.asignatura_id,
            dia=current_h.dia,
            hora_inicio=current_h.hora_fin
        ).first()
        
        if next_h:
            horarios_to_delete.append(next_h)
            current_h = next_h
        else:
            break
            
    count = len(horarios_to_delete)
    for h in horarios_to_delete:
        h.delete()
        
    msg = f'Horario "{nombre}" eliminado correctamente.' if count == 1 else f'Bloque de {count} periodos de "{nombre}" eliminado correctamente.'
    return JsonResponse({'status': 'success', 'message': msg})


@admin_required
def gestion_docentes(request):
    docentes = Docente.objects.select_related('usuario').order_by('usuario__first_name')
    return render(request, 'horarios/gestion/docentes.html', {'docentes': docentes})

@admin_required
def gestion_crear_docente(request):
    if request.method == 'POST':
        form = DocenteCreateForm(request.POST)
        if form.is_valid():
            try:
                user = Usuario.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    rol='docente'
                )
                docente = form.save(commit=False)
                docente.usuario = user
                docente.save()
                messages.success(request, 'Docente creado exitosamente.')
                return redirect('horarios:gestion_docentes')
            except Exception as e:
                messages.error(request, f'Ocurrió un error al crear el docente: {str(e)}')
    else:
        form = DocenteCreateForm()
    return render(request, 'horarios/gestion/docente_form.html', {
        'form': form, 'titulo': 'Crear Docente', 'accion': 'Crear'
    })

@admin_required
def gestion_editar_docente(request, docente_id):
    docente = get_object_or_404(Docente, pk=docente_id)
    if request.method == 'POST':
        form = DocenteEditForm(request.POST, instance=docente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Docente actualizado exitosamente.')
            return redirect('horarios:gestion_docentes')
    else:
        form = DocenteEditForm(instance=docente)
    return render(request, 'horarios/gestion/docente_form.html', {
        'form': form, 'docente': docente, 'titulo': f'Editar Docente', 'accion': 'Guardar cambios'
    })

@admin_required
@require_POST
def gestion_eliminar_docente(request, docente_id):
    docente = get_object_or_404(Docente, pk=docente_id)
    usuario = docente.usuario
    nombre = usuario.get_full_name() or usuario.username
    usuario.delete() # Al eliminar usuario, el docente se elimina en cascada
    messages.success(request, f'Docente "{nombre}" eliminado.')
    return redirect('horarios:gestion_docentes')

@admin_required
def gestion_cursos(request):
    cursos = Curso.objects.prefetch_related('paralelos').order_by('nombre')
    return render(request, 'horarios/gestion/cursos.html', {'cursos': cursos})


@admin_required
def gestion_crear_curso(request):
    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso creado exitosamente.')
            return redirect('horarios:gestion_cursos')
    else:
        form = CursoForm()
    return render(request, 'horarios/gestion/curso_form.html', {
        'form': form, 'titulo': 'Crear Curso', 'accion': 'Crear',
    })


@admin_required
def gestion_editar_curso(request, curso_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado exitosamente.')
            return redirect('horarios:gestion_cursos')
    else:
        form = CursoForm(instance=curso)
    return render(request, 'horarios/gestion/curso_form.html', {
        'form': form, 'titulo': f'Editar — {curso.nombre}', 'accion': 'Guardar cambios',
    })


@admin_required
@require_POST
def gestion_eliminar_curso(request, curso_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    nombre = curso.nombre
    curso.delete()
    messages.success(request, f'Curso "{nombre}" eliminado.')
    return redirect('horarios:gestion_cursos')


@admin_required
def gestion_crear_paralelo(request):
    curso_init = request.GET.get('curso')
    if request.method == 'POST':
        form = ParaleloForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paralelo creado exitosamente.')
            return redirect('horarios:gestion_cursos')
    else:
        form = ParaleloForm(initial={'curso': curso_init} if curso_init else {})
    return render(request, 'horarios/gestion/paralelo_form.html', {
        'form': form, 'titulo': 'Crear Paralelo', 'accion': 'Crear',
    })


@admin_required
def gestion_editar_paralelo(request, paralelo_id):
    paralelo = get_object_or_404(Paralelo, pk=paralelo_id)
    if request.method == 'POST':
        form = ParaleloForm(request.POST, instance=paralelo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paralelo actualizado exitosamente.')
            return redirect('horarios:gestion_cursos')
    else:
        form = ParaleloForm(instance=paralelo)
    return render(request, 'horarios/gestion/paralelo_form.html', {
        'form': form, 'titulo': f'Editar — {paralelo}', 'accion': 'Guardar cambios',
    })


@admin_required
@require_POST
def gestion_eliminar_paralelo(request, paralelo_id):
    paralelo = get_object_or_404(Paralelo, pk=paralelo_id)
    nombre = str(paralelo)
    paralelo.delete()
    messages.success(request, f'Paralelo "{nombre}" eliminado.')
    return redirect('horarios:gestion_cursos')

@admin_required
def gestion_asignaturas(request):
    asignaturas = Asignatura.objects.all().order_by('nombre')
    return render(request, 'horarios/gestion/asignaturas.html', {'asignaturas': asignaturas})

@admin_required
def gestion_crear_asignatura(request):
    if request.method == 'POST':
        form = AsignaturaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asignatura creada exitosamente.')
            return redirect('horarios:gestion_asignaturas')
    else:
        form = AsignaturaForm()
    return render(request, 'horarios/gestion/asignatura_form.html', {
        'form': form, 'titulo': 'Crear Asignatura', 'accion': 'Crear',
    })

@admin_required
def gestion_editar_asignatura(request, asignatura_id):
    asignatura = get_object_or_404(Asignatura, pk=asignatura_id)
    if request.method == 'POST':
        form = AsignaturaForm(request.POST, instance=asignatura)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asignatura actualizada exitosamente.')
            return redirect('horarios:gestion_asignaturas')
    else:
        form = AsignaturaForm(instance=asignatura)
    return render(request, 'horarios/gestion/asignatura_form.html', {
        'form': form, 'titulo': f'Editar — {asignatura.nombre}', 'accion': 'Guardar cambios',
    })

@admin_required
@require_POST
def gestion_eliminar_asignatura(request, asignatura_id):
    asignatura = get_object_or_404(Asignatura, pk=asignatura_id)
    nombre = asignatura.nombre
    asignatura.delete()
    messages.success(request, f'Asignatura "{nombre}" eliminada.')
    return redirect('horarios:gestion_asignaturas')
