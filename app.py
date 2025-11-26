from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import (
    db, Category, Subcategory, CharacterTraitType, CharacterTraitValue,
    Country, LocationType, Location, Tone, DialogueStyle
)
from generator import StoryPromptGenerator
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///story_generator.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

db.init_app(app)


# ============= WEB ROUTES =============

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/categories')
def categories_page():
    """Страница управления категориями"""
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)


@app.route('/subcategories')
def subcategories_page():
    """Страница управления подкатегориями"""
    subcategories = Subcategory.query.all()
    categories = Category.query.all()
    return render_template('subcategories.html', subcategories=subcategories, categories=categories)


@app.route('/character-traits')
def character_traits_page():
    """Страница управления характеристиками персонажей"""
    trait_types = CharacterTraitType.query.all()
    return render_template('character_traits.html', trait_types=trait_types)


@app.route('/locations')
def locations_page():
    """Страница управления локациями"""
    countries = Country.query.all()
    location_types = LocationType.query.all()
    locations = Location.query.all()
    return render_template('locations.html',
                          countries=countries,
                          location_types=location_types,
                          locations=locations)


@app.route('/tones')
def tones_page():
    """Страница управления тонами"""
    tones = Tone.query.all()
    return render_template('tones.html', tones=tones)


@app.route('/dialogue-styles')
def dialogue_styles_page():
    """Страница управления стилями диалогов"""
    dialogue_styles = DialogueStyle.query.all()
    return render_template('dialogue_styles.html', dialogue_styles=dialogue_styles)


@app.route('/generate')
def generate_page():
    """Страница генерации промпта"""
    return render_template('generate.html')


# ============= API ENDPOINTS =============

