from flask import Flask
from flask import redirect, Blueprint, render_template, request
from Db import db
from Db.models import users
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, login_required, current_user, logout_user
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

app = Flask(__name__)
app.secret_key = '123'
user_db = 'olga_rgz'
host_ip = '127.0.0.1'
host_port = '5434'
database_name = 'rgz_orm'
password = '123'

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user_db}:{password}@{host_ip}:{host_port}/{database_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_users(user_id):
    return users.query.get(int(user_id))

@app.route('/')
def glavnaya():
    if current_user.is_authenticated:
        username = current_user.username
    else:
        username = "Аноним"
    return render_template('index.html', username=username)


@app.route("/check")
def main():
    my_users = users.query.all()
    print(my_users)
    return "result in console!"

def save_photo(photo):
    # Генерируем уникальное имя файла
    if current_user.is_authenticated:
        photo_filename = str(photo.filename) + str(current_user.id)
    else:
        # Обработка для анонимного пользователя
        photo_filename = "anonymous_user_default_filename.jpg"
    
    # Определяем путь для сохранения файла
    photo_path = os.path.join('static', photo_filename)

    # Сохраняем файл на сервере
    photo.save(photo_path)

    # Возвращаем имя сохраненного файла
    return photo_filename

@app.route('/registr', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('glavnaya'))

    error = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']
        gender = request.form['gender']
        preferred_gender = request.form['preferred_gender']
        about = request.form['about']
        photo = request.files['photo']

        if not username:
            error = 'Заполните поле "Имя".'
        elif not password:
            error = 'Заполните поле "Пароль".'
        elif not age:
            error = 'Заполните поле "Возраст".'
        elif not gender:
            error = 'Выберите пол в поле "Пол".'
        elif not preferred_gender:
            error = 'Выберите пол для поиска в поле "Пол для поиска".'
        else:
            hashed_password = generate_password_hash(password)
            photo_filename = save_photo(photo)

            new_user = users(
                username=username,
                password=hashed_password,
                age=age,
                gender=gender,
                preferred_gender=preferred_gender,
                about=about,
                photo=photo_filename
            )

            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login'))

    return render_template('registr.html', error=error)


    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('glavnaya'))

    error = ''  # Инициализируем переменную error перед использованием

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users.query.filter_by(username=username).first()#поиск пользователя в базе данных по имени пользователя и получение 
        #первого совпадения с помощью метода first()

        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('glavnaya'))
            else:
                error = 'Неверный пароль'
        else:
            error = 'Пользователь не найден'

    return render_template('login.html', error_message=error)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/my_akk')
@login_required  #это декоратор, чтобы требовать аутентификации пользователя для доступа к этой странице
def my_akk():
    # Получение информации о текущем пользователе из объекта current_user
    user = current_user

    return render_template('my_akk.html', user=user)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user  # Получение информации о текущем пользователе

    if request.method == 'POST':
        # Обработка данных формы редактирования профиля
        user.username = request.form['username']
        user.age = int(request.form['age'])
        user.gender = request.form['gender']
        user.preferred_gender = request.form['preferred_gender']
        user.about = request.form['about']
        photo = request.files['photo']
        if photo:
            user.photo = save_photo(photo)

        db.session.commit()  # Сохранить изменения профиля пользователя в базе данных

        return redirect(url_for('my_akk'))

    return render_template('edit_profile.html', user=user)


@app.route('/hide_profile')#скрытие пофиля
@login_required
def hide_profile():
    user = current_user
    user.hidden = True
    db.session.commit()
    return redirect(url_for('my_akk'))

@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        # Удалите аккаунт пользователя из базы данных
        user_id = current_user.id
        deleted_user = users.query.get(user_id)

        db.session.delete(deleted_user)
        db.session.commit()

        logout_user()  # Выход из системы после удаления аккаунта
        return redirect(url_for('glavnaya'))

    return render_template('delete_account.html')


@app.route('/poisk', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        # Получаем новые параметры поиска из формы
        name = request.form['name']
        age = request.form['age']
    else:
        # Получаем текущую информацию о поиске из параметров запроса
        name = request.args.get('name')
        age = request.args.get('age')

    # Получаем пол для поиска из поля "пол для поиска" анкеты пользователя
    preferred_gender = current_user.preferred_gender

    # Формируем запрос к базе данных
    query = users.query.filter(users.gender == preferred_gender, users.hidden == False)

    if name:
        query = query.filter(users.username.ilike(f'%{name}%'))
    if age:
        query = query.filter(users.age == age)

    # Получаем текущую страницу поиска из параметров запроса
    offset = int(request.args.get('offset', 0))# используется для получения значения параметра "offset" из запроса. 
    #Если параметр присутствует в запросе, то будет возвращено его значение в виде строки. Если параметр отсутствует, 
    #то будет возвращено значение по умолчанию, то есть 0.

    # Применяем смещение для определения следующих результатов поиска
    query = query.offset(offset)

    # Ограничиваем количество результатов поиска до 3
    query = query.limit(3)

    results = query.all()

    return render_template('poisk.html', results=results, name=name, age=age, offset=offset + 3, show_previous=offset > 0)


@app.route('/unhide_profile')#видимость профиля
@login_required
def unhide_profile():
    user = current_user
    user.hidden = False
    db.session.commit()
    return redirect(url_for('my_akk'))