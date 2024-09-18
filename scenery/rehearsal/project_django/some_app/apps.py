from django.apps import AppConfig


class SomeAppConfig(AppConfig):
    """
    Dynamically configured based on called by
    python -m scenery.rehearsal 
    OR
    python scenery/rehearsal/project_django/manage.py
    """

    default_auto_field = "django.db.models.BigAutoField"
    
    if __name__ == "scenery.rehearsal.project_django.some_app.apps":
        name = "scenery.rehearsal.project_django.some_app"
    elif __name__ == "some_app.apps":
        name = 'some_app'
    else:
        raise Exception("Unexpected call.")