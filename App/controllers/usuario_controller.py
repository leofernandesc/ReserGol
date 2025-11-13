from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models.usuario_model import db, Usuario

bcrypt = Bcrypt()

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

            if usuario and bcrypt.check_password_hash(usuario.senha_hash, senha):
                login_user(usuario, remember=lembrar)
                flash(f'Bem-vindo, {usuario.nome}!', 'success')
                proximo = request.args.get('next')
                return redirect(proximo) if proximo else redirect(url_for('dashboard'))
            else:
                flash('Email ou senha incorretos!', 'danger')

        return render_template('login.html')

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
        """Exibe as informações do perfil do usuário atual"""
        return render_template('perfil.html', usuario=current_user)

    @login_required
    def editar_perfil():
        """Permite o usuário editar suas informações de perfil"""
        if request.method == 'POST':
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha_atual = request.form.get('senha_atual')
            senha_nova = request.form.get('senha_nova')
            senha_confirmar = request.form.get('senha_confirmar')

            # Validações
            if not nome or not email:
                flash('Nome e email são obrigatórios!', 'danger')
                return redirect(url_for('editar_perfil'))

            # Verifica se email já está em uso por outro usuário
            usuario_existe = Usuario.query.filter_by(email=email).first()
            if usuario_existe and usuario_existe.id != current_user.id:
                flash('Este email já está em uso por outro usuário!', 'warning')
                return redirect(url_for('editar_perfil'))

            # Atualiza nome e email
            current_user.nome = nome
            current_user.email = email

            # Se o usuário quer alterar a senha
            if senha_nova:
                # Verifica se forneceu a senha atual
                if not senha_atual:
                    flash('Para alterar a senha, você precisa informar a senha atual!', 'danger')
                    return redirect(url_for('editar_perfil'))

                # Verifica se a senha atual está correta
                if not bcrypt.check_password_hash(current_user.senha_hash, senha_atual):
                    flash('Senha atual incorreta!', 'danger')
                    return redirect(url_for('editar_perfil'))

                # Verifica se as senhas novas coincidem
                if senha_nova != senha_confirmar:
                    flash('As senhas novas não coincidem!', 'danger')
                    return redirect(url_for('editar_perfil'))

                # Atualiza a senha
                current_user.senha_hash = bcrypt.generate_password_hash(senha_nova).decode('utf-8')

            # Salva as alterações no banco
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('perfil'))

        return render_template('editar_perfil.html', usuario=current_user)
