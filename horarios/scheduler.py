import asyncio
import logging
import random
from collections import defaultdict
from asgiref.sync import sync_to_async
from django.db import transaction
from .models import Leccion, DisponibilidadDocente, SesionGenerador, BorradorHorario, Horario, Aula

logger = logging.getLogger(__name__)

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
DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']

class ScheduleState:
    def __init__(self):
        # 5 días, 9 periodos
        self.docente_grid = defaultdict(lambda: [[None]*9 for _ in range(5)])
        self.grupo_grid = defaultdict(lambda: defaultdict(lambda: [[None]*9 for _ in range(5)]))
        self.aula_grid = defaultdict(lambda: [[None]*9 for _ in range(5)])
        self.leccion_slots = defaultdict(list)
        self.bloqueos = set()

    def horas_docente_dia(self, docente_id, dia_idx):
        """Cuántas horas tiene ya asignadas el docente en un día."""
        return sum(1 for p in range(9) if self.docente_grid[docente_id][dia_idx][p] is not None)

    def is_valid(self, leccion, dia_idx, per_idx):
        docente_id = leccion.docente_id
        curso_id = leccion.curso_id
        paralelo_id = leccion.paralelo_id
        aula_id = leccion.aula_requerida_id

        # 1. Bloqueos manuales del docente
        if (docente_id, dia_idx, per_idx) in self.bloqueos:
            return False
            
        # 2. Solapamiento Docente
        if self.docente_grid[docente_id][dia_idx][per_idx] is not None:
            return False
            
        # 3. Solapamiento Grupo
        if self.grupo_grid[curso_id][paralelo_id][dia_idx][per_idx] is not None:
            return False
            
        # 4. Solapamiento Aula (si requiere)
        if aula_id and self.aula_grid[aula_id][dia_idx][per_idx] is not None:
            return False

        # 5. Restricciones de la Lección (mismo día)
        slots_mismo_dia = [p for d, p in self.leccion_slots[leccion.id] if d == dia_idx]
        if slots_mismo_dia:
            if not leccion.permitir_doble:
                return False
            if len(slots_mismo_dia) >= leccion.max_horas_seguidas:
                return False
            # Periodos adyacentes para no dejar huecos
            if not any(abs(p - per_idx) == 1 for p in slots_mismo_dia):
                return False

        # 6. Máximas horas seguidas generales del docente (evitar burnout)
        row = self.docente_grid[docente_id][dia_idx]
        row[per_idx] = leccion.id  # Colocar temporalmente
        max_consec = 0
        current_consec = 0
        for p in range(9):
            if row[p] is not None:
                current_consec += 1
                if current_consec > max_consec:
                    max_consec = current_consec
            else:
                current_consec = 0
        row[per_idx] = None  # Quitar temporal
        
        if max_consec > 5:
            return False

        return True

    def place(self, leccion, dia_idx, per_idx):
        self.docente_grid[leccion.docente_id][dia_idx][per_idx] = leccion.id
        self.grupo_grid[leccion.curso_id][leccion.paralelo_id][dia_idx][per_idx] = leccion.id
        if leccion.aula_requerida_id:
            self.aula_grid[leccion.aula_requerida_id][dia_idx][per_idx] = leccion.id
        self.leccion_slots[leccion.id].append((dia_idx, per_idx))

    def remove(self, leccion, dia_idx, per_idx):
        self.docente_grid[leccion.docente_id][dia_idx][per_idx] = None
        self.grupo_grid[leccion.curso_id][leccion.paralelo_id][dia_idx][per_idx] = None
        if leccion.aula_requerida_id:
            self.aula_grid[leccion.aula_requerida_id][dia_idx][per_idx] = None
        self.leccion_slots[leccion.id].remove((dia_idx, per_idx))


