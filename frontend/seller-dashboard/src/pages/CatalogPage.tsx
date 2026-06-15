import { FormEvent, useEffect, useState } from "react";
import { sellerApi, type Product } from "../api";

export function CatalogPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [price, setPrice] = useState("");
  const [currency, setCurrency] = useState("RUB");
  const [keywords, setKeywords] = useState("");

  async function load() {
    const data = await sellerApi.products();
    setProducts(data.products);
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await sellerApi.createProduct({
        title,
        price,
        currency,
        keywords: keywords
          .split(",")
          .map((k) => k.trim())
          .filter(Boolean),
        is_active: true,
      });
      setTitle("");
      setPrice("");
      setKeywords("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function toggle(product: Product) {
    await sellerApi.updateProduct(product.id, {
      title: product.title,
      price: product.price,
      currency: product.currency,
      keywords: product.keywords,
      is_active: !product.is_active,
    });
    await load();
  }

  async function remove(id: number) {
    await sellerApi.deleteProduct(id);
    await load();
  }

  return (
    <div>
      <h2>Каталог</h2>
      {error && <p className="error">{error}</p>}

      <div className="card">
        <h3>Добавить товар</h3>
        <form onSubmit={onCreate}>
          <input placeholder="Название" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <input placeholder="Цена" value={price} onChange={(e) => setPrice(e.target.value)} required />
          <input placeholder="Валюта" value={currency} onChange={(e) => setCurrency(e.target.value)} />
          <input
            placeholder="Keywords через запятую"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
          />
          <button type="submit">Добавить</button>
        </form>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Товар</th>
              <th>Цена</th>
              <th>Keywords</th>
              <th>Статус</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id}>
                <td>{p.title}</td>
                <td>
                  {p.price} {p.currency}
                </td>
                <td>{p.keywords.join(", ") || "—"}</td>
                <td>{p.is_active ? "активен" : "выкл"}</td>
                <td className="row">
                  <button className="secondary" onClick={() => void toggle(p)}>
                    {p.is_active ? "Выключить" : "Включить"}
                  </button>
                  <button className="danger" onClick={() => void remove(p.id)}>
                    Удалить
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
