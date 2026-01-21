"""
ui/dialogs/__init__.py
UI dialogs package initialization
"""

from ui.dialogs.setup_wizard import SetupWizard
from ui.dialogs.settings_dialog import SettingsDialog

__all__ = [
    'SetupWizard',
    'SettingsDialog'
]