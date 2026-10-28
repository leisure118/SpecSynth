import os
import sys
import re
import argparse
import subprocess
import shutil
import glob

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==========================================
# Module 1: File Manager (FileManager)
# Responsible for merging multiple files into a single context-complete temporary file,
# and splitting them back after processing.
# ==========================================
class FileManager:
    def __init__(self):
        # Marker pattern for locating file boundaries
        self.marker_pattern = re.compile(r'/\* === MARKER: (.+?) === \*/')
        self.include_prefix = "// [AutoMerge] "

    def merge_files(self, file_list, output_path):
        """
        Merge multiple source files into one temporary file.
        Strategy: topologically order local includes, then keep the entry file last.
        Also comment out local includes to prevent redefinition.
        """
        
        # --- Helper function: detect if file contains main function definition ---
        def has_main_function(filepath):
            if not filepath.endswith('.c'):
                return False
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Match int main(...) or void main(...)
                    # \b ensures word boundary, preventing matches to 'domain' etc.
                    # ^\s* ensures main is at function start (though not strict, usually sufficient in C source files)
                    # More robust regex: find return type + main + left parenthesis
                    if re.search(r'\b(?:int|void)\s+main\s*\(', content):
                        return True
            except Exception:
                pass
            return False

        # 1. Pre-scan to find file containing main function
        main_file_path = None
        for f in file_list:
            if has_main_function(f):
                main_file_path = os.path.abspath(f)
                break # Assume only one entry file
        
        if main_file_path:
            print(f"[Merge] Detected entry file (containing main function): {os.path.basename(main_file_path)}")
        else:
            print("[Merge] No main function auto-detected, will merge in default order.")

        # 2. Resolve local include dependencies and place every dependency first.
        normalized_files = [os.path.abspath(path) for path in file_list]
        by_basename = {os.path.basename(path): path for path in normalized_files}
        framac_harness_files = []
        for path in normalized_files:
            if not path.endswith('.c') or path == main_file_path:
                continue
            with open(path, 'r', encoding='utf-8', errors='ignore') as source:
                content = source.read()
            if "__FRAMAC__" in content and re.search(r'\b(?:int|void)\s+main\s*\(', content):
                framac_harness_files.append(path)
        use_framac_harness = bool(framac_harness_files)
        if use_framac_harness:
            print("[Merge] Frama-C harness detected in: " + ", ".join(os.path.basename(path) for path in framac_harness_files))
        dependencies = {path: [] for path in normalized_files}
        include_pattern = re.compile(r'^\s*#include\s+"([^"]+)"', re.MULTILINE)
        for path in normalized_files:
            with open(path, 'r', encoding='utf-8', errors='ignore') as source:
                for include_name in include_pattern.findall(source.read()):
                    dependency = by_basename.get(os.path.basename(include_name))
                    if dependency and dependency != path:
                        dependencies[path].append(dependency)

        ordered = []
        visiting = set()
        visited = set()

        def visit(path):
            if path in visited:
                return
            if path in visiting:
                print(f"[Merge] Include cycle detected at {os.path.basename(path)}; keeping stable order.")
                return
            visiting.add(path)
            for dependency in sorted(set(dependencies[path])):
                visit(dependency)
            visiting.remove(path)
            visited.add(path)
            ordered.append(path)

        def root_key(path):
            return (2 if path == main_file_path else 0 if path.endswith('.h') else 1, path)

        for path in sorted(normalized_files, key=root_key):
            visit(path)
        if main_file_path in ordered:
            ordered.remove(main_file_path)
            ordered.append(main_file_path)
        sorted_files = ordered
        print("[Merge] Dependency order: " + " -> ".join(os.path.basename(path) for path in sorted_files))
        
        # 3. Start merging
        merged_content = []
        merged_content.append("/* === AUTO-GENERATED MERGED FILE FOR AUTOSPEC === */\n")
        
        print(f"[Merge] Merging {len(sorted_files)} files...")
        
        for filepath in sorted_files:
            filename = os.path.basename(filepath)
            # Add file anchor for later splitting
            merged_content.append(f"\n\n/* === MARKER: {filepath} === */\n")

            is_production_main = use_framac_harness and filepath == main_file_path
            if is_production_main:
                merged_content.append("#if !defined(__FRAMAC__) /* AutoMerge: use the project verification harness under Frama-C */\n")
            if filepath.endswith('.c'):
                merged_content.append("#ifdef X509_FILE_NUM\n#undef X509_FILE_NUM\n#endif\n")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                # Comment only bundled project headers. External quoted headers
                # such as Frama-C's __fc_builtin.h must remain active.
                include_match = re.match(r'^\s*#include\s+"([^"]+)"', line)
                if include_match and os.path.basename(include_match.group(1)) in by_basename:
                    merged_content.append(f"{self.include_prefix}{line}")
                else:
                    merged_content.append(line)
            if is_production_main:
                merged_content.append("#endif /* !defined(__FRAMAC__) */\n")
                    
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(merged_content)
        
        print(f"[Merge] Merge completed, output to: {output_path}")

    def split_and_write_back(self, merged_path):
        """
        [Modified version] Find final results from AutoSpec output directory and write back.
        Logic: out/{stem}_0001/{stem}_{max_iter}/{stem}_merged.c
        """
        # 1. Basic path calculation
        merged_abs_path = os.path.abspath(merged_path)
        base_dir = os.path.dirname(merged_abs_path)    # current directory
        file_name = os.path.basename(merged_abs_path)  # temp_autospec_merged.c
        file_stem = os.path.splitext(file_name)[0]     # temp_autospec_merged
        
        # 2. Locate project directory (out/temp_autospec_merged_0001)
        out_root = os.path.join(base_dir, "out")
        project_dir_name = f"{file_stem}_0001"
        project_dir_path = os.path.join(out_root, project_dir_name)

        if not os.path.exists(project_dir_path):
            print(f"[Split Error] Cannot find AutoSpec output directory: {project_dir_path}")
            print("Please check if AutoSpec ran successfully and generated the out directory.")
            return

        # 3. Find maximum iteration directory (e.g. temp_autospec_merged_0005)
        # Get all subdirectories
        try:
            subdirs = [
                d for d in os.listdir(project_dir_path) 
                if os.path.isdir(os.path.join(project_dir_path, d)) and d.startswith(file_stem)
            ]
        except OSError:
            print(f"[Split Error] Cannot read directory: {project_dir_path}")
            return

        if not subdirs:
            print(f"[Split Error] No iteration directories found in {project_dir_path}.")
            return

        # Sort to find directory with maximum suffix number
        # Assume directory name format: filename_XXXX
        subdirs.sort() # String sorting usually works for _0001, _0002
        max_iter_dir_name = subdirs[-1]
        target_dir = os.path.join(project_dir_path, max_iter_dir_name)
        print(f"[Split] Located latest iteration directory: {max_iter_dir_name}")

        # 4. Check final_result status
        result_file = os.path.join(target_dir, "final_result")
        if not os.path.exists(result_file):
            print(f"Verification failed, not performing code write-back to protect source files.")
            return

        with open(result_file, 'r', encoding='utf-8') as f:
            status = f.readline().strip()

        if status != "Pass":
            print(f"\n[Stop] AutoSpec verification result is '{status}' (not Pass).")
            print("Verification failed, not performing code write-back to protect source files.")
            return

        print(f"[Split] AutoSpec verification passed (Pass)! Preparing to write back code...")

        # 5. Get final generated C code file
        # File name format: temp_autospec_merged_merged.c
        final_c_filename = f"{file_stem}_merged.c"
        final_c_path = os.path.join(target_dir, final_c_filename)

        if not os.path.exists(final_c_path):
            print(f"[Split Error] Cannot find final code file: {final_c_path}")
            return

        # 6. Read new content and perform splitting
        with open(final_c_path, 'r', encoding='utf-8') as f:
            content = f.read()

        parts = self.marker_pattern.split(content)
        files_updated = 0
        
        # Iterate through splits (index 1 is path, index 2 is content)
        for i in range(1, len(parts), 2):
            target_path = parts[i].strip()
            raw_content = parts[i+1]
            
            # Restore commented includes
            lines = raw_content.split('\n')
            restored_lines = []
            for line in lines:
                if line.startswith(self.include_prefix):
                    restored_lines.append(line.replace(self.include_prefix, "", 1))
                else:
                    restored_lines.append(line)
            
            final_content = "\n".join(restored_lines).strip() + "\n"
            
            print(f"  -> Writing back file: {target_path}")
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            files_updated += 1
            
        print(f"[Split] Successfully updated {files_updated} source files.")

