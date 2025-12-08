
__all__ = ["SynchronousInteractionExt"]

import asyncio
from functools import partial
import omni.ext
import omni.kit.ui
import omni.ui as ui
from .property_window import PropertyWindowExample


class SynchronousInteractionExt(omni.ext.IExt):
    """灯光控制系统扩展"""

    WINDOW_NAME = "Omni Interaction Behav"
    MENU_PATH = f"Window/{WINDOW_NAME}"

    def on_startup(self):
        """扩展启动时调用"""
        self._window = None
        self._menu = None
        
        ui.Workspace.set_show_window_fn(SynchronousInteractionExt.WINDOW_NAME, partial(self.show_window, None))

        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            self._menu = editor_menu.add_item(
                SynchronousInteractionExt.MENU_PATH, self.show_window, toggle=True, value=True
            )

        ui.Workspace.show_window(SynchronousInteractionExt.WINDOW_NAME)

    def on_shutdown(self):
        """扩展关闭时调用"""
        self._menu = None
        if self._window:
            self._window.destroy()
            self._window = None

        ui.Workspace.set_show_window_fn(SynchronousInteractionExt.WINDOW_NAME, None)

    def _set_menu(self, value):
        """设置菜单项的开/关状态"""
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(SynchronousInteractionExt.MENU_PATH, value)

    async def _destroy_window_async(self):
        """异步销毁窗口"""
        await omni.kit.app.get_app().next_update_async()
        if self._window:
            self._window.destroy()
            self._window = None

    def _visiblity_changed_fn(self, visible):
        """窗口可见性改变时的回调函数"""
        self._set_menu(visible)
        if not visible:
            asyncio.ensure_future(self._destroy_window_async())

    def show_window(self, menu, value):
        """显示或隐藏窗口"""
        if value:
            self._window = PropertyWindowExample(SynchronousInteractionExt.WINDOW_NAME, width=450, height=600)
            self._window.set_visibility_changed_fn(self._visiblity_changed_fn)
        elif self._window:
            self._window.visible = False