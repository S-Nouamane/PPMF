from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
import os 

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alumni.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/'  # Dossier pour stocker les images

db = SQLAlchemy(app)

# Modèle de l'utilisateur
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    linkedin = db.Column(db.String(200), nullable=True)
    social_media = db.Column(db.String(200), nullable=True)
    current_position = db.Column(db.String(200), nullable=True)
    prep_course = db.Column(db.Text, nullable=True)
    user_type = db.Column(db.String(10), nullable=False)
    share_data = db.Column(db.Boolean, default=False)  # Champ pour le partage des données
    school = db.Column(db.String(100), nullable=True)  # Nouveau champ pour l'école
    field_of_study = db.Column(db.String(100), nullable=True)  # Nouveau champ pour le domaine d'études
    profile_picture = db.Column(db.String(200), nullable=True)  # Champ pour la photo de profil
# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        password = generate_password_hash(request.form['password'])
        linkedin = request.form.get('linkedin')
        social_media = request.form.get('social_media')
        current_position = request.form.get('current_position')
        prep_course = request.form.get('prep_course')
        user_type = request.form['user_type']
        school = request.form.get('school') if user_type == 'alumni' else None
        field_of_study = request.form.get('field_of_study') if user_type == 'alumni' else None
        
        # Vérifier si l'utilisateur est un alumni et s'il a choisi de partager ses données
        if user_type == 'alumni':
            share_data = 'share_data' in request.form  # Vérifier si la case est cochée
        else:
            share_data = False  # Les étudiants ne partagent pas de données
        
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            password=password,
            linkedin=linkedin,
            social_media=social_media,
            current_position=current_position,
            prep_course=prep_course,
            user_type=user_type,
            share_data=share_data,  # Enregistrer le choix de partage des données
            school=school,  # Enregistrer le nom de l'école
            field_of_study=field_of_study  # Enregistrer le domaine d'études
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return f"An error occurred: {e}"

    return render_template('register.html')

@app.route('/delete_account/<int:user_id>', methods=['POST'])
def delete_account(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        session.clear()  # Déconnexion de l'utilisateur après la suppression
        return redirect(url_for('home'))
    return "Utilisateur non trouvé.", 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('profile', user_id=user.id))
        return "Invalid credentials."
    return render_template('login.html')

@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    user = User.query.get(user_id)
    if request.method == 'POST':
        user.phone = request.form['phone']
        user.linkedin = request.form['linkedin']
        user.social_media = request.form['social_media']
        user.current_position = request.form['current_position']
        user.prep_course = request.form['prep_course']
        user.school = request.form.get('school')
        user.field_of_study = request.form.get('field_of_study')

        # Gestion du téléchargement de la photo de profil
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):  # Vérifiez si le fichier est autorisé
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                user.profile_picture = url_for('static', filename='uploads/' + filename)
            else:
                raise BadRequest("Invalid file type. Only images are allowed.")

        db.session.commit()
        return redirect(url_for('profile', user_id=user.id))

    return render_template('profile.html', user=user)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    alumni_list = User.query.filter_by(share_data=True).all()  # Récupérer les alumni qui partagent leurs données
    return render_template('dashboard.html', user=user, alumni=alumni_list)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Initialiser la base de données
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)