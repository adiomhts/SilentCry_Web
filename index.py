from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_babel import Babel, _
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
import os
import logging
import bleach
from telegram import Bot
import asyncio
import re
import unicodedata

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

# --- Releases configuration -------------------------------------------------
# Map release display name -> list of lyric filenames (names as on disk inside lyrics/)
# Keep filenames exactly as they appear in the `lyrics` directory.
RELEASES = {
    # single 'Insomnie'
    'Insomnie (single)': ['insomnie.txt'],
    # single 'Bludný kruh' (example: contains 4 songs)
    'Bludný kruh (single)': ['silent cry.txt', 'insomnie.txt', 'green deal.txt', 'bludný kruh.txt'],
}


def slugify(text: str) -> str:
    """Create a simple ASCII-friendly slug from text or filename.

    Examples: 'Insomnie' -> 'insomnie', 'bludný kruh.txt' -> 'bludny-kruh'
    """
    text = text.lower()
    # remove extension
    text = re.sub(r"\.[^.]+$", "", text)
    # replace non-alnum with hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip('-')
    return text


# Build mappings: slug -> filename and filename -> slug
def build_slug_maps(releases: dict):
    slug_to_file = {}
    file_to_slug = {}
    for rel, files in releases.items():
        for fname in files:
            s = slugify(fname)
            # ensure uniqueness (append index if collision)
            original = s
            i = 1
            while s in slug_to_file and slug_to_file[s] != fname:
                s = f"{original}-{i}"
                i += 1
            slug_to_file[s] = fname
            file_to_slug[fname] = s
    return slug_to_file, file_to_slug


SLUG_TO_FILE, FILE_TO_SLUG = build_slug_maps(RELEASES)


def _strip_parentheses(text: str) -> str:
    # remove parenthetical parts like '(single)'
    return re.sub(r"\([^)]*\)", "", text).strip()


def _ascii_normalize(text: str) -> str:
    # lowercase, remove diacritics, collapse spaces
    nf = unicodedata.normalize('NFKD', text)
    ascii_text = nf.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r"[^a-z0-9 ]+", " ", ascii_text.lower()).strip()


def find_cover_for_release(release_name: str):
    """Try to find a cover image filename in static/img/albums that matches the release name.

    Matching strategy:
    - try slugified release name (hyphens)
    - try simple ascii-normalized tokens: check if all words of release base name appear in image filename
    - fallback to None
    Returns the relative static path (e.g. 'img/albums/bludny kruh.jpg') or None
    """
    img_dir = os.path.join(app.static_folder, 'img', 'albums')
    if not os.path.exists(img_dir):
        return None

    # candidates: slug, base name
    base = _strip_parentheses(release_name)
    slug = slugify(release_name)
    # first try slug match
    for ext in ('.webp', '.jpg', '.jpeg', '.png'):
        p = os.path.join(img_dir, f"{slug}{ext}")
        if os.path.exists(p):
            return os.path.relpath(p, app.static_folder).replace('\\', '/')

    # then try ascii token match
    target = _ascii_normalize(base)
    target_tokens = [t for t in target.split() if t]
    for fname in os.listdir(img_dir):
        name_lower = _ascii_normalize(os.path.splitext(fname)[0])
        if all(tok in name_lower.split() for tok in target_tokens):
            return os.path.relpath(os.path.join(img_dir, fname), app.static_folder).replace('\\', '/')

    return None

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
    if not os.path.exists(lyrics_dir):
        lyrics_dir = os.path.join(app.root_path, 'lyrics')
    descriptions_dir = os.path.join(lyrics_dir, 'descriptions')

    releases_info = []
    for rel_name, files in RELEASES.items():
        songs = []
        for fname in files:
            song_slug = FILE_TO_SLUG.get(fname) or slugify(fname)
            audio_mp3 = os.path.join(app.static_folder, 'audio', f"{fname.replace('.txt', '.mp3')}")
            audio_flac = os.path.join(app.static_folder, 'audio', f"{fname.replace('.txt', '.flac')}")
            has_audio = os.path.exists(audio_mp3) or os.path.exists(audio_flac)
            release_slug = slugify(rel_name)
            cover_candidates = []
            img_dir = os.path.join(app.static_folder, 'img', 'albums')
            # try a smarter cover lookup
            cover = find_cover_for_release(rel_name)
            if cover:
                cover_candidates.append(cover)
            songs.append({'filename': fname, 'slug': song_slug, 'has_audio': has_audio})



        cover = cover_candidates[0] if cover_candidates else None
        releases_info.append({'name': rel_name, 'slug': slugify(rel_name), 'songs': songs, 'cover': cover})

    logger.debug(f"Rendering lyrics.html with locale: {lang}")
    return render_template('lyrics.html', releases=releases_info, lang=lang)


