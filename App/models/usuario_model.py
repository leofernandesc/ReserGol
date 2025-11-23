from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    
    # Novos campos para controle de bloqueio
    tentativas_login = db.Column(db.Integer, default=0)
    bloqueado_ate = db.Column(db.DateTime, nullable=True)
    
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
