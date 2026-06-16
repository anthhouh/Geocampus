from django.contrib.auth.forms import PasswordChangeForm

def config_modal_context(request):
    """
    Inject the password_form into every template context so the
    configuration modal (included in base_app.html) works sitewide.
    """
    password_form = None
    user_avatar_url = None
    if request.user.is_authenticated:
        password_form = PasswordChangeForm(request.user)
        try:
            if hasattr(request.user, 'perfil_docente') and request.user.perfil_docente.foto:
                user_avatar_url = request.user.perfil_docente.foto.url
        except Exception:
            pass
    return {'password_form': password_form, 'user_avatar_url': user_avatar_url}
