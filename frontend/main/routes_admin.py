from flask import Blueprint, render_template, request, redirect, url_for
from models.stock import StockModel
from models.dashboard_admin import DashboardAdm


admin_stock = Blueprint('admin_stock', __name__, url_prefix='/admin/stock')


@admin_stock.route('/')
def index():
    stocks = StockModel.get_all()
    rule_count = DashboardAdm.get_rule_count()

    return render_template('admin/stock/index.html', stocks=stocks, rule_count=rule_count)


@admin_stock.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        StockModel.create(request.form)
        return redirect(url_for('admin_stock.index'))

    return render_template('admin/stock/create.html')


@admin_stock.route('/edit/<int:id>')
def edit(id):
    stock = StockModel.get_by_id(id)
    return render_template('admin/stock/edit.html', stock=stock)


@admin_stock.route('/update/<int:id>', methods=['POST'])
def update(id):
    StockModel.update(id, request.form)
    return redirect(url_for('admin_stock.index'))


@admin_stock.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    StockModel.delete(id)
    return redirect(url_for('admin_stock.index'))