# Categories API
@app.route('/api/categories', methods=['GET', 'POST'])
def api_categories():
    if request.method == 'POST':
        data = request.json
        category = Category(
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(category)
        db.session.commit()
        return jsonify(category.to_dict()), 201

    categories = Category.query.all()
    return jsonify([c.to_dict() for c in categories])


@app.route('/api/categories/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_category(id):
    category = Category.query.get_or_404(id)

    if request.method == 'DELETE':
        db.session.delete(category)
        db.session.commit()
        return '', 204

    if request.method == 'PUT':
        data = request.json
        category.name = data['name']
        category.description = data.get('description', '')
        db.session.commit()
        return jsonify(category.to_dict())

    return jsonify(category.to_dict())


# Subcategories API
@app.route('/api/subcategories', methods=['GET', 'POST'])
def api_subcategories():
    if request.method == 'POST':
        data = request.json
        subcategory = Subcategory(
            category_id=data['category_id'],
            name=data['name'],
            description=data.get('description', ''),
            num_characters_min=data.get('num_characters_min', 1),
            num_characters_max=data.get('num_characters_max', 1)
        )
        subcategory.set_character_specs(data.get('character_specs', []))
        subcategory.set_allowed_perspectives(data.get('allowed_perspectives', ['третье_лицо']))
        db.session.add(subcategory)
        db.session.commit()
        return jsonify(subcategory.to_dict()), 201

    subcategories = Subcategory.query.all()
    return jsonify([s.to_dict() for s in subcategories])


@app.route('/api/subcategories/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_subcategory(id):
    subcategory = Subcategory.query.get_or_404(id)

    if request.method == 'DELETE':
        db.session.delete(subcategory)
        db.session.commit()
        return '', 204

    if request.method == 'PUT':
        data = request.json
        subcategory.category_id = data['category_id']
        subcategory.name = data['name']
        subcategory.description = data.get('description', '')
        subcategory.num_characters_min = data.get('num_characters_min', 1)
        subcategory.num_characters_max = data.get('num_characters_max', 1)
        subcategory.set_character_specs(data.get('character_specs', []))
        subcategory.set_allowed_perspectives(data.get('allowed_perspectives', ['третье_лицо']))
        db.session.commit()
        return jsonify(subcategory.to_dict())

    return jsonify(subcategory.to_dict())


# Character Trait Types API
@app.route('/api/character-trait-types', methods=['GET', 'POST'])
def api_character_trait_types():
    if request.method == 'POST':
        data = request.json
        trait_type = CharacterTraitType(
            name=data['name'],
            applies_to_male=data.get('applies_to_male', True),
            applies_to_female=data.get('applies_to_female', True),
            applies_to_nonbinary=data.get('applies_to_nonbinary', True)
        )
        db.session.add(trait_type)
        db.session.commit()
        return jsonify(trait_type.to_dict()), 201

    trait_types = CharacterTraitType.query.all()
    return jsonify([t.to_dict() for t in trait_types])


@app.route('/api/character-trait-types/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_character_trait_type(id):
    trait_type = CharacterTraitType.query.get_or_404(id)

    if request.method == 'DELETE':
        db.session.delete(trait_type)
        db.session.commit()
        return '', 204

    if request.method == 'PUT':
        data = request.json
        trait_type.name = data['name']
        trait_type.applies_to_male = data.get('applies_to_male', True)
        trait_type.applies_to_female = data.get('applies_to_female', True)
        trait_type.applies_to_nonbinary = data.get('applies_to_nonbinary', True)
        db.session.commit()
        return jsonify(trait_type.to_dict())

    return jsonify(trait_type.to_dict())


# Character Trait Values API
@app.route('/api/character-trait-values', methods=['POST'])
def api_character_trait_values_create():
    data = request.json
    trait_value = CharacterTraitValue(
        trait_type_id=data['trait_type_id'],
        value=data['value']
    )
    db.session.add(trait_value)
    db.session.commit()
    return jsonify(trait_value.to_dict()), 201


@app.route('/api/character-trait-values/<int:id>', methods=['DELETE'])
def api_character_trait_value_delete(id):
    trait_value = CharacterTraitValue.query.get_or_404(id)
    db.session.delete(trait_value)
    db.session.commit()
    return '', 204


# Countries API
@app.route('/api/countries', methods=['GET', 'POST'])
def api_countries():
    if request.method == 'POST':
        data = request.json
        country = Country(name=data['name'])
        db.session.add(country)
        db.session.commit()
        return jsonify(country.to_dict()), 201

    countries = Country.query.all()
    return jsonify([c.to_dict() for c in countries])


@app.route('/api/countries/<int:id>', methods=['DELETE'])
def api_country_delete(id):
    country = Country.query.get_or_404(id)
    db.session.delete(country)
    db.session.commit()
    return '', 204


# Location Types API
@app.route('/api/location-types', methods=['GET', 'POST'])
def api_location_types():
    if request.method == 'POST':
        data = request.json
        location_type = LocationType(name=data['name'])
        db.session.add(location_type)
        db.session.commit()
        return jsonify(location_type.to_dict()), 201

    location_types = LocationType.query.all()
    return jsonify([l.to_dict() for l in location_types])


@app.route('/api/location-types/<int:id>', methods=['DELETE'])
def api_location_type_delete(id):
    location_type = LocationType.query.get_or_404(id)
    db.session.delete(location_type)
    db.session.commit()
    return '', 204


# Locations API
@app.route('/api/locations', methods=['GET', 'POST'])
def api_locations():
    if request.method == 'POST':
        data = request.json
        location = Location(
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(location)
        db.session.commit()
        return jsonify(location.to_dict()), 201

    locations = Location.query.all()
    return jsonify([l.to_dict() for l in locations])


@app.route('/api/locations/<int:id>', methods=['DELETE', 'PUT'])
def api_location(id):
    location = Location.query.get_or_404(id)

    if request.method == 'DELETE':
        db.session.delete(location)
        db.session.commit()
        return '', 204

    if request.method == 'PUT':
        data = request.json
        location.name = data['name']
        location.description = data.get('description', '')
        db.session.commit()
        return jsonify(location.to_dict())


# Tones API
@app.route('/api/tones', methods=['GET', 'POST'])
def api_tones():
    if request.method == 'POST':
        data = request.json
        tone = Tone(
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(tone)
        db.session.commit()
        return jsonify(tone.to_dict()), 201

    tones = Tone.query.all()
    return jsonify([t.to_dict() for t in tones])


@app.route('/api/tones/<int:id>', methods=['DELETE', 'PUT'])
def api_tone(id):
    tone = Tone.query.get_or_404(id)

    if request.method == 'DELETE':
        db.session.delete(tone)
        db.session.commit()
        return '', 204

    if request.method == 'PUT':
        data = request.json
        tone.name = data['name']
        tone.description = data.get('description', '')
        db.session.commit()
        return jsonify(tone.to_dict())


# Dialogue Styles API
@app.route('/api/dialogue-styles', methods=['GET', 'POST'])
def api_dialogue_styles():
    if request.method == 'POST':
        data = request.json
        dialogue_style = DialogueStyle(
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(dialogue_style)
        db.session.commit()
        return jsonify(dialogue_style.to_dict()), 201

    dialogue_styles = DialogueStyle.query.all()
    return jsonify([d.to_dict() for d in dialogue_styles])


@app.route('/api/dialogue-styles/<int:id>', methods=['DELETE', 'PUT'])
def api_dialogue_style(id):
    dialogue_style = DialogueStyle.query.get_or_404(id)

    if request.method == 'DELETE':
        db.session.delete(dialogue_style)
        db.session.commit()
        return '', 204

    if request.method == 'PUT':
        data = request.json
        dialogue_style.name = data['name']
        dialogue_style.description = data.get('description', '')
        db.session.commit()
        return jsonify(dialogue_style.to_dict())


# Generate Prompt API
@app.route('/api/generate-prompt', methods=['POST'])
def api_generate_prompt():
    generator = StoryPromptGenerator(db.session)
    prompt = generator.generate_prompt()
    return jsonify({'prompt': prompt})


# ============= DATABASE INITIALIZATION =============

def init_db():
    """Инициализация базы данных с примерами данных"""
    with app.app_context():
        db.create_all()

        # Проверяем, есть ли уже данные
        if Category.query.first():
            print("База данных уже содержит данные")
            return

        # Создаем примеры категорий
        cat1 = Category(name="Романтика", description="Истории о любви и отношениях")
        cat2 = Category(name="Приключения", description="Захватывающие приключенческие истории")
        cat3 = Category(name="Драма", description="Глубокие драматические истории")

        db.session.add_all([cat1, cat2, cat3])
        db.session.commit()

        # Создаем подкатегории
        subcat1 = Subcategory(
            category_id=cat1.id,
            name="Первая любовь",
            description="История о первой юношеской любви",
            num_characters_min=2,
            num_characters_max=2
        )
        subcat1.set_character_specs([
            {
                "gender": "мужской",
                "age_min": 16,
                "age_max": 20,
                "can_have_initiative": True,
                "role": "Главный герой",
                "role_description": "Молодой человек, впервые влюбляющийся"
            },
            {
                "gender": "женский",
                "age_min": 16,
                "age_max": 20,
                "can_have_initiative": True,
                "role": "Возлюбленная",
                "role_description": "Девушка, в которую влюбляется главный герой"
            }
        ])
        subcat1.set_allowed_perspectives(["первое_лицо", "третье_лицо"])

        subcat2 = Subcategory(
            category_id=cat2.id,
            name="Поиск сокровищ",
            description="Группа искателей приключений ищет древнее сокровище",
            num_characters_min=3,
            num_characters_max=5
        )
        subcat2.set_character_specs([
            {
                "gender": "мужской",
                "age_min": 25,
                "age_max": 45,
                "can_have_initiative": True,
                "role": "Лидер экспедиции",
                "role_description": "Опытный искатель приключений, возглавляющий группу"
            },
            {
                "gender": "женский",
                "age_min": 25,
                "age_max": 45,
                "can_have_initiative": True,
                "role": "Эксперт",
                "role_description": "Специалист по древним артефактам"
            },
            {
                "gender": "мужской",
                "age_min": 18,
                "age_max": 30,
                "can_have_initiative": False,
                "role": "Новичок",
                "role_description": "Молодой участник экспедиции без опыта"
            }
        ])
        subcat2.set_allowed_perspectives(["третье_лицо", "переключение"])

        db.session.add_all([subcat1, subcat2])
        db.session.commit()

        # Создаем типы характеристик
        trait_hair = CharacterTraitType(
            name="Длина волос",
            applies_to_male=True,
            applies_to_female=True,
            applies_to_nonbinary=True
        )
        db.session.add(trait_hair)
        db.session.commit()

        # Значения для длины волос
        hair_values = ["короткие", "средние", "длинные", "очень длинные", "лысый/ая"]
        for val in hair_values:
            db.session.add(CharacterTraitValue(trait_type_id=trait_hair.id, value=val))

        trait_temper = CharacterTraitType(
            name="Темперамент",
            applies_to_male=True,
            applies_to_female=True,
            applies_to_nonbinary=True
        )
        db.session.add(trait_temper)
        db.session.commit()

        temper_values = ["холерик", "сангвиник", "флегматик", "меланхолик"]
        for val in temper_values:
            db.session.add(CharacterTraitValue(trait_type_id=trait_temper.id, value=val))

        # Создаем страны
        countries_list = ["Россия", "США", "Франция", "Япония", "Италия", "Германия", "Испания"]
        for country_name in countries_list:
            db.session.add(Country(name=country_name))

        # Создаем типы локаций
        location_types_list = ["Большой город", "Маленький город", "Сельская местность"]
        for lt_name in location_types_list:
            db.session.add(LocationType(name=lt_name))

        # Создаем конкретные места
        locations_list = [
            {"name": "Кафе", "description": "Уютное маленькое кафе в центре города"},
            {"name": "Парк", "description": "Большой городской парк с аллеями"},
            {"name": "Библиотека", "description": "Старая библиотека с редкими книгами"},
            {"name": "Пляж", "description": "Песчаный пляж у моря"},
            {"name": "Школа", "description": "Обычная средняя школа"},
        ]
        for loc in locations_list:
            db.session.add(Location(name=loc["name"], description=loc["description"]))

        # Создаем тоны
        tones_list = [
            {"name": "Романтический", "description": "Мягкий и нежный тон повествования"},
            {"name": "Напряженный", "description": "Держит читателя в напряжении"},
            {"name": "Юмористический", "description": "Легкий и веселый тон"},
            {"name": "Меланхоличный", "description": "Грустный и задумчивый тон"},
        ]
        for tone in tones_list:
            db.session.add(Tone(name=tone["name"], description=tone["description"]))

        # Создаем стили диалогов
        dialogue_styles_list = [
            {"name": "Естественный", "description": "Диалоги как в реальной жизни"},
            {"name": "Формальный", "description": "Вежливые и официальные диалоги"},
            {"name": "Разговорный", "description": "Непринужденный разговорный стиль"},
            {"name": "Поэтичный", "description": "Красивые литературные диалоги"},
        ]
        for style in dialogue_styles_list:
            db.session.add(DialogueStyle(name=style["name"], description=style["description"]))

        db.session.commit()
        print("База данных успешно инициализирована с примерами данных!")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
