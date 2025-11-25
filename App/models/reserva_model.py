from models.usuario_model import db
from datetime import datetime

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quadra_id = db.Column(db.Integer, db.ForeignKey('quadra.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='ativa')  # ativa, cancelada, concluída
    criada_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    quadra = db.relationship('Quadra', backref='reservas')
    usuario = db.relationship('Usuario', backref='reservas')
    
    def __repr__(self):
        return f'<Reserva {self.id} - Quadra {self.quadra_id} - {self.data}>'
