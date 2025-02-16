from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gymtracker.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)

class Routine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class RoutineExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    routine_id = db.Column(db.Integer, db.ForeignKey('routine.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/add_exercise', methods=['GET', 'POST'])
@login_required
def add_exercise():
    if request.method == 'POST':
        name = request.form['name']
        new_exercise = Exercise(name=name, user_id=current_user.id)
        db.session.add(new_exercise)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_exercise.html')

@app.route('/view_exercises')
@login_required
def view_exercises():
    exercises = Exercise.query.filter_by(user_id=current_user.id).all()
    return render_template('view_exercises.html', exercises=exercises)

@app.route('/exercise/<int:exercise_id>')
@login_required
def exercise(exercise_id):
    records = Record.query.filter_by(exercise_id=exercise_id).all()
    exercise = Exercise.query.get_or_404(exercise_id)
    return render_template('exercise.html', records=records, exercise_name=exercise.name, exercise_id=exercise_id)

@app.route('/add_record/<int:exercise_id>', methods=['GET', 'POST'])
@login_required
def add_record(exercise_id):
    if request.method == 'POST':
        date = request.form['date']
        sets = request.form['sets']
        reps = request.form['reps']
        weight = request.form['weight']
        new_record = Record(exercise_id=exercise_id, date=date, sets=sets, reps=reps, weight=weight)
        db.session.add(new_record)
        db.session.commit()
        return redirect(url_for('exercise', exercise_id=exercise_id))
    return render_template('add_record.html', exercise_id=exercise_id)

@app.route('/delete_exercise/<int:exercise_id>', methods=['POST'])
@login_required
def delete_exercise(exercise_id):
    Exercise.query.filter_by(id=exercise_id, user_id=current_user.id).delete()
    Record.query.filter_by(exercise_id=exercise_id).delete()
    db.session.commit()
    return redirect(url_for('view_exercises'))

@app.route('/add_routine', methods=['GET', 'POST'])
@login_required
def add_routine():
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        exercise_ids = request.form.getlist('exercise_id')
        sets_list = request.form.getlist('sets')
        reps_list = request.form.getlist('reps')
        weight_list = request.form.getlist('weight')

        new_routine = Routine(name=name, date=date, user_id=current_user.id)
        db.session.add(new_routine)
        db.session.commit()

        for i, exercise_id in enumerate(exercise_ids):
            new_routine_exercise = RoutineExercise(
                routine_id=new_routine.id,
                exercise_id=exercise_id,
                sets=sets_list[i],
                reps=reps_list[i],
                weight=weight_list[i]
            )
            db.session.add(new_routine_exercise)

        db.session.commit()
        return redirect(url_for('index'))

    exercises = Exercise.query.filter_by(user_id=current_user.id).all()
    return render_template('add_routine.html', exercises=exercises)

@app.route('/view_routines')
@login_required
def view_routines():
    routines = Routine.query.filter_by(user_id=current_user.id).all()
    return render_template('view_routines.html', routines=routines)

@app.route('/routine/<int:routine_id>')
@login_required
def routine(routine_id):
    routine = Routine.query.get_or_404(routine_id)
    routine_exercises = RoutineExercise.query.filter_by(routine_id=routine.id).all()
    
    exercise_details = []
    for routine_exercise in routine_exercises:
        exercise = Exercise.query.get(routine_exercise.exercise_id)
        exercise_details.append({
            'name': exercise.name,
            'sets': routine_exercise.sets,
            'reps': routine_exercise.reps,
            'weight': routine_exercise.weight
        })
    
    return render_template('routine.html', routine=routine, exercise_details=exercise_details)



@app.route('/edit_routine/<int:routine_id>', methods=['GET', 'POST'])
@login_required
def edit_routine(routine_id):
    routine = Routine.query.get_or_404(routine_id)
    if request.method == 'POST':
        routine.name = request.form['name']
        routine.date = request.form['date']
        db.session.commit()

        RoutineExercise.query.filter_by(routine_id=routine.id).delete()
        exercise_ids = request.form.getlist('exercise_id')
        sets_list = request.form.getlist('sets')
        reps_list = request.form.getlist('reps')
        weight_list = request.form.getlist('weight')

        for i, exercise_id in enumerate(exercise_ids):
            new_routine_exercise = RoutineExercise(
                routine_id=routine.id,
                exercise_id=exercise_id,
                sets=sets_list[i],
                reps=reps_list[i],
                weight=weight_list[i]
            )
            db.session.add(new_routine_exercise)

        db.session.commit()
        return redirect(url_for('view_routines'))

    exercises = Exercise.query.filter_by(user_id=current_user.id).all()
    routine_exercises = RoutineExercise.query.filter_by(routine_id=routine.id).all()
    return render_template('edit_routine.html', routine=routine, exercises=exercises, routine_exercises=routine_exercises)


@app.route('/delete_routine/<int:routine_id>', methods=['POST'])
@login_required
def delete_routine(routine_id):
    Routine.query.filter_by(id=routine_id).delete()
    RoutineExercise.query.filter_by(routine_id=routine_id).delete()
    db.session.commit()
    return redirect(url_for('view_routines'))


@app.route('/toggle_theme', methods=['POST'])
@login_required
def toggle_theme():
    session['dark_mode'] = not session.get('dark_mode', False)
    return '', 204

if __name__ == '__main__':
    app.secret_key = 'supersecretkey'
    with app.app_context():
        db.create_all()
    app.run(debug=True)