def post_process_spec_migration(file_list):
    """
    [新增后处理] 遍历所有文件，查找同名的 .c 和 .h 对。
    将 .c 中非静态函数的 ACSL 规约移动到 .h 中对应的声明处。
    """
    print("\n=== Step 3.5: 规约迁移 (Post-Process Migration) ===")
    
    # 1. 建立索引：找出输入列表中成对的 .c 和 .h
    # 格式: {'x509_utils': {'c': '.../x509_utils.c', 'h': '.../x509_utils.h'}}
    pairs = {}
    for f in file_list:
        stem = os.path.splitext(os.path.basename(f))[0]
        ext = os.path.splitext(f)[1]
        if stem not in pairs:
            pairs[stem] = {}
        pairs[stem][ext] = f

    # 正则：匹配 /*@ ... */ 块，且后面紧跟函数定义
    # Group 1: 规约内容
    # Group 2: 规约后的空白
    # Group 3: 函数名
    spec_regex = re.compile(r'(/\*@.*?\*/)(\s+)(?=(?:[\w\*]+\s+)*?(\w+)\s*\()', re.DOTALL)

    files_updated = 0

    for stem, paths in pairs.items():
        # 只有当 .c 和 .h 同时存在时才处理
        if '.c' not in paths or '.h' not in paths:
            continue
            
        c_path = paths['.c']
        h_path = paths['.h']
        
        print(f"[Migrate] 正在分析: {os.path.basename(c_path)} <-> {os.path.basename(h_path)}")

        with open(c_path, 'r', encoding='utf-8') as f:
            c_content = f.read()
        with open(h_path, 'r', encoding='utf-8') as f:
            h_content = f.read()

        is_h_modified = False
        
        def replace_callback(match):
            nonlocal h_content, is_h_modified
            
            spec_block = match.group(1)
            spacing = match.group(2)
            func_name = match.group(3)

            # 过滤 1: 如果是 Loop Invariant，绝对不移动
            if "loop invariant" in spec_block:
                return match.group(0)

            # [修改点] 改进正则：向左捕获同一行的内容 (即返回类型 int/void 等)
            # [^\n]* 匹配行首到函数名之间的所有内容 (包括返回类型)
            # \b      确保匹配到函数名的边界
            decl_pattern = re.compile(rf'([^\n]*\b{func_name}\s*\(.*?\)\s*;)', re.DOTALL)
            
            if decl_pattern.search(h_content):
                print(f"  -> 移动函数 '{func_name}' 的规约至头文件")
                
                # 使用 lambda 避免转义问题
                # 此时 m.group(1) 包含了 "int check_ia5_string(...);" 完整声明
                h_content = decl_pattern.sub(lambda m: f"{spec_block}\n{m.group(1)}", h_content, count=1)
                
                is_h_modified = True
                return spacing # 从 .c 删除
            
            return match.group(0)

        # 执行正则替换
        new_c_content = spec_regex.sub(replace_callback, c_content)

        # 如果发生了迁移，写入文件
        if is_h_modified:
            with open(c_path, 'w', encoding='utf-8') as f:
                f.write(new_c_content)
            with open(h_path, 'w', encoding='utf-8') as f:
                f.write(h_content)
            files_updated += 2

    print(f"[Migrate] 完成。更新了 {files_updated} 个文件。")