@app.route('/player/<release_slug>')
def player(release_slug):
    """Render a single player page for a whole release. Optional query param 'song' to start at a specific song slug."""
    lang = get_locale()
    # find release by slug
    release_name = None
    for rel in RELEASES.keys():
        if slugify(rel) == release_slug:
            release_name = rel
            break
    if not release_name:
        logger.warning(f"Unknown release slug: {release_slug}")
        return redirect(url_for('lyrics'))

    # locate files and preload lyrics/description
    lyrics_dir = os.path.join(app.static_folder, 'lyrics')
    if not os.path.exists(lyrics_dir):
        lyrics_dir = os.path.join(app.root_path, 'lyrics')

    playlist = []
    for fname in RELEASES[release_name]:
        slug = FILE_TO_SLUG.get(fname) or slugify(fname)
        # read lyrics
        lyrics_text = ''
        fpath = os.path.join(lyrics_dir, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r', encoding='utf-8') as fh:
                    lyrics_text = fh.read()
            except Exception as e:
                logger.error(f"Failed to read {fpath}: {e}")

        # read description
        desc = ''
        desc_file = f"{fname.replace('.txt', '')}_description.txt"
        desc_path = os.path.join(lyrics_dir, 'descriptions', desc_file)
        if os.path.exists(desc_path):
            try:
                with open(desc_path, 'r', encoding='utf-8') as fh:
                    desc = fh.read()
            except Exception as e:
                logger.error(f"Failed to read {desc_path}: {e}")

        audio_mp3 = url_for('static', filename=f"audio/{fname.replace('.txt', '.mp3')}")
        audio_flac = url_for('static', filename=f"audio/{fname.replace('.txt', '.flac')}")
        has_audio = os.path.exists(os.path.join(app.static_folder, 'audio', f"{fname.replace('.txt', '.mp3')}")) or \
                    os.path.exists(os.path.join(app.static_folder, 'audio', f"{fname.replace('.txt', '.flac')}"))

        playlist.append({
            'filename': fname,
            'slug': slug,
            'title': fname.replace('.txt', ''),
            'lyrics': lyrics_text,
            'description': desc,
            'audio_mp3': audio_mp3,
            'audio_flac': audio_flac,
            'has_audio': has_audio,
        })

    # cover: use smarter finder (handles diacritics/spaces)
    cover = find_cover_for_release(release_name)

    # initial index if song query param provided
    start_song = request.args.get('song')
    start_index = 0
    if start_song:
        for i, item in enumerate(playlist):
            if item['slug'] == start_song:
                start_index = i
                break

    return render_template('lyrics_player.html', playlist=playlist, current_index=start_index,
                           title=playlist[start_index]['title'] if playlist else '', lyrics=playlist[start_index]['lyrics'] if playlist else '',
                           description=playlist[start_index]['description'] if playlist else '', audio_mp3=playlist[start_index]['audio_mp3'] if playlist else '',
                           audio_flac=playlist[start_index]['audio_flac'] if playlist else '', release_name=release_name, release_cover=cover, lang=lang)

@app.route('/gallery')
def gallery():
    gallery_dir = os.path.join(app.static_folder, 'gallery')
    images = [f for f in os.listdir(gallery_dir) if f.endswith(('.jpg', '.png', '.webp')) and f != 'IMG_3209.webp']
    return render_template('gallery.html', gallery_images=images, lang=get_locale())


@app.route('/lyrics/<song_slug>')
def lyrics_player(song_slug):
    lang = get_locale()
    # resolve slug -> filename
    fname = SLUG_TO_FILE.get(song_slug)
    if not fname:
        # try to infer by slugifying filenames found in RELEASES
        for s, f in SLUG_TO_FILE.items():
            if s == song_slug:
                fname = f
                break
    if not fname:
        logger.warning(f"Lyrics player: unknown song slug {song_slug}")
        return redirect(url_for('lyrics'))

    # locate lyrics file
    lyrics_dir = os.path.join(app.static_folder, 'lyrics')
    if not os.path.exists(lyrics_dir):
        lyrics_dir = os.path.join(app.root_path, 'lyrics')

    lyrics_path = os.path.join(lyrics_dir, fname)
    lyrics_text = ''
    if os.path.exists(lyrics_path):
        try:
            with open(lyrics_path, 'r', encoding='utf-8') as f:
                lyrics_text = f.read()
        except Exception as e:
            logger.error(f"Failed to read lyrics for {fname}: {e}")

    # description
    descriptions_dir = os.path.join(lyrics_dir, 'descriptions')
    desc = ''
    desc_file = f"{fname.replace('.txt', '')}_description.txt"
    desc_path = os.path.join(descriptions_dir, desc_file)
    if os.path.exists(desc_path):
        try:
            with open(desc_path, 'r', encoding='utf-8') as f:
                desc = f.read()
        except Exception as e:
            logger.error(f"Failed to read description {desc_path}: {e}")

    # find release that contains this file and build playlist of slugs
    playlist = []
    release_cover = None
    release_name = None
    for rel, files in RELEASES.items():
        if fname in files:
            release_name = rel
            for f in files:
                s = FILE_TO_SLUG.get(f) or slugify(f)
                # check audio presence
                audio_mp3_p = os.path.join(app.static_folder, 'audio', f"{f.replace('.txt', '.mp3')}")
                audio_flac_p = os.path.join(app.static_folder, 'audio', f"{f.replace('.txt', '.flac')}")
                has_audio_flag = os.path.exists(audio_mp3_p) or os.path.exists(audio_flac_p)
                playlist.append({'filename': f, 'slug': s, 'title': f.replace('.txt', ''), 'has_audio': has_audio_flag})
            # attempt to find cover using robust finder (handles diacritics/spaces)
            release_cover = find_cover_for_release(rel)
            break

    # compute indexes for navigation
    current_index = next((i for i, s in enumerate(playlist) if s['slug'] == song_slug), 0)
    prev_slug = playlist[current_index - 1]['slug'] if current_index > 0 else None
    next_slug = playlist[current_index + 1]['slug'] if current_index < len(playlist) - 1 else None

    # audio URLs
    audio_mp3 = url_for('static', filename=f"audio/{fname.replace('.txt', '.mp3')}")
    audio_flac = url_for('static', filename=f"audio/{fname.replace('.txt', '.flac')}")

    logger.debug(f"Rendering lyrics_player for {fname} (slug={song_slug})")
    return render_template('lyrics_player.html', title=fname.replace('.txt', ''), lyrics=lyrics_text,
                           description=desc, audio_mp3=audio_mp3, audio_flac=audio_flac,
                           playlist=playlist, current_index=current_index, prev_slug=prev_slug,
                           next_slug=next_slug, release_name=release_name, release_cover=release_cover,
                           lang=lang)


@app.route('/lyrics/metadata/<song_slug>')
def lyrics_metadata(song_slug):
    """Return JSON metadata for a song (used by the player for dynamic updates)."""
    fname = SLUG_TO_FILE.get(song_slug)
    if not fname:
        return jsonify({'error': 'unknown song'}), 404

    # locate lyrics and description
    lyrics_dir = os.path.join(app.static_folder, 'lyrics')
    if not os.path.exists(lyrics_dir):
        lyrics_dir = os.path.join(app.root_path, 'lyrics')

    lyrics_text = ''
    lyrics_path = os.path.join(lyrics_dir, fname)
    if os.path.exists(lyrics_path):
        try:
            with open(lyrics_path, 'r', encoding='utf-8') as f:
                lyrics_text = f.read()
        except Exception:
            lyrics_text = ''

    desc = ''
    desc_file = f"{fname.replace('.txt', '')}_description.txt"
    desc_path = os.path.join(lyrics_dir, 'descriptions', desc_file)
    if os.path.exists(desc_path):
        try:
            with open(desc_path, 'r', encoding='utf-8') as f:
                desc = f.read()
        except Exception:
            desc = ''

    # find release
    release_name = None
    playlist = []
    release_cover = None
    for rel, files in RELEASES.items():
        if fname in files:
            release_name = rel
            for f in files:
                s = FILE_TO_SLUG.get(f) or slugify(f)
                audio_mp3 = url_for('static', filename=f"audio/{f.replace('.txt', '.mp3')}")
                audio_flac = url_for('static', filename=f"audio/{f.replace('.txt', '.flac')}")
                has_audio = os.path.exists(os.path.join(app.static_folder, 'audio', f"{f.replace('.txt', '.mp3')}")) or \
                            os.path.exists(os.path.join(app.static_folder, 'audio', f"{f.replace('.txt', '.flac')}"))
                playlist.append({'filename': f, 'slug': s, 'title': f.replace('.txt', ''), 'audio_mp3': audio_mp3, 'audio_flac': audio_flac, 'has_audio': has_audio})
            # cover
            img_dir = os.path.join(app.static_folder, 'img', 'albums')
            rel_slug = slugify(rel)
            if os.path.exists(img_dir):
                for ext in ('.webp', '.jpg', '.jpeg', '.png'):
                    p = os.path.join(img_dir, f"{rel_slug}{ext}")
                    if os.path.exists(p):
                        release_cover = os.path.relpath(p, app.static_folder).replace('\\', '/')
                        break
            break

    # build response
    resp = {
        'filename': fname,
        'slug': song_slug,
        'title': fname.replace('.txt', ''),
        'lyrics': lyrics_text,
        'description': desc,
        'release_name': release_name,
        'release_cover': release_cover,
        'playlist': playlist,
    }
    return jsonify(resp)

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
            'description': _('Black Logo T-Shirt')
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