def _ordered_slots(leccion, state):
    """
    Genera el orden en que se probarán los slots (dia, periodo) para una lección.

    Estrategia:
    1. Si la lección ya tiene UN slot y horas_semanales == 2:
       → Fuerza que el segundo slot sea ADYACENTE en el MISMO DÍA (doble período obligatorio).
    2. Si la lección ya tiene un slot y horas_semanales >= 3:
       → Primero intenta completar un doble en el mismo día (adyacente).
       → Si no es posible, busca en otros días con menos carga.
    3. Si es el primer slot:
       → Elige el día con menos carga del docente (distribución semanal).
       → Periodos en orden aleatorio para evitar siempre la misma hora.
    """
    docente_id = leccion.docente_id
    slots_actuales = state.leccion_slots[leccion.id]
    dias_ya_usados = {d for d, p in slots_actuales}
    horas_total = leccion.horas_semanales

    # ── Caso: ya hay slots colocados ────────────────────────────────────────────
    if slots_actuales:
        ultimo_dia, ultimo_per = slots_actuales[-1]
        slots_mismo_dia = [p for d, p in slots_actuales if d == ultimo_dia]
        horas_en_dia = len(slots_mismo_dia)

        # ¿Conviene intentar COMPLETAR UN DOBLE en el mismo día?
        # Sí, si: tenemos exactamente 1 hora en ese día y el max_horas_seguidas lo permite
        quiere_doble = (
            horas_en_dia == 1
            and leccion.permitir_doble
            and leccion.max_horas_seguidas >= 2
        )
        # Para lecciones de 2 horas exactas: el doble es OBLIGATORIO (muy alta prioridad)
        doble_obligatorio = quiere_doble and horas_total == 2

        if quiere_doble:
            # Primero: periodos adyacentes en el mismo día
            adyacentes = [ultimo_per - 1, ultimo_per + 1]
            random.shuffle(adyacentes)
            for per_idx in adyacentes:
                if 0 <= per_idx < 9:
                    yield ultimo_dia, per_idx

            # Si el doble era obligatorio (2h) y no se colocó aquí, el backtrack
            # fallará para ese día → solo devolvemos slots del mismo día para forzarlo.
            # Para lecciones de 3+h: también intentar otros días si el adyacente no sirvió.
            if doble_obligatorio:
                # Mismo día, resto de periodos (muy poco probable que funcionen, pero los probamos)
                otros_mismo_dia = [p for p in range(9) if p not in adyacentes and p != ultimo_per]
                random.shuffle(otros_mismo_dia)
                for per_idx in otros_mismo_dia:
                    yield ultimo_dia, per_idx
                return  # No intentamos otros días para 2h → backtrack se encargará

        # Para 3+h con días_separados o cuando el día actual ya está lleno:
        # repartir a otro día con menos carga
        def peso_dia(d):
            carga = state.horas_docente_dia(docente_id, d)
            if leccion.dias_separados and d in dias_ya_usados:
                carga += 10
            # Muy penalizar el mismo día si ya tiene >= max_horas_seguidas
            slots_en_d = len([p for dd, p in slots_actuales if dd == d])
            if slots_en_d >= leccion.max_horas_seguidas:
                carga += 20
            return carga + random.random()

        dias_ordenados = sorted(range(5), key=peso_dia)
        for dia_idx in dias_ordenados:
            periodos = list(range(9))
            random.shuffle(periodos)
            for per_idx in periodos:
                yield dia_idx, per_idx
        return

    # ── Caso: primer slot (sin nada colocado aún) ────────────────────────────
    def peso_dia_inicial(d):
        carga = state.horas_docente_dia(docente_id, d)
        return carga + random.random()

    dias_ordenados = sorted(range(5), key=peso_dia_inicial)
    for dia_idx in dias_ordenados:
        periodos = list(range(9))
        random.shuffle(periodos)
        for per_idx in periodos:
            yield dia_idx, per_idx


