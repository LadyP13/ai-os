"""
Permission definitions for AI-OS agent capabilities.
"""

PERMISSIONS = {
    "filesystem_read": {
        "label": "Read Files",
        "description": "Browse and read files on this computer",
        "icon": "📖",
        "default": False
    },
    "filesystem_write": {
        "label": "Write Files",
        "description": "Create and edit files",
        "icon": "✏️",
        "default": False
    },
    "filesystem_delete": {
        "label": "Delete Files",
        "description": "Delete files and folders",
        "icon": "🗑️",
        "default": False
    },
    "post_telegram": {
        "label": "Post to Telegram",
        "description": "Send messages to Telegram channels",
        "icon": "📱",
        "default": True
    },
    "organize_files": {
        "label": "Organize Files",
        "description": "Move and sort files (requires approval per action)",
        "icon": "📁",
        "default": False
    },
    "leave_notes": {
        "label": "Leave Notes",
        "description": "Create notes and messages on your desktop",
        "icon": "💌",
        "default": True
    },
    "update_memory": {
        "label": "Update Memory",
        "description": "Write to memory/notes repository",
        "icon": "🧠",
        "default": True
    },
    "git_push": {
        "label": "Git Push",
        "description": "Push commits to GitHub",
        "icon": "⬆️",
        "default": False
    },
    "create_art": {
        "label": "Create Art",
        "description": "Generate and save creative content",
        "icon": "🎨",
        "default": True
    }
}
