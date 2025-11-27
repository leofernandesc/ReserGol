import os
from flask import Flask, render_template, redirect, url_for, request, flash
from datetime import datetime, date, timedelta
from flask_login import LoginManager, login_required
from controllers.usuario_controller import UsuarioController
from models.usuario_model import db, Usuario
from models.quadra_model import db, Quadra, DataDisponivel, HorarioDisponivel
from flask_mail import Mail, Message
from models.reserva_model import Reserva

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

# ===== ROTAS ADMIN =====
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

@app.route('/admin/bloquear-usuario/<int:usuario_id>')
def admin_bloquear_usuario(usuario_id):
    return UsuarioController.admin_bloquear_usuario(usuario_id)

# ROTAS - Administração de Quadras (Admin)
@app.route('/admin/quadras')
@login_required
def admin_quadras():
    from controllers.quadra_controller import QuadraController
    return QuadraController.admin_listar_quadras()

@app.route('/admin/quadra/nova', methods=['GET', 'POST'])
@login_required
def admin_cadastrar_quadra():
    from controllers.quadra_controller import QuadraController
    return QuadraController.admin_cadastrar_quadra()

@app.route('/admin/quadra/<int:quadra_id>/editar', methods=['GET', 'POST'])
@login_required
def admin_editar_quadra(quadra_id):
    from controllers.quadra_controller import QuadraController
    return QuadraController.admin_editar_quadra(quadra_id)

@app.route('/admin/quadra/<int:quadra_id>/remover')
@login_required
def admin_remover_quadra(quadra_id):
    from controllers.quadra_controller import QuadraController
    return QuadraController.admin_remover_quadra(quadra_id)


# ===== ROTAS QUADRAS =====
@app.route('/quadras')
def listar_quadras():
    from controllers.quadra_controller import QuadraController
    return QuadraController.listar_quadras()

@app.route('/minhas-quadras')
@login_required
def minhas_quadras():
    from controllers.quadra_controller import QuadraController
    return QuadraController.minhas_quadras()

@app.route('/cadastrar-quadra', methods=['GET', 'POST'])
@login_required
def cadastrar_quadra():
    from controllers.quadra_controller import QuadraController
    return QuadraController.cadastrar_quadra()

@app.route("/editar-quadra/<int:quadra_id>", methods=["GET", "POST"])
def editar_quadra(quadra_id):
    quadra = Quadra.query.get_or_404(quadra_id)

    # Próximos 7 dias
    proximos_dias = [date.today() + timedelta(days=i) for i in range(7)]
    
    datas = []
    horarios = {}
    
    for d in proximos_dias:
        # Tenta buscar data existente no banco
        data_obj = DataDisponivel.query.filter_by(quadra_id=quadra.id, data=d).first()
        if not data_obj:
            # Cria objeto em memória só para exibição
            data_obj = DataDisponivel(quadra_id=quadra.id, data=d)
        datas.append(data_obj)

        # Horários fixos das 6h às 23h
        if data_obj.id:
            horarios[d] = HorarioDisponivel.query.filter_by(data_id=data_obj.id).all()
        else:
            horarios[d] = [HorarioDisponivel(horario=f"{h:02d}:00") for h in range(6, 24)]

    if request.method == "POST":
        # Excluir datas
        datas_excluir = request.form.getlist("datas_excluir")
        for d_id in datas_excluir:
            data = DataDisponivel.query.get(int(d_id))
            if data:
                db.session.delete(data)

        # Excluir horários
        horarios_excluir = request.form.getlist("horarios_excluir")
        for h_id in horarios_excluir:
            horario = HorarioDisponivel.query.get(int(h_id))
            if horario:
                db.session.delete(horario)

        # Editar campos da quadra
        quadra.nome = request.form.get("nome", quadra.nome)
        quadra.endereco = request.form.get("endereco", quadra.endereco)
        quadra.tipo = request.form.get("tipo", quadra.tipo)
        quadra.preco_hora = request.form.get("preco_hora", quadra.preco_hora)
        quadra.descricao = request.form.get("descricao", quadra.descricao)

        db.session.commit()
        flash("Quadra atualizada com sucesso!")
        return redirect(url_for("editar_quadra", quadra_id=quadra_id))

    return render_template(
        "quadras/editar.html",
        quadra=quadra,
        datas=datas,
        horarios=horarios
    )
    
@app.route('/deletar-quadra/<int:quadra_id>')
@login_required
def deletar_quadra(quadra_id):
    from controllers.quadra_controller import QuadraController
    return QuadraController.deletar_quadra(quadra_id)

# ===== ROTAS RESERVAS =====
@app.route('/reservar/<int:quadra_id>', methods=['GET', 'POST'])
@login_required
def reservar_quadra(quadra_id):
    from controllers.reserva_controller import ReservaController
    return ReservaController.reservar(quadra_id)

@app.route('/minhas-reservas')
@login_required
def minhas_reservas():
    from controllers.reserva_controller import ReservaController
    return ReservaController.minhas_reservas()

@app.route('/cancelar-reserva/<int:reserva_id>')
@login_required
def cancelar_reserva(reserva_id):
    from controllers.reserva_controller import ReservaController
    return ReservaController.cancelar_reserva(reserva_id)

# ROTAS - Gerenciamento de Quadras pelo Dono
@app.route('/quadra/<int:quadra_id>/reservas')
@login_required
def ver_reservas_quadra(quadra_id):
    from controllers.quadra_controller import QuadraController
    return QuadraController.ver_reservas_quadra(quadra_id)

@app.route('/quadra/<int:quadra_id>/horarios', methods=['GET', 'POST'])
@login_required
def gerenciar_horarios_quadra(quadra_id):
    from controllers.quadra_controller import QuadraController
    return QuadraController.gerenciar_horarios(quadra_id)

@app.route('/reserva/<int:reserva_id>/cancelar-dono')
@login_required
def dono_cancelar_reserva(reserva_id):
    from controllers.quadra_controller import QuadraController
    return QuadraController.cancelar_reserva_dono(reserva_id)

# ===== INICIALIZAÇÃO =====
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
        print("Admin criado: admin@resergol.com / admin123")

if __name__ == '__main__':
    app.run(debug=True)
