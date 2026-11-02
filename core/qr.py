from PIL import Image, ImageDraw

_H_BLOCKS = {
    1: (17, 1, 9, 0, 0), 2: (28, 1, 16, 0, 0), 3: (22, 2, 13, 0, 0), 4: (16, 4, 9, 0, 0),
    5: (22, 2, 11, 2, 12), 6: (28, 4, 15, 0, 0), 7: (26, 4, 13, 1, 14), 8: (26, 4, 14, 2, 15),
    9: (24, 4, 12, 4, 13), 10: (28, 6, 15, 2, 16), 11: (24, 3, 12, 8, 13), 12: (28, 7, 14, 4, 15),
    13: (22, 12, 11, 4, 12), 14: (24, 11, 12, 5, 13), 15: (24, 11, 12, 7, 13), 16: (30, 3, 15, 13, 16),
    17: (28, 2, 14, 17, 15), 18: (28, 2, 14, 19, 15), 19: (26, 9, 13, 16, 14), 20: (28, 15, 15, 10, 16),
}
_ECL_H_FORMAT_BITS = 0b10


def _raw_data_modules(ver):
    result = (16 * ver + 128) * ver + 64
    if ver >= 2:
        numalign = ver // 7 + 2
        result -= (25 * numalign - 10) * numalign - 55
        if ver >= 7:
            result -= 36
    return result


def _data_codewords(ver):
    ec, b1, d1, b2, d2 = _H_BLOCKS[ver]
    return b1 * d1 + b2 * d2


