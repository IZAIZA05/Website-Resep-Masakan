from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
import os
from os.path import join, dirname
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Memuat variabel lingkungan dari file .env
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Deklarasi variabel untuk menghubungkan ke MongoDB
MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

# Menghubungkan ke MongoDB
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

# Pengaturan aplikasi Flask
app = Flask(__name__)

# Konfigurasi folder upload dan ekstensi file yang diizinkan
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Fungsi untuk memeriksa apakah ekstensi file yang diunggah diperbolehkan
def allowed_file(filename):
    # Mengecek apakah file memiliki ekstensi yang valid
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    # Mengambil semua resep dari MongoDB
    recipes = list(db.recipes.find({}, {'_id': False}))
    return render_template('index.html', recipes=recipes)

@app.route("/add", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        # Mengambil data dari form
        name = request.form['name']
        description = request.form['description']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        category = request.form['category']
        image = request.files.get('image')  # Menangani file gambar

        image_url = None  # Defaultkan ke None jika tidak ada gambar yang diunggah

        # Menangani file yang diunggah
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename='uploads/' + filename)

        # Menyiapkan dokumen untuk dimasukkan ke MongoDB
        recipe_doc = {
            "name": name,
            "description": description,  # Menambahkan field deskripsi
            "ingredients": ingredients,
            "instructions": instructions,
            "category": category,
            "image": image_url  # Menyimpan URL gambar
        }

        # Memasukkan resep ke MongoDB
        db.recipes.insert_one(recipe_doc)

        return redirect(url_for('home'))

    return render_template('add_recipe.html')

@app.route("/recipe/<string:name>")
def recipe_detail(name):
    # Mengambil detail resep dari MongoDB berdasarkan nama
    recipe = db.recipes.find_one({"name": name}, {'_id': False})
    return render_template('recipe_detail.html', recipe=recipe)

@app.route("/recipe/edit/<string:name>", methods=["GET", "POST"])
def edit_recipe(name):
    recipe = db.recipes.find_one({"name": name}, {'_id': False})

    if request.method == "POST":
        # Mengambil data dari form
        name = request.form['name']
        description = request.form['description']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        category = request.form['category']
        image = request.files.get('image')

        image_url = recipe['image']  # Menjaga gambar yang ada jika tidak diganti

        # Menangani file gambar jika ada
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename='uploads/' + filename)

        # Menyiapkan dokumen untuk update data resep
        updated_recipe = {
            "name": name,
            "description": description,
            "ingredients": ingredients,
            "instructions": instructions,
            "category": category,
            "image": image_url
        }

        # Mengupdate resep di MongoDB
        db.recipes.update_one({"name": name}, {"$set": updated_recipe})

        return redirect(url_for('recipe_detail', name=name))

    return render_template('edit_recipe.html', recipe=recipe)

@app.route("/recipes", methods=["GET"])
def get_recipes():
    # Mengambil semua resep dari MongoDB dan mengembalikan dalam format JSON
    recipes = list(db.recipes.find({}, {'_id': False}))
    return jsonify({"recipes": recipes})

# Menambahkan conditional untuk menjalankan server hanya jika file ini yang dieksekusi
if __name__ == '__main__':
    # Menjalankan aplikasi Flask
    app.run('0.0.0.0', port=5000, debug=True)
