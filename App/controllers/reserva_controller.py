from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from models.quadra_model import Quadra, DataDisponivel
from models.reserva_model import Reserva
from models.usuario_model import db
from datetime import datetime, timedelta, date

class ReservaController:

    @staticmethod
    @login_required
    def reservar(quadra_id):
        quadra = Quadra.query.get_or_404(quadra_id)

        data_escolhida = request.form.get("data") or date.today().isoformat()
        data_obj = datetime.strptime(data_escolhida, "%Y-%m-%d").date()

        data_disponivel = DataDisponivel.query.filter_by(
            quadra_id=quadra.id,
            data=data_obj
        ).first()
        horarios_possiveis = [h.horario for h in data_disponivel.horarios] if data_disponivel else []

        horarios_bloqueados = [hb.hora for hb in quadra.horarios_bloqueados if hb.data == data_obj]

        reservas_ativas = Reserva.query.filter_by(
            quadra_id=quadra.id,
            data=data_obj,
            status="ativa"
        ).all()
        horarios_reservados = [r.hora_inicio.strftime("%H:%M") for r in reservas_ativas]

        horarios_possiveis_str = [h.strftime("%H:%M") if isinstance(h, (datetime, date, timedelta)) else str(h) for h in horarios_possiveis]

        horarios_disponiveis = [
            h for h in horarios_possiveis_str if h not in horarios_bloqueados and h not in horarios_reservados
        ]

        # cria reserva
        if request.method == "POST" and request.form.get("hora"):
            hora_str = request.form["hora"]
            hora_inicio = datetime.strptime(hora_str, "%H:%M").time()
            hora_fim = (datetime.combine(date.today(), hora_inicio) + timedelta(hours=1)).time()

            nova_reserva = Reserva(
                quadra_id=quadra.id,
                usuario_id=current_user.id,
                data=data_obj,
                hora_inicio=hora_inicio,
                hora_fim=hora_fim
            )

            db.session.add(nova_reserva)
            db.session.commit()

            flash("Reserva realizada com sucesso!", "success")
            return redirect(url_for("minhas_reservas"))

        hoje_str = date.today().isoformat()
        horarios_dict = [
            {"horario": datetime.strptime(h, "%H:%M"), "reservado": False} for h in horarios_disponiveis
        ]

        horarios_indisponiveis = [
            datetime.strptime(h, "%H:%M") for h in horarios_reservados + horarios_bloqueados
        ]

        return render_template(
            "reservar.html",
            quadra=quadra,
            data_escolhida=data_escolhida,
            hoje=hoje_str,
            horarios_disponiveis=horarios_dict,
            horarios_indisponiveis=horarios_indisponiveis
        )
    
    @staticmethod
    @login_required
    def minhas_reservas():
        """Lista todas as reservas do usuário atual"""
        reservas = Reserva.query.filter_by(
            usuario_id=current_user.id
        ).order_by(Reserva.data.desc(), Reserva.hora_inicio.desc()).all()
        
        return render_template('reservas/minhas_reservas.html', reservas=reservas)
    
    @staticmethod
    @login_required
    def cancelar_reserva(reserva_id):
        """Cancela uma reserva do usuário"""
        reserva = Reserva.query.get_or_404(reserva_id)
        
        if reserva.usuario_id != current_user.id:
            flash('Você não tem permissão para cancelar esta reserva!', 'danger')
            return redirect(url_for('minhas_reservas'))
        
        if reserva.status == 'cancelada':
            flash('Esta reserva já foi cancelada!', 'warning')
            return redirect(url_for('minhas_reservas'))
        
        reserva.status = 'cancelada'
        db.session.commit()
        
        flash('Reserva cancelada com sucesso!', 'success')
        return redirect(url_for('minhas_reservas'))
