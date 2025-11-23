from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    
    # Sistema de Roles/Permissões
    role = db.Column(db.String(20), default='usuario', nullable=False)  # 'usuario', 'dono_quadra', 'admin'
    
    # Campos de bloqueio (já existentes)
    tentativas_login = db.Column(db.Integer, default=0)
    bloqueado_ate = db.Column(db.DateTime, nullable=True)
    
    # Relacionamento com quadras (um dono pode ter várias quadras)
    quadras = db.relationship('Quadra', backref='dono', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Usuario {self.email}>'
    
    def esta_bloqueado(self):
        """Verifica se o usuário está bloqueado"""
        if self.bloqueado_ate is None:
            return False
        return datetime.utcnow() < self.bloqueado_ate
    
    def resetar_tentativas(self):
        """Reseta contador de tentativas após login bem-sucedido"""
        self.tentativas_login = 0
        self.bloqueado_ate = None
    
    # Métodos de verificação de permissão
    def is_admin(self):
        """Verifica se é administrador"""
        return self.role == 'admin'
    
    def is_dono_quadra(self):
        """Verifica se é dono de quadra"""
        return self.role == 'dono_quadra' or self.role == 'admin'
    
    def tem_permissao(self, role_necessaria):
        """Verifica se tem a permissão necessária"""
        hierarquia = {
            'usuario': 1,
            'dono_quadra': 2,
            'admin': 3
        }
        return hierarquia.get(self.role, 0) >= hierarquia.get(role_necessaria, 0)
