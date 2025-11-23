from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.usuario_model import db
from models.quadra_model import Quadra

class QuadraController:
    
    def listar_quadras():
        """Lista todas as quadras ativas"""
        quadras = Quadra.query.filter_by(ativa=True).all()
        return render_template('quadras/listar.html', quadras=quadras)
    
    @login_required
    def minhas_quadras():
        """Dono visualiza suas próprias quadras"""
        if not current_user.is_dono_quadra():
            flash('Você precisa ser dono de quadra para acessar esta página!', 'danger')
            return redirect(url_for('index'))
        
        quadras = Quadra.query.filter_by(dono_id=current_user.id).all()
        return render_template('quadras/minhas_quadras.html', quadras=quadras)
    
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
