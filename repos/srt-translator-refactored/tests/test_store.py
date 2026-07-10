"""
tests/test_store.py — Unit tests for thread-safe EventBus and GlobalStore.
"""

import unittest
from app.core.store import EventBus, GlobalStore


class TestStore(unittest.TestCase):
    def test_event_bus_subscribe_emit(self):
        bus = EventBus()
        called_args = []
        
        def callback(*args, **kwargs):
            called_args.append((args, kwargs))
            
        bus.subscribe("test_event", callback)
        bus.emit("test_event", 1, 2, name="test")
        
        self.assertEqual(len(called_args), 1)
        self.assertEqual(called_args[0], ((1, 2), {"name": "test"}))

    def test_event_bus_unsubscribe(self):
        bus = EventBus()
        called_count = 0
        
        def callback():
            nonlocal called_count
            called_count += 1
            
        bus.subscribe("click", callback)
        bus.emit("click")
        bus.unsubscribe("click", callback)
        bus.emit("click")
        
        self.assertEqual(called_count, 1)

    def test_global_store_state_changes(self):
        store = GlobalStore()
        
        # Test default values
        self.assertFalse(store.get("is_running"))
        self.assertEqual(store.get("progress_pct"), 0.0)
        
        # Listen to state changes
        changed_keys = []
        
        def on_change(key, value, old_val):
            changed_keys.append((key, value, old_val))
            
        store.event_bus.subscribe("state_changed", on_change)
        
        # Modify state
        store.set("is_running", True)
        self.assertTrue(store.get("is_running"))
        
        self.assertEqual(len(changed_keys), 1)
        self.assertEqual(changed_keys[0], ("is_running", True, False))
        
        # Modify again to same value (should not trigger event)
        store.set("is_running", True)
        self.assertEqual(len(changed_keys), 1)

    def test_global_store_key_specific_event(self):
        store = GlobalStore()
        specific_called = False
        
        def on_is_running_changed(value, old_val):
            nonlocal specific_called
            specific_called = (value, old_val)
            
        store.event_bus.subscribe("state_changed:is_running", on_is_running_changed)
        store.set("is_running", True)
        
        self.assertEqual(specific_called, (True, False))


if __name__ == "__main__":
    unittest.main()
