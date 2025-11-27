import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, current_user, login_required
from flask_mail import Mail
from datetime import datetime, date, timedelta
from models import db, bcrypt

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
bcrypt.init_app(app)

# Importar models APÓS inicializar db
from models.usuario_model import Usuario
from models.quadra_model import Quadra
from models.reserva_model import Reserva
from controllers.usuario_controller import UsuarioController
from controllers.quadra_controller import QuadraController
from controllers.reserva_controller import ReservaController

mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ===== ROTAS PÚBLICAS =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    return UsuarioController.registro()

@app.route('/login', methods=['GET', 'POST'])
def login():
    return UsuarioController.login()

# ===== ROTAS AUTENTICADAS - USUÁRIO =====
@app.route('/logout')
def logout():
    return UsuarioController.logout()

@app.route('/perfil')
@login_required
def perfil():
    return UsuarioController.perfil()

@app.route('/editar-perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    return UsuarioController.editar_perfil()

@app.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    return UsuarioController.esqueci_senha()

@app.route('/resetar-senha/<token>', methods=['GET', 'POST'])
def resetar_senha(token):
    return UsuarioController.resetar_senha(token)

# ===== ROTAS ADMIN - USUÁRIOS =====
@app.route('/admin/usuarios')
@login_required
def admin_usuarios():
    return UsuarioController.admin_listar_usuarios()

@app.route('/admin/usuario/<int:usuario_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_editar_usuario(usuario_id):
    return UsuarioController.admin_editar_usuario(usuario_id)

@app.route('/admin/usuario/<int:usuario_id>/promover')
@login_required
def promover_usuario(usuario_id):
    return UsuarioController.promover_para_dono(usuario_id)

@app.route('/admin/usuario/<int:usuario_id>/rebaixar')
@login_required
def rebaixar_usuario(usuario_id):
    return UsuarioController.rebaixar_para_usuario(usuario_id)

@app.route('/admin/usuario/<int:usuario_id>/remover')
@login_required
def admin_remover_usuario(usuario_id):
    return UsuarioController.admin_remover_usuario(usuario_id)

@app.route('/admin/usuario/<int:usuario_id>/desbloquear')
@login_required
def admin_desbloquear_usuario(usuario_id):
    return UsuarioController.admin_desbloquear_usuario(usuario_id)

@app.route('/admin/usuario/<int:usuario_id>/bloquear')
@login_required
def admin_bloquear_usuario(usuario_id):
    return UsuarioController.admin_bloquear_usuario(usuario_id)

# ===== ROTAS ADMIN - QUADRAS =====
@app.route('/admin/quadras')
@login_required
def admin_quadras():
    return QuadraController.admin_listar_quadras()

@app.route('/admin/quadra/nova', methods=['GET', 'POST'])
@login_required
def admin_cadastrar_quadra():
    return QuadraController.admin_cadastrar_quadra()

@app.route('/admin/quadra/<int:quadra_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_editar_quadra(quadra_id):
    return QuadraController.admin_editar_quadra(quadra_id)

@app.route('/admin/quadra/<int:quadra_id>/remover')
@login_required
def admin_remover_quadra(quadra_id):
    return QuadraController.admin_remover_quadra(quadra_id)

@app.route('/admin/quadra/<int:quadra_id>/reservas')
@login_required
def admin_ver_reservas_quadra(quadra_id):
    return QuadraController.admin_ver_reservas_quadra(quadra_id)

@app.route('/admin/quadra/<int:quadra_id>/reserva/<int:reserva_id>/cancelar')
@login_required
def admin_cancelar_reserva_quadra(quadra_id, reserva_id):
    return QuadraController.admin_cancelar_reserva_quadra(quadra_id, reserva_id)

# ===== ROTAS QUADRAS - DONO =====
@app.route('/quadras')
def listar_quadras():
    return QuadraController.listar_quadras()

@app.route('/minhas-quadras')
@login_required
def minhas_quadras():
    return QuadraController.minhas_quadras()

@app.route('/cadastrar-quadra', methods=['GET', 'POST'])
@login_required
def cadastrar_quadra():
    return QuadraController.cadastrar_quadra()

@app.route('/quadra/<int:quadra_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_quadra(quadra_id):
    return QuadraController.editar_quadra(quadra_id)

@app.route('/quadra/<int:quadra_id>/deletar')
@login_required
def deletar_quadra(quadra_id):
    return QuadraController.deletar_quadra(quadra_id)

@app.route('/quadra/<int:quadra_id>/reservas')
@login_required
def ver_reservas_quadra(quadra_id):
    return QuadraController.ver_reservas_quadra(quadra_id)

@app.route('/quadra/<int:quadra_id>/gerenciar-horarios')
@login_required
def gerenciar_horarios_quadra(quadra_id):
    return QuadraController.gerenciar_horarios(quadra_id)

# ===== ROTAS RESERVAS =====
@app.route('/reservar/<int:quadra_id>', methods=['GET', 'POST'])
@login_required
def reservar_quadra(quadra_id):
    return ReservaController.reservar(quadra_id)

@app.route('/minhas-reservas')
@login_required
def minhas_reservas():
    return ReservaController.minhas_reservas()

@app.route('/reserva/<int:reserva_id>/cancelar')
@login_required
def cancelar_reserva(reserva_id):
    return ReservaController.cancelar_reserva(reserva_id)

@app.route('/quadra/<int:quadra_id>/reserva/<int:reserva_id>/cancelar-dono')
@login_required
def dono_cancelar_reserva(quadra_id, reserva_id):
    return QuadraController.cancelar_reserva_dono(reserva_id)

# ===== INICIALIZAÇÃO DO BANCO =====
with app.app_context():
    db.create_all()
    
    # Cria admin padrão se não existir
    admin = Usuario.query.filter_by(email='admin@resergol.com').first()
    if not admin:
        senha_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = Usuario(
            nome='Administrador',
            email='admin@resergol.com',
            senha_hash=senha_hash,
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin criado: admin@resergol.com / admin123")

if __name__ == '__main__':
    app.run(debug=True)
