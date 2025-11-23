from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_mail import Message
from models.usuario_model import db, Usuario
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta

bcrypt = Bcrypt()

# ===== FUNÇÕES FORA DA CLASSE =====
def gerar_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='redefinir-senha')

def validar_token(token, tempo_expiracao=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='redefinir-senha', max_age=tempo_expiracao)
    except Exception:
        return None
    return email

def enviar_email_reset(email, token):
    from app import mail  # Importa aqui para evitar import circular
    link = url_for('resetar_senha', token=token, _external=True)
    msg = Message("Redefinir sua senha - ReserGol",
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[email])
    msg.body = f"Para redefinir sua senha, acesse: {link}"
    mail.send(msg)

# ===== CLASSE CONTROLLER =====
class UsuarioController:
    def registro():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha = request.form.get('senha')

            if not nome or not email or not senha:
                flash('Todos os campos são obrigatórios!', 'danger')
                return redirect(url_for('registro'))

            usuario_existe = Usuario.query.filter_by(email=email).first()
            if usuario_existe:
                flash('Este email já está cadastrado!', 'warning')
                return redirect(url_for('registro'))

            senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')
            novo_usuario = Usuario(nome=nome, email=email, senha_hash=senha_hash)
            db.session.add(novo_usuario)
            db.session.commit()

            flash('Registro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))

        return render_template('registro.html')
    
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            email = request.form.get('email')
            senha = request.form.get('senha')
            lembrar = request.form.get('lembrar')

            usuario = Usuario.query.filter_by(email=email).first()

            # Verifica se o usuário existe
            if not usuario:
                flash('Email ou senha incorretos!', 'danger')
                return render_template('login.html')

            # Verifica se a conta está bloqueada
            if usuario.esta_bloqueado():
                tempo_restante = (usuario.bloqueado_ate - datetime.utcnow()).total_seconds() / 60
                flash(f'Conta bloqueada temporariamente. Tente novamente em {int(tempo_restante)} minutos.', 'danger')
                return render_template('login.html')

            # Verifica a senha
            if bcrypt.check_password_hash(usuario.senha_hash, senha):
                # Login bem-sucedido - reseta tentativas
                usuario.resetar_tentativas()
                db.session.commit()
                
                login_user(usuario, remember=lembrar)
                flash(f'Bem-vindo, {usuario.nome}!', 'success')
                proximo = request.args.get('next')
                return redirect(proximo) if proximo else redirect(url_for('dashboard'))
            else:
                # Senha incorreta - incrementa tentativas
                usuario.tentativas_login += 1
                
                # Define o limite de tentativas
                MAX_TENTATIVAS = 5
                TEMPO_BLOQUEIO_MINUTOS = 15
                
                if usuario.tentativas_login >= MAX_TENTATIVAS:
                    # Bloqueia a conta por 15 minutos
                    usuario.bloqueado_ate = datetime.utcnow() + timedelta(minutes=TEMPO_BLOQUEIO_MINUTOS)
                    db.session.commit()
                    flash(f'Conta bloqueada por {TEMPO_BLOQUEIO_MINUTOS} minutos devido a múltiplas tentativas de login.', 'danger')
                else:
                    tentativas_restantes = MAX_TENTATIVAS - usuario.tentativas_login
                    db.session.commit()
                    flash(f'Email ou senha incorretos! Você tem {tentativas_restantes} tentativa(s) restante(s).', 'danger')

        return render_template('login.html')

    
    def esqueci_senha():
        if request.method == 'POST':
            email = request.form.get('email')
            usuario = Usuario.query.filter_by(email=email).first()
            if not usuario:
                flash('Nenhum usuário com esse email!', 'danger')
                return redirect(url_for('esqueci_senha'))

            token = gerar_token(email)
            enviar_email_reset(email, token)
            flash('Email de redefinição enviado!', 'info')
            return redirect(url_for('login'))
        return render_template('esqueci_senha.html')

    def resetar_senha(token):
        email = validar_token(token)
        if not email:
            flash('Link expirado ou inválido. Solicite novamente.', 'danger')
            return redirect(url_for('esqueci_senha'))

        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario:
            flash('Usuário não encontrado!', 'danger')
            return redirect(url_for('esqueci_senha'))

        if request.method == 'POST':
            senha_nova = request.form.get('senha_nova')
            senha_confirmar = request.form.get('senha_confirmar')
            if not senha_nova or senha_nova != senha_confirmar:
                flash('As senhas devem ser iguais e não podem estar em branco!', 'danger')
                return redirect(url_for('resetar_senha', token=token))
            usuario.senha_hash = bcrypt.generate_password_hash(senha_nova).decode('utf-8')
            db.session.commit()
            flash('Senha redefinida com sucesso. Faça login!', 'success')
            return redirect(url_for('login'))
        return render_template('resetar_senha.html', token=token)

    @login_required
    def dashboard():
        return render_template('dashboard.html', usuario=current_user)

    @login_required
    def logout():
        logout_user()
        flash('Logout realizado com sucesso!', 'info')
        return redirect(url_for('index'))

    @login_required
    def lista_usuarios():
        usuarios = Usuario.query.all()
        return render_template('lista_usuarios.html', usuarios=usuarios)

    @login_required
    def perfil():
        return render_template('perfil.html', usuario=current_user)

    @login_required
    def editar_perfil():
        if request.method == 'POST':
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha_atual = request.form.get('senha_atual')
            senha_nova = request.form.get('senha_nova')
            senha_confirmar = request.form.get('senha_confirmar')

            if not nome or not email:
                flash('Nome e email são obrigatórios!', 'danger')
                return redirect(url_for('editar_perfil'))

            usuario_existe = Usuario.query.filter_by(email=email).first()
            if usuario_existe and usuario_existe.id != current_user.id:
                flash('Este email já está em uso por outro usuário!', 'warning')
                return redirect(url_for('editar_perfil'))

            current_user.nome = nome
            current_user.email = email

            if senha_nova:
                if not senha_atual:
                    flash('Para alterar a senha, você precisa informar a senha atual!', 'danger')
                    return redirect(url_for('editar_perfil'))

                if not bcrypt.check_password_hash(current_user.senha_hash, senha_atual):
                    flash('Senha atual incorreta!', 'danger')
                    return redirect(url_for('editar_perfil'))

                if senha_nova != senha_confirmar:
                    flash('As senhas novas não coincidem!', 'danger')
                    return redirect(url_for('editar_perfil'))

                current_user.senha_hash = bcrypt.generate_password_hash(senha_nova).decode('utf-8')

            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('perfil'))

        return render_template('editar_perfil.html', usuario=current_user)
