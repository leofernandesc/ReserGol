from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from models import db
from models.quadra_model import Quadra
from models.reserva_model import Reserva
from datetime import datetime, timedelta, date, time

class ReservaController:
    
    @staticmethod
    @login_required
    def reservar(quadra_id):
        quadra = Quadra.query.get_or_404(quadra_id)
        
        if not quadra.ativa:
            flash('Esta quadra não está disponível para reservas!', 'danger')
            return redirect(url_for('listar_quadras'))
        
        # Data escolhida ou hoje
        data_escolhida = request.form.get('data', date.today().isoformat())
        try:
            data_obj = datetime.strptime(data_escolhida, '%Y-%m-%d').date()
        except:
            data_obj = date.today()
        
        # Validar se data não é no passado
        if data_obj < date.today():
            flash('Não é possível reservar datas passadas!', 'danger')
            data_obj = date.today()
        
        # Limitar a 30 dias no futuro
        data_limite = date.today() + timedelta(days=30)
        if data_obj > data_limite:
            flash('Reservas limitadas aos próximos 30 dias!', 'danger')
            data_obj = data_limite
        
        # Gerar horários disponíveis (6h às 23h)
        horarios_possiveis = []
        for hora in range(6, 23):
            horario_str = f'{hora:02d}:00'
            horarios_possiveis.append(horario_str)
        
        # Buscar reservas ativas e canceladas neste dia
        reservas_neste_dia = Reserva.query.filter_by(
            quadra_id=quadra.id,
            data=data_obj
        ).all()
        
        # Horários já reservados (ativas)
        horarios_reservados = set()
        for reserva in reservas_neste_dia:
            if reserva.status == 'ativa':
                horarios_reservados.add(reserva.hora_inicio.strftime('%H:%M'))
        
        # Horários disponíveis
        horarios_disponiveis = [h for h in horarios_possiveis if h not in horarios_reservados]
        
        # Processar formulário POST
        if request.method == 'POST' and request.form.get('hora'):
            hora_str = request.form.get('hora')
            
            # Validar horário
            if hora_str not in horarios_disponiveis:
                flash('Este horário não está mais disponível!', 'danger')
                return redirect(url_for('reservar_quadra', quadra_id=quadra_id))
            
            try:
                hora_inicio = datetime.strptime(hora_str, '%H:%M').time()
                hora_fim = (datetime.combine(date.today(), hora_inicio) + timedelta(hours=1)).time()
                
                # Verificar conflito novamente
                conflito = Reserva.query.filter(
                    Reserva.quadra_id == quadra.id,
                    Reserva.data == data_obj,
                    Reserva.hora_inicio == hora_inicio,
                    Reserva.status == 'ativa'
                ).first()
                
                if conflito:
                    flash('Este horário foi reservado por outro usuário! Tente outro.', 'warning')
                    return redirect(url_for('reservar_quadra', quadra_id=quadra_id))
                
                # Criar nova reserva
                nova_reserva = Reserva(
                    quadra_id=quadra.id,
                    usuario_id=current_user.id,
                    data=data_obj,
                    hora_inicio=hora_inicio,
                    hora_fim=hora_fim,
                    status='ativa'
                )
                db.session.add(nova_reserva)
                db.session.commit()
                
                flash(f'Reserva realizada com sucesso! Quadra: {quadra.nome}, Data: {data_obj.strftime("%d/%m/%Y")}, Horário: {hora_str}', 'success')
                return redirect(url_for('minhas_reservas'))
            
            except Exception as e:
                flash(f'Erro ao realizar reserva: {str(e)}', 'danger')
                return redirect(url_for('reservar_quadra', quadra_id=quadra_id))
        
        # Preparar dados para template
        horarios_dict = [
            {
                'horario': h,
                'disponivel': h in horarios_disponiveis
            }
            for h in horarios_possiveis
        ]
        
        # Calcular data máxima (30 dias a partir de hoje)
        data_maxima = (date.today() + timedelta(days=30)).isoformat()
        
        return render_template('reservas/reservar.html',
                             quadra=quadra,
                             data_escolhida=data_escolhida,
                             data_maxima=data_maxima,
                             horarios=horarios_dict,
                             horarios_disponiveis=horarios_disponiveis)
    
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
        
        # Só pode cancelar reservas futuras
        if reserva.data < date.today():
            flash('Não é possível cancelar reservas passadas!', 'danger')
            return redirect(url_for('minhas_reservas'))
        
        reserva.status = 'cancelada'
        db.session.commit()
        flash('Reserva cancelada com sucesso!', 'success')
        return redirect(url_for('minhas_reservas'))
