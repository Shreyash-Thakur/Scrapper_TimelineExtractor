from pathlib import Path
p = Path('urls.txt')
print('exists', p.exists())
text = p.read_text(encoding='utf-8')
lines = [l for l in text.splitlines() if l.strip() and not l.strip().startswith('#')]
print('total lines:', len(lines))
print('first 5:')
for i, l in enumerate(lines[:5], 1):
    print(i, l)
