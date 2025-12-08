import asyncio
import time
from functools import partial
from typing import List, Optional

import omni.ui as ui
import omni.kit.commands
import omni.usd
from pxr import Sdf

from .light_manager import LightManager
from .door_manager import DoorManager
from .ui_components import (
    main_window_style, ColorWidget, CustomCollsableFrame, 
    build_collapsable_header, _get_search_glyph,
    cl_text_gray, cl_text, cls_button_gradient,
    cl_attribute_red, build_gradient_image
)


class PropertyWindowExample(ui.Window):

    def __init__(self, title: str, delegate=None, **kwargs):
        self.__label_width = 120
        self.light_manager = LightManager()
        self.door_manager = DoorManager()
        
        # Light state variables
        self.color_temperature_enabled = True
        self.current_color = [1.0, 1.0, 1.0]
        self.current_intensity = 15000
        self.current_exposure = 1.0
        self.current_specular = 1.0
        self.current_temperature = 6500.0
        
        # Door control state variables
        self.slide_distance = 1.0
        self.hinge_angle = 90.0
        self.door_direction = "push"  # push/pull
        self.animation_speed = 1.0  # Default speed
        
        # UI control references
        self.room_combobox = None
        self.lighting_combobox = None
        self.path_field = None
        self.room_combobox_model = None
        self.lighting_combobox_model = None
        self.color_widget = None
        self.temperature_checkbox_image = None
        
        # Door control UI control references
        self.door_room_combobox = None
        self.door_combobox = None
        self.door_room_combobox_model = None
        self.door_combobox_model = None
        
        # Slider references
        self.intensity_slider = None
        self.exposure_slider = None
        self.specular_slider = None
        self.temperature_slider = None
        self.slide_distance_slider = None
        self.hinge_angle_slider = None
        self.animation_speed_slider = None

        # Input field references
        self.intensity_field = None
        self.exposure_field = None
        self.specular_field = None
        self.temperature_field = None
        self.slide_distance_field = None
        self.hinge_angle_field = None
        self.animation_speed_field = None

        # Status labels
        self.group_status_label = None
        self.selection_count_label = None
        self.door_status_label = None
        self.door_info_label = None

        # Reset button references
        self.top_reset_button = None
        self.door_reset_button = None

        # Option list storage
        self.current_room_options = []
        self.current_lighting_options = []
        self.current_door_room_options = []  # 存储房间信息字典
        self.current_door_options = []
        
        # Default value related state and control references
        self.has_recorded_defaults = False
        self.record_defaults_button = None
        self.reset_to_defaults_button = None

        # Currently selected door information
        self.current_door_info = None

        # Door operation button references
        self.open_door_btn = None
        self.close_door_btn = None

        # UI container references (for dynamic show/hide)
        self.slide_distance_container = None
        self.hinge_angle_container = None
        self.door_direction_container = None
        self.double_sliding_mode_container = None
        self.door_orientation_container = None

        super().__init__(title, **kwargs)

        self.frame.style = main_window_style
        self.frame.set_build_fn(self._build_fn)

    def destroy(self):
        """Destroy window and all its child controls"""
        super().destroy()

    @property
    def label_width(self):
        """Property label width"""
        return self.__label_width

    @label_width.setter
    def label_width(self, value):
        """Set property label width"""
        self.__label_width = value
        self.frame.rebuild()

    # ==============================================================================
    # Light control related methods
    # ==============================================================================

    def _on_search_clicked(self):
        """Search button click event"""
        try:
            search_path = self.path_field.model.get_value_as_string() if self.path_field else "/World/lights/"
            
            if not self.light_manager.check_path_exists(search_path):
                self._show_warning_message(f"Path '{search_path}' does not exist")
                return
            
            room_names = self.light_manager.get_room_names(search_path)
            
            if not room_names:
                self._show_warning_message(f"No rooms found under path '{search_path}'")
                return
            
            self._update_room_combobox(room_names)
            
            if room_names:
                self._on_room_selected(room_names[0])
            
            self._show_success_message(f"Found {len(room_names)} rooms")
            
        except Exception as e:
            self._show_error_message(f"Error during search: {str(e)}")

    def _show_warning_message(self, message):
        """Show warning message"""
        print(f"Warning: {message}")
        if self.group_status_label:
            self.group_status_label.text = message

    def _show_success_message(self, message):
        """Show success message"""
        print(f"Success: {message}")
        if self.group_status_label:
            self.group_status_label.text = message

    def _show_error_message(self, message):
        """Show error message"""
        print(f"Error: {message}")
        if self.group_status_label:
            self.group_status_label.text = message

    def _update_room_combobox(self, room_names):
        """Update room dropdown options"""
        if not self.room_combobox or not self.room_combobox_model:
            return
            
        self.current_room_options = room_names.copy()
        
        children = self.room_combobox_model.get_item_children()
        for i in range(len(children) - 1, -1, -1):
            self.room_combobox_model.remove_item(children[i])
        
        for name in room_names:
            self.room_combobox_model.append_child_item(None, ui.SimpleStringModel(name))
        
        if room_names:
            self.room_combobox.model.get_item_value_model().set_value(0)

    def _update_lighting_combobox(self, lighting_names):
        """Update lighting dropdown options"""
        if not self.lighting_combobox or not self.lighting_combobox_model:
            return
            
        self.current_lighting_options = lighting_names.copy()
        
        children = self.lighting_combobox_model.get_item_children()
        for i in range(len(children) - 1, -1, -1):
            self.lighting_combobox_model.remove_item(children[i])
        
        for name in lighting_names:
            self.lighting_combobox_model.append_child_item(None, ui.SimpleStringModel(name))
        
        if lighting_names:
            self.lighting_combobox.model.get_item_value_model().set_value(0)

    def _on_room_selected(self, room_name):
        """Room selection callback"""
        try:
            self.light_manager.current_room = room_name
            
            lights_path = self.path_field.model.get_value_as_string() if self.path_field else "/World/lights/"
            room_path = f"{lights_path.rstrip('/')}/{room_name}"
            
            lighting_names = self.light_manager.get_lighting_names(room_path)
            
            if not lighting_names:
                self._show_warning_message(f"No lighting groups found in room '{room_name}'")
                self._update_lighting_combobox([])
                self.light_manager.selected_lights = []
                self._reset_ui_to_defaults()
                self._update_defaults_buttons_state()
                return
            
            self._update_lighting_combobox(lighting_names)
            
            if lighting_names:
                self._on_lighting_selected(lighting_names[0])
            
        except Exception as e:
            self._show_error_message(f"Error selecting room: {str(e)}")

    def _on_lighting_selected(self, lighting_name):
        """Lighting group selection callback"""
        try:
            self.light_manager.current_lighting = lighting_name
            
            lights_path = self.path_field.model.get_value_as_string() if self.path_field else "/World/lights/"
            room_path = f"{lights_path.rstrip('/')}/{self.light_manager.current_room}"
            lighting_path = f"{room_path}/{lighting_name}"
            
            lights = self.light_manager.get_lights_in_lighting_group(lighting_path)
            
            if not lights:
                self._show_warning_message(f"No lights found in lighting group '{lighting_name}'")
                self.light_manager.selected_lights = []
                self._reset_ui_to_defaults()
                self._update_defaults_buttons_state()
                return
            
            self.light_manager.selected_lights = lights
            
            self._on_record_defaults()
            
            if lights:
                self._update_ui_with_light_properties(lights[0])
            
            if self.selection_count_label:
                self.selection_count_label.text = f"Selected: {len(lights)} lights"
            
            self._update_defaults_buttons_state()
            
        except Exception as e:
            self._show_error_message(f"Error selecting lighting group: {str(e)}")

    def _update_ui_with_light_properties(self, light_prim):
        """Update UI with light properties"""
        try:
            if not light_prim:
                self._reset_ui_to_defaults()
                return
                
            color = self.light_manager.get_light_color(light_prim)
            intensity = self.light_manager.get_light_intensity(light_prim)
            exposure = self.light_manager.get_light_exposure(light_prim)
            temperature = self.light_manager.get_light_color_temperature(light_prim)
            temp_enabled = self.light_manager.is_color_temperature_enabled(light_prim)
            specular = self.light_manager.get_light_specular(light_prim)
            
            self.current_color = color
            self.current_intensity = intensity
            self.current_exposure = exposure
            self.current_temperature = temperature
            self.color_temperature_enabled = temp_enabled
            self.current_specular = specular
            
            async def update_ui_async():
                await asyncio.sleep(0.1)
                if self.color_widget:
                    self.color_widget.set_color(color)
                
                if self.intensity_slider:
                    self.intensity_slider.model.set_value(intensity)
                if self.intensity_field:
                    self.intensity_field.model.set_value(intensity)
                
                if self.exposure_slider:
                    self.exposure_slider.model.set_value(exposure)
                if self.exposure_field:
                    self.exposure_field.model.set_value(exposure)
                
                if self.temperature_slider:
                    self.temperature_slider.model.set_value(temperature)
                if self.temperature_field:
                    self.temperature_field.model.set_value(temperature)
                
                if self.specular_slider:
                    self.specular_slider.model.set_value(specular)
                if self.specular_field:
                    self.specular_field.model.set_value(specular)
                
                if self.temperature_checkbox_image:
                    self.temperature_checkbox_image.name = "checked" if temp_enabled else "unchecked"
            
            asyncio.ensure_future(update_ui_async())
            
        except Exception as e:
            self._show_error_message(f"Error updating UI properties: {str(e)}")

    def _reset_ui_to_defaults(self):
        """Reset UI to default values"""
        self.current_color = [1.0, 1.0, 1.0]
        self.current_intensity = 15000
        self.current_exposure = 1.0
        self.current_specular = 1.0
        self.current_temperature = 6500.0
        self.color_temperature_enabled = True
        
        if self.color_widget:
            self.color_widget.set_color(self.current_color)
        if self.intensity_slider:
            self.intensity_slider.model.set_value(self.current_intensity)
        if self.intensity_field:
            self.intensity_field.model.set_value(self.current_intensity)
        if self.exposure_slider:
            self.exposure_slider.model.set_value(self.current_exposure)
        if self.exposure_field:
            self.exposure_field.model.set_value(self.current_exposure)
        if self.temperature_slider:
            self.temperature_slider.model.set_value(self.current_temperature)
        if self.temperature_field:
            self.temperature_field.model.set_value(self.current_temperature)
        if self.specular_slider:
            self.specular_slider.model.set_value(self.current_specular)
        if self.specular_field:
            self.specular_field.model.set_value(self.current_specular)
        if self.temperature_checkbox_image:
            self.temperature_checkbox_image.name = "checked"

    def _on_color_changed(self, color):
        """Color change callback"""
        try:
            for light_prim in self.light_manager.selected_lights:
                self.light_manager.set_light_color(light_prim, color)
        except Exception as e:
            self._show_error_message(f"Error setting color: {str(e)}")

    def _on_intensity_changed(self, intensity):
        """Intensity change callback"""
        try:
            for light_prim in self.light_manager.selected_lights:
                self.light_manager.set_light_intensity(light_prim, intensity)
        except Exception as e:
            self._show_error_message(f"Error setting intensity: {str(e)}")

    def _on_exposure_changed(self, exposure):
        """Exposure change callback"""
        try:
            for light_prim in self.light_manager.selected_lights:
                self.light_manager.set_exposure(light_prim, exposure)
        except Exception as e:
            self._show_error_message(f"Error setting exposure: {str(e)}")

    def _on_specular_changed(self, specular):
        """Specular change callback"""
        try:
            for light_prim in self.light_manager.selected_lights:
                self.light_manager.set_specular(light_prim, specular)
        except Exception as e:
            self._show_error_message(f"Error setting specular: {str(e)}")

    def _on_temperature_changed(self, temperature):
        """Color temperature change callback"""
        try:
            for light_prim in self.light_manager.selected_lights:
                self.light_manager.set_color_temperature(light_prim, temperature)
        except Exception as e:
            self._show_error_message(f"Error setting color temperature: {str(e)}")

    def _on_temperature_toggled(self, enabled):
        """Color temperature toggle callback"""
        try:
            self.color_temperature_enabled = enabled
            
            success_count = 0
            total_lights = len(self.light_manager.selected_lights)
            
            for light_prim in self.light_manager.selected_lights:
                if self.light_manager.enable_color_temperature(light_prim, enabled):
                    success_count += 1
            
            if total_lights > 0:
                if success_count == total_lights:
                    self._show_success_message(f"Successfully set color temperature enabled state for {success_count} lights")
                else:
                    self._show_warning_message(f"Partial success: {success_count}/{total_lights} lights")
            else:
                self._show_warning_message("No selected lights to set")
                
        except Exception as e:
            self._show_error_message(f"Error toggling color temperature: {str(e)}")

    def _on_turn_on_lights(self):
        """Turn on all lights"""
        try:
            for light_prim in self.light_manager.selected_lights:
                self.light_manager.set_light_enabled(light_prim, True)
            self._show_success_message(f"Turned on {len(self.light_manager.selected_lights)} lights")
        except Exception as e:
            self._show_error_message(f"Error turning on lights: {str(e)}")

    def _on_turn_off_lights(self):
        """Turn off all lights"""
        try:
            for light_prim in self.light_manager.selected_lights:
                self.light_manager.set_light_enabled(light_prim, False)
            self._show_success_message(f"Turned off {len(self.light_manager.selected_lights)} lights")
        except Exception as e:
            self._show_error_message(f"Error turning off lights: {str(e)}")

    def _on_reset_all(self):
        """Reset all lights"""
        try:
            self.light_manager.reset_all_lights()
            self.current_color = [1.0, 1.0, 1.0]
            self.current_intensity = 15000
            self.current_exposure = 1.0
            self.current_specular = 1.0
            self.current_temperature = 6500.0
            self.color_temperature_enabled = True
            
            if self.light_manager.selected_lights:
                self._update_ui_with_light_properties(self.light_manager.selected_lights[0])
            
            self._show_success_message(f"Reset {len(self.light_manager.selected_lights)} lights")
        except Exception as e:
            self._show_error_message(f"Error resetting lights: {str(e)}")

    def _on_reset_vision_sync(self):
        """Reset Vision Sync page to default values"""
        try:
            if self.path_field:
                self.path_field.model.set_value("/World/lights/")
            
            if self.room_combobox and self.room_combobox_model:
                children = self.room_combobox_model.get_item_children()
                for i in range(len(children) - 1, -1, -1):
                    self.room_combobox_model.remove_item(children[i])
                self.room_combobox.model.get_item_value_model().set_value(0)
            
            if self.lighting_combobox and self.lighting_combobox_model:
                children = self.lighting_combobox_model.get_item_children()
                for i in range(len(children) - 1, -1, -1):
                    self.lighting_combobox_model.remove_item(children[i])
                self.lighting_combobox.model.get_item_value_model().set_value(0)
            
            self.light_manager.selected_lights = []
            self.light_manager.clear_recorded_defaults()
            self._update_defaults_buttons_state()
            
            if self.group_status_label:
                self.group_status_label.text = "Enter path and click 'Search' to discover lights"
            
            if self.selection_count_label:
                self.selection_count_label.text = "Selected: 0 lights"
            
            self._show_success_message("Light control page reset")
        except Exception as e:
            self._show_error_message(f"Error resetting light control page: {str(e)}")

    def _on_record_defaults(self):
        """Record current values as defaults"""
        try:
            if not self.light_manager.selected_lights:
                self._show_warning_message("No selected lights, cannot record defaults")
                return
            
            if self.light_manager.record_current_values_as_defaults():
                self.has_recorded_defaults = True
                self._update_defaults_buttons_state()
                self._show_success_message(f"Recorded current values as defaults for {len(self.light_manager.selected_lights)} lights")
            else:
                self._show_error_message("Failed to record defaults")
                
        except Exception as e:
            self._show_error_message(f"Error recording defaults: {str(e)}")

    def _on_reset_to_defaults(self):
        """Reset to recorded defaults"""
        try:
            if not self.light_manager.has_recorded_defaults():
                self._show_warning_message("No recorded defaults, please record defaults first")
                return
            
            if self.light_manager.reset_to_recorded_defaults():
                if self.light_manager.selected_lights:
                    self._update_ui_with_light_properties(self.light_manager.selected_lights[0])
                self._show_success_message("Reset to recorded defaults")
            else:
                self._show_error_message("Failed to reset to defaults")
                
        except Exception as e:
            self._show_error_message(f"Error resetting to defaults: {str(e)}")

    def _update_defaults_buttons_state(self):
        """Update default value related button states"""
        has_lights = len(self.light_manager.selected_lights) > 0
        has_defaults = self.light_manager.has_recorded_defaults()
        
        if self.record_defaults_button:
            self.record_defaults_button.enabled = has_lights
        
        if self.reset_to_defaults_button:
            self.reset_to_defaults_button.enabled = has_lights and has_defaults

    # ==============================================================================
    # Door control related methods
    # ==============================================================================

    def _on_door_search_clicked(self):
        """Door search button click event"""
        try:
            search_path = ""  # Fixed search World path
            
            # 首先尝试搜索引用的 USD
            self.door_manager.find_referenced_stages()
            
            # 获取所有房间信息（包括引用的 USD）
            room_infos = self.door_manager.get_room_names(search_path)
            
            if not room_infos:
                self._show_door_warning_message(f"No rooms with doors found under path '{search_path}'")
                # 尝试在根路径搜索
                room_infos = self.door_manager.get_room_names("/")
                if not room_infos:
                    self._show_door_warning_message("No doors found in the entire scene")
                    return
            
            # 统计来自引用和当前场景的房间数量
            referenced_count = sum(1 for room in room_infos if room["is_scene_referenced"])
            current_scene_count = len(room_infos) - referenced_count
            
            self._update_door_room_combobox(room_infos)
            
            if room_infos:
                # 选择第一个房间
                first_room_display = room_infos[0]["display_name"]
                self._on_door_room_selected(first_room_display)
            
            # 显示更详细的搜索结果
            message = f"Found {len(room_infos)} rooms with doors"
            if referenced_count > 0:
                message += f" ({referenced_count} from referenced subscenes, {current_scene_count} from current scene)"
            self._show_door_success_message(message)
            
        except Exception as e:
            self._show_door_error_message(f"Error searching for doors: {str(e)}")

    def _show_door_warning_message(self, message):
        """Show door control warning message"""
        print(f"Door control warning: {message}")
        if self.door_status_label:
            self.door_status_label.text = message

    def _show_door_success_message(self, message):
        """Show door control success message"""
        print(f"Door control success: {message}")
        if self.door_status_label:
            self.door_status_label.text = message

    def _show_door_error_message(self, message):
        """Show door control error message"""
        print(f"Door control error: {message}")
        if self.door_status_label:
            self.door_status_label.text = message

    def _update_door_room_combobox(self, room_infos):
        """Update door room dropdown options with source info"""
        if not self.door_room_combobox or not self.door_room_combobox_model:
            return
            
        self.current_door_room_options = room_infos.copy()
        
        children = self.door_room_combobox_model.get_item_children()
        for i in range(len(children) - 1, -1, -1):
            self.door_room_combobox_model.remove_item(children[i])
        
        for room_info in room_infos:
            # 使用显示名称（包含子场景信息）
            display_name = room_info["display_name"]
            self.door_room_combobox_model.append_child_item(None, ui.SimpleStringModel(display_name))
        
        if room_infos:
            self.door_room_combobox.model.get_item_value_model().set_value(0)

    def _update_door_combobox(self, door_infos):
        """Update door dropdown options with source info"""
        if not self.door_combobox or not self.door_combobox_model:
            return
            
        self.current_door_options = door_infos.copy()
        
        children = self.door_combobox_model.get_item_children()
        for i in range(len(children) - 1, -1, -1):
            self.door_combobox_model.remove_item(children[i])
        
        for door_info in door_infos:
            display_name = f"{door_info['name']} ({door_info['type_display']})"
            
            # 添加房间来源信息
            room_scene_name = door_info.get("room_scene_name", "")
            if room_scene_name and door_info.get("room_is_scene_referenced", False):
                display_name += f" [{room_scene_name}]"
            
            self.door_combobox_model.append_child_item(None, ui.SimpleStringModel(display_name))
        
        if door_infos:
            self.door_combobox.model.get_item_value_model().set_value(0)

    def _on_door_room_selected(self, room_display_name):
        """Door room selection callback with source info"""
        try:
            # 查找对应的房间信息
            selected_room_info = None
            for room_info in self.current_door_room_options:
                if room_info["display_name"] == room_display_name:
                    selected_room_info = room_info
                    break
            
            if not selected_room_info:
                self._show_door_warning_message(f"Room not found: {room_display_name}")
                return
            
            self.door_manager.current_room = selected_room_info["name"]
            
            # 传递完整的房间信息，而不仅仅是房间名
            doors = self.door_manager.get_doors_in_room(selected_room_info)
            
            if not doors:
                self._show_door_warning_message(f"No doors found in room '{selected_room_info['display_name']}'")
                self._update_door_combobox([])
                self.current_door_info = None
                self._update_door_info_display()
                self._update_door_buttons_state()
                return
            
            self._update_door_combobox(doors)
            
            if doors:
                self._on_door_selected(doors[0])
            
        except Exception as e:
            self._show_door_error_message(f"Error selecting door room: {str(e)}")

    def _on_door_selected(self, door_info):
        """Door selection callback"""
        try:
            self.current_door_info = door_info
            self._update_door_info_display()
            
            # Update UI based on door type
            self._update_ui_based_on_door_type(door_info)
            
            # Update button states
            self._update_door_buttons_state()
            
            # 显示门是否来自引用
            room_scene_name = door_info.get("room_scene_name", "")
            if door_info.get("is_referenced", False):
                if room_scene_name:
                    self._show_door_success_message(f"Selected door: {door_info['name']} [Door from reference, Room from {room_scene_name}]")
                else:
                    self._show_door_success_message(f"Selected door: {door_info['name']} [Door from reference]")
            else:
                if room_scene_name and door_info.get("room_is_scene_referenced", False):
                    self._show_door_success_message(f"Selected door: {door_info['name']} [Room from referenced subscene: {room_scene_name}]")
                elif room_scene_name:
                    self._show_door_success_message(f"Selected door: {door_info['name']} [Room from {room_scene_name}]")
                else:
                    self._show_door_success_message(f"Selected door: {door_info['name']}")
            
        except Exception as e:
            self._show_door_error_message(f"Error selecting door: {str(e)}")

    def _update_ui_based_on_door_type(self, door_info):
        """Update UI control visibility based on door type"""
        if not door_info:
            return
        
        door_type = door_info["type"]
        
        # Hide all containers
        if self.slide_distance_container:
            self.slide_distance_container.visible = False
        if self.hinge_angle_container:
            self.hinge_angle_container.visible = False
        if self.door_direction_container:
            self.door_direction_container.visible = False
        if self.double_sliding_mode_container:
            self.double_sliding_mode_container.visible = False
        if self.door_orientation_container:
            self.door_orientation_container.visible = False
        
        # Show appropriate controls based on door type
        if "Sliding" in door_type:  # Sliding door
            # Sliding door: show slide distance, direction, and animation speed
            if self.slide_distance_container:
                full_width = self.door_manager.get_door_width(door_info) * 100
                
                if "Single" in door_type:
                    # Single sliding door: use entire width as default slide distance
                    self.slide_distance = float(full_width)
                    self.slide_distance_container.visible = True
                    
                    # Update slider and input field values
                    if self.slide_distance_slider:
                        # Set maximum and minimum values
                        max_distance = full_width * 1.5  # Can slightly exceed door width
                        min_distance = 0.1  # Minimum value 0.1 meters
                        
                        self.slide_distance_slider.model.set_max(max_distance)
                        self.slide_distance_slider.model.set_min(min_distance)
                        self.slide_distance_slider.model.set_value(float(full_width))
                    
                    if self.slide_distance_field:
                        self.slide_distance_field.model.set_max(full_width * 1.5)
                        self.slide_distance_field.model.set_min(0.1)
                        self.slide_distance_field.model.set_value(float(full_width))
                    
                    # Show door information
                    if self.door_orientation_container:
                        current_orientation = door_info.get("orientation", "x")
                        if current_orientation == "x":
                            self._show_door_success_message(f"Single sliding door | Door orientation: Slide along X-axis | Door width: {full_width/100:.2f}m | Default slide distance: {full_width/100:.2f}m")
                        else:
                            self._show_door_success_message(f"Single sliding door | Door orientation: Slide along Z-axis | Door width: {full_width/100:.2f}m | Default slide distance: {full_width/100:.2f}m")
                    
                else:  # Dual_Sliding_Panel (Dual sliding door)
                    # Dual sliding door: use half width as default slide distance
                    half_width = self.door_manager.get_door_half_width(door_info) * 100
                    self.slide_distance = float(half_width)
                    self.slide_distance_container.visible = True
                    
                    # Update slider and input field values
                    if self.slide_distance_slider:
                        # Set maximum and minimum values
                        max_distance = full_width  # Maximum value is full width
                        min_distance = 0.1  # Minimum value 0.1 meters
                        
                        self.slide_distance_slider.model.set_max(max_distance)
                        self.slide_distance_slider.model.set_min(min_distance)
                        self.slide_distance_slider.model.set_value(float(half_width))
                    
                    if self.slide_distance_field:
                        self.slide_distance_field.model.set_max(full_width)
                        self.slide_distance_field.model.set_min(0.1)
                        self.slide_distance_field.model.set_value(float(half_width))
                    
                    # Show door information
                    if self.door_orientation_container:
                        current_orientation = door_info.get("orientation", "x")
                        if current_orientation == "x":
                            self._show_door_success_message(f"Dual sliding door | Door orientation: Slide along X-axis | Door width: {full_width/100:.2f}m | Default slide distance: {half_width/100:.2f}m")
                        else:
                            self._show_door_success_message(f"Dual sliding door | Door orientation: Slide along Z-axis | Door width: {full_width/100:.2f}m | Default slide distance: {half_width/100:.2f}m")
                
                if self.door_direction_container:
                    self.door_direction_container.visible = True
                
                # Show door orientation selection (overrides auto-detection)
                if self.door_orientation_container:
                    self.door_orientation_container.visible = True
                
                # If dual sliding door, show opening mode selection
                if "Dual" in door_type and self.double_sliding_mode_container:
                    self.double_sliding_mode_container.visible = True
            
        elif "Pivot" in door_type:  # Pivot door
            # Pivot door: show hinge angle, direction, and animation speed
            if self.hinge_angle_container:
                self.hinge_angle_container.visible = True
            
            if self.door_direction_container:
                self.door_direction_container.visible = True
        
        # Animation speed control always visible
        # Direction control shown based on door type

    def _update_door_info_display(self):
        """Update door information display with room source"""
        if not self.current_door_info:
            if self.door_info_label:
                self.door_info_label.text = "Please select a door to view details"
            return
        
        door_info = self.current_door_info
        info_text = f"Door name: {door_info['name']}\n"
        info_text += f"Door type: {door_info['type_display']}\n"
        
        # 添加房间来源信息（子场景名称）
        room_scene_name = door_info.get("room_scene_name", "")
        if room_scene_name:
            if door_info.get("room_is_scene_referenced", False):
                info_text += f"Room from: {room_scene_name} (referenced subscene)\n"
            else:
                info_text += f"Room from: {room_scene_name} (current scene)\n"
        
        info_text += f"Path: {door_info['path']}\n"
        
        # 添加是否来自引用的信息
        if door_info.get("is_referenced", False):
            info_text += f"Door source: Referenced USD\n"
        else:
            info_text += f"Door source: Current Stage\n"
        
        # 添加门宽度信息
        if "width" in door_info:
            info_text += f"Door width: {door_info['width']:.2f}m\n"
        
        # 添加门状态信息
        is_open = door_info.get("is_open", False)
        status = "Open" if is_open else "Closed"
        info_text += f"Current status: {status}"
        
        if "panels" in door_info:
            panel_count = len(door_info["panels"])
            info_text += f"\nNumber of panels: {panel_count}"
        
        if self.door_info_label:
            self.door_info_label.text = info_text

    def _update_door_buttons_state(self):
        """Update open/close door button availability based on door status"""
        if not self.current_door_info:
            # When no door selected, both buttons disabled
            if self.open_door_btn:
                self.open_door_btn.enabled = False
            if self.close_door_btn:
                self.close_door_btn.enabled = False
            return
        
        is_open = self.current_door_info.get("is_open", False)
        
        # If door is open, disable open button, enable close button
        # If door is closed, enable open button, disable close button
        if self.open_door_btn:
            self.open_door_btn.enabled = not is_open
        
        if self.close_door_btn:
            self.close_door_btn.enabled = is_open

    def _on_open_door(self):
        """Open door button click event"""
        try:
            if not self.current_door_info:
                self._show_door_warning_message("Please select a door to operate")
                print("Warning: Please select a door to operate")
                return
            
            # Get current parameter values
            slide_distance = self.slide_distance
            hinge_angle = self.hinge_angle
            direction = self.door_direction
            animation_speed = self.animation_speed
            
            door_name = self.current_door_info['name']
            
            print(f"{door_name} opening...")
            self._show_door_success_message(f"Opening door: {door_name}")
            
            success = self.door_manager.open_door(
                self.current_door_info, 
                slide_distance, 
                hinge_angle, 
                direction,
                animation_speed
            )
            
            if success:
                print(f"{door_name} opened")
                self._show_door_success_message(f"{door_name} opened")
                # Update door status
                self.current_door_info["is_open"] = True
                # Update button states
                self._update_door_buttons_state()
            else:
                print(f"{door_name} failed to open")
                self._show_door_error_message("Open door operation failed")
                
        except Exception as e:
            error_msg = f"Error operating door: {str(e)}"
            print(f"Error: {error_msg}")
            self._show_door_error_message(error_msg)

    def _on_close_door(self):
        """Close door button click event"""
        try:
            if not self.current_door_info:
                self._show_door_warning_message("Please select a door to operate")
                print("Warning: Please select a door to operate")
                return
            
            animation_speed = self.animation_speed
            door_name = self.current_door_info['name']
            
            print(f"{door_name} closing...")
            self._show_door_success_message(f"Closing door: {door_name}")
            
            success = self.door_manager.close_door(self.current_door_info, animation_speed)
            
            if success:
                print(f"{door_name} closed")
                self._show_door_success_message(f"{door_name} closed")
                # Update door status
                self.current_door_info["is_open"] = False
                # Update button states
                self._update_door_buttons_state()
            else:
                print(f"{door_name} failed to close")
                self._show_door_error_message("Close door operation failed")
                
        except Exception as e:
            error_msg = f"Error closing door: {str(e)}"
            print(f"Error: {error_msg}")
            self._show_door_error_message(error_msg)

    def _on_slide_distance_changed(self, distance):
        """Sliding door distance change callback"""
        self.slide_distance = distance

    def _on_hinge_angle_changed(self, angle):
        """Pivot door angle change callback"""
        self.hinge_angle = angle

    def _on_animation_speed_changed(self, speed):
        """Animation speed change callback"""
        self.animation_speed = speed

    def _on_door_direction_changed(self, direction):
        """Door direction change callback"""
        self.door_direction = direction

    def _on_door_orientation_changed(self, orientation):
        """Door orientation change callback"""
        if self.current_door_info:
            self.current_door_info["orientation"] = orientation
            
            # Get door width information
            full_width = self.door_manager.get_door_width(self.current_door_info)
            
            # Show different messages based on door type
            door_type = self.current_door_info["type"]
            if "Single" in door_type:
                if "Sliding" in door_type:
                    # Single sliding door
                    slide_distance = full_width
                    if orientation == "x":
                        self._show_door_success_message(f"Single sliding door | Door orientation: Slide along X-axis | Door width: {full_width:.2f}m | Default slide distance: {slide_distance:.2f}m")
                    else:
                        self._show_door_success_message(f"Single sliding door | Door orientation: Slide along Z-axis | Door width: {full_width:.2f}m | Default slide distance: {slide_distance:.2f}m")
                elif "Pivot" in door_type:
                    # Single pivot door
                    if orientation == "x":
                        self._show_door_success_message(f"Single pivot door | Door orientation: Rotate along X-axis | Door width: {full_width:.2f}m")
                    else:
                        self._show_door_success_message(f"Single pivot door | Door orientation: Rotate along Z-axis | Door width: {full_width:.2f}m")
            else:  # Dual door
                if "Sliding" in door_type:
                    # Dual sliding door
                    slide_distance = self.door_manager.get_door_half_width(self.current_door_info)
                    if orientation == "x":
                        self._show_door_success_message(f"Dual sliding door | Door orientation: Slide along X-axis | Door width: {full_width:.2f}m | Default slide distance: {slide_distance:.2f}m")
                    else:
                        self._show_door_success_message(f"Dual sliding door | Door orientation: Slide along Z-axis | Door width: {full_width:.2f}m | Default slide distance: {slide_distance:.2f}m")
                elif "Pivot" in door_type:
                    # Dual pivot door
                    if orientation == "x":
                        self._show_door_success_message(f"Dual pivot door | Door orientation: Rotate along X-axis | Door width: {full_width:.2f}m")
                    else:
                        self._show_door_success_message(f"Dual pivot door | Door orientation: Rotate along Z-axis | Door width: {full_width:.2f}m")

    def _on_double_sliding_mode_changed(self, mode):
        """Dual sliding door opening mode change callback"""
        self.door_manager.set_double_sliding_mode(mode)
        if self.current_door_info and self.current_door_info["type"] == "Panel_Dual_Sliding":
            self.current_door_info["double_sliding_mode"] = mode
            self._show_door_success_message(f"Dual sliding door opening mode set to: {self.door_manager.double_sliding_modes[mode]}")

    def _on_stop_animation(self):
        """Stop animation button click event"""
        try:
            if not self.current_door_info:
                self._show_door_warning_message("Please select a door to operate")
                return
            
            self.door_manager.stop_door_animation(self.current_door_info)
            self._show_door_success_message("Door animation stopped")
            
        except Exception as e:
            self._show_door_error_message(f"Error stopping animation: {str(e)}")

    def _on_reset_door_control(self):
        """Reset door control page"""
        try:
            if self.door_room_combobox and self.door_room_combobox_model:
                children = self.door_room_combobox_model.get_item_children()
                for i in range(len(children) - 1, -1, -1):
                    self.door_room_combobox_model.remove_item(children[i])
                self.door_room_combobox.model.get_item_value_model().set_value(0)
            
            if self.door_combobox and self.door_combobox_model:
                children = self.door_combobox_model.get_item_children()
                for i in range(len(children) - 1, -1, -1):
                    self.door_combobox_model.remove_item(children[i])
                self.door_combobox.model.get_item_value_model().set_value(0)
            
            self.current_door_info = None
            self._update_door_info_display()
            
            # Hide all door parameter containers
            if self.slide_distance_container:
                self.slide_distance_container.visible = False
            if self.hinge_angle_container:
                self.hinge_angle_container.visible = False
            if self.door_direction_container:
                self.door_direction_container.visible = False
            if self.double_sliding_mode_container:
                self.double_sliding_mode_container.visible = False
            if self.door_orientation_container:
                self.door_orientation_container.visible = False
            
            # Reset button states
            self._update_door_buttons_state()
            
            if self.door_status_label:
                self.door_status_label.text = "Click 'Search' to discover doors"
            
            self._show_door_success_message("Door control page reset")
        except Exception as e:
            self._show_door_error_message(f"Error resetting door control page: {str(e)}")

    # ==============================================================================
    # UI construction methods
    # ==============================================================================

    def _build_light_properties(self):
        """Build light property controls"""
        with CustomCollsableFrame("Light Control").collapsable_frame:
            with ui.VStack(height=0, spacing=10):
                ui.Spacer(height=10)
                
                with ui.HStack():
                    ui.Spacer(width=10)
                    self.group_status_label = ui.Label("Enter path and click 'Search' to discover lights", 
                                                     word_wrap=True, alignment=ui.Alignment.LEFT,
                                                     style={"font_size": 11, "color": cl_text_gray})
                
                with ui.HStack(spacing=10, height=35):
                    self.record_defaults_button = ui.Button("Record Defaults", name="turn_on_off")
                    self.record_defaults_button.set_clicked_fn(self._on_record_defaults)
                    
                    self.reset_to_defaults_button = ui.Button("Reset to Defaults", name="reset_button")
                    self.reset_to_defaults_button.set_clicked_fn(self._on_reset_to_defaults)
                    self.reset_to_defaults_button.enabled = False
                
                self._build_color_temperature()

                # Use unified slider with input field construction method
                self._build_gradient_float_slider_with_input("Exposure", "exposure", 0, -5, 5)
                self._build_gradient_float_slider_with_input("Intensity", "intensity", 15000, 0, 100000)
                self._build_gradient_float_slider_with_input("Specular", "specular", 1.0, 0, 2)

                with ui.VStack(spacing=10):
                    with ui.HStack(spacing=10, height=35):
                        turn_on_btn = ui.Button("Turn On", name="turn_on_off")
                        turn_on_btn.set_clicked_fn(self._on_turn_on_lights)
                        
                        turn_off_btn = ui.Button("Turn Off", name="turn_on_off")
                        turn_off_btn.set_clicked_fn(self._on_turn_off_lights)

                        reset_btn = ui.Button("Reset all", name="reset_button")
                        reset_btn.set_clicked_fn(self._on_reset_all)

                    with ui.HStack():
                        ui.Spacer(width=10)
                        self.selection_count_label = ui.Label("Selected: 0 lights", 
                                                            style={"font_size": 10, "color": cl_text_gray})

    def _build_door_control(self):
        """Build door control controls"""
        with CustomCollsableFrame("Access Control").collapsable_frame:
            with ui.VStack(height=0, spacing=10):
                ui.Spacer(height=10)
                
                with ui.HStack():
                    ui.Spacer(width=10)
                    self.door_status_label = ui.Label("Click 'Search' to discover doors", 
                                                     word_wrap=True, alignment=ui.Alignment.LEFT,
                                                     style={"font_size": 11, "color": cl_text_gray})
                
                # Search controls
                with ui.HStack(height=35):
                    search_btn = ui.Button(f"{_get_search_glyph()} Search Doors", width=120, name="search")
                    search_btn.set_clicked_fn(self._on_door_search_clicked)
                    
                    ui.Spacer(width=8)
                    self.door_reset_button = ui.Image(name="reset", width=20)
                    self.door_reset_button.set_mouse_pressed_fn(lambda x, y, b, m: self._on_reset_door_control())
                
                # Room and door selection
                with ui.HStack(height=20):
                    with ui.VStack():
                        self._build_door_combobox("Select Room", [], self._on_door_room_selected, "door_room")
                
                with ui.HStack():
                    ui.Spacer(width=2)
                    self._build_door_combobox("Select Door", [], self._on_door_selected, "door")
                
                # Door information display
                with ui.HStack():
                    ui.Spacer(width=10)
                    self.door_info_label = ui.Label("Please select a door to view details", 
                                                   word_wrap=True, alignment=ui.Alignment.LEFT,
                                                   style={"font_size": 11, "color": cl_text_gray})
                
                ui.Spacer(height=5)
                with ui.HStack():
                    ui.Spacer(width=10)
                    ui.Label("Door Parameters", name="header_attribute_name")
                
                # Sliding door parameter control - wrapped in container
                with ui.HStack() as slide_container:
                    self._build_gradient_float_slider_with_input("Slide Distance", "slide_distance", 1.0, 0.1, 300)
                self.slide_distance_container = slide_container
                self.slide_distance_container.visible = False  # Initially hidden
                
                # Pivot door parameter control - wrapped in container
                with ui.HStack() as hinge_container:
                    self._build_gradient_float_slider_with_input("Pivot Angle", "hinge_angle", 90.0, 0, 180)
                self.hinge_angle_container = hinge_container
                self.hinge_angle_container.visible = False  # Initially hidden
                
                # Animation speed control - always visible
                self._build_gradient_float_slider_with_input("Speed Regulation", "animation_speed", 1.0, 0.1, 10.0)
                
                # Door direction selection - wrapped in container
                with ui.HStack() as direction_container:
                    ui.Label("Direction", name="attribute_name", width=self.label_width)
                    with ui.HStack(width=ui.Fraction(1), spacing=5):
                        push_btn = ui.Button("Push", name="turn_on_off", width=80)
                        push_btn.set_clicked_fn(lambda: self._on_door_direction_changed("push"))
                        
                        pull_btn = ui.Button("Pull", name="turn_on_off", width=80)
                        pull_btn.set_clicked_fn(lambda: self._on_door_direction_changed("pull"))
                self.door_direction_container = direction_container
                self.door_direction_container.visible = False  # Initially hidden
                
                # Door orientation selection (for sliding doors) - wrapped in container
                with ui.HStack() as orientation_container:
                    ui.Label("Door Orientation", name="attribute_name", width=self.label_width)
                    with ui.HStack(width=ui.Fraction(1), spacing=5):
                        x_axis_btn = ui.Button("X Axis", name="turn_on_off", width=80)
                        x_axis_btn.set_clicked_fn(lambda: self._on_door_orientation_changed("x"))
                        
                        z_axis_btn = ui.Button("Z Axis", name="turn_on_off", width=80)
                        z_axis_btn.set_clicked_fn(lambda: self._on_door_orientation_changed("z"))
                self.door_orientation_container = orientation_container
                self.door_orientation_container.visible = False  # Initially hidden
                
                # Dual sliding door opening mode - wrapped in container
                with ui.HStack() as mode_container:
                    ui.Label("Dual Sliding Mode", name="attribute_name", width=self.label_width)
                    with ui.HStack(width=ui.Fraction(1), spacing=5):
                        left_fixed_btn = ui.Button("Left Fixed", name="turn_on_off", width=80)
                        left_fixed_btn.set_clicked_fn(lambda: self._on_double_sliding_mode_changed("left_fixed"))
                        
                        right_fixed_btn = ui.Button("Right Fixed", name="turn_on_off", width=80)
                        right_fixed_btn.set_clicked_fn(lambda: self._on_double_sliding_mode_changed("right_fixed"))
                        
                        both_sides_btn = ui.Button("Both Sides", name="turn_on_off", width=80)
                        both_sides_btn.set_clicked_fn(lambda: self._on_double_sliding_mode_changed("both_sides"))
                self.double_sliding_mode_container = mode_container
                self.double_sliding_mode_container.visible = False  # Initially hidden
                
                # Door operation buttons - separated into two buttons
                with ui.HStack(spacing=10, height=35):
                    self.open_door_btn = ui.Button("Open Door", name="turn_on_off")
                    self.open_door_btn.set_clicked_fn(self._on_open_door)
                    self.open_door_btn.enabled = False
                    
                    self.close_door_btn = ui.Button("Close Door", name="turn_on_off")
                    self.close_door_btn.set_clicked_fn(self._on_close_door)
                    self.close_door_btn.enabled = False
                    
                    # New stop animation button
                    stop_btn = ui.Button("Pause", name="reset_button")
                    stop_btn.set_clicked_fn(self._on_stop_animation)

    def _build_gradient_float_slider_with_input(self, label_name, param_type, default_value, min_val, max_val):
        """Build gradient float slider with value input field for property"""
        def _on_value_changed(model, rect_changed, rect_default):
            if model.as_float == default_value:
                rect_changed.visible = False
                rect_default.visible = True
            else:
                rect_changed.visible = True
                rect_default.visible = False

        def _restore_default(slider, input_field):
            slider.model.set_value(default_value)
            input_field.model.set_value(default_value)
        
        def _on_input_changed(value, slider):
            try:
                float_value = float(value)
                float_value = max(min_val, min(float_value, max_val))
                slider.model.set_value(float_value)
            except ValueError:
                pass

        with ui.HStack():
            ui.Label(label_name, name=f"attribute_name", width=self.label_width)
            with ui.ZStack():
                with ui.VStack():
                    ui.Spacer(height=1.5)
                    with ui.HStack():
                        slider = ui.FloatSlider(name="float_slider", height=0, min=min_val, max=max_val)
                        slider.model.set_value(default_value)
                        ui.Spacer(width=10)
                        input_field = ui.FloatField(
                            min=min_val, 
                            max=max_val,
                            height=0,
                            width=60,
                            style={"color": cl_text}
                        )
                        input_field.model.set_value(default_value)

                        # Synchronize slider and input field
                        slider.model.add_value_changed_fn(
                            lambda model, field=input_field: field.model.set_value(model.as_float)
                        )
                        input_field.model.add_value_changed_fn(
                            lambda model, s=slider: _on_input_changed(model.as_string, s)
                        )
                        
                        # Set callback function based on parameter type
                        if param_type == "exposure":
                            self.exposure_slider = slider
                            self.exposure_field = input_field
                            slider.model.add_value_changed_fn(
                                lambda model, s=slider: self._on_exposure_changed(s.model.as_float))
                        elif param_type == "intensity":
                            self.intensity_slider = slider
                            self.intensity_field = input_field
                            slider.model.add_value_changed_fn(
                                lambda model, s=slider: self._on_intensity_changed(s.model.as_float))
                        elif param_type == "specular":
                            self.specular_slider = slider
                            self.specular_field = input_field
                            slider.model.add_value_changed_fn(
                                lambda model, s=slider: self._on_specular_changed(s.model.as_float))
                        elif param_type == "temperature":
                            self.temperature_slider = slider
                            self.temperature_field = input_field
                            slider.model.add_value_changed_fn(
                                lambda model, s=slider: self._on_temperature_changed(s.model.as_float))
                        elif param_type == "slide_distance":
                            self.slide_distance_slider = slider
                            self.slide_distance_field = input_field
                            slider.model.add_value_changed_fn(
                                lambda model, s=slider: self._on_slide_distance_changed(s.model.as_float))
                        elif param_type == "hinge_angle":
                            self.hinge_angle_slider = slider
                            self.hinge_angle_field = input_field
                            slider.model.add_value_changed_fn(
                                lambda model, s=slider: self._on_hinge_angle_changed(s.model.as_float))
                        elif param_type == "animation_speed":  # New animation speed handling
                            self.animation_speed_slider = slider
                            self.animation_speed_field = input_field
                            slider.model.add_value_changed_fn(
                                lambda model, s=slider: self._on_animation_speed_changed(s.model.as_float))
                        
                        ui.Spacer(width=1.5)
            
            ui.Spacer(width=4)
            rect_changed, rect_default = self.__build_value_changed_widget()
            slider.model.add_value_changed_fn(lambda model: _on_value_changed(model, rect_changed, rect_default))
            
            rect_changed.set_mouse_pressed_fn(lambda x, y, b, m: _restore_default(slider, input_field))
        return None

    def _build_line_dot(self, line_width, height):
        """Build line dot decoration element"""
        with ui.HStack():
            ui.Spacer(width=10)
            with ui.VStack(width=line_width):
                ui.Spacer(height=height)
                ui.Line(name="group_line", alignment=ui.Alignment.TOP)
            with ui.VStack(width=6):
                ui.Spacer(height=height-2)
                ui.Circle(name="group_circle", width=6, height=6, alignment=ui.Alignment.BOTTOM)          

    def _build_color_temperature(self):
        """Build color temperature control"""
        with ui.ZStack():
            with ui.HStack():
                ui.Spacer(width=10)
                with ui.VStack():
                    ui.Spacer(height=8)
                    ui.Line(name="group_line", alignment=ui.Alignment.RIGHT, width=0)
            with ui.VStack(height=0, spacing=10):
                with ui.HStack():
                    self._build_line_dot(10, 8)
                    ui.Label("Enable Color Temperature", name="attribute_name", width=0)
                    ui.Spacer()
                    with ui.HStack(width=0):
                        self._build_checkbox("", self.color_temperature_enabled, self._on_temperature_toggled)

                # Use unified slider with input field construction method
                self._build_gradient_float_slider_with_input(
                    "    Color Temperature", "temperature", 2700.0, 1000, 15000)

                with ui.HStack():
                    ui.Spacer(width=10)
                    ui.Line(name="group_line", alignment=ui.Alignment.TOP)

    def _build_color_widget(self, widget_name):
        """Build color control"""
        with ui.ZStack():
            with ui.HStack():
                ui.Spacer(width=10)
                with ui.VStack():
                    ui.Spacer(height=8)
                    ui.Line(name="group_line", alignment=ui.Alignment.RIGHT, width=0)
            with ui.VStack(height=0, spacing=10):
                with ui.HStack():
                    self._build_line_dot(40, 9)
                    ui.Label(widget_name, name="attribute_name", width=0)
                    self.color_widget = ColorWidget(1.0, 1.0, 1.0, on_color_changed=self._on_color_changed)
                    ui.Spacer(width=10)
                with ui.HStack():
                    ui.Spacer(width=10)
                    ui.Line(name="group_line", alignment=ui.Alignment.TOP)

    def _build_fn(self):
        """Main method to build all UI"""
        with ui.ScrollingFrame(name="main_frame"):
            with ui.VStack(height=0, spacing=10):
                self._build_head()
                self._build_light_properties()
                self._build_door_control()
                ui.Spacer(height=30)

    def _build_head(self):
        """Build window header"""
        with ui.ZStack():
            ui.Image(name="header_frame", height=180, fill_policy=ui.FillPolicy.STRETCH)
            with ui.HStack():
                ui.Spacer(width=12)
                with ui.VStack(spacing=8):
                    self._build_tabs()
                    ui.Spacer(height=1)
                    self._build_selection_widget()
                    self._build_stage_path_widget()
                    self._build_search_field()
                ui.Spacer(width=12)

    def _build_tabs(self):
        """Build tabs"""
        with ui.HStack(height=35):
            ui.Label("Synchronous Interaction", width=ui.Percent(17), name="details")
            with ui.ZStack():
                ui.Image(name="combobox", fill_policy=ui.FillPolicy.STRETCH, height=35)
                with ui.HStack():
                    ui.Spacer(width=15)

    def _build_selection_widget(self):
        """Build selection control"""
        with ui.HStack(height=20):
            add_button = ui.Button(f"{_get_search_glyph()} Search", width=60, name="search")
            add_button.set_clicked_fn(self._on_search_clicked)
            
            ui.Spacer(width=14)
            
            self.path_field = ui.StringField(name="path")
            self.path_field.model.set_value("/World/lights/")
            
            ui.Spacer(width=8)
            self.top_reset_button = ui.Image(name="reset", width=20)
            self.top_reset_button.set_mouse_pressed_fn(lambda x, y, b, m: self._on_reset_vision_sync())

    def _build_stage_path_widget(self):
        """Build stage path control"""
        with ui.HStack(height=20):
            with ui.VStack():
                self._build_combobox("Select Room", [], self._on_room_selected)

    def _build_search_field(self):
        """Build search field"""
        with ui.HStack():
            ui.Spacer(width=2)
            self._build_combobox("Select Lighting", [], self._on_lighting_selected)

    def _build_door_combobox(self, label_name, options, on_selected=None, combobox_type=""):
        """Build door control dropdown"""
        def _on_value_changed(model, rect_changed, rect_defaul):
            index = model.get_item_value_model().get_value_as_int()
            if index == 0:
                rect_changed.visible = False
                rect_defaul.visible = True
            else:
                rect_changed.visible = True
                rect_defaul.visible = False
            
            current_options = []
            if combobox_type == "door_room":
                current_options = self.current_door_room_options
            elif combobox_type == "door":
                current_options = self.current_door_options
            
            if on_selected and index < len(current_options):
                # 根据下拉框类型传递不同的参数
                if combobox_type == "door_room":
                    # 对于房间下拉框，传递显示名称
                    room_display_name = current_options[index]["display_name"]
                    on_selected(room_display_name)
                elif combobox_type == "door":
                    # 对于门下拉框，传递门信息
                    on_selected(current_options[index])
        
        def _restore_default(combo_box):
            combo_box.model.get_item_value_model().set_value(0)
        
        with ui.HStack():
            ui.Label(label_name, name=f"attribute_name", width=self.label_width)
            with ui.ZStack():
                ui.Image(name="combobox", fill_policy=ui.FillPolicy.STRETCH, height=35)
                with ui.HStack():
                    ui.Spacer(width=10)
                    with ui.VStack():
                        ui.Spacer(height=10)
                        option_list = list(options)
                        combo_box = ui.ComboBox(0, *option_list, name="dropdown_menu")
                        
                        if combobox_type == "door_room":
                            self.door_room_combobox = combo_box
                            self.door_room_combobox_model = combo_box.model
                        elif combobox_type == "door":
                            self.door_combobox = combo_box
                            self.door_combobox_model = combo_box.model
                            
            with ui.VStack(width=0):
                ui.Spacer(height=10)
                rect_changed, rect_default = self.__build_value_changed_widget()
            combo_box.model.add_item_changed_fn(lambda m, i: _on_value_changed(m, rect_changed, rect_default))
            rect_changed.set_mouse_pressed_fn(lambda x, y, b, m: _restore_default(combo_box))

    def _build_checkbox(self, label_name, default_value=True, on_changed=None):
        """Build checkbox"""
        def _restore_default(rect_changed, rect_default, current_state):
            image.name = "checked" if default_value else "unchecked"
            rect_changed.visible = False
            rect_default.visible = True
            
            if on_changed:
                on_changed(default_value)

        def _on_value_changed(image, rect_changed, rect_default):
            new_state = (image.name != "checked")
            image.name = "checked" if new_state else "unchecked"
            
            if (default_value and not new_state) or (not default_value and new_state):
                rect_changed.visible = True
                rect_default.visible = False
            else:
                rect_changed.visible = False
                rect_default.visible = True
            
            if on_changed:
                try:
                    on_changed(new_state)
                except Exception as e:
                    print(f"Callback function call failed: {str(e)}")

        with ui.HStack():
            ui.Label(label_name, name=f"attribute_bool", width=self.label_width, height=20)
            
            initial_name = "checked" if default_value else "unchecked"
            image = ui.Image(name=initial_name, fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT, height=18, width=18)
            
            if label_name == "" and "temperature" in str(on_changed):
                self.temperature_checkbox_image = image
            
            ui.Spacer()
            
            rect_changed, rect_default = self.__build_value_changed_widget()
            
            image.set_mouse_pressed_fn(lambda x, y, b, m: _on_value_changed(image, rect_changed, rect_default))
            rect_changed.set_mouse_pressed_fn(
                lambda x, y, b, m: _restore_default(rect_changed, rect_default, default_value)
            )

    def __build_value_changed_widget(self):
        """Build value change indicator control"""
        with ui.VStack(width=20):
            ui.Spacer(height=3)
            rect_changed = ui.Rectangle(name="attribute_changed", width=15, height=15, visible= False)
            ui.Spacer(height=4)
            with ui.HStack():
                ui.Spacer(width=3)
                rect_default = ui.Rectangle(name="attribute_default", width=5, height=5, visible= True)
        return rect_changed, rect_default    

    def _build_combobox(self, label_name, options, on_selected=None):
        """Build dropdown"""
        def _on_value_changed(model, rect_changed, rect_defaul):
            index = model.get_item_value_model().get_value_as_int()
            if index == 0:
                rect_changed.visible = False
                rect_defaul.visible = True
            else:
                rect_changed.visible = True
                rect_defaul.visible = False
            
            current_options = []
            if label_name == "Select Room":
                current_options = self.current_room_options
            elif label_name == "Select Lighting":
                current_options = self.current_lighting_options
            
            if on_selected and index < len(current_options):
                on_selected(current_options[index])
        
        def _restore_default(combo_box):
            combo_box.model.get_item_value_model().set_value(0)
        
        with ui.HStack():
            ui.Label(label_name, name=f"attribute_name", width=self.label_width)
            with ui.ZStack():
                ui.Image(name="combobox", fill_policy=ui.FillPolicy.STRETCH, height=35)
                with ui.HStack():
                    ui.Spacer(width=10)
                    with ui.VStack():
                        ui.Spacer(height=10)
                        option_list = list(options)
                        combo_box = ui.ComboBox(0, *option_list, name="dropdown_menu")
                        
                        if label_name == "Select Room":
                            self.room_combobox = combo_box
                            self.room_combobox_model = combo_box.model
                        elif label_name == "Select Lighting":
                            self.lighting_combobox = combo_box
                            self.lighting_combobox_model = combo_box.model
                            
            with ui.VStack(width=0):
                ui.Spacer(height=10)
                rect_changed, rect_default = self.__build_value_changed_widget()
            combo_box.model.add_item_changed_fn(lambda m, i: _on_value_changed(m, rect_changed, rect_default))
            rect_changed.set_mouse_pressed_fn(lambda x, y, b, m: _restore_default(combo_box))