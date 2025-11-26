from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models.usuario_model import db
from models.quadra_model import Quadra
from models.reserva_model import Reserva

class ReservaController:
    
    @staticmethod
    @login_required
    def reservar(quadra_id):
        """Página de reserva de horários"""
        quadra = Quadra.query.get_or_404(quadra_id)
        
        # Data escolhida (padrão: hoje)
        data_hoje = datetime.utcnow().date()
        data_escolhida_str = request.args.get('data') or request.form.get('data') or str(data_hoje)
        
        try:
            data_escolhida = datetime.strptime(data_escolhida_str, '%Y-%m-%d').date()
        except:
            data_escolhida = data_hoje
        
        # Horários possíveis (6h às 22h)
        horarios_possiveis = [f"{h:02d}:00" for h in range(6, 23)]
        
        # Pega reservas existentes para a quadra e data
        reservas = Reserva.query.filter_by(
            quadra_id=quadra_id, 
            data=data_escolhida, 
            status='ativa'
        ).all()
        
        horarios_reservados = set([r.hora_inicio.strftime('%H:%M') for r in reservas])
        
        # Processar reserva
        if request.method == 'POST' and request.form.get('hora'):
            hora = request.form['hora']
            
            if hora in horarios_reservados:
                flash('Esse horário acabou de ser reservado por outro usuário!', 'danger')
                return redirect(url_for('reservar_quadra', quadra_id=quadra_id))
            
            # Criar nova reserva
            hora_inicio = datetime.strptime(hora, '%H:%M').time()
            hora_fim = (datetime.strptime(hora, '%H:%M') + timedelta(hours=1)).time()
            
            # Captura o tipo de pagamento hipotético
            pagamento_tipo = request.form.get('pagamento')  # 'pix', 'cartao', 'boleto'
            
            nova_reserva = Reserva(
                quadra_id=quadra_id,
                usuario_id=current_user.id,
                data=data_escolhida,
                hora_inicio=hora_inicio,
                hora_fim=hora_fim,
                status='ativa',
                pagamento_tipo=pagamento_tipo
            )
            db.session.add(nova_reserva)
            db.session.commit()
            
            flash('Reserva realizada com sucesso! (Pagamento hipotético)', 'success')
            return redirect(url_for('minhas_reservas'))
        
        return render_template(
            'reservas/reservar.html',
            quadra=quadra,
            data_escolhida=data_escolhida,
            horarios_possiveis=horarios_possiveis,
            horarios_reservados=horarios_reservados
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
        
        # Verifica se a reserva é do usuário atual
        if reserva.usuario_id != current_user.id:
            flash('Você não tem permissão para cancelar esta reserva!', 'danger')
            return redirect(url_for('minhas_reservas'))
        
        # Verifica se já está cancelada
        if reserva.status == 'cancelada':
            flash('Esta reserva já foi cancelada!', 'warning')
            return redirect(url_for('minhas_reservas'))
        
        # Cancela a reserva
        reserva.status = 'cancelada'
        db.session.commit()
        
        flash('Reserva cancelada com sucesso!', 'success')
        return redirect(url_for('minhas_reservas'))
