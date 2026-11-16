"""Fill Investor Caution Score row and Figure 4.1 in each company chapter. Share prices stay Pending."""
import copy, glob, io, os, re, sys, zipfile
import docx
from docx.shared import Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from caution_score import caution, num

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
OLD_RULE = "The Investor Caution Score is pending because its scoring rule is not in the workbooks or the thesis draft."
NEW_RULE = ("The Investor Caution Score uses a rule inferred from the CG Power chapter: Pustylnick flags, plus 0.5 for an "
            "Altman Z'' grey zone and 1.0 for distress, 0.5 for negative ROA and 1.0 more below -30%, 1.5 for Beneish above -1.78, "
            "and 0.5 for two or more Montier flags, capped at 8. The rule reproduces the six CG Power values. It is not a validated scale.")
OLD_END = "The Investor Caution Score and the verified share prices are still needed to complete this chapter."
NEW_END = ("The verified share prices are still needed to complete this chapter. The Investor Caution Score follows an inferred rule, "
           "so read it as indicative.")


def chart(years, scores, path):
    fig, ax = plt.subplots(figsize=(9, 3.2), dpi=200)
    fig.patch.set_facecolor("#f4f4f0"); ax.set_facecolor("#f4f4f0")
    ax.plot(years, scores, color="#1f4e79", lw=3, marker="o", ms=9)
    for x, y in zip(years, scores):
        ax.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0, 10), ha="center", fontsize=10, color="#1b2f3a")
    ax.set_ylim(0, 8.5); ax.set_yticks(range(0, 9))
    ax.set_ylabel("Investor Caution Score", fontsize=13, color="#1b2f3a")
    ax.set_xlabel("Financial Year", fontsize=13, color="#1b2f3a")
    ax.grid(True, color="#e6e6e0", lw=0.8); [s.set_visible(False) for s in ax.spines.values()]
    ax.tick_params(colors="#1b2f3a")
    fig.tight_layout(); fig.savefig(path, facecolor=fig.get_facecolor()); plt.close(fig)


def set_text(p, text):
    for r in p.runs[1:]:
        r._r.getparent().remove(r._r)
    p.runs[0].text = text


summary = []
for path in sorted(glob.glob(os.path.join(SRC, "*.docx"))):
    name = os.path.basename(path)
    d = docx.Document(path)
    t = d.tables[0]
    hdr = [c.text for c in t.rows[0].cells][1:]
    row = {r.cells[0].text.split(" (")[0].strip(): r for r in t.rows}
    get = lambda key: [c.text for c in row[key].cells][1:]
    M = [num(x) for x in get("Beneish M-Score")] if "Beneish M-Score" in row else [num(x) for x in get([k for k in row if k.startswith("Beneish")][0])]
    Z = [num(x) for x in get([k for k in row if k.startswith("Altman")][0])]
    R = [num(x) for x in get([k for k in row if k.startswith("Dechow")][0])]
    P = [int(num(x)) for x in get([k for k in row if k.startswith("Pustylnick")][0])]
    C = [int(num(x)) for x in get([k for k in row if k.startswith("Montier")][0])]
    cr = row[[k for k in row if k.startswith("Investor Caution")][0]]
    if all(c.text.strip() != "Pending" for c in cr.cells[1:]):
        d.save(os.path.join(OUT, name)); summary.append((name, "unchanged (already complete)", None)); continue
    S = [caution(*a) for a in zip(M, Z, R, P, C)]
    for cell, s in zip(cr.cells[1:], S):
        para = cell.paragraphs[0]
        if para.runs:
            set_text(para, f"{s:.1f}")
        else:
            para.add_run(f"{s:.1f}")
    import math
    extra = ' Beneish was not computed for this company, so the score carries no Beneish points.' if any(math.isnan(x) for x in M) else ''
    paras = d.paragraphs
    for p in paras:
        if OLD_RULE in p.text:
            for r in p.runs:
                if OLD_RULE in r.text: r.text = r.text.replace(OLD_RULE, NEW_RULE + extra)
            if OLD_RULE in p.text: set_text(p, p.text.replace(OLD_RULE, NEW_RULE + extra))
        if OLD_END in p.text:
            set_text(p, p.text.replace(OLD_END, NEW_END))
    ph = next(p for p in paras if p.text.startswith("Pending. This figure needs the Investor Caution Score method"))
    png = io.BytesIO(); chart(hdr, S, png); png.seek(0)
    set_text(ph, ""); ph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ph.runs[0].add_picture(png, width=Emu(6325711), height=Emu(2249142))
    # interpretation paragraphs cloned from the Figure 4.2 heading and body paragraphs
    h42 = next(p for p in paras if p.text.startswith("Interpretation of Figure 4.2"))
    body = h42._p.getnext()
    mx, mn = max(S), min(S)
    jn = lambda v: " and ".join([", ".join([h for h, x in zip(hdr, S) if x == v][:-1]) or [h for h, x in zip(hdr, S) if x == v][0]] + ([[h for h, x in zip(hdr, S) if x == v][-1]] if sum(x == v for x in S) > 1 else []))
    high = [h for h, s in zip(hdr, S) if s >= 4.0]
    txt = (f"Figure 4.1 shows the Investor Caution Score from {hdr[0]} to {hdr[-1]}. The score was highest in {jn(mx)} ({mx:.1f}) "
           f"and lowest in {jn(mn)} ({mn:.1f}). It reached 4.0 or above in {len(high)} of {len(S)} years"
           + (f" ({', '.join(high)})." if high else ".")
           + " The score applies a rule inferred from the CG Power chapter, so it ranks years within this company and is not a validated measure."
           + " It does not establish that fraud occurred.")
    new_h = copy.deepcopy(h42._p); new_b = copy.deepcopy(body)
    ph._p.addnext(new_h); new_h.addnext(new_b)
    from docx.text.paragraph import Paragraph
    set_text(Paragraph(new_h, ph._parent), "Interpretation of Figure 4.1")
    set_text(Paragraph(new_b, ph._parent), txt)
    d.save(os.path.join(OUT, name))
    summary.append((name, "amended", S))

for s in summary: print(s[0][:34].ljust(36), s[1], s[2])
