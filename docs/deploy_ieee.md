# Deploying a Django-Based Course Rating Platform (IEEE-Style Essay)

## Abstract
This paper describes the end-to-end deployment of a Django-based course rating platform. It details server access, code retrieval from GitHub, environment preparation, application bootstrapping, and production hardening with Nginx and HTTPS. Verification includes access via IP:PORT and the assigned subdomain with TLS.

## Index Terms
Django, Nginx, Gunicorn, HTTPS, Certbot, Systemd, Reverse Proxy, SQLite

## I. Introduction
The platform supports user authentication, multi-dimensional ratings, nested comments, reactions, tags, rankings, and an admin backend. Deployment targets a Linux server with public IPv4 as documented in the school’s deployment guidance, and provides both direct HTTP and domain-based HTTPS access.

## II. System Overview
- Backend: Django 4.2, SQLite, Django Admin
- Frontend: HTML/CSS/JS templates served by Django
- Services: App server (Gunicorn or Django dev server), Nginx reverse proxy, optional TLS via Certbot

## III. Environment and Assumptions
- Server: Linux (OpenCloudOS/CentOS-like or Ubuntu)
- Python: 3.9+ available
- Ports: Open inbound `:8802` or preferred port (‘5007’) for IP access; `:80` and `:443` for domain
- DNS: `gary.yunguhs.com` A-record points to server IP (e.g., `110.40.153.38`)

## IV. Step-by-Step Deployment
1) SSH Login
```
ssh gary@110.40.153.38
```
Password : `Gary@210108024` .

2) Install prerequisites (choose one family)
- OpenCloudOS/CentOS:
```
sudo dnf install -y python3 python3-venv git nginx
sudo dnf install -y certbot python3-certbot-nginx
```
- Ubuntu/Debian:
```
sudo apt update && sudo apt install -y python3 python3-venv git nginx
sudo apt install -y certbot python3-certbot-nginx
```

3) Clone code from GitHub (HTTPS)
```
git clone https://github.com/garywanggali/rate-my-course.git
cd rate-my-course
git checkout django-port
git pull
```

4) Create Python virtual environment and install dependencies
```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || pip install "Django==4.2.27"
```

5) Initialize database and seed demo data
```
python3 manage.py migrate
python3 manage.py shell -c "from django.contrib.auth import get_user_model;U=get_user_model();U.objects.filter(username='admin').exists() or U.objects.create_superuser('admin','admin@example.com','admin123')"
python3 manage.py seed_demo_courses
python3 manage.py seed_more_demo
```

6) Quick verification (development server)
```
python3 manage.py runserver 0.0.0.0:8000
```
Visit `http://<server_ip>:8000/` and verify pages (login `admin/admin123`). Stop with `Ctrl + C`.

## V. Production Reverse Proxy and HTTPS
Use Gunicorn to serve Django and Nginx to reverse proxy (domain and TLS).

1) Start Gunicorn (socket on localhost)
```
pip install gunicorn
gunicorn rate_my_course.wsgi:application --bind 127.0.0.1:8000 --workers 3
```

2) Systemd service (auto start)
Create `/etc/systemd/system/rmc.service`:
```
[Unit]
Description=Rate My Course Django (Gunicorn)
After=network.target

[Service]
User=<your_english_name>
WorkingDirectory=/home/<your_english_name>/rate-my-course
Environment="PATH=/home/<your_english_name>/rate-my-course/.venv/bin"
ExecStart=/home/<your_english_name>/rate-my-course/.venv/bin/gunicorn rate_my_course.wsgi:application --bind 127.0.0.1:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```
Enable:
```
sudo systemctl daemon-reload && sudo systemctl enable --now rmc
sudo systemctl status rmc
```

3) Nginx site for IP and domain
Create `/etc/nginx/conf.d/rmc.conf`:
```
server {
  listen 80;
  server_name yourname.yunguhs.com;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location /static/ {
    alias /home/<your_english_name>/rate-my-course/static/;
  }
}
```
Reload:
```
sudo nginx -t && sudo systemctl reload nginx
```

4) HTTPS with Certbot (automated)
Ensure DNS A-record: `yourname.yunguhs.com -> 110.40.153.38`.
```
sudo certbot --nginx -d yourname.yunguhs.com
```
Auto-renewal: `systemctl status certbot.timer`.

## VI. Access Verification
1) Access via IP:PORT (direct HTTP)
```
python3 manage.py runserver 0.0.0.0:9527
```
Verify: `http://<server_ip>:9527/`.

2) Access via domain (HTTPS)
Verify: `https://yourname.yunguhs.com/`.
Admin: `https://yourname.yunguhs.com/admin/` (login `admin/admin123`).

## VII. Operations
- Logs:
  - Gunicorn: `journalctl -u rmc -f`
  - Nginx: `/var/log/nginx/access.log` and `error.log`
- Service management:
  - Restart app: `sudo systemctl restart rmc`
  - Reload Nginx: `sudo systemctl reload nginx`
- Security:
  - Keep `SECRET_KEY` in environment, not in code (set in systemd with `Environment=`)
  - Use HTTPS, restrict admin access if needed

## VIII. Notes on Localhost vs 127.0.0.1
Browsers treat `localhost` and `127.0.0.1` as different origins; caches, cookies, and template versions can diverge. If behavior differs, hard refresh (`Ctrl+Shift+R`) or clear site data; ensure only one server process is running.

## IX. Conclusion
The platform is deployable with minimal steps and can be hardened behind Nginx with HTTPS. Both direct IP:PORT and custom domain are supported. The approach balances fast verification with production readiness.

## References
- Django Deployment: https://docs.djangoproject.com/en/4.2/howto/deployment/
- Certbot Nginx: https://certbot.eff.org/
- Deployment tutorial: https://static.yunguhs.com/tutorials/deploy/

## Deployment Checklist (Commands)
```
# SSH
ssh <your_english_name>@110.40.153.38

# Clone
git clone https://github.com/garywanggali/rate-my-course.git
cd rate-my-course && git checkout django-port && git pull

# Python env and install
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || pip install "Django==4.2.27"

# DB init and seed
python3 manage.py migrate
python3 manage.py shell -c "from django.contrib.auth import get_user_model;U=get_user_model();U.objects.filter(username='admin').exists() or U.objects.create_superuser('admin','admin@example.com','admin123')"
python3 manage.py seed_demo_courses && python3 manage.py seed_more_demo

# Quick run (IP:PORT)
python3 manage.py runserver 0.0.0.0:9527

# Production (Gunicorn + Nginx + HTTPS)
pip install gunicorn
# create systemd unit rmc.service (as above)
sudo systemctl enable --now rmc
# create nginx conf rmc.conf (as above)
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d yourname.yunguhs.com
```

