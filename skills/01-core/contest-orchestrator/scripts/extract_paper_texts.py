# -*- coding: utf-8 -*-
"""批量提取 50 篇国赛论文文本：文本版用 pymupdf，扫描版用 rapidocr
产出: dataset/paper_texts/<year>_<topic>_<file>.txt
"""
import argparse
import os, sys, json, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pymupdf

def extract_text(path):
    """返回 (text, method)"""
    doc = pymupdf.open(path)
    pages_text = []
    for i in range(doc.page_count):
        t = doc[i].get_text()
        pages_text.append(t)
    total = sum(len(t) for t in pages_text)
    if total > 1000:
        return '\n'.join(pages_text), 'pymupdf'
    # 扫描版：OCR
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR
    engine = RapidOCR()
    ocr_pages = []
    for i in range(doc.page_count):
        pix = doc[i].get_pixmap(dpi=200)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = img[:, :, :3]
        result, _ = engine(img)
        if result:
            ocr_pages.append('\n'.join(line[1] for line in result))
    return '\n\n'.join(ocr_pages), 'rapidocr'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('index', help='JSON index containing year/topic/file/path entries')
    parser.add_argument('--out', default=str(os.path.join(os.path.dirname(__file__), '..', 'dataset', 'paper_texts')))
    args = parser.parse_args()
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    idx = json.load(open(args.index, encoding='utf-8'))
    results = {'ok': [], 'fail': []}
    for item in idx:
        key = f"{item['year']}_{item['topic']}_{os.path.splitext(item['file'])[0]}"
        safe = key.replace('：', '_')[:80] + '.txt'
        out_path = os.path.join(out_dir, safe)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
            results['ok'].append(key)
            print(f'[skip] {key} (已存在)')
            continue
        try:
            t0 = time.time()
            text, method = extract_text(item['path'])
            with io.open(out_path, 'w', encoding='utf-8') as f:
                f.write(text)
            results['ok'].append(key)
            print(f'[{"OCR" if method=="rapidocr" else "TXT"}] {key} ({len(text)} chars, {time.time()-t0:.0f}s)')
        except Exception as exc:
            results['fail'].append((key, str(exc)[:80]))
            print(f'[FAIL] {key}: {str(exc)[:80]}')
    print(f'成功 {len(results["ok"])} / 失败 {len(results["fail"])}')
    for key, error in results['fail']:
        print(f'  FAIL {key}: {error}')
    return 0 if not results['fail'] else 1


if __name__ == '__main__':
    sys.exit(main())
