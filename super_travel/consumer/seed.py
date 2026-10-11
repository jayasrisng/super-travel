"""Coherent, original illustrated capsule wardrobe; no external product claims."""

from uuid import NAMESPACE_URL, uuid5

COLORS = {
    "cream": "#e6ded0",
    "navy": "#34485a",
    "sage": "#879582",
    "clay": "#b97a63",
    "graphite": "#505354",
    "blue": "#8ea5b4",
    "sand": "#c4ad89",
    "black": "#353b3b",
    "white": "#f0ece3",
    "brown": "#8b6952",
}
NAMES = {
    "tops": [
        "Cream cotton tee",
        "Navy striped tee",
        "Sage linen shirt",
        "Clay relaxed shirt",
        "Graphite knit",
        "Blue Oxford shirt",
        "Sand cardigan",
        "Black evening top",
        "White linen blouse",
        "Brown wool sweater",
    ],
    "bottoms": [
        "Cream straight trousers",
        "Navy relaxed trousers",
        "Sage cargo trousers",
        "Clay midi skirt",
        "Graphite tailored trousers",
        "Blue everyday jeans",
        "Sand linen shorts",
        "Black evening trousers",
        "White cotton trousers",
        "Brown corduroys",
    ],
    "shoes": [
        "Cream walking sneakers",
        "Navy canvas shoes",
        "Sage waterproof walking shoes",
        "Brown comfortable loafers",
    ],
    "accessories": [
        "Cream scarf",
        "Navy cap",
        "Sage crossbody bag",
        "Clay sunglasses",
        "Graphite belt",
        "Blue light scarf",
        "Sand sun hat",
        "Black tote bag",
        "White socks",
        "Brown leather belt",
    ],
}


def seed_items(actor):
    items = []
    for category, names in NAMES.items():
        for name in names:
            color = name.split()[0].lower()
            items.append(
                {
                    "id": str(uuid5(NAMESPACE_URL, f"{actor}:{name}")),
                    "name": name,
                    "category": category,
                    "color": color,
                    "image": f"/wardrobe/{category}-{color}.svg",
                    "style": "capsule",
                    "season": ["spring", "autumn"],
                    "warmth": 3
                    if "wool" in name or "knit" in name or "cardigan" in name
                    else 1,
                    "occasions": [
                        "walking",
                        "casual",
                        "dinner",
                        "business",
                        "outdoors",
                    ],
                    "material": "mixed",
                    "weight_grams": 350,
                    "ownership_status": "owned",
                    "favorite": False,
                    "availability": "ready",
                    "version": 1,
                    "image_mode": "illustration",
                }
            )
    return items
