from flask import Flask, render_template  # <--- IMPORT ADD!
from flask_login import LoginManager
from controllers.usuario_controller import UsuarioController
from models.usuario_model import db, Usuario

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')  # <-- CORRIGIDO! Tem que ter return.

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    return UsuarioController.registro()

@app.route('/login', methods=['GET', 'POST'])
def login():
    return UsuarioController.login()

@app.route('/dashboard')
def dashboard():
    return UsuarioController.dashboard()

@app.route('/logout')
def logout():
    return UsuarioController.logout()

@app.route('/usuarios')
def lista_usuarios():
    return UsuarioController.lista_usuarios()

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
