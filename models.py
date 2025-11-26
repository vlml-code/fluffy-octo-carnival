from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Category(db.Model):
    """Главная категория рассказа"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subcategories = db.relationship('Subcategory', backref='category', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
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

    # JSON структура для определения персонажей
    # Формат: [{"gender": "м/ж/небинарный", "age_min": int, "age_max": int, "can_have_initiative": bool}]
    character_specs = db.Column(db.Text, default='[]')

    # Настройки перспективы
    # Формат: ["первое_лицо", "третье_лицо", "переключение"]
    allowed_perspectives = db.Column(db.Text, default='["третье_лицо"]')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_character_specs(self):
        return json.loads(self.character_specs) if self.character_specs else []

    def set_character_specs(self, specs):
        self.character_specs = json.dumps(specs, ensure_ascii=False)

    def get_allowed_perspectives(self):
        return json.loads(self.allowed_perspectives) if self.allowed_perspectives else []

    def set_allowed_perspectives(self, perspectives):
        self.allowed_perspectives = json.dumps(perspectives, ensure_ascii=False)

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'num_characters_min': self.num_characters_min,
            'num_characters_max': self.num_characters_max,
            'character_specs': self.get_character_specs(),
            'allowed_perspectives': self.get_allowed_perspectives(),
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
