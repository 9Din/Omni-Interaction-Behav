from pxr import Usd, UsdLux, Gf, Sdf, UsdGeom, UsdShade
from typing import List, Optional, Dict
import omni.usd
import omni.kit.commands


class LightManager:
    """Light Manager, responsible for handling light operations and hierarchical directory structure in USD scenes"""
    
    def __init__(self):
        self.stage = None
        self.selected_lights = []
        self.current_room = ""
        self.current_lighting = ""
        
        self.light_types = ["SphereLight", "RectLight", "DiskLight", "CylinderLight", "DomeLight", "DistantLight"]
        self.light_defaults = {}
    
    def get_stage(self):
        """Get current USD stage"""
        if not self.stage:
            self.stage = omni.usd.get_context().get_stage()
        return self.stage
    
    def _is_light_prim(self, prim):
        """Check if prim is a light type"""
        prim_type = prim.GetTypeName()
        return prim_type in self.light_types
    
    def get_xform_children_names(self, path):
        """Get list of Xform type child names at specified path"""
        stage = self.get_stage()
        if not stage:
            return []
            
        children_names = []
        parent_prim = stage.GetPrimAtPath(path)
        
        if parent_prim and parent_prim.IsValid():
            for child_prim in parent_prim.GetChildren():
                if child_prim.IsA(UsdGeom.Xform):
                    children_names.append(child_prim.GetName())
        
        return children_names
    
    def get_lights_in_xform(self, xform_path):
        """Get all lights in specified Xform (direct children)"""
        stage = self.get_stage()
        if not stage:
            return []
            
        lights = []
        xform_prim = stage.GetPrimAtPath(xform_path)
        
        if xform_prim and xform_prim.IsValid():
            for child_prim in xform_prim.GetChildren():
                if self._is_light_prim(child_prim):
                    lights.append(child_prim)
        
        return lights
    
    def get_all_lights_in_xform(self, xform_path):
        """Get all lights in specified Xform (including nested children)"""
        stage = self.get_stage()
        if not stage:
            return []
            
        lights = []
        xform_prim = stage.GetPrimAtPath(xform_path)
        
        if xform_prim and xform_prim.IsValid():
            def _collect_lights_recursive(prim):
                if self._is_light_prim(prim):
                    lights.append(prim)
                for child_prim in prim.GetChildren():
                    _collect_lights_recursive(child_prim)
            
            _collect_lights_recursive(xform_prim)
        
        return lights
    
    def get_light_names_in_xform(self, xform_path):
        """Get all light names in specified Xform"""
        lights = self.get_lights_in_xform(xform_path)
        return [light.GetName() for light in lights]
    
    def get_all_xforms_in_path(self, path):
        """Get all Xform type children at specified path (including nested children)"""
        stage = self.get_stage()
        if not stage:
            return []
            
        xforms = []
        parent_prim = stage.GetPrimAtPath(path)
        
        if parent_prim and parent_prim.IsValid():
            self._find_xforms_recursive(parent_prim, xforms)
        
        return xforms
    
    def _find_xforms_recursive(self, prim, xforms):
        """Recursively find Xform types"""
        if prim.IsA(UsdGeom.Xform):
            xforms.append(prim)
        
        for child_prim in prim.GetChildren():
            self._find_xforms_recursive(child_prim, xforms)
    
    def get_all_xform_names_in_path(self, path):
        """Get all Xform type child names at specified path (including nested children)"""
        xforms = self.get_all_xforms_in_path(path)
        return [xform.GetName() for xform in xforms]
    
    def check_path_exists(self, path):
        """Check if specified path exists"""
        stage = self.get_stage()
        if not stage:
            return False
            
        prim = stage.GetPrimAtPath(path)
        return prim and prim.IsValid()
    
    def find_lights_path_in_stage(self):
        """Find lights path in stage"""
        stage = self.get_stage()
        if not stage:
            return None
            
        lights_paths = []
        for prim in stage.Traverse():
            if prim.IsA(UsdGeom.Xform):
                prim_name = prim.GetName().lower()
                if "light" in prim_name or "lights" in prim_name:
                    lights_paths.append(str(prim.GetPath()))
        
        if lights_paths:
            return lights_paths[0]
        else:
            for prim in stage.Traverse():
                if prim.IsA(UsdGeom.Xform):
                    for child in prim.GetChildren():
                        if self._is_light_prim(child):
                            return str(prim.GetPath())
        
        return "/World/lights"
    
    def get_room_names(self, lights_path):
        """Get room names in first-level directory (second-level directory - Xform type)"""
        return self.get_xform_children_names(lights_path)
    
    def get_lighting_names(self, room_path):
        """Get lighting group names in room (third-level directory - Xform type)"""
        return self.get_xform_children_names(room_path)
    
    def get_lights_in_lighting_group(self, lighting_path):
        """Get all lights in lighting group"""
        return self.get_all_lights_in_xform(lighting_path)
    
    def _get_light_attribute(self, light_prim, attr_names, default_value):
        """General method to get light attribute value"""
        for attr_name in attr_names:
            attr = light_prim.GetAttribute(attr_name)
            if attr and attr.HasAuthoredValue():
                try:
                    return attr.Get()
                except Exception as e:
                    print(f"Failed to get attribute {attr_name}: {str(e)}")
        return default_value

    def _set_light_attribute(self, light_prim, attr_names, value, value_type):
        """General method to set light attribute value"""
        for attr_name in attr_names:
            attr = light_prim.GetAttribute(attr_name)
            if attr:
                try:
                    attr.Set(value)
                    return True
                except Exception as e:
                    print(f"Failed to set attribute {attr_name}: {str(e)}")
        
        # If attribute doesn't exist, create it
        try:
            attr = light_prim.CreateAttribute(attr_names[0], value_type)
            attr.Set(value)
            return True
        except Exception as e:
            print(f"Failed to create attribute {attr_names[0]}: {str(e)}")
        
        return False
    
    def set_light_color(self, light_prim, color):
        """Set light color"""
        if self._is_light_prim(light_prim):
            return self._set_light_attribute(
                light_prim, 
                ["inputs:color", "color"], 
                Gf.Vec3f(color[0], color[1], color[2]),
                Sdf.ValueTypeNames.Color3f
            )
        return False
    
    def set_light_intensity(self, light_prim, intensity):
        """Set light intensity"""
        if self._is_light_prim(light_prim):
            return self._set_light_attribute(
                light_prim,
                ["inputs:intensity", "intensity"],
                float(intensity),
                Sdf.ValueTypeNames.Float
            )
        return False
    
    def set_light_enabled(self, light_prim, enabled):
        """Enable or disable light"""
        if light_prim:
            imageable = UsdGeom.Imageable(light_prim)
            if enabled:
                imageable.MakeVisible()
            else:
                imageable.MakeInvisible()
    
    def enable_color_temperature(self, light_prim, enabled):
        """Enable or disable color temperature"""
        if self._is_light_prim(light_prim):
            return self._set_light_attribute(
                light_prim,
                ["inputs:enableColorTemperature", "enableColorTemperature"],
                bool(enabled),
                Sdf.ValueTypeNames.Bool
            )
        return False
    
    def set_color_temperature(self, light_prim, temperature):
        """Set color temperature"""
        if self._is_light_prim(light_prim):
            return self._set_light_attribute(
                light_prim,
                ["inputs:colorTemperature", "colorTemperature"],
                float(temperature),
                Sdf.ValueTypeNames.Float
            )
        return False
    
    def set_exposure(self, light_prim, exposure):
        """Set exposure value"""
        if self._is_light_prim(light_prim):
            return self._set_light_attribute(
                light_prim,
                ["inputs:exposure", "exposure"],
                float(exposure),
                Sdf.ValueTypeNames.Float
            )
        return False
    
    def set_specular(self, light_prim, specular):
        """Set specular intensity"""
        if self._is_light_prim(light_prim):
            return self._set_light_attribute(
                light_prim,
                ["inputs:specular", "specular"],
                float(specular),
                Sdf.ValueTypeNames.Float
            )
        return False
    
    def get_light_color(self, light_prim):
        """Get light color"""
        if self._is_light_prim(light_prim):
            result = self._get_light_attribute(light_prim, ["inputs:color", "color"], None)
            if result is not None:
                return [result[0], result[1], result[2]]
        return [1.0, 1.0, 1.0]
    
    def get_light_intensity(self, light_prim):
        """Get light intensity"""
        return self._get_light_attribute(light_prim, ["inputs:intensity", "intensity"], 15000.0)
    
    def get_light_exposure(self, light_prim):
        """Get light exposure value"""
        return self._get_light_attribute(light_prim, ["inputs:exposure", "exposure"], 1.0)
    
    def get_light_color_temperature(self, light_prim):
        """Get light color temperature"""
        return self._get_light_attribute(light_prim, ["inputs:colorTemperature", "colorTemperature"], 6500.0)
    
    def is_color_temperature_enabled(self, light_prim):
        """Check if color temperature is enabled"""
        return self._get_light_attribute(light_prim, ["inputs:enableColorTemperature", "enableColorTemperature"], True)
    
    def get_light_specular(self, light_prim):
        """Get light specular intensity"""
        return self._get_light_attribute(light_prim, ["inputs:specular", "specular"], 1.0)
    
    def is_light_enabled(self, light_prim):
        """Check if light is enabled"""
        if light_prim:
            imageable = UsdGeom.Imageable(light_prim)
            return imageable.ComputeVisibility() != "invisible"
        return False
    
    def reset_light(self, light_prim):
        """Reset single light to default values"""
        if self._is_light_prim(light_prim):
            self.set_light_color(light_prim, [1.0, 1.0, 1.0])
            self.set_light_intensity(light_prim, 15000.0)
            self.set_exposure(light_prim, 1.0)
            self.set_color_temperature(light_prim, 6500.0)
            self.set_specular(light_prim, 1.0)
            self.enable_color_temperature(light_prim, True)
            self.set_light_enabled(light_prim, True)
    
    def reset_all_lights(self):
        """Reset all lights to default values"""
        for light_prim in self.selected_lights:
            self.reset_light(light_prim)
    
    def record_current_values_as_defaults(self):
        """Record current selected light intensity, color temperature, and other attribute values as defaults"""
        if not self.selected_lights:
            return False
        
        for light_prim in self.selected_lights:
            light_path = str(light_prim.GetPath())
            intensity = self.get_light_intensity(light_prim)
            color_temp = self.get_light_color_temperature(light_prim)
            color = self.get_light_color(light_prim)
            exposure = self.get_light_exposure(light_prim)
            specular = self.get_light_specular(light_prim)
            
            self.light_defaults[light_path] = {
                "intensity": intensity,
                "color_temperature": color_temp,
                "color": color.copy() if color else [1.0, 1.0, 1.0],
                "exposure": exposure,
                "specular": specular
            }
        
        return True
    
    def reset_to_recorded_defaults(self):
        """Reset selected lights to previously recorded default values"""
        if not self.selected_lights:
            return False
        
        success_count = 0
        for light_prim in self.selected_lights:
            light_path = str(light_prim.GetPath())
            if light_path in self.light_defaults:
                defaults = self.light_defaults[light_path]
                
                if "color" in defaults:
                    self.set_light_color(light_prim, defaults["color"])
                if "intensity" in defaults:
                    self.set_light_intensity(light_prim, defaults["intensity"])
                if "color_temperature" in defaults:
                    self.set_color_temperature(light_prim, defaults["color_temperature"])
                if "exposure" in defaults:
                    self.set_exposure(light_prim, defaults["exposure"])
                if "specular" in defaults:
                    self.set_specular(light_prim, defaults["specular"])
                
                success_count += 1
        
        return success_count > 0
    
    def has_recorded_defaults(self):
        """Check if current selected lights have recorded defaults"""
        if not self.selected_lights:
            return False
        
        for light_prim in self.selected_lights:
            light_path = str(light_prim.GetPath())
            if light_path in self.light_defaults:
                return True
        return False
    
    def clear_recorded_defaults(self):
        """Clear all recorded default values"""
        self.light_defaults.clear()