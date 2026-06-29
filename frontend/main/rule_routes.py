from flask import Blueprint, render_template, request, redirect, url_for
from models.rule import RuleModel

admin_rule = Blueprint('admin_rule', __name__, url_prefix='/admin/rule')


@admin_rule.route('/')
def index():
    rules = RuleModel.get_all()
    return render_template('admin/rule/index.html', rules=rules)


@admin_rule.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        RuleModel.create(request.form)
        return redirect(url_for('admin_rule.index'))

    return render_template('admin/rule/create.html')


@admin_rule.route('/edit/<int:id>')
def edit(id):
    rule = RuleModel.get_by_id(id)
    return render_template('admin/rule/edit.html', rule=rule)


@admin_rule.route('/update/<int:id>', methods=['POST'])
def update(id):
    RuleModel.update(id, request.form)
    return redirect(url_for('admin_rule.index'))


@admin_rule.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    RuleModel.delete(id)
    return redirect(url_for('admin_rule.index'))