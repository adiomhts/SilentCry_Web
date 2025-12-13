# SilentCry_Web

## About the Project

`SilentCry_Web` is the official multilingual website for the music band **"Silent Cry"**. The project is a web application developed in **Python**.

## Technical Stack

### Core Framework
* **Flask:** A lightweight micro-framework for Python web applications.

### Key Libraries
* **Flask-Babel:** Used for multilingual support (i18n), allowing users to select between Czech (`cs`), English (`en`), and Russian (`ru`) languages.
* **Flask-WTF / WTForms:** Applied for creating and validating web forms, specifically for the performance request form.
* **Bleach:** Used for sanitizing user input from forms to prevent Cross-Site Scripting (XSS) attacks.
* **Pillow (PIL):** Used in the `thumbs.py` script for image processing and generating optimized WEBP gallery thumbnails.
* **Jinja2:** The templating engine used by Flask for rendering HTML pages.

### Data Storage
* Performance Requests are saved to a local text file named `requests.txt`.

## Functionality

* **Multilingualism:** Full support for interface localization.
* **Request Form:** Collects and saves performance requests with data validation and sanitization.
* **Content:** Sections for displaying song lyrics (`/lyrics`) and photos (`/gallery`).
* **Commerce:** A store page (`/store`) for presenting merchandise.
* **Integration (Optional):** Functionality is provided but commented out for sending new request notifications to **Telegram**.
