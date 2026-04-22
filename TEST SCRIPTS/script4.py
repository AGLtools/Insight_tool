import zipfile
try:
    with zipfile.ZipFile(r'c:\AGL Analytics\DATA\template.pptx', 'r') as z:
        files = [f for f in z.namelist() if 'embeddings' in f or 'ppt/slides/' in f]
        for f in sorted(files):
            print(f)
except Exception as e:
    print(f"Error: {e}")