async def generar_horario_async(sesion_id: str, max_intentos: int = 80000):
    """
    Función principal asíncrona que coordina la generación del horario.
    """
    try:
        sesion = await _obtener_sesion(sesion_id)
        if not sesion:
            return

        await _actualizar_estado_sesion(sesion, 'corriendo')

        # 1. Cargar datos
        lecciones, bloqueos = await _cargar_datos_generacion()
        
        # 2. Verificar coherencia inicial
        coherencia_valida, advertencias = _verificar_coherencia(lecciones, bloqueos)
        if not coherencia_valida:
            await _marcar_sesion_fallida(sesion, advertencias)
            return
        if advertencias:
            sesion.advertencias = advertencias
            await sync_to_async(sesion.save)()

        # 3. Inicializar Estado
        state = ScheduleState()
        for b in bloqueos:
            state.bloqueos.add((b['docente_id'], b['dia_idx'], b['per_idx']))

        # 4. Crear variables a asignar y ordenarlas (Heurística MRV estática)
        variables = []
        for lec in lecciones:
            # Calcular slots base disponibles para esta lección
            slots_libres = 0
            for d in range(5):
                for p in range(9):
                    if (lec.docente_id, d, p) not in state.bloqueos:
                        slots_libres += 1
            
            # Prioridad = cuantos menos slots libres relativos al total requerido, más difícil
            dificultad = slots_libres - lec.horas_semanales
            for i in range(lec.horas_semanales):
                variables.append({'leccion': lec, 'idx': i, 'dificultad': dificultad})
                
        # Ordenar por dificultad ascendente (las más restrictivas primero)
        variables.sort(key=lambda v: v['dificultad'])

        # 5. Ejecutar Backtracking
        contexto = {'intentos': 0, 'max_intentos': max_intentos, 'exito': False}
        await _backtrack(variables, 0, state, contexto)

        # 6. Guardar resultados
        if contexto['exito']:
            await _guardar_borrador(sesion, state.leccion_slots, lecciones)
            await _actualizar_estado_sesion(sesion, 'completado')
        else:
            await _marcar_sesion_fallida(sesion, ["No se encontró una solución viable en el límite de intentos. El horario es demasiado restrictivo."])

    except Exception as e:
        logger.error(f"Error en generación: {str(e)}", exc_info=True)
        await _marcar_sesion_fallida(sesion, [f"Error interno: {str(e)}"])


async def _backtrack(variables, var_idx, state, ctx):
    if var_idx == len(variables):
        ctx['exito'] = True
        return True
        
    ctx['intentos'] += 1
    if ctx['intentos'] > ctx['max_intentos']:
        return False
        
    # Ceder el hilo al event loop cada 1000 iteraciones
    if ctx['intentos'] % 1000 == 0:
        await asyncio.sleep(0)

    var = variables[var_idx]
    leccion = var['leccion']

    # Usar el orden de slots balanceado en vez de iterar en orden fijo
    for dia_idx, per_idx in _ordered_slots(leccion, state):
        if state.is_valid(leccion, dia_idx, per_idx):
            state.place(leccion, dia_idx, per_idx)
            
            result = await _backtrack(variables, var_idx + 1, state, ctx)
            if result:
                return True
                
            state.remove(leccion, dia_idx, per_idx)
            
            if ctx['intentos'] > ctx['max_intentos']:
                return False
                
    return False

# --- Funciones auxiliares de BD y Estado ---

@sync_to_async
def _obtener_sesion(sesion_id: str):
    try:
        return SesionGenerador.objects.get(sesion_id=sesion_id)
    except SesionGenerador.DoesNotExist:
        return None

@sync_to_async
def _actualizar_estado_sesion(sesion, estado: str, sin_asignar: list = None):
    sesion.estado = estado
    if sin_asignar is not None:
        sesion.sin_asignar = sin_asignar
    sesion.save()

@sync_to_async
def _marcar_sesion_fallida(sesion, advertencias: list):
    sesion.estado = 'fallido'
    sesion.advertencias = advertencias
    sesion.save()

