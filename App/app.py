from flask import Flask, render_template  
from flask_login import LoginManager
from controllers.usuario_controller import UsuarioController
from models.usuario_model import db, Usuario
from flask_mail import Mail, Message


app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'        
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'leonardo.fernandesc23@gmail.com'
app.config['MAIL_PASSWORD'] = 'wwxuzuzfiweapxlr'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

mail = Mail(app)


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')  

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

@app.route('/perfil')
def perfil():
    return UsuarioController.perfil()

@app.route('/editar-perfil', methods=['GET', 'POST'])
def editar_perfil():
    return UsuarioController.editar_perfil()

@app.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    return UsuarioController.esqueci_senha()

@app.route('/resetar-senha/<token>', methods=['GET', 'POST'])
def resetar_senha(token):
    return UsuarioController.resetar_senha(token)




with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
