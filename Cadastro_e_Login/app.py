from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, Usuario

app = Flask(__name__)

# Configurações de segurança
app.config['SECRET_KEY'] = 'sua-chave-secreta-super-segura-aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização das extensões
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Carregador de usuário
@login_manager.user_loader
def load_user(user_id):
    """Carrega o usuário a partir do ID armazenado na sessão"""
    return Usuario.query.get(int(user_id))

# Rota principal
@app.route('/')
def index():
    return render_template('index.html')

# Rota de registro
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registra novos usuários no sistema"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # Validação básica
        if not nome or not email or not senha:
            flash('Todos os campos são obrigatórios!', 'danger')
            return redirect(url_for('registro'))
        
        # Verifica se o email já existe
        usuario_existe = Usuario.query.filter_by(email=email).first()
        if usuario_existe:
            flash('Este email já está cadastrado!', 'warning')
            return redirect(url_for('registro'))
        
        # Cria hash da senha
        senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')
        
        # Cria novo usuário
        novo_usuario = Usuario(nome=nome, email=email, senha_hash=senha_hash)
        db.session.add(novo_usuario)
        db.session.commit()
        
        flash('Registro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('registro.html')

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Autentica usuários no sistema"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        lembrar = request.form.get('lembrar')
        
        # Busca usuário no banco
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Verifica credenciais
        if usuario and bcrypt.check_password_hash(usuario.senha_hash, senha):
            login_user(usuario, remember=lembrar)
            flash(f'Bem-vindo, {usuario.nome}!', 'success')
            
            # Redireciona para página solicitada ou dashboard
            proximo = request.args.get('next')
            return redirect(proximo) if proximo else redirect(url_for('dashboard'))
        else:
            flash('Email ou senha incorretos!', 'danger')
    
    return render_template('login.html')

# Rota protegida - Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    """Página acessível apenas para usuários autenticados"""
    return render_template('dashboard.html', usuario=current_user)

# Rota de logout
@app.route('/logout')
@login_required
def logout():
    """Efetua logout do usuário"""
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))

# Criação do banco de dados
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
