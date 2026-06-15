#!/usr/bin/env python3
"""Generate recognition_cases.yaml golden suite."""

from __future__ import annotations

from pathlib import Path

import yaml

IPHONE_16 = {"id": 1, "title": "iPhone 16", "keywords": ["айфон 16", "iphone 16"]}
IPHONE_16_PRO = {"id": 2, "title": "iPhone 16 Pro", "keywords": ["iphone 16 pro", "айфон 16 про"]}
IPHONE_15 = {"id": 3, "title": "iPhone 15", "keywords": ["iphone 15", "айфон 15"]}
SAMSUNG_S24 = {"id": 4, "title": "Samsung Galaxy S24", "keywords": ["samsung s24", "самсунг s24", "galaxy s24"]}
MACBOOK = {"id": 5, "title": "MacBook Pro M3", "keywords": ["macbook pro", "макбук про"]}
AIRPODS = {"id": 6, "title": "AirPods Pro 2", "keywords": ["airpods pro", "эйрподс"]}
PS5 = {"id": 7, "title": "PlayStation 5", "keywords": ["ps5", "плейстейшн 5"]}
IPAD = {"id": 8, "title": "iPad Air", "keywords": ["ipad air", "айпад эйр"]}

IPHONE_16_PRO_256 = {
    "id": 2,
    "title": "iPhone 16 Pro 256GB",
    "keywords": ["iphone 16 pro 256", "айфон 16 про 256"],
    "storage_gb": 256,
}
IPAD_256 = {
    "id": 8,
    "title": "iPad Air 256GB",
    "keywords": ["ipad air 256", "айпад эйр 256"],
    "storage_gb": 256,
}
IPHONE_16_PRO_256_BLACK = {
    "id": 21,
    "title": "iPhone 16 Pro 256GB Black",
    "keywords": ["iphone 16 pro 256 black"],
    "storage_gb": 256,
    "color": "black",
}
IPHONE_16_PRO_128_WHITE = {
    "id": 22,
    "title": "iPhone 16 Pro 128GB White",
    "keywords": ["iphone 16 pro 128 white"],
    "storage_gb": 128,
    "color": "white",
}

cases: list[dict] = []


def add(cid: str, text: str, expect: dict, products: list | None = None, sensitivity: str = "precise", **kwargs):
    cases.append({
        "id": cid,
        "text": text,
        "products": products or [],
        "sensitivity": sensitivity,
        "expect": expect,
        **kwargs,
    })


