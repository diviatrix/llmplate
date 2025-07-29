# LLMplate Frontend Mock Plan

## 🎯 Обзор проекта

LLMplate - это система для генерации структурированных данных с использованием LLM моделей через OpenRouter и Ollama. Система включает мощную систему шаблонов на основе Jinja2.

### Роли пользователей:
- **Guest** (неавторизованный) - только просмотр о сайте, опубликованных результатов и регистрация
- **User** - авторизованный пользователь с доступом к платформе
- **Admin** (is_superuser=true) - администратор с расширенными правами

## 📱 Структура страниц

### 1. Публичные страницы

#### 1.1 Landing Page (`/`)
- Hero секция с описанием продукта
- Преимущества системы
- Примеры использования
- CTA кнопки (Sign Up, Sign In)
- Footer с ссылками

#### 1.2 Login Page (`/login`)
- Email/Password форма
- OAuth кнопки (Google, GitHub)
- Ссылка на регистрацию
- Восстановление пароля (заглушка)

#### 1.3 Register Page (`/register`)
- Форма регистрации (email, password, full name)
- Валидация пароля (мин. 8 символов, заглавные/строчные, цифры, спецсимволы)
- OAuth кнопки
- Ссылка на логин

#### 1.4 Public Results Gallery (`/public/results`)
- Список опубликованных результатов генераций
- Фильтры по категориям
- Поиск
- Просмотр результатов (read-only)
- Информация об авторе и дате публикации

#### 1.5 About Page (`/about`)
- Описание платформы
- Примеры использования
- Преимущества
- FAQ

#### 1.6 Documentation (`/docs`)
- Getting Started
- API Reference
- Template Syntax Guide
- Examples & Tutorials
- Troubleshooting

#### 1.7 Pricing (`/pricing`)
- Тарифные планы
- Сравнение возможностей
- Калькулятор стоимости
- FAQ по оплате

#### 1.8 Legal Pages
- Terms of Service (`/terms`)
- Privacy Policy (`/privacy`)
- Cookie Policy (`/cookies`)

#### 1.9 Support (`/support`)
- Contact форма
- FAQ
- Status page (заглушка)
- Community links

### 2. Авторизованная зона

#### 2.1 Dashboard (`/dashboard`)
- Статистика использования:
  - Количество созданных шаблонов
  - Количество генераций (всего/успешных/неудачных)
  - Потраченные токены
  - Общая стоимость
- Последние генерации
- Быстрые действия

#### 2.2 Templates Management (`/templates/my`)
- Список моих шаблонов
- Создание/редактирование/удаление
- Импорт из примеров
- Переключатель публичный/приватный

#### 2.3 Template Editor (`/templates/new`, `/templates/:id/edit`)
- **Режимы редактора:**
  - Visual Builder (default)
  - JSON Editor (advanced)
  - Переключение между режимами с сохранением данных
  
