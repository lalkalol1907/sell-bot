POSITIVE = {
    "куплю", "купить", "ищу", "нужен", "нужна", "нужно", "хочу", "почём", "почем",
    "сколько", "беру", "возьму", "приобрету",
}
NEGATIVE = {
    "продаю", "продам", "отдам", "отдаю", "в наличии", "наличии", "опт", "продажа",
}
INDIRECT = {
    "кто", "где", "есть", "подскажите", "помогите", "достать", "срочно",
}


def intent_score(text: str) -> float:
    tokens = set(text.split())

    if tokens & NEGATIVE:
        return -1.0
    if tokens & POSITIVE:
        return 0.9
    if "?" in text or (tokens & INDIRECT):
        return 0.55
    return 0.1
