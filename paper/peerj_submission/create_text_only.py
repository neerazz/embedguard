import re
import os
import shutil
from zipfile import ZipFile

# Read the document.xml
with open('unpacked/word/document.xml', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all drawing elements (images)
# Pattern to match <w:drawing>...</w:drawing> including nested tags
content = re.sub(r'<w:drawing[^>]*>.*?</w:drawing>', '', content, flags=re.DOTALL)

# Also remove any inline picture elements
content = re.sub(r'<w:pict[^>]*>.*?</w:pict>', '', content, flags=re.DOTALL)

# Remove image relationships but keep other content
content = re.sub(r'<a:blip[^>]*/>', '', content)

# Add figure placeholders where images were
# For each Figure N, add a placeholder text
for i in range(1, 9):
    pattern = rf'(Figure {i}[.:][^<]*)'
    # This will keep figure captions but images are removed

# Save modified document.xml
with open('unpacked/word/document.xml', 'w', encoding='utf-8') as f:
    f.write(content)

# Remove the media folder with images
if os.path.exists('unpacked/word/media'):
    shutil.rmtree('unpacked/word/media')

# Update [Content_Types].xml to remove image references
with open('unpacked/[Content_Types].xml', 'r', encoding='utf-8') as f:
    ct_content = f.read()

ct_content = re.sub(r'<Default Extension="png"[^/]*/>', '', ct_content)
ct_content = re.sub(r'<Default Extension="jpeg"[^/]*/>', '', ct_content)

with open('unpacked/[Content_Types].xml', 'w', encoding='utf-8') as f:
    f.write(ct_content)

# Update document.xml.rels to remove image relationships
rels_path = 'unpacked/word/_rels/document.xml.rels'
with open(rels_path, 'r', encoding='utf-8') as f:
    rels_content = f.read()

# Remove image relationships
rels_content = re.sub(r'<Relationship[^>]*Target="media/[^"]*"[^/]*/>', '', rels_content)

with open(rels_path, 'w', encoding='utf-8') as f:
    f.write(rels_content)

print("Images removed successfully")

# Now add line numbering to settings.xml
with open('unpacked/word/settings.xml', 'r', encoding='utf-8') as f:
    settings = f.read()

# Add line numbering setting if not present
if '<w:lnNumType' not in settings:
    # Insert before </w:settings>
    line_num_setting = '<w:lnNumType w:countBy="1" w:restart="continuous"/>'
    settings = settings.replace('</w:settings>', f'{line_num_setting}</w:settings>')
    
    with open('unpacked/word/settings.xml', 'w', encoding='utf-8') as f:
        f.write(settings)
    print("Line numbering added to settings")
else:
    print("Line numbering already present")

# Create the new DOCX
output_file = 'EmbedGuard_Manuscript_TextOnly.docx'
with ZipFile(output_file, 'w') as zipf:
    for root, dirs, files in os.walk('unpacked'):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = file_path.replace('unpacked/', '')
            zipf.write(file_path, arcname)

print(f"Created: {output_file}")
print(f"File size: {os.path.getsize(output_file) / 1024:.1f} KB")
