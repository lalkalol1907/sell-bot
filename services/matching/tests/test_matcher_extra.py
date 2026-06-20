from app.pipeline.orchestrator import match_message, product_passes_threshold


def test_product_passes_threshold():
    assert product_passes_threshold(0.9, 0.0)
    assert product_passes_threshold(0.0, 0.8)
    assert not product_passes_threshold(0.5, 0.5)


def test_empty_text(reload_modules):
    result = match_message("", [{"id": 1, "title": "X", "keywords": ["x"]}])
    assert not result.matched
    assert result.reject_reason == "empty"


def test_no_product_after_sell_check(reload_modules):
    products = [{"id": 1, "title": "Samsung", "keywords": ["samsung galaxy"]}]
    result = match_message("куплю iphone", products)
    assert not result.matched
    assert result.reject_reason == "no_product"
