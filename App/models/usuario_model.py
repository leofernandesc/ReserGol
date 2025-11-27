from models import db, UserMixin, bcrypt, datetime

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='usuario')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Sistema de bloqueio
    tentativas_login = db.Column(db.Integer, default=0)
    bloqueado_ate = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos - usar strings para evitar referência circular
    quadras = db.relationship('Quadra', backref='dono', lazy=True, foreign_keys='Quadra.dono_id')
    reservas = db.relationship('Reserva', backref='usuario', lazy=True, foreign_keys='Reserva.usuario_id')
    
    def check_password(self, senha):
        """Verifica se a senha está correta"""
        return bcrypt.check_password_hash(self.senha_hash, senha)
    
    def esta_bloqueado(self):
        """Verifica se o usuário está bloqueado"""
        if self.bloqueado_ate is None:
            return False
        if datetime.utcnow() > self.bloqueado_ate:
            self.bloqueado_ate = None
            db.session.commit()
            return False
        return True
    
    def is_dono_quadra(self):
        """Verifica se é dono de quadra"""
        return self.role == 'dono_quadra'
    
    def is_admin(self):
        """Verifica se é administrador"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<Usuario {self.email}>'
