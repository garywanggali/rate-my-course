#!/usr/bin/env bash
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate 2>/dev/null || true
pip3 install --upgrade pip
pip3 install -r requirements.txt 2>/dev/null || pip3 install "Django==4.2.27"
python3 manage.py makemigrations core 2>/dev/null || true
python3 manage.py migrate
python3 manage.py seed_demo_courses 2>/dev/null || true
python3 manage.py seed_more_demo 2>/dev/null || true
python3 manage.py shell -c "code = '''from django.contrib.auth import get_user_model\nUser=get_user_model()\nu=User.objects.filter(username=\'admin\').first()\nif not u:\n    User.objects.create_superuser(\'admin\', \'admin@example.com\', \'admin123\')\nprint('admin ready')\n'''; exec(code)"
python3 manage.py runserver
