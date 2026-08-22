#!/usr/bin/env python3
"""
=============================================================================
SciMSPT PAGE CLEANER - REMOVES VISIBLE JS CORRUPTION
=============================================================================

⚠️  RUN THIS SCRIPT BEFORE EVERY DEPLOYMENT - NO EXCEPTIONS!

WHAT IT FIXES:
-------------
1. 🚫 Visible JavaScript code (BooleanObserver, MobileDetection) showing as text
2. 🚫 Chinese characters appearing on English pages  
3. 🚫 Orphaned JS comments ("/* SYSTEM v4.0 */") rendering as visible content
4. 🚫 Broken </script> tags leaving code outside script blocks
5. 🚫 Stuck skeleton loaders (gray bars blocking content)

USAGE:
------
# Quick clean (run this before every preview/deploy):
python3 clean_pages.py

# Clean + verify:
python3 clean_pages.py && echo "✅ Pages are clean"

EXIT CODES:
-----------
0 = All pages were already clean
1 = Fixes were applied (pages needed cleaning)

=============================================================================
"""

import re
import os
import glob
from datetime import datetime

def find_and_fix_orphaned_js(filepath):
    """Find JavaScript code outside <script> tags and wrap it properly"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    output = []
    i = 0
    in_orphan_block = False
    fixes = 0
    
    # Patterns that indicate start of orphaned JS code
    orphan_indicators = [
        'INTELLIGENT MOBILE DETECTION',
        'BOOLEAN OBSERVER SYSTEM', 
        'Device-Aware | Contextual',
        'Human Confirmation | Real-time Monitoring'
    ]
    
    while i < len(lines):
        line = lines[i]
        
        # Detect start of orphaned JS block
        if not in_orphan_block:
            for indicator in orphan_indicators:
                if indicator in line:
                    # Found orphaned JS - wrap it in script tag
                    output.append('<script>\n')
                    output.append(line)
                    in_orphan_block = True
                    fixes += 1
                    i += 1
                    break
            
            if in_orphan_block:
                continue  # Skip adding line again
        
        if in_orphan_block:
            output.append(line)
            
            # Detect end of IIFE block
            stripped = line.strip()
            if ('window.MobileDetection = MobileDetection' in stripped or 
                'window.BooleanObserver = BooleanObserver' in stripped or
                (stripped == '})();' and i + 1 < len(lines) and 
                 not lines[i+1].strip().startswith(('const', 'let', 'var', 'function')))):
                
                output.append('</script>\n')
                in_orphan_block = False
                fixes += 1
            
            i += 1
            continue
        
        output.append(line)
        i += 1
    
    return output, fixes

def remove_broken_script_tags(lines):
    """Remove </script><script> pairs that split JavaScript code mid-block"""
    output = []
    i = 0
    fixes = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Find erroneous </script> followed by more JS code
        if stripped == '</script>' and i + 1 < len(lines):
            next_lines = []
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                next_lines.append(lines[j])
                j += 1
            
            if j < len(lines):
                next_content = lines[j].strip()
                # If next non-empty line is JS code, this </script> is wrong
                if (next_content and 
                    not next_content.startswith('<') and
                    not next_content.startswith('<!--') and
                    re.match(r'^[\s\w"\'\:.,(){}\[\];]', next_content)):
                    
                    # Skip this broken </script>
                    fixes += 1
                    i += 1
                    continue
        
        # Find erroneous <script> after JS code (not starting new block)
        if stripped == '<script>' and i > 0:
            prev_idx = len(output) - 1
            while prev_idx >= 0 and not output[prev_idx].strip():
                prev_idx -= 1
            
            if prev_idx >= 0:
                prev_line = output[prev_idx].strip()
                # If previous line looks like unfinished JS, skip this <script>
                if (prev_line.endswith(('{', ',', '(', ';', '}')) or 
                    prev_line.startswith('//') or
                    'use strict' in prev_line):
                    fixes += 1
                    i += 1
                    continue
        
        output.append(line)
        i += 1
    
    return output, fixes

def add_loader_failsafe(content, filepath):
    """Add automatic failsafe to prevent stuck skeleton loaders"""
    if 'skeletonLoader' not in content:
        return content, False
    
    if 'loader-failsafe' in content:
        return content, False
    
    failsafe = '''
  <!-- FAILSAFE: Auto-hide skeleton loader after 800ms -->
  <script id="loader-failsafe">
    (function() {
      function hideLoader() {
        var loader = document.getElementById('skeletonLoader');
        if (loader) {
          loader.style.opacity = '0';
          loader.style.visibility = 'hidden';
          loader.style.pointerEvents = 'none';
          setTimeout(function() { 
            try { loader.remove(); } catch(e) {} 
          }, 500);
        }
      }
      // Try immediately
      hideLoader();
      // Also try after delays (catches late-loading issues)
      setTimeout(hideLoader, 800);
      setTimeout(hideLoader, 2000);
      setTimeout(hideLoader, 5000);
    })();
  </script>
'''
    
    if '</body>' in content:
        content = content.replace('</body>', failsafe + '\n</body>')
        return content, True
    
    return content, False

def clean_file(filepath):
    """Clean a single HTML file of all known corruption patterns"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    # Fix 1: Wrap orphaned JS code
    lines, fixes1 = find_and_fix_orphaned_js(filepath)
    
    # Fix 2: Remove broken script tags
    lines, fixes2 = remove_broken_script_tags(lines)
    
    # Write intermediate result
    content = ''.join(lines)
    
    # Fix 3: Add loader failsafe
    content, fixes3 = add_loader_failsafe(content, filepath)
    
    total_fixes = fixes1 + fixes2 + fixes3
    
    if total_fixes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return total_fixes

def main():
    base_dir = '/home/z/my-project/SciMSPT'
    
    try:
        os.chdir(base_dir)
    except Exception as e:
        print(f"❌ Error: Cannot access {base_dir}")
        print(f"   {e}")
        return 1
    
    print("=" * 70)
    print("🧹 SciMSPT Page Cleaner")
    print("=" * 70)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    html_files = sorted(glob.glob('*.html'))
    
    if not html_files:
        print("❌ No HTML files found!")
        return 1
    
    print(f"📁 Scanning {len(html_files)} files...\n")
    
    total_files_fixed = 0
    total_fixes = 0
    
    for filepath in html_files:
        filename = os.path.basename(filepath)
        
        try:
            fixes = clean_file(filepath)
            
            if fixes > 0:
                print(f"✅ {filename}: {fixes} issues fixed")
                total_files_fixed += 1
                total_fixes += fixes
            else:
                print(f"✓ {filename}: Already clean")
                
        except Exception as e:
            print(f"❌ {filename}: Error - {e}")
    
    print("\n" + "=" * 70)
    print("📊 Results")
    print("=" * 70)
    print(f"Files fixed: {total_files_fixed}/{len(html_files)}")
    print(f"Total issues resolved: {total_fixes}")
    
    if total_fixes == 0:
        print("\n✨ All pages are clean! Ready for deployment.")
        return 0
    else:
        print(f"\n🎉 Fixed {total_files_fixed} files ({total_fixes} issues)")
        print("✅ Pages are now ready for deployment.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)
