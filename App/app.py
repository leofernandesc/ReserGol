from flask import Flask, render_template  
from flask_login import LoginManager
from controllers.usuario_controller import UsuarioController
from models.usuario_model import db, Usuario
from models.quadra_model import Quadra  # ADICIONE ESTA LINHA
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'        
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seuemail@gmail.com'
app.config['MAIL_PASSWORD'] = 'suasenhaaplicativo'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Rotas existentes...
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

# ROTAS - Gerenciamento de Usuários (Admin)
@app.route('/admin/usuarios')
def admin_usuarios():
    return UsuarioController.admin_listar_usuarios()

@app.route('/admin/promover-usuario/<int:usuario_id>')
def promover_usuario(usuario_id):
    return UsuarioController.promover_para_dono(usuario_id)

@app.route('/admin/rebaixar-usuario/<int:usuario_id>')
def rebaixar_usuario(usuario_id):
    return UsuarioController.rebaixar_para_usuario(usuario_id)

@app.route('/admin/editar-usuario/<int:usuario_id>', methods=['GET', 'POST'])
def admin_editar_usuario(usuario_id):
    return UsuarioController.admin_editar_usuario(usuario_id)

@app.route('/admin/remover-usuario/<int:usuario_id>')
def admin_remover_usuario(usuario_id):
    return UsuarioController.admin_remover_usuario(usuario_id)

@app.route('/admin/desbloquear-usuario/<int:usuario_id>')
def admin_desbloquear_usuario(usuario_id):
    return UsuarioController.admin_desbloquear_usuario(usuario_id)


# NOVAS ROTAS - Quadras
@app.route('/quadras')
def listar_quadras():
    from controllers.quadra_controller import QuadraController
    return QuadraController.listar_quadras()

@app.route('/minhas-quadras')
def minhas_quadras():
    from controllers.quadra_controller import QuadraController
    return QuadraController.minhas_quadras()

@app.route('/cadastrar-quadra', methods=['GET', 'POST'])
def cadastrar_quadra():
    from controllers.quadra_controller import QuadraController
    return QuadraController.cadastrar_quadra()

@app.route('/editar-quadra/<int:quadra_id>', methods=['GET', 'POST'])
def editar_quadra(quadra_id):
    from controllers.quadra_controller import QuadraController
    return QuadraController.editar_quadra(quadra_id)

@app.route('/deletar-quadra/<int:quadra_id>')
def deletar_quadra(quadra_id):
    from controllers.quadra_controller import QuadraController
    return QuadraController.deletar_quadra(quadra_id)

@app.route('/admin/bloquear-usuario/<int:usuario_id>')
def admin_bloquear_usuario(usuario_id):
    return UsuarioController.admin_bloquear_usuario(usuario_id)


with app.app_context():
    db.create_all()
    
    # Cria admin padrão se não existir
    admin = Usuario.query.filter_by(email='admin@resergol.com').first()
    if not admin:
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        senha_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = Usuario(
            nome='Administrador',
            email='admin@resergol.com',
            senha_hash=senha_hash,
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin criado: admin@resergol.com / admin123")

if __name__ == '__main__':
    app.run(debug=True)
