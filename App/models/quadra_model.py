from models import db, datetime

class Quadra(db.Model):
    __tablename__ = 'quadras'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    endereco = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    preco_hora = db.Column(db.Float, nullable=False)
    ativa = db.Column(db.Boolean, default=True)
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    dono_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Relacionamento - usar string para evitar referência circular
    reservas = db.relationship('Reserva', backref='quadra', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Quadra {self.nome}>'