# ==========================================
# Module 2: AutoSpec Core (Core)
# Responsible for calling LLM to generate specifications and running Frama-C verification
# (In this Demo, using Mock to simulate LLM behavior)
# ==========================================
class AutoSpecCore:
    def __init__(self, model_name):
        self.model_name = model_name

    def run_external_autospec(self, target_file):
        """
        Call external AutoSpec tool.
        Command format: python3 main.py -f <target_file> -m <model_name>
        """
        cmd = [
            sys.executable,
            os.path.join(ROOT_DIR, "engine", "autospec", "main.py"),
            "-f", target_file,
            "-m", self.model_name
        ]

        
        try:
            # check=True will raise exception if command returns non-zero status code
            subprocess.run(cmd, check=True)

            # subprocess.run(cmd, check=True, capture_output=True, text=True)
            # print("[AutoSpec Core] AutoSpec execution completed.")
            
            # print("[AutoSpec Core] Execution successful.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[AutoSpec Core] Execution failed, return code: {e.returncode}")
            return False
        except Exception as e:
            print(f"[AutoSpec Core] Unknown error occurred: {e}")
            return False


def preflight_merged_file(target_file):
    """Check both normal and Frama-C preprocessing modes before using an LLM."""
    commands = [
        ["veri-clang", "-O0", "-fsyntax-only", target_file],
        [
            "frama-c",
            "-cpp-command",
            "clang -E -C -I. -I/root/.opam/default/share/frama-c/share/libc "
            "-D__FRAMAC__ -D__FC_MACHDEP_X86_64 -dD -nostdinc -m64 %1 -o %2",
            "-kernel-warn-key", "annot-error=abort",
            target_file,
        ],
    ]
    for cmd in commands:
        print("[Preflight] " + " ".join(cmd))
        completed = subprocess.run(cmd, capture_output=True, text=True)
        if completed.returncode != 0:
            print("[Preflight Error] Merged translation unit is not compilable; AutoSpec and LLM invocation were skipped.")
            print((completed.stdout or "") + (completed.stderr or ""))
            return False
    print("[Preflight] Merged translation unit compiled successfully in normal and __FRAMAC__ modes.")
    return True
        
