from models.usuario_model import db
from datetime import datetime

class Quadra(db.Model):
    __tablename__ = "quadra"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text)
    preco_hora = db.Column(db.Float, nullable=False)
    ativa = db.Column(db.Boolean, default=True)
    dono_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())

    datas_disponiveis = db.relationship(
        "DataDisponivel",
        backref="quadra",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="DataDisponivel.data"
    )

    def __repr__(self):
        return f'<Quadra {self.nome}>'


class DataDisponivel(db.Model):
    __tablename__ = "data_disponivel"

    id = db.Column(db.Integer, primary_key=True)
    quadra_id = db.Column(db.Integer, db.ForeignKey("quadra.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)

    horarios = db.relationship(
        "HorarioDisponivel",
        backref="data_disponivel",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="HorarioDisponivel.horario"
    )

    def __repr__(self):
        return f"<DataDisponivel {self.data}>"


class HorarioDisponivel(db.Model):
    __tablename__ = "horario_disponivel"

    id = db.Column(db.Integer, primary_key=True)
    data_id = db.Column(db.Integer, db.ForeignKey("data_disponivel.id"), nullable=False)
    horario = db.Column(db.String(5), nullable=False)

    def __repr__(self):
        return f"<Horario {self.horario}>"