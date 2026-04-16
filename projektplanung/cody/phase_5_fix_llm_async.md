# Phase 5 Fix: llm.py Async/Sync Bridge

**Problem:** `_run_async()` in `kb/commands/llm.py` nutzt `asyncio.run()` in einem laufenden Event Loop, was einen RuntimeError verursacht.

## Aktueller problematischer Code

```python
if loop and loop.is_running():
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()  # <- FEHLER
```

`asyncio.run()` erstellt einen neuen Event Loop und kann nicht in einem laufenden Loop verwendet werden.

## Lösung

```python
def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Kein Loop aktiv - normal starten
        return asyncio.run(coro)
    
    if loop and loop.is_running():
        # Loop ist aktiv - run_until_complete nutzen
        future = asyncio.ensure_future(coro)
        return loop.run_until_complete(future)
    else:
        return asyncio.run(coro)
```

## Schritte

### 1. Backup erstellen
```bash
cp ~/projects/kb-framework/kb/commands/llm.py ~/projects/kb-framework/kb/commands/llm.py.bak
```

### 2. _run_async() finden und ersetzen

Suche die Funktion:
```bash
grep -n "_run_async" ~/projects/kb-framework/kb/commands/llm.py
```

Ersetze den gesamten Block.

### 3. Config Key Mapping erweitern (optional)

Die Analyse zeigt auch dass `_CONFIG_KEY_TO_ENV` unvollständig ist:
- Fehlende: `temperature`, `max_tokens`, `batch_size`, `max_retries`, `retry_delay`

Falls relevant, nach dem Async-Fix auch das Mapping vervollständigen.

## Verification

```bash
cd ~/projects/kb-framework

python3 -c "
from kb.commands.llm import LLMCommand
import asyncio

# Test _run_async funktioniert
async def test_coro():
    return 'success'

result = LLMCommand()._run_async(test_coro())
print(f'✓ _run_async works: {result}')

# Test im laufenden Loop
async def test_with_loop():
    loop = asyncio.get_running_loop()
    result = await LLMCommand()._run_async(test_coro())
    return result

asyncio.run(test_with_loop())
print('✓ Works in running loop')
"
```

## Rollback

```bash
cp ~/projects/kb-framework/kb/commands/llm.py.bak \
   ~/projects/kb-framework/kb/commands/llm.py
```

## Checkliste

- [ ] Backup erstellt
- [ ] _run_async() mit run_until_complete gefixt
- [ ] Verification Tests bestanden
- [ ] Works both with and without running event loop