def main():
    explicit = [
        ("explicit_buy_01", "куплю айфон 16", IPHONE_16, "confirmed"),
        ("explicit_buy_02", "ищу iphone 16 pro", IPHONE_16_PRO, "confirmed"),
        ("explicit_buy_03", "нужен самсунг s24", SAMSUNG_S24, "confirmed"),
        ("explicit_buy_04", "хочу macbook pro m3", MACBOOK, "confirmed"),
        ("explicit_buy_05", "беру airpods pro 2", AIRPODS, "confirmed"),
        ("explicit_buy_06", "возьму ps5", PS5, "confirmed"),
        ("explicit_buy_07", "приобрету ipad air", IPAD, "confirmed"),
        ("explicit_buy_08", "купить айфон 15 срочно", IPHONE_15, "confirmed"),
        ("explicit_buy_09", "нужна прошка 16 про", IPHONE_16_PRO, "confirmed"),
        ("explicit_buy_10", "сколько стоит iphone 16?", IPHONE_16, "confirmed"),
        ("explicit_buy_11", "почём айфон 16 про", IPHONE_16_PRO, "confirmed"),
        ("explicit_buy_12", "заказать samsung galaxy s24", SAMSUNG_S24, "confirmed"),
        ("explicit_buy_13", "интересует macbook pro", MACBOOK, "confirmed"),
        ("explicit_buy_14", "куплю эйрподс про", AIRPODS, "confirmed"),
        ("explicit_buy_15", "нужно ps5 дисковая", PS5, "confirmed"),
        ("explicit_buy_16", "хочу айпад эйр 256", IPAD_256, "confirmed"),
    ]
    for cid, text, prod, level in explicit:
        add(cid, text, {"matched": True, "level": level, "product_id": prod["id"], "intent_class": "buy"}, [prod])

    implicit_texts = [
        ("implicit_buy_01", "есть у кого 16 про на 256?", IPHONE_16_PRO_256),
        ("implicit_buy_04", "подскажите где взять s24", SAMSUNG_S24),
        ("implicit_buy_05", "есть macbook pro m3?", MACBOOK),
        ("implicit_buy_07", "где найти ps5?", PS5),
        ("implicit_buy_08", "есть айпад эйр?", IPAD),
        ("implicit_buy_09", "у кого есть 16 про 256гб", IPHONE_16_PRO_256),
        ("implicit_buy_10", "помогите найти iphone 15", IPHONE_15),
        ("implicit_buy_12", "есть у кого макбук про?", MACBOOK),
        ("implicit_buy_14", "кто знает где ps5 взять", PS5),
        ("implicit_buy_15", "подскажите по айпад эйр", IPAD),
        ("implicit_buy_21", "помогите с айпадом эйр", IPAD),
    ]
    for cid, text, prod in implicit_texts:
        add(cid, text, {"matched": True, "level": "probable", "product_id": prod["id"]}, [prod], sensitivity="balanced")

    implicit_semantic_only = [
        ("implicit_buy_02", "где достать шестнадцатый про?", IPHONE_16_PRO),
        ("implicit_buy_03", "кто может подсказать где купить айфон 16?", IPHONE_16),
        ("implicit_buy_06", "достать airpods pro можно?", AIRPODS),
        ("implicit_buy_11", "срочно нужен самсунг s24", SAMSUNG_S24),
        ("implicit_buy_13", "где купить эйрподс?", AIRPODS),
        ("implicit_buy_16", "ищу 16-ку для себя", IPHONE_16),
        ("implicit_buy_17", "где достать прошку 16?", IPHONE_16_PRO),
        ("implicit_buy_18", "можно ли найти s24 ultra", SAMSUNG_S24),
        ("implicit_buy_19", "есть у кого airpods?", AIRPODS),
        ("implicit_buy_20", "ищу ps5 slim", PS5),
    ]
    for cid, text, prod in implicit_semantic_only:
        add(
            cid,
            text,
            {"matched": True, "level": "probable", "product_id": prod["id"]},
            [prod],
            sensitivity="balanced",
            nlp_v2_enabled=True,
            nlp_v2_semantic=True,
        )

    sell_texts = [
        "продаю айфон 16, состояние отличное",
        "продам iphone 16 pro 256",
        "отдам samsung s24 недорого",
        "продаю macbook pro m3",
        "продам airpods pro 2",
        "отдаю ps5 с дисководом",
        "продаю ipad air",
        "в наличии айфон 15",
        "наличии iphone 16 про",
        "оптом samsung s24",
        "реализую macbook pro",
        "сдаю ps5 в аренду нет продаю ps5",
        "продажа airpods pro",
        "продам свой айфон 16",
        "отдам айпад эйр",
    ]
    for i, text in enumerate(sell_texts, 1):
        prods = [IPHONE_16, IPHONE_16_PRO, SAMSUNG_S24, MACBOOK, AIRPODS, PS5, IPAD]
        add(
            f"sell_reject_{i:02d}",
            text,
            {"matched": False, "reject_reason": "sell_intent", "intent_class": "sell"},
            prods,
        )

    discussion = [
        ("discussion_01", "у меня айфон 16 тормозит после обновления", IPHONE_16),
        ("discussion_02", "iphone 16 pro глючит экран", IPHONE_16_PRO),
        ("discussion_03", "samsung s24 батарея садится быстро", SAMSUNG_S24),
        ("discussion_04", "macbook pro m3 перегревается", MACBOOK),
        ("discussion_05", "airpods pro шумят в левом ухе", AIRPODS),
        ("discussion_06", "ps5 не включается после скачка", PS5),
        ("discussion_07", "ipad air разбился экран", IPAD),
        ("discussion_08", "айфон 15 не работает камера", IPHONE_15),
        ("discussion_09", "после обновления iphone 16 pro тормозит", IPHONE_16_PRO),
        ("discussion_10", "какой чехол на samsung s24 лучше", SAMSUNG_S24),
        ("discussion_11", "совет по macbook pro m3", MACBOOK),
        ("discussion_12", "настроил airpods pro как вам?", AIRPODS),
        ("discussion_13", "рекомендуете ps5 или xbox", PS5),
        ("discussion_14", "плёнка на ipad air какая", IPAD),
        ("discussion_15", "у меня 16 про проблема с батареей", IPHONE_16_PRO),
    ]
    for cid, text, prod in discussion:
        add(
            cid,
            text,
            {"matched": False, "reject_reason": "discussion", "intent_class": "discussion"},
            [prod],
            sensitivity="precise",
        )

    offtopic = [
        "погода сегодня отличная",
        "кто смотрел вчера матч",
        "привет всем в чате",
        "как дела у всех",
        "спасибо за помощь ребят",
        "завтра встречаемся в 18",
        "киньте мемы",
        "какой фильм посоветуете",
        "работаю удалённо уже год",
        "кто идёт на концерт",
    ]
    for i, text in enumerate(offtopic, 1):
        add(f"no_product_{i:02d}", text, {"matched": False, "reject_reason": "no_product"}, [IPHONE_16, SAMSUNG_S24])

    typos = [
        ("fuzzy_01", "куплю айфн 16", IPHONE_16),
        ("fuzzy_02", "ищу iphon 16 pro", IPHONE_16_PRO),
        ("fuzzy_03", "нужен самсунг s24 ультра", SAMSUNG_S24),
        ("fuzzy_04", "куплю макбук про m3", MACBOOK),
        ("fuzzy_05", "беру эйрподс про 2", AIRPODS),
        ("fuzzy_06", "куплю ps5", PS5),
        ("fuzzy_07", "хочу айпад эйр", IPAD),
        ("fuzzy_08", "куплю iphone шестнадцатый", IPHONE_16),
        ("fuzzy_09", "нужен galaxy s24", SAMSUNG_S24),
        ("fuzzy_10", "куплю macbook m3 pro", MACBOOK),
    ]
    for cid, text, prod in typos:
        add(cid, text, {"matched": True, "level": "confirmed", "product_id": prod["id"]}, [prod])

    multi = [
        ("multi_01", "куплю iphone 16 pro", [IPHONE_16, IPHONE_16_PRO], 2),
        ("multi_02", "ищу айфон 15", [IPHONE_16, IPHONE_15], 3),
        ("multi_03", "нужен samsung s24", [IPHONE_16, SAMSUNG_S24], 4),
        ("multi_04", "куплю macbook pro", [MACBOOK, IPHONE_16], 5),
        ("multi_05", "беру airpods pro", [AIRPODS, IPHONE_16], 6),
        ("multi_06", "хочу ps5", [PS5, IPHONE_16], 7),
        ("multi_07", "куплю ipad air", [IPAD, MACBOOK], 8),
        ("multi_08", "ищу iphone 16 pro", [IPHONE_16, IPHONE_16_PRO, IPHONE_15], 2),
        ("multi_09", "нужен iphone 16", [IPHONE_16_PRO, IPHONE_16], 1),
        ("multi_10", "куплю galaxy s24", [SAMSUNG_S24, IPHONE_16], 4),
    ]
    for cid, text, prods, pid in multi:
        add(cid, text, {"matched": True, "product_id": pid}, prods)

    sens_text = "есть айфон 16?"
    for sens, matched, level in [
        ("precise", False, None),
        ("balanced", True, "probable"),
        ("aggressive", True, "probable"),
    ]:
        exp = {"matched": matched}
        if level:
            exp["level"] = level
        add(f"sensitivity_{sens}", sens_text, exp, [IPHONE_16], sensitivity=sens)

    semantic = [
        ("semantic_01", "где достать шестнадцатый про?", IPHONE_16_PRO),
        ("semantic_02", "есть у кого 16 про на 256?", IPHONE_16_PRO_256),
        ("semantic_03", "ищу шестнадцатую прошку", IPHONE_16_PRO),
        ("semantic_04", "нужна шестнадцатая модель про", IPHONE_16_PRO),
        ("semantic_05", "где взять галакси эс 24", SAMSUNG_S24),
        ("semantic_06", "ищу макбук на m3", MACBOOK),
        ("semantic_07", "нужны беспроводные эйрподсы про", AIRPODS),
        ("semantic_08", "где найти плейстейшн пять", PS5),
        ("semantic_09", "ищу планшет эйр от эпл", IPAD),
        ("semantic_10", "достать пятнадцатую модель", IPHONE_15),
        ("semantic_11", "есть кто продаёт шестнадцатый? нет, ищу купить", IPHONE_16),
        ("semantic_12", "подскажите шестнадцатый про 256", IPHONE_16_PRO_256),
        ("semantic_13", "где купить эс двадцать четыре", SAMSUNG_S24),
        ("semantic_14", "нужен ноутбук про m3", MACBOOK),
        ("semantic_15", "ищу наушники эйрподс вторые", AIRPODS),
    ]
    for cid, text, prod in semantic:
        add(
            cid,
            text,
            {"matched": True, "level": "probable", "product_id": prod["id"]},
            [prod],
            sensitivity="balanced",
            nlp_v2_enabled=True,
            nlp_v2_semantic=True,
        )

    add(
        "variant_storage_pick_256",
        "куплю iphone 16 pro 256",
        {"matched": True, "level": "confirmed", "product_id": 21},
        [IPHONE_16_PRO, IPHONE_16_PRO_256_BLACK, IPHONE_16_PRO_128_WHITE],
    )
    add(
        "variant_color_pick_white",
        "куплю iphone 16 pro 128 белый",
        {"matched": True, "level": "confirmed", "product_id": 22},
        [IPHONE_16_PRO_256_BLACK, IPHONE_16_PRO_128_WHITE],
        sensitivity="balanced",
    )
    add(
        "variant_missing_storage_penalty",
        "куплю iphone 16 pro 256 черный",
        {"matched": True, "level": "confirmed", "product_id": 21},
        [IPHONE_16_PRO, IPHONE_16_PRO_256_BLACK],
        sensitivity="balanced",
    )
    add(
        "variant_no_attrs_in_message",
        "куплю iphone 16 pro",
        {"matched": True, "level": "confirmed", "product_id": 2},
        [IPHONE_16_PRO, IPHONE_16_PRO_256_BLACK],
    )

    add(
        "discussion_balanced_01",
        "у меня айфон 16 тормозит",
        {"matched": True, "level": "probable", "intent_class": "discussion"},
        [IPHONE_16],
        sensitivity="aggressive",
        nlp_v2_enabled=True,
        nlp_v2_semantic=True,
        nlp_v2_normalize=True,
    )

    path = Path(__file__).resolve().parent.parent / "data" / "recognition_cases.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(cases, f, allow_unicode=True, sort_keys=False, width=120)
    print(f"Wrote {len(cases)} cases to {path}")


if __name__ == "__main__":
    main()
