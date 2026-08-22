#!/usr/bin/env python3
"""
EMERGENCY PAGE CLEANER - Fixes visible JS corruption on SciMSPT pages
=====================================================================
RUN THIS BEFORE EVERY DEPLOYMENT - NO EXCEPTIONS!
"""

import re
import os
import glob
from datetime import datetime

def clean_file(filepath):
    """Remove all visible JavaScript corruption from an HTML file"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        original = content
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    in_script = False
    fixes = 0
    
    # Patterns that indicate JS header comments (should be removed if outside scripts)
    js_header_patterns = [
        r'INTELLIGENT MOBILE DETECTION',
        r'BOOLEAN OBSERVER SYSTEM',
        r'Device-Aware.*Contextual.*Helpful',
        r'Human Confirmation.*Real-time Monitoring',
    ]
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Track script context
        if '<script' in stripped and '</script>' not in stripped:
            in_script = True
        
        if '</script>' in stripped:
            # Check if NEXT lines are JS code (meaning this close was premature)
            look_ahead_idx = i + 1
            while look_ahead_idx < len(lines) and not lines[look_ahead_idx].strip():
                look_ahead_idx += 1
            
            if look_ahead_idx < len(lines):
                next_content = lines[look_ahead_idx].strip()
                # If next non-empty line looks like JS, this </script> is wrong
                if (next_content and 
                    not next_content.startswith('<') and 
                    not next_content.startswith('<!--') and
                    (re.match(r'^\s*(const|let|var|function|class|if|for|while|return|//|/\*)', next_content) or
                     any(pattern in next_content for pattern in ['MobileDetection', 'BooleanObserver']))):
                    
                    # This </script> is breaking JS flow - SKIP it
                    fixed_lines.append(f'  <!-- REMOVED BROKEN </script> at line {i+1} -->')
                    i += 1
                    fixes += 1
                    continue
            
            in_script = False
        
        # Skip orphaned JS header comments outside scripts
        if not in_script and re.match(r'^\s*/\*[=~-]+\s*$', stripped):
            # Check if this is an orphaned comment block
            block_end = min(i + 6, len(lines))
            block_text = '\n'.join(lines[i:block_end])
            
            if any(re.search(pattern, block_text, re.IGNORECASE) for pattern in js_header_patterns):
                # Skip entire comment block
                start_i = i
                while i < len(lines):
                    if '*/' in lines[i]:
                        i += 1
                        break
                    i += 1
                
                # Also skip metadata lines after comment
                while i < len(lines):
                    next_s = lines[i].strip()
                    if not next_s or next_s.startswith('<'):
                        break
                    if re.match(r'^[A-Za-z]+\s*\|', next_s) or 'Device-Aware' in next_s:
                        i += 1
                        continue
                    break
                
                fixes += 1
                continue
        
        # Skip standalone <script> tags that break JS flow
        if not in_script and stripped == '<script>':
            # Check previous line
            prev_idx = len(fixed_lines) - 1
            while prev_idx >= 0 and not fixed_lines[prev_idx].strip():
                prev_idx -= 1
            
            if prev_idx >= 0:
                prev_line = fixed_lines[prev_idx].strip()
                # If previous line looks like unfinished JS, skip this <script>
                if prev_line.endswith(('{', ',', '(', 'return', '}', ';')) or prev_line.startswith('//') or 'use strict' in prev_line:
                    fixes += 1
                    i += 1
                    continue
        
        fixed_lines.append(line)
        
        # Update script state for opening tags
        if '<script' in stripped and '</script>' not in stripped:
            in_script = True
        
        i += 1
    
    new_content = '\n'.join(fixed_lines)
    
    if fixes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True, fixes
    
    return False, 0

def add_loader_failsafe(filepath):
    """Add failsafe to prevent stuck skeleton loaders"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'skeletonLoader' not in content:
        return False
    
    # Check if failsafe already exists
    if 'loader-failsafe' in content or 'forceHideLoader' in content:
        return False
    
    failsafe = '''
  <!-- FAILSAFE: Force hide skeleton loader after 800ms -->
  <script id="loader-failsafe">
    (function() {
      var checkLoader = setInterval(function() {
        var loader = document.getElementById('skeletonLoader');
        if (loader) {
          clearInterval(checkLoader);
          setTimeout(function() {
            loader.style.opacity = '0';
            loader.style.visibility = 'hidden';
            loader.style.pointerEvents = 'none';
            setTimeout(function() { 
              if (loader && loader.parentNode) loader.remove(); 
            }, 500);
          }, 800);
        }
      }, 100);
      // Stop checking after 10 seconds
      setTimeout(function() { clearInterval(checkLoader); }, 10000);
    })();
  </script>
'''
    
    if '</body>' in content:
        content = content.replace('</body>', failsafe + '\n</body>')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    base_dir = '/home/z/my-project/SciMSPT'
    os.chdir(base_dir)
    
    print("=" * 70)
    print("🚨 EMERGENCY PAGE CLEANER")
    print("=" * 70)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    html_files = sorted(glob.glob('*.html'))
    print(f"📁 Found {len(html_files)} HTML files to clean\n")
    
    total_fixes = 0
    cleaned_files = []
    loader_fixed = []
    
    for filepath in html_files:
        filename = os.path.basename(filepath)
        
        # Clean JS corruption
        fixed, count = clean_file(filepath)
        if fixed:
            print(f"✅ {filename}: Removed {count} corruption items")
            total_fixes += count
            cleaned_files.append(filename)
        
        # Add loader failsafe
        if add_loader_failsafe(filepath):
            print(f"🛡️ {filename}: Added skeleton loader failsafe")
            loader_fixed.append(filename)
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Files with JS corruption fixed: {len(cleaned_files)}")
    print(f"Total corruption items removed: {total_fixes}")
    print(f"Files with loader failsafe added: {len(loader_fixed)}")
    
    if total_fixes == 0 and not loader_fixed:
        print("\n✅ All pages were already clean!")
    else:
        print("\n✅ Cleaning complete!")
    
    return len(cleaned_files) > 0 or len(loader_fixed) > 0

if __name__ == '__main__':
    changed = main()
    exit(0 if not changed else 1)  # Exit 0 if no changes needed
