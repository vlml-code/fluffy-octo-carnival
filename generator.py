import random
from models import (
    Category, Subcategory, CharacterTraitType,
    Country, LocationType, Location, Tone, DialogueStyle
)


class StoryPromptGenerator:
    """Генератор промптов для рассказов"""

    def __init__(self, db_session):
        self.db = db_session

    def generate_prompt(self):
        """Генерирует полный промпт для рассказа"""
        prompt_parts = []

        prompt_parts.append("Твоя задача написать рассказ.\n")

        # 1. Выбор категории
        category = self._select_random_category()
        if not category:
            return "Ошибка: нет категорий в базе данных"

        prompt_parts.append(f"\n## КАТЕГОРИЯ")
        prompt_parts.append(f"**{category.name}**")
        if category.description:
            prompt_parts.append(f"{category.description}")

        # 2. Выбор подкатегории
        subcategory = self._select_random_subcategory(category)
        if not subcategory:
            return f"Ошибка: нет подкатегорий для категории '{category.name}'"

        prompt_parts.append(f"\n## ПОДКАТЕГОРИЯ")
        prompt_parts.append(f"**{subcategory.name}**")
        if subcategory.description:
            prompt_parts.append(f"{subcategory.description}")

        # 3. Генерация персонажей
        characters = self._generate_characters(subcategory)

        # 4. Перспектива повествования (выбираем до отображения персонажей, чтобы пометить рассказчика)
        perspective_type, narrator_index = self._select_perspective(subcategory, characters)

        # Помечаем рассказчика
        if narrator_index is not None and characters:
            characters[narrator_index]["is_narrator"] = True

        # Отображаем персонажей
        if characters:
            prompt_parts.append(f"\n## ПЕРСОНАЖИ")
            for i, char in enumerate(characters, 1):
                prompt_parts.append(f"\n### Персонаж {i}")

                # Роль персонажа
                if char.get('role'):
                    prompt_parts.append(f"- Роль: {char['role']}")
                    if char.get('role_description'):
                        prompt_parts.append(f"  {char['role_description']}")

                prompt_parts.append(f"- Пол: {char['gender']}")
                prompt_parts.append(f"- Возраст: {char['age']}")

                # Помечаем рассказчика
                if char.get('is_narrator'):
                    prompt_parts.append(f"- **РАССКАЗЧИК** (повествование ведется от лица этого персонажа)")

                if char.get('has_initiative'):
                    prompt_parts.append(f"- Инициатива: Да (события происходят по воле этого персонажа)")
                else:
                    attitude = char.get('attitude', 'нейтральное')
                    prompt_parts.append(f"- Отношение к событиям: {attitude}")

                if char.get('traits'):
                    prompt_parts.append(f"- Характеристики:")
                    for trait_name, trait_value in char['traits'].items():
                        prompt_parts.append(f"  - {trait_name}: {trait_value}")

        prompt_parts.append(f"\n## ПЕРСПЕКТИВА ПОВЕСТВОВАНИЯ")
        prompt_parts.append(perspective_type)

        # 5. Второстепенные элементы
        secondary_elements = self._select_secondary_elements(category)
        if secondary_elements:
            prompt_parts.append(f"\n## ВТОРОСТЕПЕННЫЕ ЭЛЕМЕНТЫ")
            prompt_parts.append("(Опциональные элементы, которые могут быть включены в историю как дополнительные сюжетные линии, но не являются основным фокусом)")
            for elem in secondary_elements:
                prompt_parts.append(f"\n- **{elem['category']}**: {elem['subcategory']}")
                if elem.get('description'):
                    prompt_parts.append(f"  {elem['description']}")

        # 6. Место действия
        location_info = self._generate_location()
        if location_info:
            prompt_parts.append(f"\n## МЕСТО ДЕЙСТВИЯ")
            prompt_parts.append(f"- Страна: {location_info['country']}")
            prompt_parts.append(f"- Тип местности: {location_info['location_type']}")
            prompt_parts.append(f"- Место: {location_info['location']}")
            if location_info.get('location_description'):
                prompt_parts.append(f"  {location_info['location_description']}")

        # 7. Тон рассказа
        tone = self._select_random_tone()
        if tone:
            prompt_parts.append(f"\n## ТОН РАССКАЗА")
            prompt_parts.append(f"**{tone.name}**")
            if tone.description:
                prompt_parts.append(f"{tone.description}")

        # 8. Стиль диалогов
        dialogue_style = self._select_random_dialogue_style()
        if dialogue_style:
            prompt_parts.append(f"\n## СТИЛЬ ДИАЛОГОВ")
            prompt_parts.append(f"**{dialogue_style.name}**")
            if dialogue_style.description:
                prompt_parts.append(f"{dialogue_style.description}")

        return "\n".join(prompt_parts)

    def _select_random_category(self):
        """Выбирает случайную категорию"""
        categories = Category.query.all()
        return random.choice(categories) if categories else None

    def _select_random_subcategory(self, category):
        """Выбирает случайную подкатегорию для категории"""
        subcategories = Subcategory.query.filter_by(category_id=category.id).all()
        return random.choice(subcategories) if subcategories else None

    def _select_secondary_elements(self, main_category):
        """Выбирает 1-2 второстепенных элемента из других категорий

        Args:
            main_category: Основная категория (исключается из выбора)

        Returns:
            list: Список словарей с информацией о второстепенных элементах
        """
        # Получаем все категории кроме основной
        other_categories = Category.query.filter(Category.id != main_category.id).all()

        if not other_categories:
            return []

        # Выбираем 1-2 второстепенных элемента
        num_elements = random.randint(1, 2)

        secondary_elements = []
        selected_categories = random.sample(other_categories, min(num_elements, len(other_categories)))

        for category in selected_categories:
            # Выбираем случайную подкатегорию из этой категории
            subcategories = Subcategory.query.filter_by(category_id=category.id).all()
            if subcategories:
                subcategory = random.choice(subcategories)
                secondary_elements.append({
                    'category': category.name,
                    'subcategory': subcategory.name,
                    'description': subcategory.description
                })

        return secondary_elements

    def _generate_characters(self, subcategory):
        """Генерирует персонажей согласно спецификации подкатегории"""
        characters = []

        # Определяем количество персонажей
        num_chars = random.randint(
            subcategory.num_characters_min,
            subcategory.num_characters_max
        )

        # Пытаемся использовать персонажей из таблицы Character
        if subcategory.characters:
            # Используем персонажей из связанной таблицы
            available_characters = list(subcategory.characters)

            # Генерируем нужное количество персонажей
            for i in range(num_chars):
                char_template = available_characters[i % len(available_characters)]

                char = {
                    "gender": char_template.gender,
                    "age": random.randint(char_template.age_min, char_template.age_max),
                    "role": char_template.name,
                    "role_description": char_template.description,
                    "has_initiative": False,
                    "attitude": None,
                    "traits": {},
                    "is_narrator": False,
                    "can_have_initiative": char_template.can_have_initiative
                }

                characters.append(char)

            # Назначаем инициативу
            chars_can_have_initiative = [
                i for i, c in enumerate(characters)
                if c.get("can_have_initiative", True)
            ]
        else:
            # Legacy: используем character_specs если нет привязанных персонажей
            char_specs = subcategory.get_character_specs()
            if not char_specs:
                # Если нет спецификации, создаем один стандартный персонаж
                char_specs = [{
                    "gender": random.choice(["мужской", "женский", "небинарный"]),
                    "age_min": 18,
                    "age_max": 60,
                    "can_have_initiative": True
                }]

            # Генерируем персонажей
            for i in range(num_chars):
                spec = char_specs[i % len(char_specs)]

                char = {
                    "gender": spec.get("gender", "небинарный"),
                    "age": random.randint(spec.get("age_min", 18), spec.get("age_max", 60)),
                    "role": spec.get("role"),
                    "role_description": spec.get("role_description"),
                    "has_initiative": False,
                    "attitude": None,
                    "traits": {},
                    "is_narrator": False
                }

                characters.append(char)

            # Назначаем инициативу
            chars_can_have_initiative = [
                i for i, c in enumerate(characters)
                if char_specs[i % len(char_specs)].get("can_have_initiative", True)
            ]

        if chars_can_have_initiative and random.random() > 0.3:  # 70% шанс что кто-то будет с инициативой
            initiative_char_idx = random.choice(chars_can_have_initiative)
            characters[initiative_char_idx]["has_initiative"] = True

        # Для персонажей без инициативы определяем отношение
        attitudes = [
            "резко негативное (принуждение)",
            "негативное",
            "нейтральное",
            "позитивное",
            "резко позитивное (практически как инициатива)"
        ]

        for char in characters:
            if not char["has_initiative"]:
                char["attitude"] = random.choice(attitudes)

        # Назначаем характеристики
        self._assign_character_traits(characters)

        return characters

    def _assign_character_traits(self, characters):
        """Назначает случайные характеристики персонажам"""
        trait_types = CharacterTraitType.query.all()

        for char in characters:
            gender = char["gender"]

            # Фильтруем характеристики по полу
            applicable_traits = []
            for trait_type in trait_types:
                if gender == "мужской" and trait_type.applies_to_male:
                    applicable_traits.append(trait_type)
                elif gender == "женский" and trait_type.applies_to_female:
                    applicable_traits.append(trait_type)
                elif gender == "небинарный" and trait_type.applies_to_nonbinary:
                    applicable_traits.append(trait_type)

            # Назначаем случайное значение для каждой применимой характеристики
            for trait_type in applicable_traits:
                if trait_type.trait_values:
                    random_value = random.choice(trait_type.trait_values)
                    char["traits"][trait_type.name] = random_value.value

    def _select_perspective(self, subcategory, characters):
        """Выбирает перспективу повествования

        Returns:
            tuple: (текст перспективы, индекс рассказчика или None)
        """
        allowed = subcategory.get_allowed_perspectives()
        if not allowed:
            allowed = ["третье_лицо"]

        perspective_type = random.choice(allowed)

        if perspective_type == "первое_лицо" and characters:
            narrator_idx = random.randint(0, len(characters) - 1)
            char_num = narrator_idx + 1
            return (f"От первого лица (персонаж {char_num})", narrator_idx)
        elif perspective_type == "переключение" and len(characters) > 1:
            return ("С переключением между рассказчиками", None)
        else:
            return ("От третьего лица", None)

    def _generate_location(self):
        """Генерирует место действия"""
        countries = Country.query.all()
        location_types = LocationType.query.all()
        locations = Location.query.all()

        if not countries or not locations:
            return None

        country = random.choice(countries)
        location_type = random.choice(location_types) if location_types else None
        location = random.choice(locations)

        return {
            "country": country.name,
            "location_type": location_type.name if location_type else "неизвестно",
            "location": location.name,
            "location_description": location.description
        }

    def _select_random_tone(self):
        """Выбирает случайный тон"""
        tones = Tone.query.all()
        return random.choice(tones) if tones else None

    def _select_random_dialogue_style(self):
        """Выбирает случайный стиль диалогов"""
        styles = DialogueStyle.query.all()
        return random.choice(styles) if styles else None
