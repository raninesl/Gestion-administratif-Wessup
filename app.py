from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import os
import json

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Charger les utilisateurs depuis un fichier JSON (admin uniquement ici)
with open('users.json') as f:
    users = json.load(f)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with open('users.json') as f:
            users = json.load(f)

        if username in users and users[username]['password'] == password:
            session['user'] = username
            session['role'] = users[username]['role']
            return redirect(url_for('dashboard'))

        flash('Identifiants incorrects.')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    categories = {}
    base_path = app.config['UPLOAD_FOLDER']

    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)
        if os.path.isdir(folder_path):
            categories[folder] = os.listdir(folder_path)

    return render_template('dashboard.html', categories=categories)


@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))

    file = request.files.get('file')
    category = request.form.get('category')

    if file and category:
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], category)
        os.makedirs(save_path, exist_ok=True)  # Crée le dossier si nécessaire
        file.save(os.path.join(save_path, file.filename))
        print("✅ Fichier ajouté :", file.filename, "dans", category)
    else:
        print("❌ Fichier ou catégorie manquant.")

    return redirect(url_for('dashboard'))

@app.route('/delete/<path:filename>', methods=['POST'])
def delete(filename):
    if 'user' not in session:
        return redirect(url_for('login'))
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return redirect(url_for('dashboard'))

@app.route('/add-category', methods=['POST'])
def add_category():
    if 'user' not in session:
        return redirect(url_for('login'))

    category_name = request.form.get('new_category')
    if category_name:
        folder_name = category_name.strip().lower().replace(' ', '_')
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(folder_path, exist_ok=True)
        print(f"✅ Nouvelle section créée : {folder_name}")
    return redirect(url_for('dashboard'))

import shutil  # pour supprimer tout un dossier

@app.route('/delete-category/<category>', methods=['POST'])
def delete_category(category):
    if 'user' not in session:
        return redirect(url_for('login'))

    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], category)

    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)  # supprime le dossier et tout son contenu
        print(f"🗑 Section supprimée : {category}")
    return redirect(url_for('dashboard'))

@app.route('/add-user', methods=['GET', 'POST'])
def add_user():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        with open('users.json', 'r+') as f:
            users = json.load(f)
            if username in users:
                flash('❌ Utilisateur déjà existant.', 'danger')
            else:
                users[username] = {
                    "password": password,
                    "role": "user"
                }
                f.seek(0)
                json.dump(users, f, indent=4)
                f.truncate()
                flash(f'✅ Utilisateur "{username}" ajouté avec succès.', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_user.html')


@app.route('/users')
def manage_users():
    if 'user' not in session:
        return redirect(url_for('login'))

    with open('users.json') as f:
        users = json.load(f)
    
    return render_template('users.html', users=users)

@app.route('/delete-user', methods=['POST'])
def delete_user():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = request.form.get('username')
    if username != 'admin':  # sécurité : on ne supprime pas l’admin principal
        with open('users.json', 'r+') as f:
            users = json.load(f)
            if username in users:
                users.pop(username)
                f.seek(0)
                json.dump(users, f, indent=4)
                f.truncate()
    return redirect(url_for('manage_users'))

@app.route('/users')
def manage_documents():
    if 'user' not in session:
        return redirect(url_for('login'))

    with open('users.json') as f:
        users = json.load(f)

    return render_template('users.html', users=users)

@app.route('/change-password/<username>', methods=['GET', 'POST'])
def change_user_password(username):
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        with open('users.json', 'r+') as f:
            users = json.load(f)
            users[username] = new_password
            f.seek(0)
            json.dump(users, f, indent=4)
            f.truncate()
        return redirect(url_for('manage_users'))

    return render_template('change_user_password.html', username=username)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
