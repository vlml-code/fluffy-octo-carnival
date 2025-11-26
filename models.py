from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


# Ассоциативная таблица для связи подкатегорий и персонажей
subcategory_characters = db.Table('subcategory_characters',
    db.Column('subcategory_id', db.Integer, db.ForeignKey('subcategories.id'), primary_key=True),
    db.Column('character_id', db.Integer, db.ForeignKey('characters.id'), primary_key=True)
)


class Category(db.Model):
    """Главная категория рассказа"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subcategories = db.relationship('Subcategory', backref='category', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_premium': self.is_premium,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Subcategory(db.Model):
    """Подкатегория - основа истории"""
    __tablename__ = 'subcategories'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Настройки персонажей
    num_characters_min = db.Column(db.Integer, default=1)
    num_characters_max = db.Column(db.Integer, default=1)

    # JSON структура для определения персонажей (legacy, для обратной совместимости)
    # Формат: [{"gender": "м/ж/небинарный", "age_min": int, "age_max": int, "can_have_initiative": bool}]
    character_specs = db.Column(db.Text, default='[]')

    # JSON список ID персонажей из таблицы characters
    character_ids = db.Column(db.Text, default='[]')

    # JSON настройки выбранных персонажей
    # Формат: [{"character_id": int, "allowed_age_groups": [str], "is_primary": bool, "follow_primary_age": bool}]
    character_settings = db.Column(db.Text, default='[]')

    # Настройки перспективы
    # Формат: ["первое_лицо", "третье_лицо", "переключение"]
    allowed_perspectives = db.Column(db.Text, default='["третье_лицо"]')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с персонажами (many-to-many)
    characters = db.relationship('Character', secondary=subcategory_characters, back_populates='subcategories')

    def get_character_specs(self):
        return json.loads(self.character_specs) if self.character_specs else []

    def set_character_specs(self, specs):
        self.character_specs = json.dumps(specs, ensure_ascii=False)

    def get_allowed_perspectives(self):
        return json.loads(self.allowed_perspectives) if self.allowed_perspectives else []

    def set_allowed_perspectives(self, perspectives):
        self.allowed_perspectives = json.dumps(perspectives, ensure_ascii=False)

    def get_character_ids(self):
        """Получить список ID персонажей"""
        return json.loads(self.character_ids) if self.character_ids else []

    def set_character_ids(self, ids):
        """Установить список ID персонажей"""
        self.character_ids = json.dumps(ids, ensure_ascii=False)

    def get_character_settings(self):
        return json.loads(self.character_settings) if self.character_settings else []

    def set_character_settings(self, settings):
        self.character_settings = json.dumps(settings, ensure_ascii=False)

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'num_characters_min': self.num_characters_min,
            'num_characters_max': self.num_characters_max,
            'character_specs': self.get_character_specs(),
            'character_ids': self.get_character_ids(),
            'character_settings': self.get_character_settings(),
            'characters': [c.to_dict() for c in self.characters],
            'allowed_perspectives': self.get_allowed_perspectives(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Character(db.Model):
    """Шаблон персонажа для рассказов"""
    __tablename__ = 'characters'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Роль/название персонажа
    description = db.Column(db.Text)  # Описание роли
    gender = db.Column(db.String(50), nullable=False)  # мужской, женский, небинарный
    age_min = db.Column(db.Integer, default=18)
    age_max = db.Column(db.Integer, default=60)
    can_have_initiative = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с подкатегориями (many-to-many)
    subcategories = db.relationship('Subcategory', secondary=subcategory_characters, back_populates='characters')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'gender': self.gender,
            'age_min': self.age_min,
            'age_max': self.age_max,
            'can_have_initiative': self.can_have_initiative,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CharacterTraitType(db.Model):
    """Тип характеристики персонажа (например, длина волос, темперамент)"""
    __tablename__ = 'character_trait_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    # Применимость по полу
    applies_to_male = db.Column(db.Boolean, default=True)
    applies_to_female = db.Column(db.Boolean, default=True)
    applies_to_nonbinary = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    trait_values = db.relationship('CharacterTraitValue', backref='trait_type', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'applies_to_male': self.applies_to_male,
            'applies_to_female': self.applies_to_female,
            'applies_to_nonbinary': self.applies_to_nonbinary,
            'values': [v.to_dict() for v in self.trait_values],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CharacterTraitValue(db.Model):
    """Возможное значение для типа характеристики"""
    __tablename__ = 'character_trait_values'

    id = db.Column(db.Integer, primary_key=True)
    trait_type_id = db.Column(db.Integer, db.ForeignKey('character_trait_types.id'), nullable=False)
    value = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'trait_type_id': self.trait_type_id,
            'value': self.value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Country(db.Model):
    """Страна для места действия"""
    __tablename__ = 'countries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class LocationType(db.Model):
    """Тип места (большой город, маленький город, сельская местность)"""
    __tablename__ = 'location_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Location(db.Model):
    """Конкретное место действия"""
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Tone(db.Model):
    """Тон рассказа"""
    __tablename__ = 'tones'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DialogueStyle(db.Model):
    """Стиль диалогов"""
    __tablename__ = 'dialogue_styles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
