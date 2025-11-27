from models import db, datetime

class Reserva(db.Model):
    __tablename__ = 'reservas'
    
    id = db.Column(db.Integer, primary_key=True)
    quadra_id = db.Column(db.Integer, db.ForeignKey('quadras.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    data = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='ativa')
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Reserva {self.id} - {self.data}>'
