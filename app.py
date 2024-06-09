from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import json
import os
import folium
import branca

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management and flash messages

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Create the database
with app.app_context():
    db.create_all()

# Load site data with correct encoding
with open('data/sites.json', encoding='utf-8') as f:
    sites = json.load(f)

# Ensure the upload folder exists
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def index():
    # Create a Folium map
    m = folium.Map(location=[41.3275, 19.8189], zoom_start=7)
    
    # Add markers to the map
    for site in sites:
        html = f"""
            <h1>{site['name']}</h1><br>
            <p><b>Category:</b> {site['category']}</p>
            <p><b>Typology:</b> {site['typology']}</p>
            <p><b>Field:</b> {site['field']}</p>
            <p><b>Place:</b> {site['place']}</p>
            <p><b>Municipality:</b> {site['municipality']}</p>
            <p><b>County:</b> {site['county']}</p>
            <p><b>Info:</b> {site.get('info', 'No additional information available')}</p>
            <p><b>Opening Hours:</b> {site.get('opening_hours', 'N/A')}</p>
            <p><b>Admission Fee:</b> {site.get('admission_fee', 'N/A')}</p>
            <p><b>Contact Info:</b> {site.get('contact_info', 'N/A')}</p>
            <p><b>Tags:</b> {site.get('tags', 'N/A')}</p>
        """
        if site.get('image'):
            html += f'<img src="/{site["image"]}" width="200"><br>'

        html += "</p>"

        iframe = branca.element.IFrame(html=html, width=300, height=400)
        popup = folium.Popup(iframe, max_width=300)
        folium.Marker([site['latitude'], site['longitude']], popup=popup).add_to(m)
    
    # Save the map to an HTML file in the static directory
    map_path = 'static/map.html'
    m.save(map_path)
    
    return render_template("index.html")

@app.route("/sites/<site_type>")
def get_sites(site_type):
    filtered_sites = [site for site in sites if site['category'] == site_type]
    return jsonify(filtered_sites)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
    return render_template("login.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match, please try again.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists, please choose another.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered, please use another.', 'danger')
        else:
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route("/add_site", methods=['GET', 'POST'])
def add_site():
    if 'username' not in session:
        flash('You need to be logged in to add a site.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Generate the next ID
        if sites:
            last_id = sites[-1]['id']
            new_id_num = int(last_id[2:]) + 1
            new_id = f"HS{new_id_num:03d}"
        else:
            new_id = "HS001"

        # Handle file upload
        image_file = request.files['image']
        if image_file:
            image_filename = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
            image_file.save(image_filename)
            image_filename = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        else:
            image_filename = None

        new_site = {
            "id": new_id,
            "name": request.form['name'],
            "category": request.form['category'],
            "typology": request.form['typology'],
            "field": request.form['field'],
            "place": request.form['place'],
            "municipality": request.form['municipality'],
            "county": request.form['county'],
            "latitude": request.form['latitude'],
            "longitude": request.form['longitude'],
            "info": request.form['info'],
            "opening_hours": request.form.get('opening_hours', ''),
            "admission_fee": request.form.get('admission_fee', ''),
            "contact_info": request.form.get('contact_info', ''),
            "tags": request.form.get('tags', ''),
            "image": image_filename.replace('\\', '/')
        }
        sites.append(new_site)
        with open('data/sites.json', 'w', encoding='utf-8') as f:
            json.dump(sites, f, ensure_ascii=False, indent=4)
        flash('Site added successfully!', 'success')
        return redirect(url_for('index'))
    
    # Generate the next ID for GET request
    if sites:
        last_id = sites[-1]['id']
        new_id_num = int(last_id[2:]) + 1
        new_id = f"HS{new_id_num:03d}"
    else:
        new_id = "HS001"
    
    return render_template("add_site.html", new_id=new_id)

if __name__ == "__main__":
    app.run(debug=True)
