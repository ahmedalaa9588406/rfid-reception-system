# replaced simple static imports with a robust loader that supports:
#  - new package modules under gui/dialogs/
#  - legacy single-file gui/dialogs.py (loaded dynamically if present)
import importlib.util
import sys
from pathlib import Path

# Try to import package submodules (if they exist)
TransactionsDialog = None
ReportDialog = None
SettingsDialog = None
ViewAllCardsDialog = None

pkg_dir = Path(__file__).parent

# Helper to import a module if file exists
def _import_submodule(module_name, file_name):
    module_path = pkg_dir / file_name
    if module_path.exists():
        spec = importlib.util.spec_from_file_location(f"rfid_reception.gui.dialogs.{module_name}", str(module_path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod
    return None

# Try loading individual dialog modules (new split layout)
mod = _import_submodule('transactions_dialog', 'transactions_dialog.py')
if mod:
    TransactionsDialog = getattr(mod, 'TransactionsDialog', None)

mod = _import_submodule('report_dialog', 'report_dialog.py')
if mod:
    ReportDialog = getattr(mod, 'ReportDialog', None)

mod = _import_submodule('settings_dialog', 'settings_dialog.py')
if mod:
    SettingsDialog = getattr(mod, 'SettingsDialog', None)

mod = _import_submodule('view_all_cards_dialog', 'view_all_cards_dialog.py')
if mod:
    ViewAllCardsDialog = getattr(mod, 'ModernViewAllCardsDialog', None)

# If no split modules found, try to load legacy single-file gui/dialogs.py
if not any([TransactionsDialog, ReportDialog, SettingsDialog, ViewAllCardsDialog]):
    legacy_path = Path(__file__).parent.parent / 'dialogs.py'
    if legacy_path.exists():
        spec = importlib.util.spec_from_file_location("rfid_reception.gui._legacy_dialogs", str(legacy_path))
        legacy = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = legacy
        spec.loader.exec_module(legacy)
        TransactionsDialog = getattr(legacy, 'TransactionsDialog', None)
        ReportDialog = getattr(legacy, 'ReportDialog', None)
        SettingsDialog = getattr(legacy, 'SettingsDialog', None)

# Provide a minimal fallback to avoid attribute errors (keeps imports safe)
# If the legacy module was loaded above, prefer its dialog classes for any that are still None.
if 'legacy' in locals():
    if TransactionsDialog is None:
        TransactionsDialog = getattr(legacy, 'TransactionsDialog', None)
    if ReportDialog is None:
        ReportDialog = getattr(legacy, 'ReportDialog', None)
    if SettingsDialog is None:
        SettingsDialog = getattr(legacy, 'SettingsDialog', None)
    if ViewAllCardsDialog is None:
        ViewAllCardsDialog = getattr(legacy, 'ViewAllCardsDialog', None)
    ManualCardInsertDialog = getattr(legacy, 'ManualCardInsertDialog', None)
else:
    # Ensure the name exists even if no legacy module was found
    ManualCardInsertDialog = None

__all__ = ['TransactionsDialog', 'ReportDialog', 'SettingsDialog', 'ManualCardInsertDialog', 'ViewAllCardsDialog']
