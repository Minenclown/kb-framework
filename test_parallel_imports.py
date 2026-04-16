#!/usr/bin/env python3
"""
Test: Parallel Imports Without Deadlock
========================================

Verifies that all 4 deadlock/race-condition fixes work correctly:
1. Module-level get_instance() replaced with lazy functions
2. sys.path.insert() removed from import-time code
3. KBConfig.get_instance() race condition fixed
4. Logger-cache race condition fixed

Run: python3 test_parallel_imports.py
"""

import threading
import sys
import time
import importlib
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure kb-framework is importable
sys.path.insert(0, str(Path(__file__).parent))


def reset_kb_state():
    """Reset all singleton state between test rounds."""
    # Clear kb modules from sys.modules
    to_delete = [k for k in sys.modules if k.startswith('kb')]
    for k in to_delete:
        del sys.modules[k]
    
    # We can't easily call KBConfig.reset() without importing it first,
    # but clearing sys.modules effectively resets everything


def test_parallel_import_config(num_threads=10):
    """Test: Parallel imports of KBConfig.get_instance() don't deadlock."""
    print(f"\n{'='*60}")
    print(f"TEST 1: Parallel KBConfig.get_instance() ({num_threads} threads)")
    print(f"{'='*60}")
    
    errors = []
    success_count = threading.Event()
    success_count._count = 0
    count_lock = threading.Lock()
    
    def import_config(thread_id):
        try:
            from kb.base.config import KBConfig
            config = KBConfig.get_instance()
            with count_lock:
                success_count._count += 1
            return (thread_id, True, str(config.base_path))
        except Exception as e:
            return (thread_id, False, traceback.format_exc())
    
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=import_config, args=(i,), name=f"ConfigThread-{i}")
        threads.append(t)
    
    start = time.time()
    for t in threads:
        t.start()
    
    for t in threads:
        t.join(timeout=10)  # 10s timeout = deadlock detection
        if t.is_alive():
            errors.append(f"Thread {t.name} DEADLOCKED (did not finish in 10s)")
    
    elapsed = time.time() - start
    
    # Collect results
    results = {}
    for t in threads:
        # Threads stored results via return; we need to check differently
        pass
    
    if errors:
        print(f"❌ FAILED: {len(errors)} errors")
        for e in errors:
            print(f"   {e}")
        return False
    
    if success_count._count == num_threads:
        print(f"✅ PASSED: All {num_threads} threads got config in {elapsed:.3f}s")
        return True
    else:
        print(f"⚠️  PARTIAL: {success_count._count}/{num_threads} succeeded in {elapsed:.3f}s")
        return False


def test_parallel_import_library(num_threads=10):
    """Test: Parallel imports of knowledge_base modules don't deadlock."""
    print(f"\n{'='*60}")
    print(f"TEST 2: Parallel knowledge_base imports ({num_threads} threads)")
    print(f"{'='*60}")
    
    errors = []
    results = []
    results_lock = threading.Lock()
    
    def import_library(thread_id):
        try:
            from kb.knowledge_base.chroma_integration import ChromaIntegration, _get_default_chroma_path
            path = _get_default_chroma_path()
            
            from kb.knowledge_base.chroma_plugin import ChromaDBPlugin, _get_default_chroma_path as cp_path
            from kb.knowledge_base.embedding_pipeline import EmbeddingPipeline, _get_default_chroma_path as ep_path
            
            # Verify lazy functions return same value
            with results_lock:
                results.append({
                    'thread': thread_id,
                    'path': path,
                    'all_same': (path == cp_path() == ep_path())
                })
            return (thread_id, True, path)
        except Exception as e:
            with results_lock:
                results.append({
                    'thread': thread_id,
                    'error': str(e)
                })
            return (thread_id, False, traceback.format_exc())
    
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=import_library, args=(i,), name=f"LibThread-{i}")
        threads.append(t)
    
    start = time.time()
    for t in threads:
        t.start()
    
    for t in threads:
        t.join(timeout=10)
        if t.is_alive():
            errors.append(f"Thread {t.name} DEADLOCKED (did not finish in 10s)")
    
    elapsed = time.time() - start
    
    if errors:
        print(f"❌ FAILED: {len(errors)} deadlocked threads")
        for e in errors:
            print(f"   {e}")
        return False
    
    success = sum(1 for r in results if 'error' not in r)
    all_same = all(r.get('all_same', False) for r in results if 'error' not in r)
    
    if success == num_threads and all_same:
        print(f"✅ PASSED: All {num_threads} threads imported successfully in {elapsed:.3f}s")
        print(f"   All lazy paths consistent: {all_same}")
        return True
    elif success == num_threads:
        print(f"⚠️  PARTIAL: All threads succeeded but paths inconsistent")
        return False
    else:
        print(f"❌ FAILED: {success}/{num_threads} threads succeeded")
        for r in results:
            if 'error' in r:
                print(f"   Thread {r['thread']}: {r['error']}")
        return False


