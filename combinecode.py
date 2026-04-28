import os

output_file = 'all_project_code.txt'
root_dir = r'c:\Users\saeid\ragmind discussed' # Update this to your project root directory # Update this to your project root directory

exclude_dirs = {'venv', '.git', '__pycache__', 'node_modules', '.idea', 'qdrant_data', 'qdrant_data_test', 'uploads', '.history'}

valid_extensions = {'.py', '.js', '.ts', '.html', '.css', '.tsx', '.jsx', '.sql', '.sh', '.bat', '.json', '.md', '.yml'}

with open(output_file, 'w', encoding='utf-8') as outfile:
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for file in filenames:
            ext = os.path.splitext(file)[1].lower()
            if ext in valid_extensions or file in {'Dockerfile', '.env.example'}:
                filepath = os.path.join(dirpath, file)
                rel_path = os.path.relpath(filepath, root_dir)
                if file == 'combine_code.py' or file == output_file:
                    continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        
                    outfile.write(f"\n{'='*80}\n")
                    outfile.write(f"File: {rel_path}\n")
                    outfile.write(f"{'='*80}\n\n")
                    outfile.write(content)
                    outfile.write("\n")
                except Exception as e:
                    print(f"Failed to read {rel_path}: {e}")

print(f"Code combined successfully into {output_file}")
