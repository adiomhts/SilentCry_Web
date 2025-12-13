from flask import Flask, render_template, request, redirect, url_for, session
from flask_babel import Babel, _
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
import os
import logging
import bleach
from telegram import Bot
import asyncio

app = Flask(__name__)
app.config['BABEL_DEFAULT_LOCALE'] = 'cs'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
app.config['SECRET_KEY'] = 'github'
app.config['WTF_CSRF_ENABLED'] = True

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('app')

# Инициализация Telegram-бота
# TELEGRAM_BOT_TOKEN = 'token'
# TELEGRAM_CHAT_ID = '0000'
# telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

babel = Babel(app)

def get_locale():
    if 'lang' in request.args:
        lang = request.args.get('lang')
        if lang in ['cs', 'en', 'ru']:
            session['lang'] = lang
            logger.debug(f"Language set to: {lang}")
        else:
            lang = session.get('lang', app.config['BABEL_DEFAULT_LOCALE'])
            logger.debug(f"Invalid lang in request, using session/default: {lang}")
    else:
        lang = session.get('lang', app.config['BABEL_DEFAULT_LOCALE'])
        logger.debug(f"No lang in request, using session/default: {lang}")
    return lang

babel.init_app(app, locale_selector=get_locale)

# Форма для запроса выступления
class PerformanceRequestForm(FlaskForm):
    name = StringField(_('Jméno'), validators=[DataRequired()])
    email = StringField(_('Email'), validators=[DataRequired(), Email()])
    date = StringField(_('Datum vystoupení'), validators=[DataRequired()])
    location = StringField(_('Místo'), validators=[DataRequired()])
    details = TextAreaField(_('Další podrobnosti'))
    submit = SubmitField(_('Odeslat žádost'))

@app.route('/')
def index():
    lang = get_locale()
    logger.debug(f"Rendering index.html with locale: {lang}")
    return render_template('index.html', lang=lang)

@app.route('/request', methods=['GET', 'POST'])
def request_performance():
    lang = get_locale()
    form = PerformanceRequestForm()
    if request.method == 'POST' and form.validate_on_submit():
        name = bleach.clean(form.name.data)
        email = bleach.clean(form.email.data)
        date = bleach.clean(form.date.data)
        location = bleach.clean(form.location.data)
        details = bleach.clean(form.details.data)
        
        with open('requests.txt', 'a') as f:
            f.write(f"Name: {name}, Email: {email}, Date: {date}, Location: {location}, Details: {details}\n")
        
        # message = (
        #     f"Новый запрос на выступление:\n"
        #     f"Имя: {name}\n"
        #     f"Email: {email}\n"
        #     f"Дата: {date}\n"
        #     f"Место: {location}\n"
        #     f"Детали: {details or 'Нет'}"
        # )
        #
        # try:
        #     asyncio.run(telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message))
        #     logger.debug("Сообщение успешно отправлено в Telegram")
        # except Exception as e:
        #     logger.error(f"Ошибка при отправке в Telegram: {e}")

        return redirect(url_for('index'))
    logger.debug(f"Rendering request.html with locale: {lang}")
    return render_template('request.html', form=form, lang=lang)

@app.route('/lyrics')
def lyrics():
    lang = get_locale()
    lyrics_dir = os.path.join(app.static_folder, 'lyrics')
    descriptions_dir = os.path.join(lyrics_dir, 'descriptions')
    lyrics_files = [f for f in os.listdir(lyrics_dir) if f.endswith('.txt')]
    lyrics_content = {}
    for file in lyrics_files:
        with open(os.path.join(lyrics_dir, file), 'r', encoding='utf-8') as f:
            content = f.read()
        
        description_file = f"{file.replace('.txt', '')}_description.txt"
        description_path = os.path.join(descriptions_dir, description_file)
        description = ''
        if os.path.exists(description_path):
            with open(description_path, 'r', encoding='utf-8') as f:
                description = f.read()
        
        lyrics_content[file] = {'content': content, 'description': description}
    
    logger.debug(f"Rendering lyrics.html with locale: {lang}")
    return render_template('lyrics.html', lyrics_content=lyrics_content, lang=lang)

@app.route('/gallery')
def gallery():
    gallery_dir = os.path.join(app.static_folder, 'gallery')
    images = [f for f in os.listdir(gallery_dir) if f.endswith(('.jpg', '.png', '.webp')) and f != 'IMG_3209.webp']
    return render_template('gallery.html', gallery_images=images, lang=get_locale())

@app.route('/store')
def store():
    merch_items = [
        {
            'name': _('Black Logo T-Shirt'),
            'main_image': 'img/merch/tshirt-black/main.jpg',
            'gallery': [
                'img/merch/tshirt-black/main.jpg',
                'img/merch/tshirt-black/front.jpg',
                'img/merch/tshirt-black/back.jpg',
                'img/merch/tshirt-black/detail.jpg'
            ],
            'description': _('T-shirt with "Silent Cry" prints')
        },
        {
            'name': _('Coffee Mug'),
            'main_image': 'img/merch/mug/main.jpg',
            'gallery': [
                'img/merch/mug/main.jpg'
            ],
            'description': _('Mug with logo')
        },
        {
            'name': _('Stickers Pack'),
            'main_image': 'img/merch/stickers/main.jpg',
            'gallery': [
                'img/merch/stickers/main.jpg'
            ],
            'description': _('Set of stickers with band designs')
        }
    ]
    return render_template('store.html', merch_items=merch_items, lang=get_locale())

if __name__ == '__main__':
    app.run(debug=False)