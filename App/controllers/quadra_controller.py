from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.usuario_model import db
from models.quadra_model import Quadra

class QuadraController:
    
    @staticmethod
    def listar_quadras():
        """Lista todas as quadras ativas"""
        quadras = Quadra.query.filter_by(ativa=True).all()
        return render_template('quadras/listar.html', quadras=quadras)
    
    @staticmethod
    @login_required
    def minhas_quadras():
        """Dono visualiza suas próprias quadras"""
        if not current_user.is_dono_quadra():
            flash('Você precisa ser dono de quadra para acessar esta página!', 'danger')
            return redirect(url_for('index'))
        
        quadras = Quadra.query.filter_by(dono_id=current_user.id).all()
        return render_template('quadras/minhas_quadras.html', quadras=quadras)
    
    @staticmethod
    @login_required
    def cadastrar_quadra():
        """Dono cadastra uma nova quadra"""
        if not current_user.is_dono_quadra():
            flash('Você precisa ser dono de quadra para cadastrar!', 'danger')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            nome = request.form.get('nome')
            endereco = request.form.get('endereco')
            tipo = request.form.get('tipo')
            descricao = request.form.get('descricao')
            preco_hora = request.form.get('preco_hora')
            
            if not nome or not endereco or not tipo or not preco_hora:
                flash('Preencha todos os campos obrigatórios!', 'danger')
                return redirect(url_for('cadastrar_quadra'))
            
            nova_quadra = Quadra(
                nome=nome,
                endereco=endereco,
                tipo=tipo,
                descricao=descricao,
                preco_hora=float(preco_hora),
                dono_id=current_user.id
            )
            db.session.add(nova_quadra)
            db.session.commit()
            
            flash('Quadra cadastrada com sucesso!', 'success')
            return redirect(url_for('minhas_quadras'))
        
        return render_template('quadras/cadastrar.html')
    
    @staticmethod
    @login_required
    def editar_quadra(quadra_id):
        """Dono edita sua quadra"""
        quadra = Quadra.query.get_or_404(quadra_id)
        
        # Verifica se é o dono ou admin
        if quadra.dono_id != current_user.id and not current_user.is_admin():
            flash('Você não tem permissão para editar esta quadra!', 'danger')
            return redirect(url_for('minhas_quadras'))
        
        if request.method == 'POST':
            quadra.nome = request.form.get('nome')
            quadra.endereco = request.form.get('endereco')
            quadra.tipo = request.form.get('tipo')
            quadra.descricao = request.form.get('descricao')
            quadra.preco_hora = float(request.form.get('preco_hora'))
            
            db.session.commit()
            flash('Quadra atualizada com sucesso!', 'success')
            return redirect(url_for('minhas_quadras'))
        
        return render_template('quadras/editar.html', quadra=quadra)
    
    @staticmethod
    @login_required
    def deletar_quadra(quadra_id):
        """Dono deleta sua quadra"""
        quadra = Quadra.query.get_or_404(quadra_id)
        
        if quadra.dono_id != current_user.id and not current_user.is_admin():
            flash('Você não tem permissão para deletar esta quadra!', 'danger')
            return redirect(url_for('minhas_quadras'))
        
        db.session.delete(quadra)
        db.session.commit()
        flash('Quadra deletada com sucesso!', 'success')
        return redirect(url_for('minhas_quadras'))
    
    @staticmethod
    @login_required
    def ver_reservas_quadra(quadra_id):
        """Dono visualiza todas as reservas da sua quadra"""
        quadra = Quadra.query.get_or_404(quadra_id)
        
        # Verifica se é o dono ou admin
        if quadra.dono_id != current_user.id and not current_user.is_admin():
            flash('Você não tem permissão para visualizar estas reservas!', 'danger')
            return redirect(url_for('minhas_quadras'))
        
        from models.reserva_model import Reserva
        from datetime import datetime
        
        # Filtros
        filtro_status = request.args.get('status', 'todas')
        filtro_data = request.args.get('data', '')
        
        # Query base
        query = Reserva.query.filter_by(quadra_id=quadra_id)
        
        # Aplica filtros
        if filtro_status != 'todas':
            query = query.filter_by(status=filtro_status)
        
        if filtro_data:
            try:
                data_filtro = datetime.strptime(filtro_data, '%Y-%m-%d').date()
                query = query.filter_by(data=data_filtro)
            except:
                pass
        
        reservas = query.order_by(Reserva.data.desc(), Reserva.hora_inicio.desc()).all()
        
        return render_template('quadras/reservas_quadra.html', 
                             quadra=quadra, 
                             reservas=reservas,
                             filtro_status=filtro_status,
                             filtro_data=filtro_data)
    
    @staticmethod
    @login_required
    def gerenciar_horarios(quadra_id):
        """Dono gerencia horários disponíveis da quadra"""
        quadra = Quadra.query.get_or_404(quadra_id)
        
        # Verifica se é o dono ou admin
        if quadra.dono_id != current_user.id and not current_user.is_admin():
            flash('Você não tem permissão!', 'danger')
            return redirect(url_for('minhas_quadras'))
        
        from models.reserva_model import Reserva
        from datetime import datetime, timedelta
        
        # Pega próximos 7 dias
        hoje = datetime.utcnow().date()
        proximos_dias = [(hoje + timedelta(days=i)) for i in range(7)]
        
        # Conta reservas por dia
        estatisticas = []
        for dia in proximos_dias:
            total_reservas = Reserva.query.filter_by(
                quadra_id=quadra_id,
                data=dia,
                status='ativa'
            ).count()
            estatisticas.append({
                'data': dia,
                'reservas': total_reservas,
                'disponivel': 17 - total_reservas  # 6h-23h = 17 horários
            })
        
        return render_template('quadras/gerenciar_horarios.html',
                             quadra=quadra,
                             estatisticas=estatisticas)
    
    @staticmethod
    @login_required
    def cancelar_reserva_dono(reserva_id):
        """Dono cancela uma reserva da sua quadra"""
        from models.reserva_model import Reserva
        
        reserva = Reserva.query.get_or_404(reserva_id)
        
        # Verifica se é o dono da quadra ou admin
        if reserva.quadra.dono_id != current_user.id and not current_user.is_admin():
            flash('Você não tem permissão!', 'danger')
            return redirect(url_for('minhas_quadras'))
        
        if reserva.status == 'cancelada':
            flash('Esta reserva já foi cancelada!', 'warning')
            return redirect(url_for('ver_reservas_quadra', quadra_id=reserva.quadra_id))
        
        reserva.status = 'cancelada'
        db.session.commit()
        
        flash(f'Reserva de {reserva.usuario.nome} foi cancelada!', 'success')
        return redirect(url_for('ver_reservas_quadra', quadra_id=reserva.quadra_id))