def test_parallel_logger(num_threads=10):
    """Test: Parallel logger creation doesn't race."""
    print(f"\n{'='*60}")
    print(f"TEST 3: Parallel KBLogger.get_logger() ({num_threads} threads)")
    print(f"{'='*60}")
    
    errors = []
    results = []
    results_lock = threading.Lock()
    
    def get_logger(thread_id):
        try:
            from kb.base.logger import KBLogger
            log_name = f"kb.test.thread_{thread_id}"
            logger = KBLogger.get_logger(log_name)
            with results_lock:
                results.append({'thread': thread_id, 'logger': logger.name})
            return (thread_id, True, logger.name)
        except Exception as e:
            with results_lock:
                results.append({'thread': thread_id, 'error': str(e)})
            return (thread_id, False, traceback.format_exc())
    
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=get_logger, args=(i,), name=f"LoggerThread-{i}")
        threads.append(t)
    
    start = time.time()
    for t in threads:
        t.start()
    
    for t in threads:
        t.join(timeout=10)
        if t.is_alive():
            errors.append(f"Thread {t.name} DEADLOCKED")
    
    elapsed = time.time() - start
    
    if errors:
        print(f"❌ FAILED: {len(errors)} errors")
        return False
    
    success = sum(1 for r in results if 'error' not in r)
    if success == num_threads:
        print(f"✅ PASSED: All {num_threads} threads got loggers in {elapsed:.3f}s")
        return True
    else:
        print(f"❌ FAILED: {success}/{num_threads} threads succeeded")
        return False


def test_config_race_condition():
    """Test: KBConfig.get_instance() with different base_path values is thread-safe."""
    print(f"\n{'='*60}")
    print(f"TEST 4: KBConfig get_instance() race condition (mixed base_path)")
    print(f"{'='*60}")
    
    errors = []
    results = []
    results_lock = threading.Lock()
    
    def get_config_with_path(thread_id, base_path):
        try:
            from kb.base.config import KBConfig
            config = KBConfig.get_instance(base_path=base_path)
            with results_lock:
                results.append({
                    'thread': thread_id,
                    'base_path': str(config.base_path),
                    'requested': str(base_path) if base_path else 'None'
                })
            return (thread_id, True)
        except Exception as e:
            with results_lock:
                results.append({
                    'thread': thread_id,
                    'error': str(e),
                    'requested': str(base_path) if base_path else 'None'
                })
            return (thread_id, False, traceback.format_exc())
    
    # Mix of None (fast path) and explicit paths
    import tempfile
    tmp1 = tempfile.mkdtemp(prefix="kb_test1_")
    tmp2 = tempfile.mkdtemp(prefix="kb_test2_")
    
    threads = []
    for i in range(10):
        if i % 3 == 0:
            path = tmp1
        elif i % 3 == 1:
            path = tmp2
        else:
            path = None
        t = threading.Thread(
            target=get_config_with_path, 
            args=(i, path),
            name=f"ConfigRace-{i}"
        )
        threads.append(t)
    
    start = time.time()
    for t in threads:
        t.start()
    
    for t in threads:
        t.join(timeout=10)
        if t.is_alive():
            errors.append(f"Thread {t.name} DEADLOCKED")
    
    elapsed = time.time() - start
    
    # Clean up
    import shutil
    shutil.rmtree(tmp1, ignore_errors=True)
    shutil.rmtree(tmp2, ignore_errors=True)
    
    if errors:
        print(f"❌ FAILED: {len(errors)} deadlocked threads")
        for e in errors:
            print(f"   {e}")
        return False
    
    success = sum(1 for r in results if 'error' not in r)
    if success == 10:
        print(f"✅ PASSED: All 10 threads completed without exception in {elapsed:.3f}s")
        return True
    else:
        print(f"❌ FAILED: {success}/10 threads succeeded")
        for r in results:
            if 'error' in r:
                print(f"   Thread {r['thread']} (requested={r['requested']}): {r['error']}")
        return False


