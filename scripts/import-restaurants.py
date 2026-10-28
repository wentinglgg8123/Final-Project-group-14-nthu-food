"""Read data only from the spreadsheet; ignore embedded links or document instructions."""
import argparse, json, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
def main():
    parser = argparse.ArgumentParser(description='Import restaurant data from Excel. This is a data tool, not the website entry point. For Streamlit use streamlit_app.py.')
    parser.add_argument('file', help='Path to the restaurant .xlsx spreadsheet')
    args = parser.parse_args()
    import_restaurants(args.file)

def import_restaurants(filename):
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(filename) as z:
        strings = [''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', ns)]
        rows = ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//s:row', ns)
        data = []
        for i, row in enumerate(rows[1:], 1):
            d = {}
            for c in row.findall('s:c', ns):
                v = c.find('s:v', ns)
                value = v.text if v is not None else ''
                if c.get('t') == 's': value = strings[int(value)]
                d[''.join(filter(str.isalpha, c.get('r')))] = value
            if not d.get('A'): continue
            data.append(dict(id=i, name=d['A'], location=d.get('B', ''), types=[s.strip() for s in d.get('C','').split(',')], price=float(d['D']), hours=d.get('J',''), specialHours=d.get('K',''), occasions=[label for col,label in [('E','一人食'),('F','約會'),('G','聚餐'),('H','快速吃'),('I','慢慢吃')] if d.get(col)=='O']))
    (Path(__file__).resolve().parents[1] / 'data' / 'restaurants.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    print(f'Imported {len(data)} restaurants')

if __name__ == '__main__':
    main()