- **Visual Builder включает:**
  - **Основная информация:**
    - Название и описание (текстовые поля)
    - Категория (dropdown)
    - Теги (tag input с автокомплитом)
    
  - **Variables Builder:**
    - Drag & drop интерфейс для создания переменных
    - Типы полей: string, number, boolean, array, object
    - Для каждой переменной:
      - Имя (key)
      - Тип данных
      - Описание
      - Обязательность
      - Значение по умолчанию
      - Валидация (min/max для чисел, pattern для строк)
    - Визуальное дерево для вложенных объектов
    - Авто-генерация JSON Schema
    
  - **Prompts Builder:**
    - Две секции: System Prompt и User Prompt
    - Rich text editor с поддержкой Jinja2
    - Панель доступных переменных (drag to insert)
    - Подсветка синтаксиса переменных {{variable}}
    - Авто-подсказки при вводе {{
    - Preview с подстановкой тестовых значений
    
  - **Output Schema Builder:**
    - Визуальный конструктор JSON Schema
    - Предустановленные шаблоны схем
    - Drag & drop для структуры
    - Валидация схемы в реальном времени
    
  - **Настройки:**
    - Provider settings (temperature, max_tokens)
    - Validation mode selector
    - Custom validation rules editor
    - Public/Private toggle
    
- **JSON Editor режим:**
  - Monaco editor (VS Code editor)
  - Syntax highlighting
  - Auto-completion
  - Schema validation
  - Прямое редактирование всех полей
  
- **Live Preview панель:**
  - Разделенный экран
  - Тестовые данные для переменных
  - Rendered prompts preview
  - Ожидаемый output preview
  
- **Валидация в реальном времени:**
  - Проверка синтаксиса Jinja2
  - Проверка JSON Schema
  - Проверка использования переменных

#### 2.4 Generation Interface (`/generate`)
- Выбор режима: Single/Batch
- **Single mode:**
  - Выбор шаблона
  - Выбор провайдера (OpenRouter/Ollama)
  - Выбор модели с фильтрами:
    - По провайдеру
    - Бесплатные/платные
    - С доступом в интернет
  - Заполнение переменных
  - Количество генераций (1-100)
  - Кнопка запуска
- **Batch mode:**
  - Добавление нескольких заданий (до 10)
  - Для каждого задания:
    - Выбор шаблона
    - Выбор модели
    - Свои переменные
    - Количество генераций
  - Общий запуск всех заданий

#### 2.5 Generation Progress (`/generate/:jobId`)
- Прогресс бар
- Статус генерации
- Промежуточные результаты
- Кнопка отмены
- Информация о токенах и стоимости

#### 2.6 Generation Results (`/generate/:jobId/results`)
- Таблица/карточки с результатами
- Экспорт в форматы:
  - JSON
  - CSV
  - PDF
  - Excel
  - Markdown
  - HTML
  - XML
  - TXT
- Кнопка повторной генерации
- Кнопка "Опубликовать результаты" (сделать доступными для Guest)

#### 2.7 History (`/history`)
- Список всех генераций
- Фильтры:
  - По статусу
  - По шаблону
  - По дате
- Пагинация
- Быстрые действия

#### 2.8 Providers (`/providers`)
- Список доступных провайдеров
- Статус подключения
- Количество моделей
- Тест соединения

#### 2.9 Models Catalog (`/models`)
- Полный список моделей
- Фильтры:
  - По провайдеру
  - Бесплатные/платные
  - С интернетом
- Информация о модели:
  - Цены за токены
  - Возможности
  - Лимиты

#### 2.10 Profile (`/profile`)
- Информация о пользователе
- Смена пароля (для non-OAuth)
- OAuth привязки

### 3. Административная панель (для Admin)

#### 3.1 Admin Dashboard (`/admin`)
- Общая статистика системы
- Графики использования
- Активные задачи

#### 3.2 Users Management (`/admin/users`)
- Список пользователей
- Поиск и фильтры
- Изменение ролей
- Блокировка/разблокировка

#### 3.3 System Templates (`/admin/templates`)
- Управление примерами шаблонов
- Модерация публичных шаблонов

#### 3.4 System Settings (`/admin/settings`)
- Настройки провайдеров
- Лимиты и квоты
- Настройки безопасности

## 🧩 Компоненты UI

### Общие компоненты:
1. **Header**
   - Логотип
   - Навигация
   - User menu

2. **Sidebar** (для авторизованных)
   - Основная навигация
   - Быстрые действия
   - Статус подключений

3. **Footer**
   - Навигационные ссылки:
     - Product: About, Pricing, Docs
     - Legal: Terms, Privacy, Cookies
     - Support: Help, Contact, Status
   - Social links
   - Копирайт
   - Версия API

### Формы:
1. **AuthForm**
   - Email/Password поля
   - OAuth кнопки
   - Валидация

2. **TemplateForm**
   - Multi-step wizard
   - JSON editor для schemas
   - Markdown preview

3. **GenerationForm**
   - Dynamic fields по переменным
   - Model selector с фильтрами

### Таблицы и списки:
1. **DataTable**
   - Сортировка
   - Фильтрация
   - Пагинация
   - Bulk actions

2. **CardGrid**
   - Карточки шаблонов
   - Lazy loading
   - Фильтры

### Модальные окна:
1. **ConfirmDialog**
2. **ExportDialog**
3. **PreviewDialog**
4. **ErrorDialog**

### Специальные компоненты:
1. **ProgressTracker**
   - WebSocket подключение
   - Real-time обновления
   - Анимации

2. **CodeEditor**
   - Syntax highlighting
   - Auto-completion
   - Validation

3. **VisualTemplateBuilder**
   - Variables builder с drag & drop
   - Prompts editor с переменными
   - Output schema constructor
   - Real-time JSON generation
   - Полное соответствие Template model

## 🎨 Дизайн система

### Цветовая схема:
- Primary: #4CAF50 (зеленый)
- Secondary: #2196F3 (синий)
- Error: #f44336
- Warning: #ff9800
- Success: #4CAF50
- Info: #2196F3
- Background: #f5f5f5
- Surface: #ffffff
- Text Primary: #212121
- Text Secondary: #757575

### Типографика:
- Заголовки: Inter, system-ui
- Основной текст: Inter, system-ui
- Код: 'Fira Code', monospace

### Spacing:
- Base unit: 8px
- Padding: 8px, 16px, 24px, 32px
- Margin: то же

### Компоненты:
- Border radius: 4px (inputs), 8px (cards)
- Shadows: Material Design shadows
- Transitions: 200ms ease-in-out

## 🔄 User Flows

### 1. Guest просмотр результатов:
1. Landing → Public Results
2. Просмотр списка
3. Выбор результата
4. Просмотр деталей (read-only)
5. CTA для регистрации

### 2. Регистрация и первый вход:
1. Landing → Register
2. Заполнение формы
3. Подтверждение (заглушка)
4. Redirect на Dashboard
5. Onboarding tour

### 3. Создание шаблона:
1. Dashboard → Templates
2. New Template
3. Заполнение формы (wizard)
4. Валидация
5. Preview
6. Save

### 4. Генерация данных:
1. Dashboard → Generate
2. Выбор режима (Single/Batch)
3. Если Single:
   - Выбор шаблона
   - Выбор модели
   - Заполнение переменных
4. Если Batch:
   - Добавление заданий
   - Настройка каждого
5. Start generation
6. Progress tracking
7. View results
8. Export

### 5. Публикация результатов:
1. Generation Results → Publish button
2. Confirm dialog
3. Set public access
4. Get shareable link
5. Share or embed

### 6. OAuth flow:
1. Login → OAuth provider
2. Authorize
3. Callback
4. Create/update user
5. Redirect to Dashboard

## 📱 Responsive Design

### Breakpoints:
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

### Mobile адаптация:
- Hamburger menu
- Stack layouts
- Touch-friendly controls
- Swipe gestures
- Bottom sheets

## 🔌 Интеграции (моки)

### 1. API calls:
- Использовать fetch с mock responses
- Имитация задержек
- Обработка ошибок

### 2. Progress tracking:
- Polling через setInterval
- GET /generate/{job_id} каждые 2 секунды
- Остановка при статусе completed/failed/cancelled

### 3. OAuth:
- Redirect на mock pages
- Immediate callback

## 📊 Состояния и данные

### 1. Глобальное состояние:
- User info
- Auth token
- Active generations

### 2. Локальное состояние:
- Form data
- UI state (modals, drawers)
- Filters and sorting

### 3. Mock данные:
- 10-20 примеров шаблонов
- 5-10 примеров генераций
- Список моделей
- User profiles

## 🚀 Технологический стек для моков

### Основа:
- Pure HTML5
- CSS3 (с CSS Grid и Flexbox)
- Vanilla JavaScript (ES6+)

### Библиотеки (через CDN):
- Alpine.js для реактивности
- Tailwind CSS для стилей
- Prism.js для подсветки кода
- Chart.js для графиков
- Marked.js для markdown

### Инструменты:
- Local storage для состояния
- Service Worker для offline
- Progressive Web App

## 📝 TODO для реализации моков

1. Создать базовую структуру файлов
2. Реализовать компоненты
3. Создать все страницы
4. Добавить mock API
5. Реализовать навигацию
6. Добавить анимации
7. Тестирование на разных устройствах
8. Документация для разработчиков