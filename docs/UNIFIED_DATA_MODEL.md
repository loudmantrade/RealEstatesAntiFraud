# Unified Data Model (UDM)

## Обзор

Unified Data Model (UDM) - это стандартизированная модель данных для представления объявлений о недвижимости из различных источников. Все source plugins должны преобразовывать данные в формат UDM.

## Полная схема UDM

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["listing_id", "source", "type", "property_type", "location", "price"],
  "properties": {

    "listing_id": {
      "type": "string",
      "format": "uuid",
      "description": "Уникальный идентификатор объявления в системе"
    },

    "source": {
      "type": "object",
      "required": ["plugin_id", "platform", "original_id", "url"],
      "properties": {
        "plugin_id": {
          "type": "string",
          "description": "ID плагина-источника",
          "example": "plugin-source-avito"
        },
        "platform": {
          "type": "string",
          "description": "Название платформы-источника",
          "example": "avito.ru"
        },
        "original_id": {
          "type": "string",
          "description": "ID объявления на источнике"
        },
        "url": {
          "type": "string",
          "format": "uri",
          "description": "Прямая ссылка на объявление"
        },
        "api_response": {
          "type": "object",
          "description": "Сырой ответ API (если применимо)"
        }
      }
    },

    "type": {
      "type": "string",
      "enum": ["sale", "rent", "daily_rent"],
      "description": "Тип сделки"
    },

    "property_type": {
      "type": "string",
      "enum": [
        "apartment",
        "room",
        "house",
        "townhouse",
        "part_house",
        "land",
        "commercial",
        "office",
        "retail",
        "warehouse",
        "free_purpose",
        "garage",
        "parking"
      ],
      "description": "Тип недвижимости"
    },

    "location": {
      "type": "object",
      "required": ["country", "city"],
      "properties": {
        "country": {
          "type": "string",
          "description": "Страна",
          "example": "Russia"
        },
        "country_code": {
          "type": "string",
          "description": "ISO код страны",
          "example": "RU"
        },
        "region": {
          "type": "string",
          "description": "Регион/область",
          "example": "Moscow Oblast"
        },
        "city": {
          "type": "string",
          "description": "Город",
          "example": "Moscow"
        },
        "district": {
          "type": "string",
          "description": "Район города"
        },
        "subdistrict": {
          "type": "string",
          "description": "Микрорайон"
        },
        "street": {
          "type": "string",
          "description": "Улица"
        },
        "house_number": {
          "type": "string",
          "description": "Номер дома"
        },
        "address": {
          "type": "string",
          "description": "Полный адрес"
        },
        "coordinates": {
          "type": "object",
          "properties": {
            "lat": {
              "type": "number",
              "minimum": -90,
              "maximum": 90
            },
            "lng": {
              "type": "number",
              "minimum": -180,
              "maximum": 180
            }
          }
        },
        "postal_code": {
          "type": "string"
        },
        "metro": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "line": {"type": "string"},
              "distance_m": {"type": "integer"},
              "walk_time_min": {"type": "integer"},
              "transport_time_min": {"type": "integer"}
            }
          }
        },
        "enrichment": {
          "type": "object",
          "description": "Дополнительные данные о локации",
          "properties": {
            "population": {"type": "integer"},
            "poi_nearby": {"type": "array"},
            "transport_accessibility": {"type": "number"},
            "infrastructure_score": {"type": "number"}
          }
        }
      }
    },

    "price": {
      "type": "object",
      "required": ["amount", "currency"],
      "properties": {
        "amount": {
          "type": "number",
          "minimum": 0,
          "description": "Цена"
        },
        "currency": {
          "type": "string",
          "enum": ["RUB", "USD", "EUR", "GBP", "CNY"],
          "description": "Валюта"
        },
        "price_per_sqm": {
          "type": "number",
          "description": "Цена за квадратный метр"
        },
        "negotiable": {
          "type": "boolean",
          "description": "Возможен торг"
        },
        "with_nds": {
          "type": "boolean",
          "description": "Включен ли НДС"
        },
        "utilities_included": {
          "type": "boolean",
          "description": "Включены ли коммунальные услуги"
        },
        "deposit": {
          "type": "number",
          "description": "Залог (для аренды)"
        },
        "commission": {
          "type": "object",
          "properties": {
            "amount": {"type": "number"},
            "percentage": {"type": "number"},
            "paid_by": {
              "type": "string",
              "enum": ["buyer", "seller", "both"]
            }
          }
        },
        "price_history": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "date": {"type": "string", "format": "date-time"},
              "amount": {"type": "number"}
            }
          }
        }
      }
    },

    "details": {
      "type": "object",
      "properties": {
        "area_total": {
          "type": "number",
          "minimum": 0,
          "description": "Общая площадь, м²"
        },
        "area_living": {
          "type": "number",
          "description": "Жилая площадь, м²"
        },
        "area_kitchen": {
          "type": "number",
          "description": "Площадь кухни, м²"
        },
        "area_land": {
          "type": "number",
          "description": "Площадь участка, соток"
        },
        "rooms": {
          "type": "integer",
          "minimum": 0,
          "description": "Количество комнат"
        },
        "bedrooms": {
          "type": "integer",
          "description": "Количество спален"
        },
        "bathrooms": {
          "type": "integer",
          "description": "Количество санузлов"
        },
        "floor": {
          "type": "integer",
          "description": "Этаж"
        },
        "total_floors": {
          "type": "integer",
          "description": "Этажность здания"
        },
        "year_built": {
          "type": "integer",
          "minimum": 1800,
          "maximum": 2100,
          "description": "Год постройки"
        },
        "building_type": {
          "type": "string",
          "enum": [
            "panel",
            "brick",
            "monolith",
            "monolith_brick",
            "block",
            "wooden",
            "stalin",
            "khrushchev"
          ]
        },
        "condition": {
          "type": "string",
          "enum": [
            "without_finishing",
            "needs_renovation",
            "normal",
            "good",
            "excellent",
            "euro_renovation",
            "designer_renovation"
          ]
        },
        "ceiling_height": {
          "type": "number",
          "description": "Высота потолков, м"
        },
        "balcony": {
          "type": "string",
          "enum": ["none", "balcony", "loggia", "multiple"]
        },
        "windows_view": {
          "type": "string",
          "enum": ["yard", "street", "yard_and_street"]
        },
        "bathroom_type": {
          "type": "string",
          "enum": ["combined", "separate", "multiple"]
        },
        "layout": {
          "type": "string",
          "enum": ["studio", "separate", "adjacent", "free", "open"]
        },
        "heating": {
          "type": "string",
          "enum": ["central", "autonomous", "electric", "gas", "solid_fuel"]
        },
        "elevator": {
          "type": "object",
          "properties": {
            "passenger": {"type": "integer"},
            "freight": {"type": "integer"}
          }
        },
        "parking": {
          "type": "string",
          "enum": ["none", "ground", "underground", "multilevel", "nearby"]
        },
        "features": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "air_conditioning",
              "furniture",
              "refrigerator",
              "washing_machine",
              "dishwasher",
              "tv",
              "internet",
              "phone",
              "intercom",
              "security_alarm",
              "concierge",
              "closed_territory",
              "playground",
              "garbage_chute",
              "wheelchair_accessible",
              "pets_allowed",
              "children_allowed"
            ]
          }
        },
        "cadastral_number": {
          "type": "string",
          "description": "Кадастровый номер"
        }
      }
    },

    "description": {
      "type": "object",
      "properties": {
        "title": {
          "type": "string",
          "description": "Заголовок объявления"
        },
        "text": {
          "type": "string",
          "description": "Полное описание"
        },
        "language": {
          "type": "string",
          "description": "Язык описания (ISO 639-1)",
          "example": "ru"
        },
        "sentiment": {
          "type": "number",
          "minimum": -1,
          "maximum": 1,
          "description": "Sentiment score (-1 до 1)"
        },
        "keywords": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Извлеченные ключевые слова"
        },
        "entities": {
          "type": "object",
          "description": "Извлеченные сущности (NER)",
          "properties": {
            "organizations": {"type": "array"},
            "locations": {"type": "array"},
            "persons": {"type": "array"}
          }
        }
      }
    },

    "media": {
      "type": "object",
      "properties": {
        "images": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "url": {
                "type": "string",
                "format": "uri"
              },
              "thumbnail_url": {
                "type": "string",
                "format": "uri"
              },
              "caption": {
                "type": "string"
              },
              "order": {
                "type": "integer"
              },
              "width": {
                "type": "integer"
              },
              "height": {
                "type": "integer"
              },
              "size_bytes": {
                "type": "integer"
              },
              "hash": {
                "type": "string",
                "description": "Perceptual hash для детекции дубликатов"
              },
              "exif": {
                "type": "object",
                "description": "EXIF метаданные"
              },
              "analysis": {
                "type": "object",
                "description": "Результат анализа изображения",
                "properties": {
                  "quality_score": {"type": "number"},
                  "is_stock_photo": {"type": "boolean"},
                  "is_manipulated": {"type": "boolean"},
                  "reverse_search_results": {"type": "array"}
                }
              }
            }
          }
        },
        "videos": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "url": {"type": "string", "format": "uri"},
              "thumbnail_url": {"type": "string"},
              "duration_sec": {"type": "integer"},
              "platform": {
                "type": "string",
                "enum": ["youtube", "vimeo", "direct"]
              }
            }
          }
        },
        "virtual_tour": {
          "type": "string",
          "format": "uri",
          "description": "Ссылка на виртуальный тур"
        },
        "floor_plan": {
          "type": "string",
          "format": "uri",
          "description": "План помещения"
        }
      }
    },

    "seller": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["owner", "agent", "agency", "developer", "bank"]
        },
        "name": {
          "type": "string",
          "description": "Имя/название"
        },
        "company": {
          "type": "string",
          "description": "Название компании"
        },
        "inn": {
          "type": "string",
          "description": "ИНН компании"
        },
        "contacts": {
          "type": "object",
          "properties": {
            "phone": {
              "type": "array",
              "items": {
                "type": "string",
                "pattern": "^\\+?[1-9]\\d{1,14}$"
              }
            },
            "email": {
              "type": "array",
              "items": {
                "type": "string",
                "format": "email"
              }
            },
            "messenger": {
              "type": "object",
              "properties": {
                "whatsapp": {"type": "string"},
                "telegram": {"type": "string"},
                "viber": {"type": "string"}
              }
            },
            "social": {
              "type": "object",
              "properties": {
                "vk": {"type": "string"},
                "facebook": {"type": "string"},
                "instagram": {"type": "string"}
              }
            }
          }
        },
        "rating": {
          "type": "number",
          "minimum": 0,
          "maximum": 5,
          "description": "Рейтинг продавца"
        },
        "reviews_count": {
          "type": "integer",
          "description": "Количество отзывов"
        },
        "verified": {
          "type": "boolean",
          "description": "Верифицирован ли продавец"
        },
        "registration_date": {
          "type": "string",
          "format": "date-time",
          "description": "Дата регистрации на платформе"
        },
        "active_listings_count": {
          "type": "integer",
          "description": "Количество активных объявлений"
        },
        "reputation_score": {
          "type": "number",
          "description": "Внутренний скор репутации (0-100)"
        }
      }
    },

    "legal": {
      "type": "object",
      "properties": {
        "ownership_type": {
          "type": "string",
          "enum": ["private", "cooperative", "municipal", "other"]
        },
        "encumbrance": {
          "type": "boolean",
          "description": "Наличие обременений"
        },
        "mortgage_possible": {
          "type": "boolean",
          "description": "Возможна ипотека"
        },
        "deal_type": {
          "type": "string",
          "enum": ["direct", "alternative", "assignment"]
        },
        "documents": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },

    "metadata": {
      "type": "object",
      "required": ["scraped_at"],
      "properties": {
        "published_at": {
          "type": "string",
          "format": "date-time",
          "description": "Дата публикации на источнике"
        },
        "updated_at": {
          "type": "string",
          "format": "date-time",
          "description": "Дата последнего обновления"
        },
        "scraped_at": {
          "type": "string",
          "format": "date-time",
          "description": "Дата скрейпинга"
        },
        "expires_at": {
          "type": "string",
          "format": "date-time",
          "description": "Дата истечения объявления"
        },
        "views_count": {
          "type": "integer",
          "description": "Количество просмотров"
        },
        "favorites_count": {
          "type": "integer",
          "description": "Добавлено в избранное"
        },
        "status": {
          "type": "string",
          "enum": ["active", "inactive", "sold", "rented", "deleted"],
          "description": "Статус объявления"
        },
        "raw_data": {
          "type": "object",
          "description": "Сырые данные от источника"
        },
        "processing_log": {
          "type": "array",
          "description": "Лог обработки плагинами",
          "items": {
            "type": "object",
            "properties": {
              "plugin_id": {"type": "string"},
              "timestamp": {"type": "string", "format": "date-time"},
              "status": {"type": "string", "enum": ["success", "error"]},
              "message": {"type": "string"}
            }
          }
        }
      }
    },

    "fraud_detection": {
      "type": "object",
      "description": "Результаты детекции мошенничества",
      "properties": {
        "fraud_score": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Общий скор мошенничества"
        },
        "risk_level": {
          "type": "string",
          "enum": ["safe", "suspicious", "fraud"]
        },
        "signals": {
          "type": "array",
          "description": "Обнаруженные признаки мошенничества",
          "items": {
            "type": "object",
            "properties": {
              "plugin_id": {"type": "string"},
              "type": {"type": "string"},
              "severity": {"type": "number"},
              "description": {"type": "string"},
              "evidence": {"type": "object"}
            }
          }
        },
        "analyzed_at": {
          "type": "string",
          "format": "date-time"
        },
        "manual_review": {
          "type": "object",
          "properties": {
            "required": {"type": "boolean"},
            "reviewed": {"type": "boolean"},
            "reviewer": {"type": "string"},
            "verdict": {
              "type": "string",
              "enum": ["safe", "fraud", "uncertain"]
            },
            "notes": {"type": "string"}
          }
        }
      }
    }
  }
}
```

## Примеры использования

### Пример 1: Квартира на продажу

```json
{
  "listing_id": "550e8400-e29b-41d4-a716-446655440000",
  "source": {
    "plugin_id": "plugin-source-cian",
    "platform": "cian.ru",
    "original_id": "123456789",
    "url": "https://www.cian.ru/sale/flat/123456789/"
  },
  "type": "sale",
  "property_type": "apartment",
  "location": {
    "country": "Russia",
    "country_code": "RU",
    "region": "Moscow",
    "city": "Moscow",
    "district": "Arbat",
    "street": "Arbat Street",
    "house_number": "10",
    "address": "Moscow, Arbat, 10",
    "coordinates": {
      "lat": 55.752023,
      "lng": 37.617499
    },
    "metro": [
      {
        "name": "Arbatskaya",
        "line": "Blue Line",
        "distance_m": 300,
        "walk_time_min": 4
      }
    ]
  },
  "price": {
    "amount": 15000000,
    "currency": "RUB",
    "price_per_sqm": 250000,
    "negotiable": true
  },
  "details": {
    "area_total": 60,
    "area_living": 40,
    "area_kitchen": 12,
    "rooms": 2,
    "bedrooms": 1,
    "bathrooms": 1,
    "floor": 5,
    "total_floors": 9,
    "year_built": 1960,
    "building_type": "stalin",
    "condition": "good",
    "ceiling_height": 3.2,
    "balcony": "balcony",
    "features": [
      "furniture",
      "internet",
      "intercom"
    ]
  },
  "description": {
    "title": "2-комнатная квартира, 60 м², 5/9 эт.",
    "text": "Уютная двухкомнатная квартира в сталинском доме...",
    "language": "ru"
  },
  "media": {
    "images": [
      {
        "url": "https://cdn.cian.ru/images/1.jpg",
        "order": 1,
        "width": 1920,
        "height": 1080
      }
    ]
  },
  "seller": {
    "type": "agent",
    "name": "Иван Иванов",
    "company": "Агентство недвижимости XYZ",
    "contacts": {
      "phone": ["+79161234567"],
      "messenger": {
        "whatsapp": "+79161234567"
      }
    },
    "verified": true
  },
  "metadata": {
    "published_at": "2024-01-15T10:00:00Z",
    "scraped_at": "2024-01-15T11:30:00Z",
    "status": "active"
  }
}
```

### Пример 2: Дом в аренду

```json
{
  "listing_id": "660e8400-e29b-41d4-a716-446655440001",
  "source": {
    "plugin_id": "plugin-source-avito",
    "platform": "avito.ru",
    "original_id": "2987654321",
    "url": "https://www.avito.ru/moskva/doma_dachi_kottedzhi/dom_150m_uchastok_10sot-2987654321"
  },
  "type": "rent",
  "property_type": "house",
  "location": {
    "country": "Russia",
    "city": "Moscow Oblast",
    "address": "Odintsovo, Cottage Village Green Park"
  },
  "price": {
    "amount": 150000,
    "currency": "RUB",
    "utilities_included": false,
    "deposit": 150000
  },
  "details": {
    "area_total": 150,
    "area_land": 10,
    "rooms": 4,
    "bedrooms": 3,
    "bathrooms": 2,
    "total_floors": 2,
    "year_built": 2020,
    "condition": "excellent",
    "features": [
      "furniture",
      "air_conditioning",
      "internet",
      "parking",
      "closed_territory"
    ]
  },
  "seller": {
    "type": "owner",
    "contacts": {
      "phone": ["+79267654321"]
    }
  },
  "metadata": {
    "published_at": "2024-01-10T14:00:00Z",
    "scraped_at": "2024-01-15T12:00:00Z",
    "status": "active"
  }
}
```

## Валидация UDM

### Python Validator

```python
from jsonschema import validate, ValidationError
import json

