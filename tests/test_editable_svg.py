"""Isolated conversion checks; optional image dependencies are not required by Atlas CI."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

ENTRY = Path(__file__).resolve().parents[1] / 'skills/image-to-editable-svg/scripts/vectorize.py'
spec = importlib.util.spec_from_file_location('local_svg', ENTRY)
svg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(svg)


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.labels = self.root / 'labels.json'
        self.data = {'canvas': [320, 180], 'labels': [{'id': 'caption', 'lines': [
            {'text': 'Sample', 'box': [40, 40, 90, 60]}]}]}
        self.labels.write_text(json.dumps(self.data))

    def test_canvas_and_duplicate_and_bounds_fail(self):
        with self.assertRaises(ValueError): svg.manifest(self.labels, (321, 180))
        self.data['labels'].append(self.data['labels'][0])
        self.labels.write_text(json.dumps(self.data))
        with self.assertRaises(ValueError): svg.manifest(self.labels)
        self.data['labels'] = self.data['labels'][:1]
        self.data['labels'][0]['lines'][0]['box'] = [0, 0, 400, 10]
        self.labels.write_text(json.dumps(self.data))
        with self.assertRaises(ValueError): svg.manifest(self.labels)

    def fixture(self):
        root = ET.Element(svg.SVG + 'svg')
        ET.SubElement(root, svg.SVG + 'path', {'id': 'geometry-1', 'fill': '#112233', 'd': 'M0 0h20v20z'})
        ET.SubElement(root, svg.SVG + 'text', {'id': 'caption-line-1'}).text = 'Sample'
        path = self.root / 'fixture.svg'
        ET.ElementTree(root).write(path)
        return path

    def test_edits_and_audit_and_no_overwrite(self):
        path = self.fixture(); before = path.read_bytes()
        self.assertEqual(svg.audit(path, self.data)['text_lines'], 1)
        output = self.root / 'edited.svg'
        svg.edit(path, output, 'caption-line-1', 'Modified', 'geometry-1', '#ABCDEF')
        self.assertEqual(path.read_bytes(), before)
        changed = ET.parse(output).getroot()
        self.assertEqual(changed.find(svg.SVG + 'text').text, 'Modified')
        self.assertEqual(changed.find(svg.SVG + 'path').get('fill'), '#ABCDEF')
        with self.assertRaises(FileExistsError): svg.edit(path, output, 'caption-line-1', 'Again')
        with self.assertRaises(ValueError): svg.edit(path, self.root / 'bad.svg', 'unknown', 'X')
        tree = ET.parse(path); ET.SubElement(tree.getroot(), svg.SVG + 'image'); tree.write(path)
        with self.assertRaises(ValueError): svg.audit(path, self.data)

    def test_real_tracing_when_dependencies_available(self):
        try:
            from PIL import Image, ImageDraw
            import vtracer, numpy
        except ImportError:
            self.skipTest('Run with the conversion runtime for tracing integration checks')
        image = Image.new('RGB', (320, 180), 'white')
        drawing = ImageDraw.Draw(image)
        drawing.rectangle((15, 20, 140, 100), fill='#bfe6f2', outline='black', width=2)
        drawing.text((40, 42), 'Sample', fill='black')
        path = self.root / 'input.png'; image.save(path); before = path.read_bytes()
        output = self.root / 'result'
        result = svg.rebuild(path, self.labels, output)
        self.assertGreater(result['paths'], 0)
        self.assertEqual(result['images'], 0)
        self.assertEqual(result['text_lines'], 1)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(json.loads((output / 'report.json').read_text())['cleanup_outside_boxes'], 0)
        with self.assertRaises(FileExistsError): svg.rebuild(path, self.labels, output)
        # A textured region cannot silently be erased using a guessed flat fill.
        for x in range(40, 90):
            for y in range(40, 60): image.putpixel((x,y), ((x*7)%256, (y*11)%256, (x*y)%256))
        image.save(path)
        with self.assertRaises(ValueError): svg.rebuild(path, self.labels, self.root / 'mixed')


if __name__ == '__main__': unittest.main()