@sync_to_async
def _cargar_datos_generacion():
    lecciones = list(Leccion.objects.select_related('docente', 'asignatura', 'curso', 'paralelo', 'aula_requerida').all())
    disp = DisponibilidadDocente.objects.filter(tipo='bloqueado')
    
    bloqueos = []
    for d in disp:
        dia_idx = DIAS.index(d.dia.lower())
        hora_str = d.hora_inicio.strftime("%H:%M:%S")
        per_idx = next((i for i, r in enumerate(PERIODOS_ROWS) if r[1] == hora_str), None)
        if per_idx is not None:
            bloqueos.append({'docente_id': d.docente_id, 'dia_idx': dia_idx, 'per_idx': per_idx})
            
    return lecciones, bloqueos

def _verificar_coherencia(lecciones, bloqueos):
    advertencias = []
    horas_por_docente = defaultdict(int)
    
    for lec in lecciones:
        horas_por_docente[lec.docente_id] += lec.horas_semanales
        
    for docente_id, horas in horas_por_docente.items():
        bloqueos_doc = sum(1 for b in bloqueos if b['docente_id'] == docente_id)
        horas_libres = (5 * 9) - bloqueos_doc
        if horas > horas_libres:
            advertencias.append(f"El docente ID {docente_id} necesita {horas} horas, pero solo tiene {horas_libres} libres.")
            
    return len(advertencias) == 0, advertencias

@sync_to_async
def _guardar_borrador(sesion, leccion_slots, lecciones):
    lecciones_dict = {l.id: l for l in lecciones}
    nuevos_borradores = []
    
    with transaction.atomic():
        # Limpiar borradores anteriores de esta sesión si existieran
        BorradorHorario.objects.filter(sesion=sesion).delete()
        
        for leccion_id, slots in leccion_slots.items():
            lec = lecciones_dict[leccion_id]
            for dia_idx, per_idx in slots:
                hora_inicio = PERIODOS_ROWS[per_idx][1]
                hora_fin = PERIODOS_ROWS[per_idx][2]
                
                nuevos_borradores.append(BorradorHorario(
                    sesion=sesion,
                    leccion=lec,
                    dia=DIAS[dia_idx],
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                    aula=lec.aula_requerida,
                    docente_id_cache=lec.docente_id,
                    curso_id_cache=lec.curso_id,
                    paralelo_id_cache=lec.paralelo_id,
                    asignatura_id_cache=lec.asignatura_id
                ))
                
        BorradorHorario.objects.bulk_create(nuevos_borradores)


@sync_to_async
def publicar_horario(sesion_id: str):
    """
    Publica el borrador generado, sobrescribiendo por completo los horarios 
    definitivos de los grupos involucrados.
    """
    with transaction.atomic():
        sesion = SesionGenerador.objects.get(sesion_id=sesion_id)
        borradores = sesion.borradores.select_related('leccion', 'aula').all()
        
        # Identificar grupos afectados
        grupos_afectados = set()
        for b in borradores:
            grupos_afectados.add((b.leccion.curso_id, b.leccion.paralelo_id))
            
        # Eliminar TODOS los Horarios actuales de esos grupos 
        for curso_id, paralelo_id in grupos_afectados:
            Horario.objects.filter(curso_id=curso_id, paralelo_id=paralelo_id).delete()
            
        # Crear los nuevos Horarios
        nuevos_horarios = []
        for b in borradores:
            nuevos_horarios.append(Horario(
                docente=b.leccion.docente,
                curso=b.leccion.curso,
                paralelo=b.leccion.paralelo,
                asignatura=b.leccion.asignatura,
                aula=b.aula,
                dia=b.dia,
                hora_inicio=b.hora_inicio,
                hora_fin=b.hora_fin,
                tipo='clase'
            ))
        Horario.objects.bulk_create(nuevos_horarios)
        
        sesion.publicado = True
        sesion.save()
        return len(nuevos_horarios), len(grupos_afectados)
