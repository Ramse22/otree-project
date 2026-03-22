from os import environ

# Configuration settings on server side
SESSION_CONFIGS = [
    dict(
        name="test_1",
        num_demo_participants=3,
        app_sequence=["Tragedie_des_communs_ecologie"],
    )
]

# settings for html pages
LANGUAGE_CODE = "en"
REAL_WORLD_CURRENCY_CODE = "UM "  # "Unités Monétaires"
USE_POINTS = False
DEMO_PAGE_INTRO_HTML = ""
PARTICIPANT_FIELDS = []
SESSION_FIELDS = []
ROOMS = [
    dict(
        name="default_room",
        display_name="Salle - Tragédie des communs (jeu écologique)",
    )
]

ADMIN_USERNAME = "admin"
# for security, admin password is set in an environment variable
ADMIN_PASSWORD = environ.get("OTREE_ADMIN_PASSWORD")
# same for secret key
SECRET_KEY = environ.get("OTREE_SECRET_KEY", "default_secret_key")

INSTALLED_APPS = ["otree"]
