from django import template

register = template.Library()

# Map of keyword → Material Symbols icon name
_SUBJECT_ICON_MAP = {
    # Matemáticas
    'matemática': 'calculate',
    'matematica': 'calculate',
    'algebra': 'calculate',
    'geometria': 'calculate',
    'geometría': 'calculate',
    'calculo': 'calculate',
    'cálculo': 'calculate',
    'estadistica': 'bar_chart',
    'estadística': 'bar_chart',

    # Lengua / Literatura / Español
    'lengua': 'menu_book',
    'literatura': 'auto_stories',
    'español': 'menu_book',
    'comunicación': 'menu_book',
    'comunicacion': 'menu_book',
    'lectura': 'menu_book',
    'escritura': 'edit',

    # Inglés
    'inglés': 'translate',
    'ingles': 'translate',
    'idioma': 'translate',
    'segundo idioma': 'translate',

    # Ciencias Naturales / Biología
    'ciencias naturales': 'eco',
    'biologia': 'biotech',
    'biología': 'biotech',
    'ciencias': 'science',
    'natural': 'eco',

    # Física
    'física': 'bolt',
    'fisica': 'bolt',

    # Química
    'química': 'science',
    'quimica': 'science',

    # Historia / Sociales / CC.SS
    'historia': 'history_edu',
    'sociales': 'public',
    'estudios sociales': 'public',
    'geografía': 'map',
    'geografia': 'map',
    'sociedad': 'public',

    # Arte / Música
    'arte': 'palette',
    'artes': 'palette',
    'artes plásticas': 'palette',
    'plasticas': 'palette',
    'dibujo': 'gesture',
    'música': 'music_note',
    'musica': 'music_note',

    # Educación Física / Deportes
    'educación física': 'sports_soccer',
    'educacion fisica': 'sports_soccer',
    'deporte': 'sports_basketball',
    'deportes': 'sports_basketball',
    'cultura física': 'fitness_center',
    'cultura fisica': 'fitness_center',

    # Tecnología / Informática / CAIAI
    'tecnología': 'computer',
    'tecnologia': 'computer',
    'informática': 'computer',
    'informatica': 'computer',
    'computación': 'computer',
    'computacion': 'computer',
    'c.a.i.a': 'computer',
    'caiai': 'computer',
    'caia': 'computer',
    'taller': 'build',

    # Religión / Orientación
    'religión': 'church',
    'religion': 'church',
    'orientación': 'self_improvement',
    'orientacion': 'self_improvement',
    'religión y orientación': 'church',
    'religion y orientacion': 'church',
    'valores': 'favorite',
    'ética': 'balance',
    'etica': 'balance',

    # Filosofía / Psicología
    'filosofía': 'psychology',
    'filosofia': 'psychology',
    'psicología': 'psychology',
    'psicologia': 'psychology',

    # Economía / Contabilidad / Emprendimiento
    'economía': 'currency_exchange',
    'economia': 'currency_exchange',
    'contabilidad': 'receipt_long',
    'emprendimiento': 'business_center',
    'comercio': 'store',
    'marketing': 'campaign',
    'administración': 'manage_accounts',
    'administracion': 'manage_accounts',

    # Investigación
    'investigación': 'search',
    'investigacion': 'search',
    'metodología': 'manage_search',
    'metodologia': 'manage_search',
    'proyecto': 'assignment',
    'proyectos': 'assignment',
}

_DEFAULT_ICON = 'menu_book'


@register.filter
def subject_icon(nombre):
    """Returns a Material Symbols icon name for a subject name."""
    if not nombre:
        return _DEFAULT_ICON
    name_lower = nombre.lower().strip()
    # First try exact match
    if name_lower in _SUBJECT_ICON_MAP:
        return _SUBJECT_ICON_MAP[name_lower]
    # Then keyword match
    for keyword, icon in _SUBJECT_ICON_MAP.items():
        if keyword in name_lower:
            return icon
    return _DEFAULT_ICON
