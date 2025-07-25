# Классификатор музыкальных жанров

Это веб-приложение для автоматического определения жанра музыки по аудиофайлу. Проект был разработан в рамках производственной практики в СПбПУ.

## Запуск

Для запуска проекта вам понадобится **Docker**.

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/TamaraGG/music-genre-classifier.git
    cd music-genre-classifier
    ```

2.  **Запустите все сервисы:**
    ```bash
    docker-compose up --build
    ```

3.  **Откройте приложение:**
    Перейдите в браузере по адресу `http://localhost:80`

## Архитектура и технологии

Проект использует микросервисную архитектуру:

-   **`ai-service`** (Python, Flask, TensorFlow) — обрабатывает аудио и выполняет предсказания.
-   **`backend`** (Java, Spring Boot) — основной сервер приложения.
-   **`frontend`** (HTML, CSS, JS) — пользовательский интерфейс.
-   **`database`** (PostgreSQL) — хранит историю запросов.

## Модель машинного обучения

Используется гибридная модель: сверточная-рекуррентная сеть (CRNN) извлекает признаки из аудио, а классификатор XGBoost определяет жанр. Точность модели на тестовых данных составляет **~65%**.