# ==========================================
# Helper function: Cleanup
# ==========================================
def cleanup_artifacts(merged_file):
    print("\n=== Step 4: Cleanup temporary files ===")
    
    # 1. Clean up merged temporary file
    if os.path.exists(merged_file):
        try:
            os.remove(merged_file)
            # print(f"[Cleanup] Deleted merged file: {merged_file}")
        except OSError as e:
            print(f"[Cleanup Error] Failed to delete {merged_file}: {e}")
    
    # 2. Clean up intermediate files generated by AutoSpec
    # Define file patterns to clean up
    cleanup_patterns = [
        "*.c.pickle",
        "*_infilled.c",
        "*_marked.c"
    ]
    
    for pattern in cleanup_patterns:
        # glob.glob supports wildcard search
        files_to_remove = glob.glob(pattern)
        for filepath in files_to_remove:
            try:
                os.remove(filepath)
                # print(f"[Cleanup] Deleted intermediate file: {filepath}")
            except OSError as e:
                print(f"[Cleanup Error] Failed to delete {filepath}: {e}")


# ==========================================
# Main entry (Main)
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="AutoSpec Unified Workflow (Demo)")
    parser.add_argument("--init", action="store_true", help="Initialize demo C files")
    parser.add_argument("-i", "--input", nargs='+', help="Input source files (.c and .h)")
    parser.add_argument("-m", "--model", help="Model name")

    args = parser.parse_args()


    # Mode 2: Run workflow
    if not args.input:
        parser.print_help()
        return

    # Get absolute paths
    input_files = [os.path.abspath(f) for f in args.input]
    # Temporary merged file
    temp_file = os.path.abspath("project_level_temp.c")
    
    fm = FileManager()
    core = AutoSpecCore(model_name=args.model)

    try:
        print("=== Step 1: Merge ===")
        fm.merge_files(input_files, temp_file)
        if not preflight_merged_file(temp_file):
            raise RuntimeError("Merged translation unit preflight failed before AutoSpec/LLM execution.")
        
        print("\n=== Step 2: Generate & Verify ===")
        # In this large file, AutoSpec can see both Implementation and Call Site simultaneously
        autospec_ok = core.run_external_autospec(temp_file)
        if not autospec_ok:
            raise RuntimeError("AutoSpec failed; skipping split and broad fallback WP verification.")
        
        print("\n=== Step 3: Split & Write Back ===")
        # Write code with specifications back to original files
        fm.split_and_write_back(temp_file)
        post_process_spec_migration(input_files)
    
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            cleanup_artifacts(temp_file)

if __name__ == "__main__":
    main()
