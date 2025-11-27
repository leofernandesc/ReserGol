from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.usuario_model import Usuario
from models.quadra_model import Quadra
from models.reserva_model import Reserva
from datetime import datetime, timedelta

class QuadraController:
    
    @staticmethod
    def listar_quadras():
        quadras = Quadra.query.filter_by(ativa=True).all()
        return render_template('quadras/listar.html', quadras=quadras)
    
    @staticmethod
    @login_required
    def minhas_quadras():
        if not current_user.is_dono_quadra():
            flash('Você precisa ser dono de quadra para acessar esta página!', 'danger')
            return redirect(url_for('index'))
        
        quadras = Quadra.query.filter_by(dono_id=current_user.id).all()
        return render_template('quadras/minhas_quadras.html', quadras=quadras)
    
    @staticmethod
    @login_required
    def cadastrar_quadra():
        if not current_user.is_dono_quadra():
            flash('Você precisa ser dono de quadra para cadastrar!', 'danger')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            nome = request.form.get('nome')
            endereco = request.form.get('endereco')
            tipo = request.form.get('tipo')
            descricao = request.form.get('descricao')
            preco_hora = request.form.get('preco_hora')
            
            if not all([nome, endereco, tipo, preco_hora]):
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
        quadra = Quadra.query.get_or_404(quadra_id)
        
        if quadra.dono_id != current_user.id and not current_user.is_admin():
            flash('Você não tem permissão!', 'danger')
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
        quadra = Quadra.query.get_or_404(quadra_id)
        
        if quadra.dono_id != current_user.id and not current_user.is_admin():
            flash('Você não tem permissão!', 'danger')
            return redirect(url_for('minhas_quadras'))
        
        db.session.delete(quadra)
        db.session.commit()
        flash('Quadra deletada com sucesso!', 'success')
        return redirect(url_for('minhas_quadras'))
    
    @staticmethod
    @login_required
    def ver_reservas_quadra(quadra_id):
        quadra = Quadra.query.get_or_404(quadra_id)
        
        if quadra.dono_id != current_user.id and not current_user.is_admin():
            flash('Você não tem permissão!', 'danger')
            return redirect(url_for('minhas_quadras'))
        
        filtro_status = request.args.get('status', 'todas')
        filtro_data = request.args.get('data', '')
        
        query = Reserva.query.filter_by(quadra_id=quadra_id)
        
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
        quadra = Quadra.query.get_or_404(quadra_id)
        
        if quadra.dono_id != current_user.id and not current_user.is_admin():
            flash('Você não tem permissão!', 'danger')
            return redirect(url_for('minhas_quadras'))
        
        hoje = datetime.utcnow().date()
        proximos_dias = [hoje + timedelta(days=i) for i in range(7)]
        
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
                'disponivel': 17 - total_reservas
            })
        
        return render_template('quadras/gerenciar_horarios.html',
                             quadra=quadra,
                             estatisticas=estatisticas)
    
    @staticmethod
    @login_required
    def cancelar_reserva_dono(reserva_id):
        reserva = Reserva.query.get_or_404(reserva_id)
        
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

    @staticmethod
    @login_required
    def gerenciar_horarios(quadra_id):
        """Dono gerencia horários disponíveis da quadra"""
        quadra = Quadra.query.get_or_404(quadra_id)
        
        if quadra.dono_id != current_user.id and not current_user.is_admin():
            flash('Você não tem permissão!', 'danger')
            return redirect(url_for('minhas_quadras'))
        
        # Próximos 30 dias
        hoje = date.today()
        proximos_dias = [hoje + timedelta(days=i) for i in range(30)]
        
        # Coletar estatísticas
        estatisticas = []
        for dia in proximos_dias:
            # Contar reservas ativas
            reservas_ativas = Reserva.query.filter_by(
                quadra_id=quadra_id,
                data=dia,
                status='ativa'
            ).count()
            
            total_horarios = 17  # 6h às 22h = 17 horários
            disponiveis = total_horarios - reservas_ativas
            percentual = (reservas_ativas / total_horarios) * 100
            
            estatisticas.append({
                'data': dia,
                'dia_semana': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom'][dia.weekday()],
                'reservas': reservas_ativas,
                'disponivel': disponiveis,
                'percentual': round(percentual, 1)
            })
        
        return render_template('quadras/gerenciar_horarios.html',
                             quadra=quadra,
                             estatisticas=estatisticas)
    
    # ===== ADMIN =====
    
    @staticmethod
    @login_required
    def admin_listar_quadras():
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        filtro_tipo = request.args.get('tipo', 'todos')
        filtro_status = request.args.get('status', 'todos')
        filtro_busca = request.args.get('busca', '')
        
        query = Quadra.query
        
        if filtro_tipo != 'todos':
            query = query.filter_by(tipo=filtro_tipo)
        
        if filtro_status != 'todos':
            query = query.filter_by(ativa=(filtro_status == 'ativa'))
        
        if filtro_busca:
            query = query.filter(
                (Quadra.nome.ilike(f'%{filtro_busca}%')) | 
                (Quadra.endereco.ilike(f'%{filtro_busca}%'))
            )
        
        quadras = query.all()
        
        return render_template('admin/quadras_admin.html',
                             quadras=quadras,
                             filtro_tipo=filtro_tipo,
                             filtro_status=filtro_status,
                             filtro_busca=filtro_busca)
    
    @staticmethod
    @login_required
    def admin_cadastrar_quadra():
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            nome = request.form.get('nome')
            endereco = request.form.get('endereco')
            tipo = request.form.get('tipo')
            descricao = request.form.get('descricao')
            preco_hora = request.form.get('preco_hora')
            dono_id = request.form.get('dono_id')
            
            if not all([nome, endereco, tipo, preco_hora, dono_id]):
                flash('Preencha todos os campos obrigatórios!', 'danger')
                return redirect(url_for('admin_cadastrar_quadra'))
            
            dono = Usuario.query.get(int(dono_id))
            if not dono or not dono.is_dono_quadra():
                flash('Dono inválido!', 'danger')
                return redirect(url_for('admin_cadastrar_quadra'))
            
            nova_quadra = Quadra(
                nome=nome,
                endereco=endereco,
                tipo=tipo,
                descricao=descricao,
                preco_hora=float(preco_hora),
                dono_id=int(dono_id)
            )
            db.session.add(nova_quadra)
            db.session.commit()
            
            flash('Quadra cadastrada com sucesso!', 'success')
            return redirect(url_for('admin_quadras'))
        
        donos = Usuario.query.filter_by(role='dono_quadra').all()
        return render_template('admin/cadastrar_quadra_admin.html', donos=donos)
    
    @staticmethod
    @login_required
    def admin_editar_quadra(quadra_id):
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        quadra = Quadra.query.get_or_404(quadra_id)
        
        if request.method == 'POST':
            quadra.nome = request.form.get('nome')
            quadra.endereco = request.form.get('endereco')
            quadra.tipo = request.form.get('tipo')
            quadra.descricao = request.form.get('descricao')
            quadra.preco_hora = float(request.form.get('preco_hora'))
            quadra.ativa = request.form.get('ativa') == 'on'
            
            dono_id = request.form.get('dono_id')
            if dono_id:
                dono = Usuario.query.get(int(dono_id))
                if dono and dono.is_dono_quadra():
                    quadra.dono_id = int(dono_id)
                else:
                    flash('Dono inválido!', 'danger')
                    return redirect(url_for('admin_editar_quadra', quadra_id=quadra_id))
            
            db.session.commit()
            flash('Quadra atualizada com sucesso!', 'success')
            return redirect(url_for('admin_quadras'))
        
        donos = Usuario.query.filter_by(role='dono_quadra').all()
        return render_template('admin/editar_quadra_admin.html', quadra=quadra, donos=donos)
    
    @staticmethod
    @login_required
    def admin_remover_quadra(quadra_id):
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        quadra = Quadra.query.get_or_404(quadra_id)
        db.session.delete(quadra)
        db.session.commit()
        flash('Quadra removida com sucesso!', 'success')
        return redirect(url_for('admin_quadras'))

    @staticmethod
    @login_required
    def admin_ver_reservas_quadra(quadra_id):
        """Admin visualiza todas as reservas de uma quadra"""
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        quadra = Quadra.query.get_or_404(quadra_id)
        
        filtro_status = request.args.get('status', 'todas')
        filtro_data = request.args.get('data', '')
        
        query = Reserva.query.filter_by(quadra_id=quadra_id)
        
        if filtro_status != 'todas':
            query = query.filter_by(status=filtro_status)
        
        if filtro_data:
            try:
                data_filtro = datetime.strptime(filtro_data, '%Y-%m-%d').date()
                query = query.filter_by(data=data_filtro)
            except:
                pass
        
        reservas = query.order_by(Reserva.data.desc(), Reserva.hora_inicio.desc()).all()
        
        return render_template('admin/reservas_quadra_admin.html', 
                             quadra=quadra, 
                             reservas=reservas,
                             filtro_status=filtro_status,
                             filtro_data=filtro_data)
    
    @staticmethod
    @login_required
    def admin_cancelar_reserva_quadra(quadra_id, reserva_id):
        """Admin cancela uma reserva de uma quadra"""
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        reserva = Reserva.query.get_or_404(reserva_id)
        
        if reserva.quadra_id != quadra_id:
            flash('Reserva não pertence a esta quadra!', 'danger')
            return redirect(url_for('admin_quadras'))
        
        if reserva.status == 'cancelada':
            flash('Esta reserva já foi cancelada!', 'warning')
            return redirect(url_for('admin_ver_reservas_quadra', quadra_id=quadra_id))
        
        reserva.status = 'cancelada'
        db.session.commit()
        flash(f'Reserva de {reserva.usuario.nome} foi cancelada!', 'success')
        return redirect(url_for('admin_ver_reservas_quadra', quadra_id=quadra_id))

