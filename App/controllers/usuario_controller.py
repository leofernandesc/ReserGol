from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from models import db, bcrypt  # ← Importar daqui
from models.usuario_model import Usuario
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta

def gerar_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='redefinir-senha')

def validar_token(token, tempo_expiracao=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='redefinir-senha', max_age=tempo_expiracao)
        return email
    except Exception:
        return None

def enviar_email_reset(email, token):
    from app import mail
    link = url_for('resetar_senha', token=token, _external=True)
    msg = Message(
        "Redefinir sua senha - ReserGol",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.body = f"Para redefinir sua senha, acesse: {link}"
    mail.send(msg)

class UsuarioController:
    
    @staticmethod
    def registro():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha = request.form.get('senha')
            confirmar_senha = request.form.get('confirmar_senha')
            
            if not nome or not email or not senha or not confirmar_senha:
                flash('Todos os campos são obrigatórios!', 'danger')
                return redirect(url_for('registro'))
            
            if senha != confirmar_senha:
                flash('As senhas não coincidem!', 'danger')
                return redirect(url_for('registro'))
            
            if Usuario.query.filter_by(email=email).first():
                flash('Este email já está cadastrado!', 'danger')
                return redirect(url_for('registro'))
            
            senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')
            novo_usuario = Usuario(nome=nome, email=email, senha_hash=senha_hash)
            db.session.add(novo_usuario)
            db.session.commit()
            
            flash('Registro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        
        return render_template('registro.html')
    
    @staticmethod
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            senha = request.form.get('senha')
            lembrar = request.form.get('lembrar')
            
            usuario = Usuario.query.filter_by(email=email).first()
            
            if not usuario:
                flash('Email ou senha incorretos!', 'danger')
                return render_template('login.html')
            
            if usuario.esta_bloqueado():
                tempo_restante = (usuario.bloqueado_ate - datetime.utcnow()).total_seconds() / 60
                flash(f'Conta bloqueada. Tente novamente em {int(tempo_restante)} minutos.', 'danger')
                return render_template('login.html')
            
            if not usuario.check_password(senha):
                usuario.tentativas_login += 1
                if usuario.tentativas_login >= 5:
                    usuario.bloqueado_ate = datetime.utcnow() + timedelta(hours=24)
                db.session.commit()
                flash('Email ou senha incorretos!', 'danger')
                return render_template('login.html')
            
            usuario.tentativas_login = 0
            usuario.bloqueado_ate = None
            db.session.commit()
            
            login_user(usuario, remember=bool(lembrar))
            flash(f'Bem-vindo, {usuario.nome}!', 'success')
            return redirect(url_for('index'))
        
        return render_template('login.html')
    
    @staticmethod
    def logout():
        logout_user()
        flash('Você saiu da sua conta.', 'success')
        return redirect(url_for('index'))
    
    @staticmethod
    @login_required
    def perfil():
        return render_template('perfil.html')
    
    @staticmethod
    @login_required
    def editar_perfil():
        if request.method == 'POST':
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha_atual = request.form.get('senha_atual')
            nova_senha = request.form.get('nova_senha')
            confirmar_nova_senha = request.form.get('confirmar_nova_senha')
            
            if not nome or not email:
                flash('Nome e email são obrigatórios!', 'danger')
                return redirect(url_for('editar_perfil'))
            
            usuario_existe = Usuario.query.filter_by(email=email).first()
            if usuario_existe and usuario_existe.id != current_user.id:
                flash('Este email já está em uso!', 'danger')
                return redirect(url_for('editar_perfil'))
            
            if senha_atual or nova_senha or confirmar_nova_senha:
                if not senha_atual or not nova_senha or not confirmar_nova_senha:
                    flash('Preencha todos os campos de senha!', 'danger')
                    return redirect(url_for('editar_perfil'))
                
                if not current_user.check_password(senha_atual):
                    flash('Senha atual incorreta!', 'danger')
                    return redirect(url_for('editar_perfil'))
                
                if nova_senha != confirmar_nova_senha:
                    flash('As novas senhas não coincidem!', 'danger')
                    return redirect(url_for('editar_perfil'))
                
                current_user.senha_hash = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
            
            current_user.nome = nome
            current_user.email = email
            db.session.commit()
            
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('perfil'))
        
        return render_template('editar_perfil.html')
    
    @staticmethod
    def esqueci_senha():
        if request.method == 'POST':
            email = request.form.get('email')
            usuario = Usuario.query.filter_by(email=email).first()
            
            if usuario:
                token = gerar_token(email)
                enviar_email_reset(email, token)
            
            flash('Se o email existir, você receberá um link para redefinir sua senha.', 'info')
            return redirect(url_for('login'))
        
        return render_template('esqueci_senha.html')
    
    @staticmethod
    def resetar_senha(token):
        email = validar_token(token)
        
        if not email:
            flash('Link inválido ou expirado!', 'danger')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            nova_senha = request.form.get('senha')
            confirmar_senha = request.form.get('confirmar_senha')
            
            if not nova_senha or not confirmar_senha:
                flash('Preencha todos os campos!', 'danger')
                return redirect(url_for('resetar_senha', token=token))
            
            if nova_senha != confirmar_senha:
                flash('As senhas não coincidem!', 'danger')
                return redirect(url_for('resetar_senha', token=token))
            
            usuario = Usuario.query.filter_by(email=email).first()
            usuario.senha_hash = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
            db.session.commit()
            
            flash('Senha redefinida com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        
        return render_template('resetar_senha.html')
    
    # ===== ADMIN =====
    
    @staticmethod
    @login_required
    def admin_listar_usuarios():
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        busca = request.args.get('busca', '')
        if busca:
            usuarios = Usuario.query.filter(
                (Usuario.nome.ilike(f'%{busca}%')) | 
                (Usuario.email.ilike(f'%{busca}%'))
            ).all()
        else:
            usuarios = Usuario.query.all()
        
        return render_template('admin_usuarios.html', usuarios=usuarios, busca=busca)
    
    @staticmethod
    @login_required
    def admin_editar_usuario(usuario_id):
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        usuario = Usuario.query.get_or_404(usuario_id)
        
        if request.method == 'POST':
            nome = request.form.get('nome')
            email = request.form.get('email')
            role = request.form.get('role')
            
            if not nome or not email:
                flash('Nome e email são obrigatórios!', 'danger')
                return redirect(url_for('admin_editar_usuario', usuario_id=usuario_id))
            
            usuario_existe = Usuario.query.filter_by(email=email).first()
            if usuario_existe and usuario_existe.id != usuario.id:
                flash('Este email já está em uso!', 'danger')
                return redirect(url_for('admin_editar_usuario', usuario_id=usuario_id))
            
            usuario.nome = nome
            usuario.email = email
            if usuario.id != current_user.id:
                usuario.role = role
            
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('admin_usuarios'))
        
        return render_template('admin_editar_usuario.html', usuario=usuario)
    
    @staticmethod
    @login_required
    def promover_para_dono(usuario_id):
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        usuario = Usuario.query.get_or_404(usuario_id)
        
        if usuario.role == 'admin':
            flash('Não é possível alterar o role de um administrador!', 'warning')
            return redirect(url_for('admin_usuarios'))
        
        usuario.role = 'dono_quadra'
        db.session.commit()
        flash(f'{usuario.nome} foi promovido para Dono de Quadra!', 'success')
        return redirect(url_for('admin_usuarios'))
    
    @staticmethod
    @login_required
    def rebaixar_para_usuario(usuario_id):
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        usuario = Usuario.query.get_or_404(usuario_id)
        
        if usuario.role == 'admin':
            flash('Não é possível alterar o role de um administrador!', 'warning')
            return redirect(url_for('admin_usuarios'))
        
        usuario.role = 'usuario'
        db.session.commit()
        flash(f'{usuario.nome} foi rebaixado para Usuário Comum!', 'success')
        return redirect(url_for('admin_usuarios'))
    
    @staticmethod
    @login_required
    def admin_remover_usuario(usuario_id):
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        usuario = Usuario.query.get_or_404(usuario_id)
        
        if usuario.id == current_user.id:
            flash('Você não pode remover sua própria conta!', 'warning')
            return redirect(url_for('admin_usuarios'))
        
        if usuario.role == 'admin':
            flash('Não é possível remover outro administrador!', 'warning')
            return redirect(url_for('admin_usuarios'))
        
        nome = usuario.nome
        db.session.delete(usuario)
        db.session.commit()
        
        flash(f'Usuário {nome} foi removido com sucesso!', 'success')
        return redirect(url_for('admin_usuarios'))
    
    @staticmethod
    @login_required
    def admin_desbloquear_usuario(usuario_id):
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        usuario = Usuario.query.get_or_404(usuario_id)
        usuario.tentativas_login = 0
        usuario.bloqueado_ate = None
        db.session.commit()
        
        flash(f'{usuario.nome} foi desbloqueado!', 'success')
        return redirect(url_for('admin_usuarios'))
    
    @staticmethod
    @login_required
    def admin_bloquear_usuario(usuario_id):
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        usuario = Usuario.query.get_or_404(usuario_id)
        
        if usuario.id == current_user.id:
            flash('Você não pode bloquear sua própria conta!', 'warning')
            return redirect(url_for('admin_usuarios'))
        
        if usuario.role == 'admin':
            flash('Não é possível bloquear outro administrador!', 'warning')
            return redirect(url_for('admin_usuarios'))
        
        if usuario.esta_bloqueado():
            flash(f'{usuario.nome} já está bloqueado!', 'warning')
            return redirect(url_for('admin_usuarios'))
        
        usuario.bloqueado_ate = datetime.utcnow() + timedelta(hours=24)
        usuario.tentativas_login = 5
        db.session.commit()
        
        flash(f'{usuario.nome} foi bloqueado por 24 horas!', 'success')
        return redirect(url_for('admin_usuarios'))
