# Flask App mit Login, ToDo-Ansicht, stylisch + mobile-freundlich
from flask import Flask, render_template_string, request, redirect, session, url_for
import pandas as pd
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
import os

app = Flask(__name__)
app.secret_key = 'supersecurekey'  # Sollte in echter App geheim bleiben

# Benutzer-Daten
USERNAME = "max"
PASSWORD_HASH = generate_password_hash("max")

# Pfad zur Excel-Datei
FILE_PATH = "MedAT_Lernplan_mit_Abhaken.xlsx"

# HTML-Template mit Bootstrap-Styling
TEMPLATE = """
<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>MedAT Lernplan</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body class="bg-light">
    <div class="container py-4">
      {% if session.logged_in %}
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2>📅 Nächster Lerntag: {{ next_date }}</h2>
          <a href="{{ url_for('logout') }}" class="btn btn-outline-danger">Logout</a>
        </div>
        {% if not tasks.empty %}
        <form method="post">
          <ul class="list-group">
            {% for idx, row in tasks.iterrows() %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <div>
                <input class="form-check-input me-2" type="checkbox" name="done" value="{{ idx }}" {% if row['Abgehakt'] %}checked{% endif %}>
                <strong>{{ row['Zeit von'] }}–{{ row['Zeit bis'] }}</strong>: {{ row['Fach/Inhalt'] }}
              </div>
            </li>
            {% endfor %}
          </ul>
          <button type="submit" class="btn btn-success mt-3">✅ Speichern</button>
        </form>
        {% else %}
        <p class="alert alert-info">🎉 Keine anstehenden Aufgaben mehr!</p>
        {% endif %}
      {% else %}
        <h2 class="mb-4">🔐 Login</h2>
        {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
        <form method="post">
          <div class="mb-3">
            <label class="form-label">Benutzername</label>
            <input type="text" name="username" class="form-control">
          </div>
          <div class="mb-3">
            <label class="form-label">Passwort</label>
            <input type="password" name="password" class="form-control">
          </div>
          <button type="submit" class="btn btn-primary">Einloggen</button>
        </form>
      {% endif %}
    </div>
  </body>
</html>
"""

def load_calendar():
    return pd.read_excel(FILE_PATH)

def save_calendar(df):
    df.to_excel(FILE_PATH, index=False)

def get_next_learning_day(df):
    df_future = df[(df['Aktivität'] == 'Lernen') & (~df['Abgehakt'])].copy()
    if df_future.empty:
        return None, pd.DataFrame()
    df_future['Datum_dt'] = pd.to_datetime(df_future['Datum'], dayfirst=True)
    next_day = df_future.sort_values('Datum_dt').iloc[0]['Datum']
    tasks = df[(df['Datum'] == next_day) & (df['Aktivität'] == 'Lernen')]
    return next_day, tasks

@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("logged_in"):
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            if username == USERNAME and check_password_hash(PASSWORD_HASH, password):
                session["logged_in"] = True
                return redirect(url_for("index"))
            else:
                return render_template_string(TEMPLATE, error="Falsche Zugangsdaten.", session=session)
        return render_template_string(TEMPLATE, error=None, session=session)

    df = load_calendar()
    next_date, next_tasks = get_next_learning_day(df)

    if request.method == "POST":
        selected = request.form.getlist("done")
        selected = list(map(int, selected))
        for idx in next_tasks.index:
            df.at[idx, 'Abgehakt'] = idx in selected
        save_calendar(df)
        return redirect(url_for("index"))

    return render_template_string(TEMPLATE, next_date=next_date, tasks=next_tasks, session=session)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
