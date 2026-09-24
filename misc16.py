#!/usr/bin/env python3
"""MISC-16 toolkit: build, convert and run MISC-16 memory images.

Image format (same as MISC_tc_proof.png): 64 px wide, one instruction
(four 16-bit words, MSB first) per row, white = 1, black = 0.
Works with .png and .pgm (P2 plain or P5 binary) files.

  python3 misc16.py prog.bf [--pgm] [--run]         -> prog.png (or prog.pgm)
  python3 misc16.py build prog.bf [--pgm] [--run]   same thing
  python3 misc16.py build OUT.png|OUT.pgm "BF code"  inline code, explicit name
  python3 misc16.py run   IMAGE|prog.bf [--steps N]  run and show the tape
  python3 misc16.py dump  IMAGE                      print the words as binary

The interpreter only understands + - < > [ ]; everything else in a .bf
file (comments, . and ,) is stripped. End the program with [] on a
nonzero cell to halt; otherwise the zero words after it act as '+'.
"""
import sys

M = 1 << 16

# ---------- image I/O ----------
def read_image(path):
    if path.lower().endswith(".pgm"):
        data = open(path, "rb").read()
        magic = data[:2]
        # tokenise header (and body for P2), skipping comments
        toks, i = [], 2
        while len(toks) < (3 if magic == b"P5" else 10**9) and i < len(data):
            if data[i:i+1] == b"#":
                while i < len(data) and data[i:i+1] not in b"\n": i += 1
            elif data[i:i+1].isspace(): i += 1
            else:
                j = i
                while j < len(data) and not data[j:j+1].isspace(): j += 1
                toks.append(int(data[i:j])); i = j
        w, h, maxv = toks[:3]
        if magic == b"P2":
            px = toks[3:3 + w*h]
        else:
            px = list(data[i+1:i+1 + w*h])
        rows = [[1 if px[r*w+c] > maxv//2 else 0 for c in range(w)] for r in range(h)]
    else:
        from PIL import Image
        im = Image.open(path).convert("L")
        w, h = im.size
        rows = [[1 if im.getpixel((c, r)) > 127 else 0 for c in range(w)] for r in range(h)]
    words = []
    for row in rows:
        for k in range(0, len(row), 16):
            words.append(int("".join(map(str, row[k:k+16])), 2))
    return words

def write_image(path, words):
    while len(words) % 4: words.append(0)
    rows = [[(words[r*4 + k] >> (15 - b)) & 1 for k in range(4) for b in range(16)]
            for r in range(len(words)//4)]
    if path.lower().endswith(".pgm"):
        with open(path, "w") as f:
            f.write(f"P2\n# MISC-16 memory image: 1 row = 1 instruction, 1 = white\n64 {len(rows)}\n1\n")
            for row in rows: f.write(" ".join(map(str, row)) + "\n")
    else:
        from PIL import Image
        im = Image.new("1", (64, len(rows)))
        im.putdata([v for row in rows for v in row])
        im.save(path)

# ---------- the machine ----------
def s16(x): return x - M if x & 0x8000 else x
def s14(x): return x - 0x4000 if x & 0x2000 else x

def run(words, steps=10_000_000, trace_halt=True):
    mem = [0] * M
    mem[:len(words)] = words
    pc = n = 0
    while n < steps:
        # halt idiom for the BF interpreter: "[]" on a nonzero cell spins forever
        if trace_halt and pc == 0:
            ip = (mem[154] + 4) % M
            cell = mem[(mem[155] + 12) % M]
            if mem[ip] == 91 and mem[(ip+1) % M] == 93 and cell:
                return mem, n, True
        d, a, c, j = (mem[(pc + k) % M] for k in range(4))
        A = a if j & 0x8000 else mem[(pc + a) % M]
        C = c if j & 0x4000 else mem[(pc + c) % M]
        r = (A - C) % M
        mem[(pc + d) % M] = r
        pc = (pc + 4 * s14(j & 0x3FFF)) % M if r & 0x8000 else (pc + 4) % M
        n += 1
    return mem, n, False

# ---------- patched interpreter (the listing with two fixes) ----------
ORIGINAL = """
0000000000000101000000001001101000000000000000000100000000000001
0000000010010100000000000000000000000000010111010100000000001011
0000000000000101000000001001001100000000000000000100000000000001
0000000010001100000000000000000000000000000000010100000000100001
0000000010001001000000000000000000000000000000001100000000000001
0000000010000110000000001000011000000000000000010100000000000001
0000000000000101000000001000001000000000000110000100000000000001
0000000001111100000000000000000000000000010110110111111111111110
0000000001111000000000000111100000000000000000100100000000000010
0000000001110101000000000111010111111111111111100100000000000001
0000000001110001000000000111000100000000000000010100000000011010
0000000001101100000000000000000000000000000000011111111111111010
0000000001101000000000000110100011111111111111100100000000001011
0000000000000110000000000110011100000000001011000100000000000001
0000000001100000000000000000000000000000000000001000000000010110
0000000001011101000000000000000000000000000000001100000000000001
0000000001011010000000000101101011111111111111110100000000000001
0000000000000101000000000101011000000000010001000100000000000001
0000000001010000000000000000000000000000010110110111111111111110
0000000001001100000000000100110000000000000000100100000000000010
0000000001001001000000000100100100000000000000100100000000000001
0000000001000101000000000100010111111111111111110100000000001111
0000000001000000000000000000000000000000000000011111111111111010
0000000000111100000000000011110011111111111000110100000000000011
0000000000111011000000000011101111111111111111110100000000000001
0000000000110100000000000000000000000000000000011100000000001011
0000000000110000000000000011000011111111111111100100000000000011
0000000000101111000000000010111100000000000000010100000000000001
0000000000101000000000000000000000000000000000011100000000001000
0000000000100100000000000010010011111111111100010100000000000011
0000000000100001000000000000000100000000000000001100000000000001
0000000000011100000000000000000000000000000000011100000000000010
0000000000011001000000000000000000000000000000011100000000000001
0000000000001000000000000001011100000000011111000100000000000001
0000000000000101000000000001001100000000011111000100000000000001
0000000000000000000000000000000000000000000011010000000000000001
0000000000001010000000000000101000000000000000010100000000000001
0000000000000100000000000000000000000000000000011111111111011011
0000000000000000000000000000000000000000100110001000101011001101
"""
def patched_interpreter():
    w = []
    for line in ORIGINAL.split():
        w += [int(line[i:i+16], 2) for i in range(0, 64, 16)]
    w[146] = 0xFFFF            # I36: ip -= -1   (was ip -= 1)
    w[134] = w[138] = 0x0080   # I33/I34: dp-128 (was dp-124)
    return w

def bf_clean(code):
    code = "".join(ch for ch in code if ch in "+-<>[]")
    depth = 0
    for ch in code:
        depth += (ch == "[") - (ch == "]")
        if depth < 0: sys.exit("error: unmatched ']' in program")
    if depth: sys.exit("error: unmatched '[' in program")
    return code

def bf_image(code):
    return patched_interpreter() + [ord(ch) for ch in bf_clean(code)]

def do_run(words, steps):
    mem, n, halted = run(words, steps)
    base, dp = 0x8ACD + 12, (mem[155] + 12) % M
    lo, hi = min(base, dp), max(base, dp)
    while hi + 1 < M and mem[hi+1]: hi += 1
    print(("halted ([] idiom)" if halted else "step limit reached"), f"after {n:,} MISC instructions")
    print("tape:", " ".join(f"[{s16(mem[a])}]" if a == dp else str(s16(mem[a])) for a in range(lo, hi+1)))

def main():
    args = sys.argv[1:]
    flags = {a for a in args if a.startswith("--")}
    steps = 10_000_000
    if "--steps" in args:
        steps = int(args[args.index("--steps") + 1]); args.remove(str(steps))
    args = [a for a in args if not a.startswith("--")]
    if not args: print(__doc__); return
    # bare "misc16.py prog.bf" is shorthand for build
    if args[0].lower().endswith(".bf"): args = ["build"] + args
    cmd = args[0]
    if cmd == "build" and len(args) >= 2:
        if args[1].lower().endswith(".bf"):
            src = args[1]
            code = open(src, encoding="utf-8", errors="replace").read()
            stem = src[:src.rfind(".")]
            out = args[2] if len(args) > 2 else stem + (".pgm" if "--pgm" in flags else ".png")
        else:
            out, code = args[1], (args[2] if len(args) > 2 else "")
        words = bf_image(code)
        write_image(out, list(words))
        print(f"wrote {out}: 39 interpreter rows + {(len(words)-156+3)//4} program rows ({len(words)-156} chars)")
        if "--run" in flags: do_run(words, steps)
    elif cmd == "run" and len(args) >= 2:
        p = args[1]
        words = bf_image(open(p, encoding="utf-8", errors="replace").read()) if p.lower().endswith(".bf") else read_image(p)
        do_run(words, steps)
    elif cmd == "dump" and len(args) >= 2:
        w = read_image(args[1])
        for i in range(0, len(w), 4):
            print("".join(f"{x:016b}" for x in w[i:i+4]))
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
