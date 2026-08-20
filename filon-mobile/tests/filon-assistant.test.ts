import { describe, expect, it } from "vitest";

import { parseFilonAdviceSse } from "../lib/filon-assistant";

describe("parseFilonAdviceSse", () => {
  it("keeps only verified result cards with a valid merchant and price", () => {
    const result = parseFilonAdviceSse('data: {"type":"step","i":0}\n\ndata: {"type":"results","data":{"usage":"ordinateur portable","offers":1,"real":true,"cards":[{"offer_id":42,"product_ean":"1234567890123","rank":"Le plus polyvalent","name":"PC vérifié","price":699,"merchant":"Marchand","image":"https://merchant.example/product.jpg,https://merchant.example/second.jpg","link":"https://merchant.example/item","why":"Offre catalogue.","buy":true},{"name":"Carte incomplète"}]}}\n\n');
    expect(result.real).toBe(true);
    expect(result.cards).toEqual([{ offerId: 42, productEan: "1234567890123", rank: "Le plus polyvalent", name: "PC vérifié", price: 699, merchant: "Marchand", imageUrl: "https://merchant.example/product.jpg", link: "https://merchant.example/item", why: "Offre catalogue.", buy: true }]);
  });

  it("returns an explicit empty verified state rather than synthetic cards", () => {
    const result = parseFilonAdviceSse('data: {"type":"results","data":{"usage":"besoin rare","offers":0,"real":false,"cards":[]}}\n\n');
    expect(result.real).toBe(false);
    expect(result.cards).toEqual([]);
  });
});
