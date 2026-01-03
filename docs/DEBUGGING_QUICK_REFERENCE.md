# Debugging Quick Reference

## Before Claiming a Fix

**STOP. Ask yourself:**

1. ✅ Have I observed the actual problem (not assumed)?
2. ✅ Have I created a test to verify my hypothesis?
3. ✅ Does the test confirm my hypothesis is correct?
4. ✅ Have I verified the fix works in the problem environment?
5. ✅ Have I measured the improvement (before/after)?

**If ANY answer is NO → Don't claim it's fixed yet.**

## The Process

```
OBSERVE → HYPOTHESIZE → TEST → VERIFY → DOCUMENT
```

**Never skip steps. Never assume.**

## Common Mistakes

❌ "I found the root cause!" → You found a *possible* cause
❌ "It works locally!" → Test in the actual problem environment
❌ "One more fix should do it" → Verify previous fixes first
❌ "The diagnostics will show..." → Actually check the diagnostics

## When You Confirm a Solution

1. Document in `docs/DEBUGGING_SESSIONS.md`
2. Include test scripts that verify the fix
3. Note false leads (they're valuable)
4. Record what you learned

## Quick Commands

```bash
# Run debugging helper
python scripts/debug_helper.py

# Show checklist
python scripts/debug_helper.py --checklist

# View debugging guide
cat docs/DEBUGGING_GUIDE.md
```

## Remember

**"I think I found it" ≠ "I fixed it"**

Always verify. Always test. Always document.
