const elements = document.querySelectorAll('.animate-on-scroll');
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, { threshold: 0.2 });

elements.forEach(element => observer.observe(element));

// Плавная прокрутка для ссылок
document.querySelectorAll('.nav-bar a').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href.startsWith('#') && !href.includes('lang=')) {
            e.preventDefault();
            const targetId = href.substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 70,
                    behavior: 'smooth'
                });
            }
        }
    });
});

// Переключение языков
function switchLanguage(lang) {
    const url = new URL(window.location.href);
    url.hash = '';
    url.searchParams.set('lang', lang);
    window.location.href = url.toString();
}

// Применение уменьшенного размера шрифта для русского языка
function applyRussianFontSize() {
    const isRussian = window.currentLang === 'ru' || new URLSearchParams(window.location.search).get('lang') === 'ru';
    console.log('Checking language:', window.currentLang, 'URL lang:', new URLSearchParams(window.location.search).get('lang'), 'Is Russian:', isRussian);
    
    if (isRussian) {
        console.log('Russian language detected, applying font sizes');
        const navLinks = document.querySelectorAll('.nav-bar a');
        console.log('Found nav-bar links:', navLinks.length);
        navLinks.forEach(link => {
            const fontSize = window.innerWidth > 1120 ? '1rem' : '0.75rem';
            link.style.setProperty('font-size', fontSize, 'important');
            console.log(`Set font-size for nav-bar link: ${fontSize}`);
        });

        const burgerLinks = document.querySelectorAll('#burgerMenu a');
        console.log('Found burgerMenu links:', burgerLinks.length);
        burgerLinks.forEach(link => {
            link.style.setProperty('font-size', '0.9rem', 'important');
            console.log('Set font-size for burgerMenu link: 0.9rem');
        });
    } else {
        console.log('Non-Russian language, no font size changes applied');
    }
}

// Применяем стили при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    applyRussianFontSize();
    setTimeout(applyRussianFontSize, 100);
});

// Управление бургер-меню
if (window.innerWidth <= 1120) {
    document.getElementById('burgerBtn').addEventListener('click', function() {
        const menu = document.getElementById('burgerMenu');
        menu.classList.toggle('hidden');
    });

    document.addEventListener('click', function(event) {
        const burgerBtn = document.getElementById('burgerBtn');
        const burgerMenu = document.getElementById('burgerMenu');
        if (!burgerBtn.contains(event.target) && !burgerMenu.contains(event.target)) {
            burgerMenu.classList.add('hidden');
        }
    });
}

// Обновление поведения при изменении размера окна
window.addEventListener('resize', function() {
    const burgerMenu = document.getElementById('burgerMenu');
    if (window.innerWidth > 1120) {
        burgerMenu.classList.add('hidden');
    }
    applyRussianFontSize();
});

// Анимация элементов галереи
const galleryItems = document.querySelectorAll('.gallery-item');
const galleryObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, { threshold: 0.15 });

galleryItems.forEach(item => galleryObserver.observe(item));

// Обработка кликов по миниатюрам в мерче
document.querySelectorAll('.gallery-thumbnail').forEach(thumb => {
    thumb.addEventListener('click', function() {
        const mainImage = this.closest('.merch-item').querySelector('.main-image');
        mainImage.src = this.src;
    });
});

// Открытие изображения на весь экран
document.querySelectorAll('.gallery-image').forEach(img => {
    img.addEventListener('click', function() {
        const modal = document.getElementById('fullscreen-modal');
        const fullscreenImg = document.getElementById('fullscreen-image');
        fullscreenImg.src = this.src;
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    });
});

// Закрытие модального окна
document.getElementById('close-modal').addEventListener('click', function() {
    document.getElementById('fullscreen-modal').classList.add('hidden');
    document.body.style.overflow = '';
});

document.getElementById('fullscreen-modal').addEventListener('click', function(e) {
    if (e.target === this) {
        this.classList.add('hidden');
        document.body.style.overflow = '';
    }
});

document.querySelectorAll('.gallery-thumbnail').forEach(thumb => {
    thumb.addEventListener('click', function () {
        const container = this.closest('.merch-item');
        const mainImage = container.querySelector('.main-image');
        mainImage.src = this.src;

        // Удаляем активный класс у всех
        container.querySelectorAll('.gallery-thumbnail').forEach(t => t.classList.remove('active-thumb'));
        this.classList.add('active-thumb');
    });
});
