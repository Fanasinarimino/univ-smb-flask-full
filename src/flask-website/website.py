from flask import Flask, render_template, request, redirect, url_for, session, Response
import requests
import re

app = Flask(__name__)
app.secret_key = "supersecretkey"

API = "https://studious-space-fiesta-vpvvx76xgjj4hpw96-5001.app.github.dev"

# ============================================================
#           FONCTION POUR GÉNÉRER LA CONFIG NGINX
# ============================================================

def generate_nginx_config(kind, item):
    if kind == "ws":
        return f"""
server {{
    listen 80;
    server_name {item['name']};
    location / {{
        proxy_pass http://{item['ip_bind']};
    }}
}}
""".strip()

    if kind == "rp":
        return f"""
server {{
    listen 80;
    server_name {item['name']};
    location / {{
        proxy_pass {item['pass']};
        proxy_set_header Host $host;
    }}
}}
""".strip()

    if kind == "lb":
        return f"""
upstream backend {{
    server {item['ip_bind']};
}}

server {{
    listen 80;
    server_name {item['name']};
    location / {{
        proxy_pass http://backend;
    }}
}}
""".strip()

    return "Configuration non disponible."


# ============================================================
#           COMMANDES DOCKER / INSTALLATION
# ============================================================

def generate_setup_commands(item):
    return f"""
# Installation Docker
sudo apt update
sudo apt install docker.io -y

# Lancer un conteneur Nginx
docker run -d --name {item['name']} -p 80:80 nginx

# Copier la configuration
docker cp {item['name']}.conf {item['name']}:/etc/nginx/conf.d/default.conf

# Redémarrer Nginx
docker exec {item['name']} nginx -s reload
""".strip()


# ============================================================
#           AUTHENTIFICATION
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin":
            session["logged"] = True
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Identifiants incorrects", session=session)

    return render_template("login.html", session=session)


@app.before_request
def require_login():
    allowed = ("login", "static", "logout", "home")
    if request.endpoint not in allowed and "logged" not in session:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- ACCUEIL ----------------
@app.route("/")
def home():
    return render_template("home.html", session=session)


# ============================================================
#                     VALIDATION FORMULAIRE
# ============================================================

def validate_form(name, ip, password):
    errors = []

    if not name.strip():
        errors.append("Le nom est obligatoire.")
    if not ip.strip():
        errors.append("L'adresse IP est obligatoire.")
    if not password.strip():
        errors.append("Le mot de passe est obligatoire.")

    if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
        errors.append("Adresse IP invalide.")

    return errors


# ============================================================
#                     WEB SERVERS
# ============================================================

@app.route("/ws/list")
def ws_list():
    items = requests.get(f"{API}/config/ws").json()
    return render_template(
        "list.html",
        type="ws",
        title="Web Servers",
        items=items,
        create_url=url_for("ws_create"),
        detail_route="ws_detail",
        delete_route="ws_delete",
        session=session
    )

@app.route("/ws/<int:id>")
def ws_detail(id):
    item = requests.get(f"{API}/config/ws/{id}").json()
    config = generate_nginx_config("ws", item)
    commands = generate_setup_commands(item)

    return render_template(
        "detail.html",
        type="ws",
        title=f"Web Server #{id}",
        item=item,
        config=config,
        commands=commands,
        back_url=url_for("ws_list"),
        session=session
    )

@app.route("/ws/create", methods=["GET", "POST"])
def ws_create():
    if request.method == "POST":
        name = request.form["name"]
        ip = request.form["ip_bind"]
        password = request.form["pass"]

        errors = validate_form(name, ip, password)
        if errors:
            return render_template(
                "create.html",
                type="Web Server",
                title="Créer un Web Server",
                errors=errors,
                back_url=url_for("ws_list"),
                session=session
            )

        data = {"name": name, "ip_bind": ip, "pass": password}
        requests.post(f"{API}/config/ws", json=data)
        return redirect(url_for("ws_list"))

    return render_template(
        "create.html",
        type="Web Server",
        title="Créer un Web Server",
        back_url=url_for("ws_list"),
        session=session
    )

@app.route("/ws/delete/<int:id>", methods=["GET", "POST"])
def ws_delete(id):
    if request.method == "POST":
        requests.delete(f"{API}/config/ws/{id}")
        return redirect(url_for("ws_list"))

    return render_template(
        "delete.html",
        type="Web Server",
        id=id,
        back_url=url_for("ws_list"),
        session=session
    )


# ============================================================
#                     REVERSE PROXY
# ============================================================

