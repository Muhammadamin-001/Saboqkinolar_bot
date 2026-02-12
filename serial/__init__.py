# serial/__init__.py
"""
🎞️ SERIAL MODULI
Seriallarni yuklash, o'chirish va boshqarish uchun barcha funksiyalar
"""


from .serial_db import (
    create_serial,
    add_season,
    add_episode,
    add_full_files,
    delete_serial,
    delete_season,
    delete_episode,  # ✅ SHUDAN IMPORT QILINADI
    get_serial,
    get_all_serials,
    get_season,
    get_episode,
    check_episode_exists,
    check_serial_code_exists,
)

from .serial_states import (
    is_serial_uploading,
    clear_serial_state,
    get_serial_state,
    set_serial_state,
    get_state_step,
    is_waiting_for,
)

from .serial_user import (
    show_serial_for_user,
    show_episodes_for_user,
    send_episode_to_user,
)

from utils.admin_utils import (
    is_admin,
    user_panel, 
    admin_panel
    )
from config.settings import ADMIN_ID

__all__ = [
    
    
    #serial_db.py
    'create_serial',
    'add_season',
    'add_episode',
    'add_full_files',
    'delete_serial',
    'delete_season',
    'delete_episode',  # ✅ SHUDAN
    'get_serial',
    'get_all_serials',
    'get_season',
    'get_episode',
    'check_episode_exists',
    'check_serial_code_exists',
    
    # serial_states.py
    'is_serial_uploading',
    'clear_serial_state',
    'get_serial_state',
    'set_serial_state',
    'get_state_step',
    'is_waiting_for',
    
    # serial_user.py
    'show_serial_for_user',
    'show_episodes_for_user',
    'send_episode_to_user',
    
    # config.settings
    'ADMIN_ID',
    #utils
    'is_admin',
    'user_panel', 
    'admin_panel'
]