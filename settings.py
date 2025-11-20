from os import environ
SESSION_CONFIG_DEFAULTS = dict(real_world_currency_per_point=1, participation_fee=0)
SESSION_CONFIGS = [dict(name='test_1', num_demo_participants=3, app_sequence=['Tragedie_des_communs_ecologie'])]
LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'UM '
USE_POINTS = False
DEMO_PAGE_INTRO_HTML = ''
PARTICIPANT_FIELDS = []
SESSION_FIELDS = []
ROOMS = []

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

SECRET_KEY = environ.get('OTREE_SECRET_KEY', 'default_secret_key')

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = ['otree']


