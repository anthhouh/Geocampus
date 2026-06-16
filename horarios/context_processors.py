from django.contrib.auth.forms import PasswordChangeForm

def config_modal_context(request):
    """
    Inject the password_form into every template context so the
    configuration modal (included in base_app.html) works sitewide.
    """
    password_form = None
    if request.user.is_authenticated:
        password_form = PasswordChangeForm(request.user)
    return {'password_form': password_form}
