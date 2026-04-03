import os
import fnmatch

def generate_markdown(root_dir, output_file):
    # Directories and files to ignore
    ignore_dirs = ['.git', '.venv', 'node_modules', '__pycache__', 'dist', 'build', '.next', '.idea', '.vscode']
    ignore_files = ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', '*.pyc', '*.pyo', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.webp', '*.svg', 'generate_codebase_md.py']
    
    with open(output_file, 'w', encoding='utf-8') as md_file:
        md_file.write("# Full Codebase\n\n")
        
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Mutate dirnames in-place to skip ignored directories
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
            
            for filename in filenames:
                # Check against ignore file patterns
                should_ignore = False
                for pattern in ignore_files:
                    if fnmatch.fnmatch(filename, pattern):
                        should_ignore = True
                        break
                
                if should_ignore:
                    continue
                
                filepath = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(filepath, root_dir)
                
                # Determine language for markdown syntax highlighting
                ext = os.path.splitext(filename)[1].lower()
                lang = ''
                if ext in ['.py']: lang = 'python'
                elif ext in ['.ts', '.tsx']: lang = 'typescript'
                elif ext in ['.js', '.jsx']: lang = 'javascript'
                elif ext in ['.css']: lang = 'css'
                elif ext in ['.html']: lang = 'html'
                elif ext in ['.json']: lang = 'json'
                elif ext in ['.md']: lang = 'markdown'
                elif ext in ['.sh']: lang = 'bash'
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    md_file.write(f"## {rel_path}\n\n")
                    md_file.write(f"```{lang}\n")
                    md_file.write(content)
                    if not content.endswith('\n'):
                        md_file.write('\n')
                    md_file.write("```\n\n")
                except Exception as e:
                    md_file.write(f"## {rel_path}\n\n")
                    md_file.write(f"*(Could not read file: {e})*\n\n")

if __name__ == '__main__':
    root = r"c:\Users\akars\OneDrive\Desktop\kuber attack path visualizer"
    out_file = os.path.join(root, "CODEBASE.md")
    generate_markdown(root, out_file)
    print(f"Codebase exported to {out_file}")
