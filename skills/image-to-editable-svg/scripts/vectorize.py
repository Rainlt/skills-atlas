#!/usr/bin/env python3
"""Local tracing plus human-verified live text; no OCR or remote recognition."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import shutil
import time
import xml.etree.ElementTree as ET

NS = 'http://www.w3.org/2000/svg'
SVG = '{' + NS + '}'
ET.register_namespace('', NS)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def manifest(path, size=None):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    canvas = data['canvas']
    if (len(canvas) != 2 or any(type(n) is not int or n <= 0 for n in canvas)
            or (size is not None and list(size) != canvas)):
        raise ValueError('Canvas must match image dimensions')
    ids = {'reconstructed-labels'}
    for label in data['labels']:
        key = label['id']
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', key) or key in ids or key.startswith('geometry-'):
            raise ValueError('Invalid or duplicate label id')
        if not label['lines']:
            raise ValueError('Empty label')
        ids.add(key)
        for i, line in enumerate(label['lines'], 1):
            text_id = key + '-line-' + str(i)
            if text_id in ids:
                raise ValueError('Duplicate generated text id')
            ids.add(text_id)
            box = line['box']
            if (len(box) != 4 or any(type(n) is not int for n in box)
                    or not (0 <= box[0] < box[2] <= canvas[0] and 0 <= box[1] < box[3] <= canvas[1])):
                raise ValueError('Text box outside canvas')
            if not isinstance(line['text'], str) or not line['text'].strip():
                raise ValueError('Text must be nonempty')
            for field in ('font_size', 'x', 'baseline'):
                if field in line and (not isinstance(line[field], (float, int))
                                      or not math.isfinite(line[field])):
                    raise ValueError('Invalid text position or size')
            if line.get('font_size', 1) <= 0:
                raise ValueError('Font size must be positive')
    return data


def expected_text(data):
    return {label['id'] + '-line-' + str(i): line['text']
            for label in data['labels'] for i, line in enumerate(label['lines'], 1)}


def audit(path, data):
    root = ET.parse(path).getroot()
    if root.tag != SVG + 'svg':
        raise ValueError('Not a namespaced SVG')
    actual = {n.get('id'): ''.join(n.itertext()) for n in root.iter(SVG + 'text')}
    image_count = sum(1 for n in root.iter() if n.tag.rsplit('}', 1)[-1] == 'image')
    unsafe = [n for n in root.iter() if n.tag.rsplit('}', 1)[-1] in ('script', 'foreignObject')]
    text_nodes = list(root.iter(SVG + 'text'))
    if actual != expected_text(data) or len(actual) != len(text_nodes) or image_count or unsafe:
        raise ValueError('Text mismatch, embedded image, duplicate text ID or active content')
    return {'paths': len(list(root.iter(SVG + 'path'))), 'text_lines': len(text_nodes),
            'images': image_count, 'text_matches_manifest': True,
            'scope': 'Structural checks only; visual and scientific correctness require review.'}


def rebuild(image, labels, output):
    from PIL import Image, ImageDraw
    import numpy as np
    import vtracer
    image, output = Path(image), Path(output)
    original_hash = hashlib.sha256(image.read_bytes()).hexdigest()
    with Image.open(image) as source:
        rgba = source.convert('RGBA')
    white = Image.new('RGBA', rgba.size, 'white')
    white.alpha_composite(rgba)
    flat = white.convert('RGB')
    data = manifest(labels, flat.size)
    clean = flat.copy()
    mask = np.zeros((flat.height, flat.width), dtype=bool)
    backgrounds = []
    for label in data['labels']:
        for line in label['lines']:
            x0, y0, x1, y1 = line['box']
            color, frequency = Counter(flat.crop((x0, y0, x1, y1)).get_flattened_data()).most_common(1)[0]
            ratio = frequency / ((x1 - x0) * (y1 - y0))
            if ratio < .45:
                raise ValueError('Non-flat background in ' + label['id'] + '; review the text box')
            ImageDraw.Draw(clean).rectangle((x0, y0, x1 - 1, y1 - 1), fill=color)
            mask[y0:y1, x0:x1] = True
            backgrounds.append({'label': label['id'], 'box': line['box'], 'color': color, 'ratio': ratio})
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(image, output / ('original' + image.suffix.lower()))
    write_json(output / 'labels.json', data)
    flat.save(output / 'original-white.png')
    clean.save(output / 'cleaned.png')
    options = dict(colormode='color', hierarchical='stacked', mode='spline', filter_speckle=4,
                   color_precision=6, layer_difference=16, corner_threshold=60, length_threshold=4.0,
                   max_iterations=10, splice_threshold=45, path_precision=3)
    timings = {}
    for source, target in [('original-white.png', 'baseline.svg'), ('cleaned.png', 'geometry.svg')]:
        start = time.perf_counter()
        vtracer.convert_image_to_svg_py(str(output / source), str(output / target), **options)
        timings[target] = time.perf_counter() - start
    root = ET.parse(output / 'geometry.svg').getroot()
    root.set('viewBox', '0 0 {} {}'.format(*data['canvas']))
    for i, path in enumerate(root.iter(SVG + 'path'), 1):
        path.set('id', 'geometry-' + str(i))
    texts = ET.SubElement(root, SVG + 'g', {'id': 'reconstructed-labels'})
    for label in data['labels']:
        group = ET.SubElement(texts, SVG + 'g', {'id': label['id']})
        for i, line in enumerate(label['lines'], 1):
            x0, y0, x1, y1 = line['box']
            attrs = {'id': label['id'] + '-line-' + str(i),
                     'x': str(line.get('x', x0)), 'y': str(line.get('baseline', y1 - 2)),
                     'font-size': str(line.get('font_size', (y1 - y0) * .85)),
                     'font-family': line.get('font_family', 'sans-serif'),
                     'font-weight': line.get('font_weight', 'bold'), 'fill': line.get('fill', '#000000')}
            ET.SubElement(group, SVG + 'text', attrs).text = line['text']
    ET.ElementTree(root).write(output / 'editable.svg', encoding='utf-8', xml_declaration=True)
    stats = audit(output / 'editable.svg', data)
    outside_changes = int(np.any(np.asarray(flat) != np.asarray(clean), axis=2)[~mask].sum())
    if hashlib.sha256(image.read_bytes()).hexdigest() != original_hash or outside_changes:
        raise ValueError('Input changed or cleanup escaped declared boxes')
    write_json(output / 'report.json', dict(input_sha256=original_hash, canvas=data['canvas'],
               labels=len(data['labels']), cleanup_outside_boxes=outside_changes, backgrounds=backgrounds,
               versions={k: importlib.metadata.version(k) for k in ('vtracer', 'Pillow', 'numpy')},
               trace_options=options, trace_seconds=timings, svg=stats,
               visual_review='pending; inspect cleaned image, geometry, labels and edit proof'))
    return {'output': str(output.resolve()), **stats}


def edit(source, output, text_id=None, text=None, path_id=None, fill=None):
    tree = ET.parse(source)
    if bool(text_id) != (text is not None) or bool(path_id) != (fill is not None) or not (text_id or path_id):
        raise ValueError('Provide a complete text and/or path edit')
    if fill is not None and not re.fullmatch(r'#[0-9a-fA-F]{6}', fill):
        raise ValueError('Fill must be #RRGGBB')
    for key, tag, attribute, value in [(text_id, 'text', None, text), (path_id, 'path', 'fill', fill)]:
        if key is None:
            continue
        nodes = [n for n in tree.iter(SVG + tag) if n.get('id') == key]
        if len(nodes) != 1:
            raise ValueError('Target must identify exactly one ' + tag + ': ' + key)
        if attribute:
            nodes[0].set(attribute, value)
        else:
            if len(nodes[0]):
                raise ValueError('Nested text needs a deliberate sub-span edit')
            nodes[0].text = value
    with open(output, 'xb') as handle:
        tree.write(handle, encoding='utf-8', xml_declaration=True)
    return {'edited': str(Path(output).resolve())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    inspect = commands.add_parser('inspect'); inspect.add_argument('image')
    build = commands.add_parser('rebuild')
    for key in ('image', 'manifest', 'output'): build.add_argument(key)
    check = commands.add_parser('audit'); check.add_argument('svg'); check.add_argument('manifest')
    change = commands.add_parser('edit'); change.add_argument('svg'); change.add_argument('output')
    for key in ('text-id', 'text', 'path-id', 'fill'): change.add_argument('--' + key)
    args = parser.parse_args()
    if args.command == 'inspect':
        from PIL import Image
        with Image.open(args.image) as image:
            result = {'canvas': list(image.size), 'mode': image.mode}
    elif args.command == 'rebuild': result = rebuild(args.image, args.manifest, args.output)
    elif args.command == 'audit': result = audit(args.svg, manifest(args.manifest))
    else: result = edit(args.svg, args.output, args.text_id, args.text, args.path_id, args.fill)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
