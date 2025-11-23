from models.usuario_model import db

class Quadra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'futebol', 'tenis', 'basquete', etc
    descricao = db.Column(db.Text)
    preco_hora = db.Column(db.Float, nullable=False)
    ativa = db.Column(db.Boolean, default=True)  # Se está disponível para reservas
    
    # Chave estrangeira para o dono
    dono_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<Quadra {self.nome}>'