@app.route("/rp/list")
def rp_list():
    items = requests.get(f"{API}/config/rp").json()
    return render_template(
        "list.html",
        type="rp",
        title="Reverse Proxies",
        items=items,
        create_url=url_for("rp_create"),
        detail_route="rp_detail",
        delete_route="rp_delete",
        session=session
    )

@app.route("/rp/<int:id>")
def rp_detail(id):
    item = requests.get(f"{API}/config/rp/{id}").json()
    config = generate_nginx_config("rp", item)
    commands = generate_setup_commands(item)

    return render_template(
        "detail.html",
        type="rp",
        title=f"Reverse Proxy #{id}",
        item=item,
        config=config,
        commands=commands,
        back_url=url_for("rp_list"),
        session=session
    )

@app.route("/rp/create", methods=["GET", "POST"])
def rp_create():
    if request.method == "POST":
        name = request.form["name"]
        ip = request.form["ip_bind"]
        password = request.form["pass"]

        errors = validate_form(name, ip, password)
        if errors:
            return render_template(
                "create.html",
                type="Reverse Proxy",
                title="Créer un Reverse Proxy",
                errors=errors,
                back_url=url_for("rp_list"),
                session=session
            )

        data = {"name": name, "ip_bind": ip, "pass": password}
        requests.post(f"{API}/config/rp", json=data)
        return redirect(url_for("rp_list"))

    return render_template(
        "create.html",
        type="Reverse Proxy",
        title="Créer un Reverse Proxy",
        back_url=url_for("rp_list"),
        session=session
    )

@app.route("/rp/delete/<int:id>", methods=["GET", "POST"])
def rp_delete(id):
    if request.method == "POST":
        requests.delete(f"{API}/config/rp/{id}")
        return redirect(url_for("rp_list"))

    return render_template(
        "delete.html",
        type="Reverse Proxy",
        id=id,
        back_url=url_for("rp_list"),
        session=session
    )


# ============================================================
#                     LOAD BALANCER
# ============================================================

@app.route("/lb/list")
def lb_list():
    items = requests.get(f"{API}/config/lb").json()
    return render_template(
        "list.html",
        type="lb",
        title="Load Balancers",
        items=items,
        create_url=url_for("lb_create"),
        detail_route="lb_detail",
        delete_route="lb_delete",
        session=session
    )

@app.route("/lb/<int:id>")
def lb_detail(id):
    item = requests.get(f"{API}/config/lb/{id}").json()
    config = generate_nginx_config("lb", item)
    commands = generate_setup_commands(item)

    return render_template(
        "detail.html",
        type="lb",
        title=f"Load Balancer #{id}",
        item=item,
        config=config,
        commands=commands,
        back_url=url_for("lb_list"),
        session=session
    )

@app.route("/lb/create", methods=["GET", "POST"])
def lb_create():
    if request.method == "POST":
        name = request.form["name"]
        ip = request.form["ip_bind"]
        password = request.form["pass"]

        errors = validate_form(name, ip, password)
        if errors:
            return render_template(
                "create.html",
                type="Load Balancer",
                title="Créer un Load Balancer",
                errors=errors,
                back_url=url_for("lb_list"),
                session=session
            )

        data = {"name": name, "ip_bind": ip, "pass": password}
        requests.post(f"{API}/config/lb", json=data)
        return redirect(url_for("lb_list"))

    return render_template(
        "create.html",
        type="Load Balancer",
        title="Créer un Load Balancer",
        back_url=url_for("lb_list"),
        session=session
    )

@app.route("/lb/delete/<int:id>", methods=["GET", "POST"])
def lb_delete(id):
    if request.method == "POST":
        requests.delete(f"{API}/config/lb/{id}")
        return redirect(url_for("lb_list"))

    return render_template(
        "delete.html",
        type="Load Balancer",
        id=id,
        back_url=url_for("lb_list"),
        session=session
    )


# ============================================================
#                     IDENTITÉ
# ============================================================

@app.route("/identity")
def identity_page():
    users = requests.get(f"{API}/identity").json()
    return render_template("identity.html", users=users, session=session)


# ============================================================
#                     TÉLÉCHARGEMENT CONFIG
# ============================================================

@app.route("/download/<type>/<int:id>")
def download_config(type, id):
    item = requests.get(f"{API}/config/{type}/{id}").json()
    config = generate_nginx_config(type, item)

    return Response(
        config,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={type}_{id}.conf"}
    )


# ============================================================
#                     LANCEMENT
# ============================================================

if __name__ == "__main__":
    app.run(port=5000, debug=True)
