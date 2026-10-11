"""Generate original consistent fashion illustrations, not product photos or virtual try-on."""

from pathlib import Path

from super_travel.consumer.seed import COLORS, NAMES

SHAPES = {
    "tops": '<path d="M88 52 L120 41 Q140 57 160 41 L192 52 220 109 191 123 179 98 180 226 100 226 101 98 89 123 60 109 Z"/><path class="detail" d="M120 41 Q140 77 160 41 M104 217H177"/>',
    "bottoms": '<path d="M93 42H187L198 231 153 237 140 115 128 237 83 231Z"/><path class="detail" d="M93 61H187 M140 62V114 M106 62Q106 91 93 98 M174 62Q174 91 189 98"/>',
    "shoes": '<path d="M70 118L114 130 149 157 203 164Q227 172 217 199H66Q53 177 61 149Z"/><path class="detail" d="M64 187H219 M126 143L143 130 M137 152L154 141 M149 158L166 150 M70 118L87 152"/>',
    "accessories": '<path d="M81 119Q80 92 107 84H176Q202 92 201 119L213 220H68Z"/><path class="detail" d="M108 87V64Q108 34 141 34Q174 34 174 64V87 M77 136H206 M129 133V159H153V133"/>',
}
ACCESSORIES = {
    "scarf": '<path d="M106 40H157L178 96 152 116 164 222 129 228 111 129 79 222 52 211 98 98Z"/><path class="detail" d="M106 40L121 110 152 116 M129 213L160 208"/>',
    "cap": '<path d="M63 153Q61 58 146 58Q223 63 205 160Z"/><path d="M205 160Q161 123 94 151L58 167Q126 208 205 160Z"/><path class="detail" d="M146 58Q177 94 172 142"/>',
    "hat": '<path d="M97 129L109 57Q147 40 181 63L185 128Z"/><path d="M44 146Q82 103 189 122Q239 128 238 149Q218 179 126 176Q61 173 44 146Z"/><path class="detail" d="M99 108Q142 121 184 108"/>',
    "glasses": '<path d="M49 109Q81 91 119 108L112 159Q68 178 53 147Z M164 108Q198 91 232 109L225 148Q207 177 167 158Z"/><path class="detail" d="M118 116Q141 100 164 117 M50 110L39 75 M231 111L245 75"/>',
    "belt": '<path d="M58 69Q44 126 83 188Q126 234 203 170L192 152Q119 203 95 161Q77 130 78 95Z"/><rect x="174" y="137" width="51" height="49" rx="5" fill="none"/><path class="detail" d="M201 140V179 M112 181L115 179 M129 182L132 180 M144 179L148 177"/>',
    "socks": '<path d="M62 48H117L113 168 75 224Q42 235 32 210L64 149Z M151 48H206L202 168 164 224Q131 235 121 210L153 149Z"/><path class="detail" d="M62 76H116 M151 76H205 M61 164L98 187 M151 164L187 187"/>',
}


def garment_shape(category, name):
    if category == "accessories":
        for label, key in [
            ("scarf", "scarf"),
            ("cap", "cap"),
            ("hat", "hat"),
            ("sunglasses", "glasses"),
            ("belt", "belt"),
            ("socks", "socks"),
        ]:
            if label in name:
                return ACCESSORIES[key]
    if "skirt" in name:
        return '<path d="M112 51H174L216 219Q142 245 65 219Z"/><path class="detail" d="M110 68H178 M121 71L95 220 M164 71L188 221"/>'
    if "shorts" in name:
        return '<path d="M93 58H187L196 175 150 177 140 111 129 177 83 175Z"/><path class="detail" d="M93 77H187 M140 77V110"/>'
    if "shirt" in name or "blouse" in name:
        return (
            SHAPES[category]
            + '<path class="detail" d="M122 44L139 69 158 44 M140 70V222 M141 93H142 M141 120H142 M141 151H142 M141 184H142"/>'
        )
    return SHAPES[category]


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "apps/web/public/wardrobe"
    root.mkdir(parents=True, exist_ok=True)
    for category, names in NAMES.items():
        for name in names:
            color = name.split()[0].lower()
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 280" role="img" aria-label="Illustration of {name}"><defs><pattern id="h" width="7" height="7" patternUnits="userSpaceOnUse"><path d="M0 7L7 0" stroke="#403a32" stroke-opacity=".05"/></pattern></defs><ellipse cx="140" cy="247" rx="68" ry="6" fill="#403a32" opacity=".07"/><g fill="{COLORS[color]}" stroke="#504a40" stroke-width="1.6" stroke-linejoin="round">{garment_shape(category, name)}</g><style>.detail{{fill:none;stroke:#504a40;stroke-opacity:.45;stroke-width:1}}</style></svg>'''
            (root / f"{category}-{color}.svg").write_text(svg)
    print("34 original garment illustrations generated")
