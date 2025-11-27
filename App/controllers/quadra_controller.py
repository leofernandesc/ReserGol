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

    # ============================================
    # MÉTODOS DE ADMINISTRAÇÃO (ADMIN ONLY)
    # ============================================
    
    @staticmethod
    @login_required
    def admin_listar_quadras():
        """Admin visualiza todas as quadras do sistema"""
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        # Filtros
        filtro_tipo = request.args.get('tipo', 'todos')
        filtro_status = request.args.get('status', 'todos')
        filtro_busca = request.args.get('busca', '')
        
        # Query base
        query = Quadra.query
        
        # Aplica filtros
        if filtro_tipo != 'todos':
            query = query.filter_by(tipo=filtro_tipo)
        
        if filtro_status != 'todos':
            query = query.filter_by(ativa=(filtro_status == 'ativa'))
        
        if filtro_busca:
            query = query.filter(Quadra.nome.ilike(f'%{filtro_busca}%') | Quadra.endereco.ilike(f'%{filtro_busca}%'))
        
        quadras = query.all()
        
        return render_template('admin/quadras_admin.html',
                             quadras=quadras,
                             filtro_tipo=filtro_tipo,
                             filtro_status=filtro_status,
                             filtro_busca=filtro_busca)

    @staticmethod
    @login_required
    def admin_cadastrar_quadra():
        """Admin cadastra uma nova quadra"""
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
            
            if not nome or not endereco or not tipo or not preco_hora or not dono_id:
                flash('Preencha todos os campos obrigatórios!', 'danger')
                return redirect(url_for('admin_cadastrar_quadra'))
            
            # Valida se o dono existe e é dono de quadra
            from models.usuario_model import Usuario
            dono = Usuario.query.get(int(dono_id))
            if not dono or not dono.is_dono_quadra():
                flash('Dono inválido! Selecione um usuário com permissão de dono.', 'danger')
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
        
        # Lista donos disponíveis
        from models.usuario_model import Usuario
        donos = Usuario.query.filter_by(role='dono_quadra').all()
        
        return render_template('admin/cadastrar_quadra_admin.html', donos=donos)

    @staticmethod
    @login_required
    def admin_editar_quadra(quadra_id):
        """Admin edita uma quadra existente"""
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
                from models.usuario_model import Usuario
                dono = Usuario.query.get(int(dono_id))
                if dono and dono.is_dono_quadra():
                    quadra.dono_id = int(dono_id)
                else:
                    flash('Dono inválido!', 'danger')
                    return redirect(url_for('admin_editar_quadra', quadra_id=quadra_id))
            
            db.session.commit()
            flash('Quadra atualizada com sucesso!', 'success')
            return redirect(url_for('admin_quadras'))
        
        # Lista donos disponíveis
        from models.usuario_model import Usuario
        donos = Usuario.query.filter_by(role='dono_quadra').all()
        
        return render_template('admin/editar_quadra_admin.html', quadra=quadra, donos=donos)

    @staticmethod
    @login_required
    def admin_remover_quadra(quadra_id):
        """Admin remove uma quadra"""
        if not current_user.is_admin():
            flash('Acesso negado!', 'danger')
            return redirect(url_for('index'))
        
        quadra = Quadra.query.get_or_404(quadra_id)
        
        db.session.delete(quadra)
        db.session.commit()
        flash('Quadra removida com sucesso!', 'success')
        return redirect(url_for('admin_quadras'))
