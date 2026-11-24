import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy.exc import IntegrityError
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

ALUNO_NOME = 'Matheus Quadros Leal dos Santos'
ALUNO_PRONTUARIO = 'PT3036103'

# Disciplinas disponíveis no formulário (ordem do enunciado).
DISCIPLINAS = ['DSWA5', 'GPSA5', 'IHCA5', 'SODA5', 'PJIA5', 'TCOA5']

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or \
    'pt3036103-avaliacao-semestral'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'avaliacao.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)


class Disciplina(db.Model):
    __tablename__ = 'disciplinas'
    id = db.Column(db.Integer, primary_key=True)
    sigla = db.Column(db.String(16), unique=True, nullable=False)
    professores = db.relationship('Professor', backref='disciplina',
                                  lazy='dynamic')

    def __repr__(self):
        return '<Disciplina %r>' % self.sigla


class Professor(db.Model):
    __tablename__ = 'professores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), nullable=False)
    disciplina_id = db.Column(db.Integer, db.ForeignKey('disciplinas.id'),
                              nullable=False)

    def __repr__(self):
        return '<Professor %r>' % self.nome


class ProfessorForm(FlaskForm):
    nome = StringField('Cadastre o novo Professor:',
                       validators=[DataRequired(), Length(max=64)])
    disciplina = SelectField('Disciplina associada:', coerce=int)
    submit = SubmitField('Cadastrar')


def init_db():
    """Cria as tabelas (se não existirem) e garante as disciplinas."""
    db.create_all()
    for sigla in DISCIPLINAS:
        if Disciplina.query.filter_by(sigla=sigla).first() is None:
            db.session.add(Disciplina(sigla=sigla))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


with app.app_context():
    init_db()


@app.route('/')
def index():
    return render_template(
        'index.html',
        nome=ALUNO_NOME,
        prontuario=ALUNO_PRONTUARIO,
        current_time=datetime.utcnow(),
    )


@app.route('/professores', methods=['GET', 'POST'], strict_slashes=False)
def professores():
    form = ProfessorForm()
    form.disciplina.choices = [
        (d.id, d.sigla) for d in Disciplina.query.order_by(Disciplina.id).all()
    ]

    if form.validate_on_submit():
        nome = form.nome.data.strip()
        disciplina = db.session.get(Disciplina, form.disciplina.data)
        ja_existe = Professor.query.filter_by(
            nome=nome, disciplina_id=disciplina.id).first()
        if ja_existe:
            flash('Este professor já está cadastrado nessa disciplina.')
        else:
            db.session.add(Professor(nome=nome, disciplina=disciplina))
            db.session.commit()
            flash('Professor cadastrado com sucesso!')
        return redirect(url_for('professores'))

    lista = Professor.query.order_by(Professor.id).all()
    return render_template('professores.html', form=form, professores=lista)


# Tratamento de erros. Os módulos não desenvolvidos (disciplinas, alunos,
# cursos, ocorrências) NÃO têm rota: o link cai no 404 e mostra
# "Não disponível".
@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def erro_interno(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