def _gf_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(degree):
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = _gf_mul(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = _gf_mul(root, 0x02)
    return result


def _rs_remainder(data, divisor):
    result = [0] * len(divisor)
    for b in data:
        factor = b ^ result.pop(0)
        result.append(0)
        for i, coef in enumerate(divisor):
            result[i] ^= _gf_mul(coef, factor)
    return result


class QrCode:
    def __init__(self, text):
        data = text.encode("utf-8")
        for ver in range(1, 21):
            ccbits = 8 if ver < 10 else 16
            if 4 + ccbits + 8 * len(data) <= _data_codewords(ver) * 8:
                break
        else:
            raise ValueError("Text too long for QR version 20")
        self.version = ver
        self.size = ver * 4 + 17
        self.modules = [[False] * self.size for _ in range(self.size)]
        self._isfunc = [[False] * self.size for _ in range(self.size)]

        codewords = self._encode_data(data, ccbits)
        self._draw_function_patterns()
        self._draw_codewords(self._add_ecc_and_interleave(codewords))

        best_mask, best_penalty = 0, None
        for mask in range(8):
            self._apply_mask(mask)
            self._draw_format_bits(mask)
            penalty = self._penalty()
            if best_penalty is None or penalty < best_penalty:
                best_mask, best_penalty = mask, penalty
            self._apply_mask(mask)
        self._apply_mask(best_mask)
        self._draw_format_bits(best_mask)

    def _encode_data(self, data, ccbits):
        bits = []

        def put(val, n):
            bits.extend((val >> i) & 1 for i in reversed(range(n)))

        put(0b0100, 4)
        put(len(data), ccbits)
        for b in data:
            put(b, 8)
        capacity = _data_codewords(self.version) * 8
        put(0, min(4, capacity - len(bits)))
        put(0, (-len(bits)) % 8)
        pad = 0xEC
        while len(bits) < capacity:
            put(pad, 8)
            pad ^= 0xEC ^ 0x11
        return [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]

    def _add_ecc_and_interleave(self, data):
        ec, b1, d1, b2, d2 = _H_BLOCKS[self.version]
        assert (b1 * (d1 + ec) + b2 * (d2 + ec)) == _raw_data_modules(self.version) // 8
        divisor = _rs_divisor(ec)
        blocks, k = [], 0
        for count, length in ((b1, d1), (b2, d2)):
            for _ in range(count):
                dat = data[k:k + length]
                k += length
                blocks.append((dat, _rs_remainder(dat, divisor)))
        result = []
        for i in range(max(d1, d2)):
            result.extend(dat[i] for dat, _ in blocks if i < len(dat))
        for i in range(ec):
            result.extend(ecc[i] for _, ecc in blocks)
        return result

    def _set_func(self, x, y, dark):
        self.modules[y][x] = dark
        self._isfunc[y][x] = True

    def _alignment_positions(self):
        ver = self.version
        if ver == 1:
            return []
        numalign = ver // 7 + 2
        step = (ver * 8 + numalign * 3 + 5) // (numalign * 4 - 4) * 2
        result = [self.size - 7 - i * step for i in range(numalign - 1)] + [6]
        return list(reversed(result))

    def _draw_function_patterns(self):
        for i in range(self.size):
            self._set_func(6, i, i % 2 == 0)
            self._set_func(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (self.size - 4, 3), (3, self.size - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < self.size and 0 <= y < self.size:
                        self._set_func(x, y, max(abs(dx), abs(dy)) not in (2, 4))
        pos = self._alignment_positions()
        n = len(pos)
        for i in range(n):
            for j in range(n):
                if (i, j) in ((0, 0), (0, n - 1), (n - 1, 0)):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self._set_func(pos[i] + dx, pos[j] + dy, max(abs(dx), abs(dy)) != 1)
        self._draw_format_bits(0)
        if self.version >= 7:
            rem = self.version
            for _ in range(12):
                rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
            bits = self.version << 12 | rem
            for i in range(18):
                bit = (bits >> i) & 1 == 1
                a, b = self.size - 11 + i % 3, i // 3
                self._set_func(a, b, bit)
                self._set_func(b, a, bit)

    def _draw_format_bits(self, mask):
        data = _ECL_H_FORMAT_BITS << 3 | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412

        def bit(i):
            return (bits >> i) & 1 == 1

        for i in range(6):
            self._set_func(8, i, bit(i))
        self._set_func(8, 7, bit(6))
        self._set_func(8, 8, bit(7))
        self._set_func(7, 8, bit(8))
        for i in range(9, 15):
            self._set_func(14 - i, 8, bit(i))
        for i in range(8):
            self._set_func(self.size - 1 - i, 8, bit(i))
        for i in range(8, 15):
            self._set_func(8, self.size - 15 + i, bit(i))
        self._set_func(8, self.size - 8, True)

    def _draw_codewords(self, data):
        i, total = 0, len(data) * 8
        right = self.size - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(self.size):
                for j in range(2):
                    x = right - j
                    upward = ((right + 1) & 2) == 0
                    y = self.size - 1 - vert if upward else vert
                    if not self._isfunc[y][x] and i < total:
                        self.modules[y][x] = (data[i >> 3] >> (7 - (i & 7))) & 1 == 1
                        i += 1
            right -= 2

    _MASKS = (
        lambda x, y: (x + y) % 2,
        lambda x, y: y % 2,
        lambda x, y: x % 3,
        lambda x, y: (x + y) % 3,
        lambda x, y: (x // 3 + y // 2) % 2,
        lambda x, y: x * y % 2 + x * y % 3,
        lambda x, y: (x * y % 2 + x * y % 3) % 2,
        lambda x, y: ((x + y) % 2 + x * y % 3) % 2,
    )

    def _apply_mask(self, mask):
        fn = self._MASKS[mask]
        for y in range(self.size):
            row, func = self.modules[y], self._isfunc[y]
            for x in range(self.size):
                if not func[x] and fn(x, y) == 0:
                    row[x] = not row[x]

    def _penalty(self):
        size, m = self.size, self.modules
        penalty = 0
        lines = [m[y] for y in range(size)] + [[m[y][x] for y in range(size)] for x in range(size)]
        finder_a = [True, False, True, True, True, False, True, False, False, False, False]
        finder_b = list(reversed(finder_a))
        for line in lines:
            run, prev = 0, None
            for v in line:
                if v == prev:
                    run += 1
                else:
                    if run >= 5:
                        penalty += run - 2
                    run, prev = 1, v
            if run >= 5:
                penalty += run - 2
            for i in range(size - 10):
                seg = line[i:i + 11]
                if seg == finder_a or seg == finder_b:
                    penalty += 40
        for y in range(size - 1):
            for x in range(size - 1):
                c = m[y][x]
                if c == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                    penalty += 3
        dark = sum(sum(row) for row in m)
        total = size * size
        penalty += (abs(dark * 20 - total * 10) + total - 1) // total * 10 - 10 if dark * 20 != total * 10 else 0
        return penalty


def render_qr(text, scale=16, border=4, logo=None, logo_ratio=0.24, dark=(17, 24, 39), light=(255, 255, 255)):
    qr = QrCode(text)
    n = qr.size + border * 2
    img = Image.new("RGB", (n * scale, n * scale), light)
    draw = ImageDraw.Draw(img)
    for y in range(qr.size):
        for x in range(qr.size):
            if qr.modules[y][x]:
                px, py = (x + border) * scale, (y + border) * scale
                draw.rectangle([px, py, px + scale - 1, py + scale - 1], fill=dark)
    if logo is not None:
        side = int(qr.size * scale * logo_ratio)
        pad = max(scale // 2, side // 12)
        cx = cy = img.width // 2
        box = [cx - side // 2 - pad, cy - side // 2 - pad, cx + side // 2 + pad, cy + side // 2 + pad]
        draw.rounded_rectangle(box, radius=side // 4, fill=light)
        mark = logo.convert("RGBA").resize((side, side), Image.LANCZOS)
        img.paste(mark, (cx - side // 2, cy - side // 2), mark)
    return img