def validate_udm(listing: dict) -> bool:
    """Validate listing against UDM schema"""
    with open('udm_schema.json') as f:
        schema = json.load(f)

    try:
        validate(instance=listing, schema=schema)
        return True
    except ValidationError as e:
        print(f"Validation error: {e.message}")
        return False
```

## Преобразование в UDM

### Mapping Helper

```python
class UDMMapper:
    """Helper class for mapping to UDM format"""

    @staticmethod
    def create_listing(
        listing_id: str,
        source: dict,
        listing_type: str,
        property_type: str,
        location: dict,
        price: dict,
        **kwargs
    ) -> dict:
        """Create UDM listing with required fields"""

        listing = {
            'listing_id': listing_id,
            'source': source,
            'type': listing_type,
            'property_type': property_type,
            'location': location,
            'price': price,
            'metadata': {
                'scraped_at': datetime.utcnow().isoformat() + 'Z'
            }
        }

        # Add optional fields
        if 'details' in kwargs:
            listing['details'] = kwargs['details']
        if 'description' in kwargs:
            listing['description'] = kwargs['description']
        if 'media' in kwargs:
            listing['media'] = kwargs['media']
        if 'seller' in kwargs:
            listing['seller'] = kwargs['seller']

        return listing
```

## Расширение UDM

Если вам нужны дополнительные поля, используйте:

1. **metadata.raw_data** - для специфичных данных источника
2. **Custom fields** - добавьте в корень с префиксом `x_`

```json
{
  "listing_id": "...",
  "x_custom_field": "custom value",
  "metadata": {
    "raw_data": {
      "source_specific_field": "value"
    }
  }
}
```

## См. также

- [Plugin Development Guide](./PLUGIN_DEVELOPMENT.md)
- [Architecture Documentation](../ARCHITECTURE.md)
