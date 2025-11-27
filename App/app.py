import os
from flask import Flask, render_template, redirect, url_for, request, flash
from datetime import datetime, date, timedelta
from flask_login import LoginManager, current_user, login_required
from controllers.usuario_controller import UsuarioController
from models.usuario_model import db, Usuario
from models.quadra_model import HorarioBloqueado, db, Quadra, DataDisponivel, HorarioDisponivel
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
@login_required
def editar_quadra(quadra_id):
    quadra = Quadra.query.get_or_404(quadra_id)

    if request.method == "POST":
        # Limpa bloqueios antigos do dono
        HorarioBloqueado.query.filter_by(quadra_id=quadra_id).delete()

        # Para cada checkbox marcado → é UM BLOQUEIO
        for key in request.form:
            if key.startswith("horario_"):
                _, data_str, hora_str = key.split("_")
                nova_data = datetime.strptime(data_str, "%Y-%m-%d").date()

                # Salva horário bloqueado
                hb = HorarioBloqueado(
                    quadra_id=quadra_id,
                    data=nova_data,
                    hora=hora_str
                )
                db.session.add(hb)

        db.session.commit()
        flash("Horários bloqueados atualizados com sucesso!", "success")
        return redirect(url_for("editar_quadra", quadra_id=quadra_id))

    # GET → construir agenda invertida: marcados = bloqueados
    dias = [datetime.today().date() + timedelta(days=i) for i in range(7)]
    agenda = {}

    for d in dias:
        bloqueios = HorarioBloqueado.query.filter_by(
            quadra_id=quadra_id,
            data=d
        ).all()
        agenda[d.strftime("%Y-%m-%d")] = {b.hora for b in bloqueios}

    return render_template(
        "quadras/editar.html",
        quadra=quadra,
        dias=dias,
        agenda=agenda
    )
    
@app.route('/deletar-quadra/<int:quadra_id>')
@login_required
def deletar_quadra(quadra_id):
    from controllers.quadra_controller import QuadraController
    return QuadraController.deletar_quadra(quadra_id)

# ===== ROTAS RESERVAS =====
@app.route("/reservar/<int:quadra_id>", methods=["GET", "POST"])
def reservar_quadra(quadra_id):
    quadra = Quadra.query.get_or_404(quadra_id)
    hoje = date.today()
    data_escolhida = request.form.get("data", hoje.strftime("%Y-%m-%d"))
    data_date = datetime.strptime(data_escolhida, "%Y-%m-%d").date()

    # --- Bloqueios do dono ---
    bloqueios = HorarioBloqueado.query.filter_by(
        quadra_id=quadra_id,
        data=data_date
    ).all()
    horas_bloqueadas = {b.hora for b in bloqueios}

    # --- Reservas já feitas ---
    reservas = Reserva.query.filter_by(
        quadra_id=quadra_id,
        data=data_date,
        status="ativa"
    ).all()
    horas_reservadas = {r.hora_inicio.strftime("%H:%M") for r in reservas}

    # --- Gerar horários disponíveis para mostrar ---
    horarios_disponiveis = []
    horarios_indisponiveis = []

    for h in range(6, 24):
        hora_str = f"{h:02d}:00"
        dt_hora = datetime.combine(data_date, datetime.strptime(hora_str, "%H:%M").time())

        if hora_str in horas_bloqueadas:
            # Não adiciona nos horários disponíveis, nem no select
            continue

        if hora_str in horas_reservadas:
            horarios_indisponiveis.append(dt_hora)
            horarios_disponiveis.append({
                "horario": dt_hora,
                "reservado": True
            })
            continue

        horarios_disponiveis.append({
            "horario": dt_hora,
            "reservado": False
        })

    # --- Criar reserva ---
    if request.method == "POST" and request.form.get("hora"):
        hora_str = request.form.get("hora")
        hora_inicio = datetime.strptime(hora_str, "%H:%M").time()
        hora_fim = (datetime.combine(data_date, hora_inicio) + timedelta(hours=1)).time()

        nova_reserva = Reserva(
            quadra_id=quadra.id,
            usuario_id=current_user.id,
            data=data_date,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim
        )
        db.session.add(nova_reserva)
        db.session.commit()

        flash("Reserva confirmada com sucesso!", "success")
        return redirect(url_for("listar_quadras"))

    return render_template(
        "reservas/reservar.html",
        quadra=quadra,
        hoje=hoje.strftime("%Y-%m-%d"),
        data_escolhida=data_escolhida,
        horarios_disponiveis=horarios_disponiveis,
        horarios_indisponiveis=horarios_indisponiveis
    )

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

@app.route("/quadra/<int:quadra_id>/salvar-horarios", methods=["POST"])
@login_required
def salvar_horarios_quadra(quadra_id):
    quadra = Quadra.query.get_or_404(quadra_id)

    # Apaga todos horários
    DataDisponivel.query.filter_by(quadra_id=quadra_id).delete()

    # Recria com base nos checkbox
    for key in request.form:
        if key.startswith("horario_"):
            _, data_str, hora_str = key.split("_")

            nova_data = datetime.strptime(data_str, "%Y-%m-%d").date()
            nova_hora = datetime.strptime(hora_str, "%H:%M").time()

            novo = DataDisponivel(
                quadra_id=quadra_id,
                data=nova_data,
                horario=nova_hora
            )
            db.session.add(novo)

    db.session.commit()
    flash("Horários atualizados!", "success")
    return redirect(url_for("editar_quadra", quadra_id=quadra_id))


# ROTAS - Gerenciamento de Quadras pelo Dono
@app.route('/quadra/<int:quadra_id>/reservas')
@login_required
def ver_reservas_quadra(quadra_id):
    from controllers.quadra_controller import QuadraController
    return QuadraController.ver_reservas_quadra(quadra_id)

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