def test_no_sys_path_mutation():
    """Test: Importing knowledge_base modules doesn't mutate sys.path."""
    print(f"\n{'='*60}")
    print(f"TEST 5: No sys.path mutation on import")
    print(f"{'='*60}")
    
    # Record sys.path before
    path_before = sys.path.copy()
    
    # Import all three problematic modules
    try:
        from kb.knowledge_base.chroma_integration import ChromaIntegration
        from kb.knowledge_base.chroma_plugin import ChromaDBPlugin
        from kb.knowledge_base.embedding_pipeline import EmbeddingPipeline
    except Exception as e:
        print(f"❌ FAILED: Import error: {e}")
        return False
    
    # Check sys.path after
    path_after = sys.path.copy()
    
    # Filter out our own test insert
    test_insert = str(Path(__file__).parent)
    new_entries = [
        p for p in path_after 
        if p not in path_before and p != test_insert
    ]
    
    if not new_entries:
        print(f"✅ PASSED: sys.path unchanged after imports")
        return True
    else:
        print(f"❌ FAILED: sys.path gained {len(new_entries)} new entries:")
        for e in new_entries:
            print(f"   + {e}")
        return False


def test_import_order_independence():
    """Test: Different import orders all work without deadlock."""
    print(f"\n{'='*60}")
    print(f"TEST 6: Import order independence")
    print(f"{'='*60}")
    
    import itertools
    
    modules = [
        'kb.base.config',
        'kb.base.logger', 
        'kb.library.knowledge_base.chroma_integration',
        'kb.library.knowledge_base.chroma_plugin',
        'kb.library.knowledge_base.embedding_pipeline',
    ]
    
    # Test a subset of permutations (full 5! = 120 is too many)
    # Test the most problematic orderings
    test_orders = [
        # Library first (most likely to cause issues before fix)
        ['kb.library.knowledge_base.chroma_integration', 'kb.library.knowledge_base.chroma_plugin', 'kb.library.knowledge_base.embedding_pipeline', 'kb.base.config', 'kb.base.logger'],
        # Config first (should always work)
        ['kb.base.config', 'kb.base.logger', 'kb.library.knowledge_base.chroma_integration', 'kb.library.knowledge_base.chroma_plugin', 'kb.library.knowledge_base.embedding_pipeline'],
        # Interleaved
        ['kb.base.config', 'kb.library.knowledge_base.chroma_integration', 'kb.base.logger', 'kb.library.knowledge_base.chroma_plugin', 'kb.library.knowledge_base.embedding_pipeline'],
    ]
    
    all_passed = True
    for order in test_orders:
        # Reset state
        to_delete = [k for k in list(sys.modules.keys()) if k.startswith('kb')]
        for k in to_delete:
            del sys.modules[k]
        
        # Need to re-reset KBConfig singleton
        try:
            from kb.base.config import KBConfig
            KBConfig.reset()
        except:
            pass
        
        # Clear again after reset
        to_delete = [k for k in list(sys.modules.keys()) if k.startswith('kb')]
        for k in to_delete:
            del sys.modules[k]
        
        try:
            for mod in order:
                importlib.import_module(mod)
            print(f"   ✅ Order: {' → '.join(m.split('.')[-1] for m in order)}")
        except Exception as e:
            print(f"   ❌ Order: {' → '.join(m.split('.')[-1] for m in order)} — {e}")
            all_passed = False
    
    if all_passed:
        print(f"✅ PASSED: All import orders work")
    else:
        print(f"❌ FAILED: Some import orders failed")
    
    return all_passed


def main():
    print("=" * 60)
    print("KB-Framework Deadlock Fix Verification")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"Threads available: {threading.active_count()}")
    
    results = []
    
    # Run all tests
    results.append(("Parallel Config Import", test_parallel_import_config(10)))
    results.append(("Parallel Library Import", test_parallel_import_library(10)))
    results.append(("Parallel Logger Creation", test_parallel_logger(10)))
    results.append(("Config Race Condition", test_config_race_condition()))
    results.append(("No sys.path Mutation", test_no_sys_path_mutation()))
    results.append(("Import Order Independence", test_import_order_independence()))
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All deadlock fixes verified!")
    else:
        print("\n⚠️  Some tests failed — review the output above")
    
    return passed == total


if __name__ == "__main__":
    import os
    os.environ.setdefault("KB_BASE_PATH", "/tmp/kb_test_parallel")
    success = main()
    sys.exit(0 if success else 1)