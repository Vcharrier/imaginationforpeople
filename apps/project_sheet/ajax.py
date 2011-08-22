"""
Ajax views for handling project sheet creation and edition.
"""
from django.forms.models import modelform_factory
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.template.defaultfilters import linebreaksbr
from django.utils import simplejson, translation
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from dajaxice.core import dajaxice_functions

from .models import I4pProjectTranslation
from .forms import I4pProjectObjectiveForm, I4pProjectThemesForm
from .utils import get_or_create_project_translation_by_slug, get_project_translation_by_slug

TEXTFIELD_MAPPINGS = {
    'about_section_txt': 'about_section',
    'project_uniqueness_txt': 'uniqueness_section',
    'project_value_txt': 'value_section',
    'project_scalability_txt': 'scalability_section',
    'project_translation_progress' : 'completion_progress',
    }

def project_textfield_load(request, project_slug=None):
    """
    Load the source of a text field (project description, ...),
    without the markup rendered (useful for JS editing, to prevent
    html tags from being edited without interpretation).
    """
    if not project_slug:
        return HttpResponse('')

    try:
        language_code = request.GET['language_code']
        section = request.GET['id']
    except KeyError:
        return HttpResponseBadRequest()

    # Check if we allow this field
    if not section in TEXTFIELD_MAPPINGS:
        return HttpResponseNotFound()

    # Activate requested language
    translation.activate(language_code)

    # get the project translation and its base
    project_translation = get_project_translation_by_slug(project_translation_slug=project_slug,
                                                          language_code=language_code)

    # Get the text
    choices = project_translation._meta.get_field(TEXTFIELD_MAPPINGS[section]).choices
    if choices : # it's possible because choices are Charfield
        choice_dict = {}
        for key, value in choices:
            choice_dict[key] = u"%s" % value
        resp = simplejson.dumps(choice_dict)
    else:
        resp = getattr(project_translation, TEXTFIELD_MAPPINGS[section]) or ''

    return HttpResponse(resp)

@require_POST
@csrf_exempt
def project_textfield_save(request, project_slug=None):
    """
    Edit a text field
    """
    language_code = request.POST['language_code']
    section = request.POST['id']
    value = request.POST['value']

    # Activate requested language
    translation.activate(language_code)

    project_translation = get_or_create_project_translation_by_slug(project_translation_slug=project_slug, 
                                                                    language_code=language_code)
    
    # Check if we allow this field
    if not section in TEXTFIELD_MAPPINGS:
        return HttpResponseNotFound()

    # Resolve the fieldname
    fieldname = TEXTFIELD_MAPPINGS[section]

    FieldForm = modelform_factory(I4pProjectTranslation, fields=(fieldname,))

    form = FieldForm({fieldname: value}, instance=project_translation)

    if form.is_valid():
        form.save()
        if project_translation._meta.get_field(fieldname).choices:
            text = getattr(project_translation, "get_%s_display" % fieldname)()
        else:
            text = linebreaksbr(value)
            
        return HttpResponse(simplejson.dumps({'text': text or '',
                                              'redirect': project_slug is None,
                                              'redirect_url': project_translation.get_absolute_url()}), 'application/json')
    else:
        return HttpResponseNotFound()


def project_update_related(request, language_code, related_form, project_slug):
    """
    Update themes and objective of a given project, in a given language
    """
    # Activate requested language
    translation.activate(language_code)

    # get the project translation and its base
    project_translation = get_project_translation_by_slug(project_translation_slug=project_slug,
                                                          language_code=language_code)

    parent_project = project_translation.project


    # Convert tags to string list, separated by comma
    if isinstance(related_form['themes'], list):
        related_form['themes'] = ", ".join(related_form['themes'])
    
    if not isinstance(related_form['objective-form-objective'], list):
        related_form['objective-form-objective'] = related_form['objective-form-objective'].split(',')

    project_themes_form = I4pProjectThemesForm(related_form,
                                               instance=project_translation)
    
    project_objective_form = I4pProjectObjectiveForm(related_form,
                                                     instance=parent_project,
                                                     prefix="objective-form")


    if project_themes_form.is_valid():
        project_themes_form.save()
        
    if  project_objective_form.is_valid():
        project_objective_form.save()
    else:
        print project_objective_form.errors

    return simplejson.dumps({})


# Dajax Registration
dajaxice_functions.register(project_update_related)





