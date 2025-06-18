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
        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
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



@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
