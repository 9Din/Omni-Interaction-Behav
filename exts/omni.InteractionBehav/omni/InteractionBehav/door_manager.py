from pxr import Usd, UsdGeom, Gf, Sdf, UsdPhysics
from typing import List, Optional, Dict, Tuple
import omni.usd
import omni.kit.commands
import asyncio
import math
import os
import re


class DoorManager:
    """Door Manager, responsible for handling door operations in USD scenes including referenced USDs"""
    
    def __init__(self):
        self.stage = None
        self.selected_doors = []
        self.current_room = ""
        self.current_door = ""
        
        # Door type definitions
        self.door_types = {
            "Panel_Single_Sliding": "Single Sliding Door",
            "Panel_Single_Pivot": "Single Pivot Door", 
            "Panel_Dual_Sliding": "Dual Sliding Door",
            "Panel_Dual_Pivot": "Dual Pivot Door"
        }
        
        # Dual sliding door opening modes
        self.double_sliding_modes = {
            "left_fixed": "Left fixed, right sliding",
            "right_fixed": "Right fixed, left sliding", 
            "both_sides": "Both sides sliding"
        }
        
        # Store door initial states and animation states
        self.door_initial_states = {}
        self.door_target_states = {}
        self.animation_tasks = {}
        self.is_animating = {}
        
        # Current dual sliding door opening mode
        self.current_double_sliding_mode = "both_sides"
        # Door width cache
        self.door_width_cache = {}
        # Door orientation cache
        self.door_orientation_cache = {}
        
        # Search configuration
        self.search_include_references = True
        self.search_max_depth = 10
        self.search_all_loaded_prims = True
        
        # Common root path patterns to search for
        self.common_root_paths = ["/World", "/Root", "/root", "/Scene", "/scene", "/Set", "/set"]
        
    def get_stage(self):
        """Get current USD stage"""
        if not self.stage:
            self.stage = omni.usd.get_context().get_stage()
        return self.stage
    
    def check_path_exists(self, path):
        """Check if specified path exists"""
        stage = self.get_stage()
        if not stage:
            return False
            
        prim = stage.GetPrimAtPath(path)
        return prim and prim.IsValid()
    
    def _get_all_prims_with_traversal(self, stage, start_path="/"):
        """获取所有 Prim（包括引用的）"""
        all_prims = []
        
        def _traverse(prim, depth=0):
            if depth > self.search_max_depth:
                return
            
            all_prims.append(prim)
            
            # 使用 GetFilteredChildren 获取所有子节点（包括引用的）
            try:
                for child in prim.GetFilteredChildren(
                    Usd.PrimIsActive & Usd.PrimIsLoaded & Usd.PrimIsDefined
                ):
                    _traverse(child, depth + 1)
            except Exception as e:
                print(f"Error traversing children of {prim.GetPath()}: {str(e)}")
        
        if start_path and start_path != "/":
            start_prim = stage.GetPrimAtPath(start_path)
            if start_prim and start_prim.IsValid():
                _traverse(start_prim)
        else:
            # 从根开始
            root_prim = stage.GetPrimAtPath("/")
            if root_prim and root_prim.IsValid():
                _traverse(root_prim)
        
        return all_prims
    
    def _find_common_root_paths(self, stage):
        """查找场景中常见的根路径"""
        found_roots = []
        
        # 首先检查常见的根路径
        for root_path in self.common_root_paths:
            prim = stage.GetPrimAtPath(root_path)
            if prim and prim.IsValid():
                found_roots.append(root_path)
        
        # 如果没有找到常见的根路径，则查找所有Xform类型的根节点
        if not found_roots:
            root_prim = stage.GetPrimAtPath("/")
            if root_prim and root_prim.IsValid():
                for child in root_prim.GetChildren():
                    if child.IsA(UsdGeom.Xform):
                        child_path = str(child.GetPath())
                        # 排除一些可能不是场景根的特殊路径
                        if not child_path.startswith(("/Looks", "/materials", "/Physics", "/Render")):
                            found_roots.append(child_path)
        
        # 如果还没有找到，返回根路径
        if not found_roots:
            found_roots = ["/"]
        
        return found_roots
    
    def _find_rooms_recursive(self, stage, prim, current_path, room_infos, depth=0):
        """递归查找包含门的房间"""
        if depth > self.search_max_depth:
            return
        
        prim_name = prim.GetName()
        prim_path = str(prim.GetPath())
        
        # 检查当前Prim是否包含门
        has_door = False
        door_prims = []
        
        # 检查当前Prim及其子级中是否有门
        def _check_for_doors(p, check_depth=0):
            if check_depth > 3:  # 只检查3层深度
                return
            
            p_name = p.GetName()
            if "_Door" in p_name:
                door_prims.append(p)
                return True
            
            for child in p.GetChildren():
                if _check_for_doors(child, check_depth + 1):
                    return True
            
            return False
        
        has_door = _check_for_doors(prim)
        
        if has_door:
            # 这是一个包含门的房间
            room_name = prim_name
            
            # 获取场景信息
            scene_name = ""
            is_scene_referenced = False
            reference_source = ""
            
            # 检查当前Prim或其父级是否有引用
            current_prim = prim
            scene_prim = None
            
            # 向上查找场景级别的Prim
            while current_prim and current_prim.IsValid():
                parent = current_prim.GetParent()
                if parent and parent.IsValid():
                    parent_name = parent.GetName().lower()
                    # 如果父级名称看起来像场景或设置
                    if any(pattern in parent_name for pattern in ["scene", "set", "level", "stage"]):
                        scene_prim = parent
                        break
                    current_prim = parent
                else:
                    break
            
            if scene_prim:
                scene_name = scene_prim.GetName()
                
                # 检查是否有引用
                if scene_prim.HasAuthoredReferences():
                    is_scene_referenced = True
                    refs = scene_prim.GetReferences()
                    for ref in refs.GetAddedOrExplicitItems():
                        if ref.assetPath:
                            ref_path = str(ref.assetPath)
                            ref_filename = os.path.basename(ref_path)
                            if '.' in ref_filename:
                                ref_filename = ref_filename[:ref_filename.rfind('.')]
                            reference_source = ref_filename
                            break
                else:
                    # 检查祖先是否有引用
                    current_check_prim = scene_prim
                    while current_check_prim and current_check_prim.IsValid():
                        if current_check_prim.HasAuthoredReferences():
                            is_scene_referenced = True
                            refs = current_check_prim.GetReferences()
                            for ref in refs.GetAddedOrExplicitItems():
                                if ref.assetPath:
                                    ref_path = str(ref.assetPath)
                                    ref_filename = os.path.basename(ref_path)
                                    if '.' in ref_filename:
                                        ref_filename = ref_filename[:ref_filename.rfind('.')]
                                    reference_source = ref_filename
                                    break
                            break
                        current_check_prim = current_check_prim.GetParent()
            
            # 创建房间信息
            room_info = {
                "name": room_name,
                "path": prim_path,
                "scene_name": scene_name,
                "is_scene_referenced": is_scene_referenced,
                "reference_source": reference_source,
                "display_name": room_name
            }
            
            # 如果子场景来自引用，修改显示名称
            if is_scene_referenced and scene_name:
                room_info["display_name"] = f"{room_name} ({scene_name})"
            
            # 避免重复添加相同房间
            room_exists = False
            for existing_room in room_infos:
                if (existing_room["name"] == room_name and 
                    existing_room["path"] == prim_path):
                    room_exists = True
                    break
            
            if not room_exists:
                room_infos.append(room_info)
        
        # 递归检查子Prim
        for child_prim in prim.GetChildren():
            if child_prim.IsA(UsdGeom.Xform) or child_prim.GetTypeName() == "Xform":
                self._find_rooms_recursive(stage, child_prim, f"{current_path}/{child_prim.GetName()}", room_infos, depth + 1)
    
    def get_room_names(self, search_path=None):
        """Get room names containing doors (including referenced USDs) with source info"""
        stage = self.get_stage()
        if not stage:
            return []
            
        room_infos = []
        
        try:
            # 如果没有指定搜索路径，则尝试常见的根路径
            if search_path is None:
                root_paths = self._find_common_root_paths(stage)
                print(f"Found root paths to search: {root_paths}")
                
                for root_path in root_paths:
                    root_prim = stage.GetPrimAtPath(root_path)
                    if root_prim and root_prim.IsValid():
                        self._find_rooms_recursive(stage, root_prim, root_path, room_infos)
            else:
                # 使用指定的搜索路径
                start_prim = stage.GetPrimAtPath(search_path)
                if start_prim and start_prim.IsValid():
                    self._find_rooms_recursive(stage, start_prim, search_path, room_infos)
            
            # 如果还没有找到房间，尝试遍历整个场景
            if not room_infos:
                print("No rooms found with common roots, searching entire stage...")
                all_prims = self._get_all_prims_with_traversal(stage, "/")
                
                for prim in all_prims:
                    prim_name = prim.GetName()
                    
                    # 检查是否包含 _Door 关键字
                    if "_Door" in prim_name:
                        parent_prim = prim.GetParent()
                        if parent_prim and parent_prim.IsValid():
                            room_name = parent_prim.GetName()
                            room_path = str(parent_prim.GetPath())
                            
                            # 检查是否已经添加了此房间
                            room_exists = False
                            for existing_room in room_infos:
                                if existing_room["path"] == room_path:
                                    room_exists = True
                                    break
                            
                            if not room_exists:
                                # 获取场景信息
                                scene_prim = parent_prim.GetParent()
                                scene_name = scene_prim.GetName() if scene_prim and scene_prim.IsValid() else ""
                                is_scene_referenced = False
                                reference_source = ""
                                
                                # 检查引用
                                if scene_prim and scene_prim.IsValid():
                                    if scene_prim.HasAuthoredReferences():
                                        is_scene_referenced = True
                                        refs = scene_prim.GetReferences()
                                        for ref in refs.GetAddedOrExplicitItems():
                                            if ref.assetPath:
                                                ref_path = str(ref.assetPath)
                                                ref_filename = os.path.basename(ref_path)
                                                if '.' in ref_filename:
                                                    ref_filename = ref_filename[:ref_filename.rfind('.')]
                                                reference_source = ref_filename
                                                break
                                
                                room_info = {
                                    "name": room_name,
                                    "path": room_path,
                                    "scene_name": scene_name,
                                    "is_scene_referenced": is_scene_referenced,
                                    "reference_source": reference_source,
                                    "display_name": room_name
                                }
                                
                                if is_scene_referenced and scene_name:
                                    room_info["display_name"] = f"{room_name} ({scene_name})"
                                
                                room_infos.append(room_info)
            
            print(f"Found {len(room_infos)} rooms with doors")
            
        except Exception as e:
            print(f"Error searching for rooms: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return room_infos
    
    def get_doors_in_room(self, room_info):
        """Get all doors in specified room (including referenced USDs)"""
        stage = self.get_stage()
        if not stage:
            return []
            
        doors = []
        room_path = room_info.get("path", "")
        
        if not room_path:
            print(f"Error: Room info missing path: {room_info}")
            return doors
        
        try:
            # 获取房间Prim
            room_prim = stage.GetPrimAtPath(room_path)
            if not room_prim or not room_prim.IsValid():
                print(f"Error: Room prim not found at path: {room_path}")
                return doors
            
            # 遍历房间内的所有Prim查找门
            all_prims = self._get_all_prims_with_traversal(stage, room_path)
            
            for prim in all_prims:
                prim_name = prim.GetName()
                
                # 检查是否包含 _Door 关键字
                if "_Door" in prim_name:
                    # 分析这个门结构
                    door_info = self._analyze_door_structure(prim)
                    if door_info:
                        # 计算门宽度和缓存
                        door_width = self.calculate_door_width(door_info)
                        door_info["width"] = door_width
                        
                        # 检测门方向
                        orientation = self.detect_door_orientation(door_info)
                        door_info["orientation"] = orientation
                        
                        # 添加房间来源信息到门信息中
                        door_info["room_name"] = room_info["name"]
                        door_info["room_path"] = room_info["path"]
                        door_info["room_scene_name"] = room_info["scene_name"]
                        door_info["room_is_scene_referenced"] = room_info["is_scene_referenced"]
                        door_info["room_reference_source"] = room_info["reference_source"]
                        
                        # 检查门是否来自引用
                        door_info["is_referenced"] = prim.HasAuthoredReferences()
                        
                        doors.append(door_info)
            
            print(f"Found {len(doors)} doors in room '{room_info['name']}'")
            
        except Exception as e:
            print(f"Error getting room doors: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return doors
    
    def _analyze_door_structure(self, door_prim):
        """Analyze door structure (supporting references)"""
        try:
            door_path = str(door_prim.GetPath())
            door_name = door_prim.GetName()
            
            # 查找门类型 - 在直接子级中查找四种门类型
            door_type = None
            door_panels = {}
            
            # 遍历直接子级
            for child_prim in door_prim.GetChildren():
                child_name = child_prim.GetName()
                
                # 检查是否是四种门类型之一
                for door_type_key in self.door_types.keys():
                    if door_type_key in child_name:
                        door_type = door_type_key
                        door_panels = self._find_door_panels(child_prim, door_type)
                        break
                
                if door_type:
                    break
            
            # 如果在直接子级中没找到，尝试在更深层次查找
            if not door_type:
                door_type, door_panels = self._find_door_type_recursive(door_prim)
            
            if door_type and door_panels:
                door_info = {
                    "path": door_path,
                    "name": door_name,
                    "type": door_type,
                    "type_display": self.door_types[door_type],
                    "panels": door_panels,
                    "prim": door_prim,
                    "is_open": False,
                    "double_sliding_mode": self.current_double_sliding_mode,
                }
                
                # Record door initial state
                self._record_door_initial_state(door_info)
                
                return door_info
            
            return None
            
        except Exception as e:
            print(f"Error analyzing door structure: {str(e)}")
            return None
    
    def _find_door_type_recursive(self, prim, max_depth=3, current_depth=0):
        """递归查找门类型和门板"""
        if current_depth >= max_depth:
            return None, {}
        
        door_type = None
        door_panels = {}
        
        try:
            # 检查当前 Prim 是否是门类型
            prim_name = prim.GetName()
            for door_type_key in self.door_types.keys():
                if door_type_key in prim_name:
                    door_type = door_type_key
                    door_panels = self._find_door_panels(prim, door_type)
                    return door_type, door_panels
            
            # 递归检查子节点
            for child_prim in prim.GetChildren():
                door_type, door_panels = self._find_door_type_recursive(child_prim, max_depth, current_depth + 1)
                if door_type:
                    return door_type, door_panels
        
        except Exception as e:
            print(f"Error in recursive door type search: {str(e)}")
        
        return None, {}
    
    def calculate_door_width(self, door_info):
        """Calculate total door width, return in meters"""
        try:
            if not door_info or "panels" not in door_info:
                return 2.0
            
            door_path = door_info["path"]
            panels = door_info["panels"]
            
            # Check cache
            if door_path in self.door_width_cache:
                return self.door_width_cache[door_path]
            
            total_width = 0.0
            stage = self.get_stage()
            
            for panel_name, panel_prim in panels.items():
                if panel_prim and panel_prim.IsValid():
                    # Get door panel bounding box
                    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
                    bbox = bbox_cache.ComputeWorldBound(panel_prim)
                    bbox_range = bbox.GetRange()
                    
                    if bbox_range:
                        # Calculate X-axis width (assuming 1 unit=1 cm in USD)
                        x_width = (bbox_range.GetMax()[0] - bbox_range.GetMin()[0]) / 100.0
                        # Calculate Z-axis width (assuming 1 unit=1 cm in USD)
                        z_width = (bbox_range.GetMax()[2] - bbox_range.GetMin()[2]) / 100.0
                        
                        # Use the larger one as width
                        width = max(x_width, z_width)
                        
                        if width > 0:
                            total_width += width
                        else:
                            # If calculation fails, use estimated value
                            if "Dual" in door_info["type"]:
                                total_width += 1.0
                            else:
                                total_width += 1.0
            
            # If no width calculated, use default value
            if total_width <= 0:
                if "Dual" in door_info["type"]:
                    total_width = 2.0
                else:
                    total_width = 1.0
            
            # Ensure minimum value
            total_width = max(0.5, total_width)
            
            # Cache result
            self.door_width_cache[door_path] = total_width
            
            print(f"Door '{door_info['name']}' calculated width: {total_width:.2f}m")
            
            return total_width
            
        except Exception as e:
            print(f"Error calculating door width: {str(e)}")
            return 2.0
    
    def get_door_width(self, door_info):
        """Get door width (meters)"""
        if not door_info:
            return 2.0
        
        door_path = door_info["path"]
        if door_path in self.door_width_cache:
            return self.door_width_cache[door_path]
        
        width = self.calculate_door_width(door_info)
        return width
    
    def get_default_slide_distance(self, door_info):
        """Get default slide distance based on door type"""
        if not door_info:
            return 2.0
        
        door_type = door_info.get("type", "")
        
        if "Single" in door_type and "Sliding" in door_type:
            full_width = self.get_door_width(door_info)
            return float(full_width)
        elif "Dual" in door_type and "Sliding" in door_type:
            full_width = self.get_door_width(door_info)
            half_width = max(0.5, full_width / 2.0)
            return float(half_width)
        else:
            return 2.0
    
    def get_single_panel_slide_distance(self, door_info):
        """Get single sliding door default slide distance"""
        full_width = self.get_door_width(door_info)
        return float(full_width)
    
    def get_dual_panel_slide_distance(self, door_info, mode="both_sides"):
        """Get dual sliding door default slide distance"""
        full_width = self.get_door_width(door_info)
        
        if mode == "both_sides":
            half_width = max(0.5, full_width / 2.0)
            return float(half_width)
        else:
            return float(full_width)
    
    def detect_door_orientation(self, door_info):
        """Detect door orientation, return sliding direction axis"""
        try:
            if not door_info or "panels" not in door_info:
                return "x"
            
            door_path = door_info["path"]
            panels = door_info["panels"]
            
            # Check cache
            if door_path in self.door_orientation_cache:
                return self.door_orientation_cache[door_path]
            
            stage = self.get_stage()
            
            # Get first door panel transformation matrix
            first_panel = list(panels.values())[0]
            if first_panel and first_panel.IsValid():
                xform = UsdGeom.Xformable(first_panel)
                transform = xform.GetLocalTransformation()
                
                # Extract rotation matrix
                rotation = transform.ExtractRotationMatrix()
                
                # Get door panel forward vector in world space
                forward_vector = Gf.Vec3d(0, 0, 1)
                world_forward = rotation.TransformDir(forward_vector)
                
                # Get door panel right vector in world space
                right_vector = Gf.Vec3d(1, 0, 0)
                world_right = rotation.TransformDir(right_vector)
                
                # Calculate angle between door panel and world coordinate axes
                x_alignment = abs(world_forward[0]) + abs(world_right[0])
                z_alignment = abs(world_forward[2]) + abs(world_right[2])
                
                # If door forward or right direction is closer to X-axis, slide along Z-axis
                if x_alignment > z_alignment:
                    orientation = "z"
                else:
                    orientation = "x"
                
                # Check for sliding constraints
                if "Sliding" in door_info["type"]:
                    for panel_name, panel_prim in panels.items():
                        for child in panel_prim.GetChildren():
                            if child.IsA(UsdPhysics.PrismaticJoint):
                                axis_attr = child.GetAttribute("axis")
                                if axis_attr and axis_attr.HasAuthoredValue():
                                    axis = axis_attr.Get()
                                    if abs(axis[0]) > 0.5:
                                        orientation = "x"
                                    elif abs(axis[2]) > 0.5:
                                        orientation = "z"
                
                # Cache result
                self.door_orientation_cache[door_path] = orientation
                return orientation
            
            return "x"
            
        except Exception as e:
            print(f"Error detecting door orientation: {str(e)}")
            return "x"
    
    def _record_door_initial_state(self, door_info):
        """Record door initial state"""
        try:
            if not door_info or "panels" not in door_info:
                return
            
            door_path = door_info["path"]
            panels = door_info["panels"]
            
            if door_path not in self.door_initial_states:
                self.door_initial_states[door_path] = {}
                self.door_target_states[door_path] = {}
                self.is_animating[door_path] = False
            
            for panel_name, panel_prim in panels.items():
                if panel_prim and panel_prim.IsValid():
                    xform = UsdGeom.Xformable(panel_prim)
                    ops = xform.GetOrderedXformOps()
                    
                    initial_transforms = {}
                    for op in ops:
                        if op.GetOpType() in [UsdGeom.XformOp.TypeTranslate, UsdGeom.XformOp.TypeRotateY]:
                            try:
                                value = op.Get()
                                initial_transforms[op.GetOpType()] = value
                            except Exception:
                                if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                                    initial_transforms[UsdGeom.XformOp.TypeTranslate] = Gf.Vec3d(0, 0, 0)
                                elif op.GetOpType() == UsdGeom.XformOp.TypeRotateY:
                                    initial_transforms[UsdGeom.XformOp.TypeRotateY] = 0.0
                    
                    self.door_initial_states[door_path][panel_name] = initial_transforms
                    
        except Exception as e:
            print(f"Error recording door initial state: {str(e)}")
    
    def _find_door_panels(self, door_assembly_prim, door_type):
        """Find door panel components (supporting references)"""
        panels = {}
        
        try:
            children = list(door_assembly_prim.GetChildren())
            
            if "Dual" in door_type:
                for child_prim in children:
                    child_name = child_prim.GetName().lower()
                    if "panel_left" in child_name or "left" in child_name:
                        panels["left"] = child_prim
                    elif "panel_right" in child_name or "right" in child_name:
                        panels["right"] = child_prim
            else:
                for child_prim in children:
                    child_name = child_prim.GetName().lower()
                    if "panel" in child_name and "left" not in child_name and "right" not in child_name:
                        panels["single"] = child_prim
                        break
            
            if not panels:
                for child_prim in children:
                    if "Dual" in door_type:
                        if len(panels) == 0:
                            panels["left"] = child_prim
                        elif len(panels) == 1:
                            panels["right"] = child_prim
                            break
                    else:
                        panels["single"] = child_prim
                        break
        
        except Exception as e:
            print(f"Error finding door panels: {str(e)}")
        
        return panels
    
    def set_double_sliding_mode(self, mode):
        """Set dual sliding door opening mode"""
        if mode in self.double_sliding_modes:
            self.current_double_sliding_mode = mode
            return True
        return False
    
    def get_door_half_width(self, door_info):
        """Get half of door width (meters)"""
        full_width = self.get_door_width(door_info)
        half_width = max(0.5, full_width / 2.0)
        return half_width
    
    def open_door(self, door_info, slide_distance=None, hinge_angle=90.0, direction="push", animation_speed=1.0):
        """Open door operation - with animation effect"""
        try:
            if not door_info or "panels" not in door_info:
                return False
            
            door_path = door_info["path"]
            
            if self.is_animating.get(door_path, False):
                print(f"Door {door_path} is animating, skipping operation")
                return False
            
            if door_info.get("is_open", False):
                self.close_door(door_info, animation_speed)
                return True
            
            door_type = door_info["type"]
            panels = door_info["panels"]
            
            self.is_animating[door_path] = True
            
            if door_type == "Panel_Dual_Sliding":
                door_info["double_sliding_mode"] = self.current_double_sliding_mode
            
            if "Sliding" in door_type:
                if slide_distance is None:
                    if "Single" in door_type:
                        slide_distance = float(self.get_door_width(door_info))
                        print(f"Single sliding door: using door width as slide distance: {slide_distance} meters")
                    else:
                        full_width = self.get_door_width(door_info)
                        double_sliding_mode = door_info.get("double_sliding_mode", "both_sides")
                        
                        if double_sliding_mode == "both_sides":
                            slide_distance = float(self.get_door_half_width(door_info))
                            print(f"Dual sliding door (both_sides mode): using half door width as slide distance: {slide_distance} meters")
                        else:
                            slide_distance = float(full_width)
                            print(f"Dual sliding door ({double_sliding_mode} mode): using door width as slide distance: {slide_distance} meters")
            
            self._calculate_target_state(door_info, slide_distance, hinge_angle, direction)
            
            if "Sliding" in door_type:
                return self._animate_sliding_door(door_info, panels, slide_distance, direction, animation_speed)
            elif "Pivot" in door_type:
                return self._animate_pivot_door(door_info, panels, hinge_angle, direction, animation_speed)
            else:
                self.is_animating[door_path] = False
                return False
                
        except Exception as e:
            print(f"Error during open door operation: {str(e)}")
            self.is_animating[door_path] = False
            return False
    
    def _calculate_target_state(self, door_info, slide_distance, hinge_angle, direction):
        """Calculate door target state"""
        try:
            door_path = door_info["path"]
            door_type = door_info["type"]
            panels = door_info["panels"]
            double_sliding_mode = door_info.get("double_sliding_mode", "both_sides")
            orientation = door_info.get("orientation", "x")
            
            if door_path not in self.door_target_states:
                self.door_target_states[door_path] = {}
            
            slide_direction = 1.0 if direction == "push" else -1.0
            rotation_direction = 1.0 if direction == "push" else -1.0
            
            for panel_name, panel_prim in panels.items():
                if panel_prim and panel_prim.IsValid():
                    target_transforms = {}
                    
                    if panel_name == "single":
                        if "Sliding" in door_type:
                            if orientation == "x":
                                target_transforms[UsdGeom.XformOp.TypeTranslate] = Gf.Vec3d(
                                    slide_distance * slide_direction, 0, 0
                                )
                            else:
                                target_transforms[UsdGeom.XformOp.TypeTranslate] = Gf.Vec3d(
                                    0, 0, slide_distance * slide_direction
                                )
                        elif "Pivot" in door_type:
                            target_transforms[UsdGeom.XformOp.TypeRotateY] = hinge_angle * rotation_direction
                    
                    else:
                        if "Sliding" in door_type:
                            target_translation = self._calculate_dual_sliding_target(
                                panel_name, slide_distance, slide_direction, double_sliding_mode, orientation
                            )
                            target_transforms[UsdGeom.XformOp.TypeTranslate] = target_translation
                        elif "Pivot" in door_type:
                            panel_multiplier = 1.0
                            if panel_name == "left":
                                panel_multiplier = -1.0
                            elif panel_name == "right":
                                panel_multiplier = 1.0
                            
                            target_transforms[UsdGeom.XformOp.TypeRotateY] = hinge_angle * rotation_direction * panel_multiplier
                    
                    self.door_target_states[door_path][panel_name] = target_transforms
                    
        except Exception as e:
            print(f"Error calculating target state: {str(e)}")
    
    def _calculate_dual_sliding_target(self, panel_name, slide_distance, slide_direction, mode, orientation="x"):
        """Calculate dual sliding door target translation"""
        
        if orientation == "x":
            if mode == "left_fixed":
                if panel_name == "left":
                    return Gf.Vec3d(0, 0, 0)
                elif panel_name == "right":
                    return Gf.Vec3d(-slide_distance * slide_direction, 0, 0)
        
            elif mode == "right_fixed":
                if panel_name == "left":
                    return Gf.Vec3d(slide_distance * slide_direction, 0, 0)
                elif panel_name == "right":
                    return Gf.Vec3d(0, 0, 0)
        
            else:
                half_distance = slide_distance / 2.0
                if panel_name == "left":
                    return Gf.Vec3d(half_distance * slide_direction, 0, 0)
                elif panel_name == "right":
                    return Gf.Vec3d(-half_distance * slide_direction, 0, 0)
        
        else:
            if mode == "left_fixed":
                if panel_name == "left":
                    return Gf.Vec3d(0, 0, 0)
                elif panel_name == "right":
                    return Gf.Vec3d(0, 0, -slide_distance * slide_direction)
        
            elif mode == "right_fixed":
                if panel_name == "left":
                    return Gf.Vec3d(0, 0, slide_distance * slide_direction)
                elif panel_name == "right":
                    return Gf.Vec3d(0, 0, 0)
        
            else:
                half_distance = slide_distance / 2.0
                if panel_name == "left":
                    return Gf.Vec3d(0, 0, half_distance * slide_direction)
                elif panel_name == "right":
                    return Gf.Vec3d(0, 0, -half_distance * slide_direction)
        
        return Gf.Vec3d(0, 0, 0)
    
    def _animate_sliding_door(self, door_info, panels, distance, direction, speed):
        """Animate opening sliding door"""
        async def animation_task():
            try:
                door_path = door_info["path"]
                
                animation_duration = 1.0 / speed
                steps = int(animation_duration * 60)
                
                for step in range(steps + 1):
                    if not self.is_animating.get(door_path, False):
                        break
                    
                    progress = step / steps
                    
                    for panel_name, panel_prim in panels.items():
                        if panel_prim and panel_prim.IsValid():
                            initial_state = self.door_initial_states.get(door_path, {}).get(panel_name, {})
                            target_state = self.door_target_states.get(door_path, {}).get(panel_name, {})
                            
                            initial_translation = initial_state.get(UsdGeom.XformOp.TypeTranslate, Gf.Vec3d(0, 0, 0))
                            target_translation = target_state.get(UsdGeom.XformOp.TypeTranslate, Gf.Vec3d(0, 0, 0))
                            
                            xform = UsdGeom.Xformable(panel_prim)
                            ops = xform.GetOrderedXformOps()
                            
                            translate_op = None
                            for op in ops:
                                if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                                    translate_op = op
                                    break
                            
                            if not translate_op:
                                translate_op = xform.AddTranslateOp()
                            
                            new_translation = Gf.Vec3d(
                                initial_translation[0] + (target_translation[0] - initial_translation[0]) * progress,
                                initial_translation[1] + (target_translation[1] - initial_translation[1]) * progress,
                                initial_translation[2] + (target_translation[2] - initial_translation[2]) * progress
                            )
                            
                            translate_op.Set(new_translation)
                    
                    await asyncio.sleep(1/60)
                
                door_info["is_open"] = True
                self.is_animating[door_path] = False
                
            except Exception as e:
                print(f"Sliding door animation error: {str(e)}")
                self.is_animating[door_path] = False
        
        asyncio.ensure_future(animation_task())
        return True
    
    def _animate_pivot_door(self, door_info, panels, angle, direction, speed):
        """Animate opening pivot door"""
        async def animation_task():
            try:
                door_path = door_info["path"]
                
                animation_duration = 1.0 / speed
                steps = int(animation_duration * 60)
                
                for step in range(steps + 1):
                    if not self.is_animating.get(door_path, False):
                        break
                    
                    progress = step / steps
                    
                    for panel_name, panel_prim in panels.items():
                        if panel_prim and panel_prim.IsValid():
                            initial_state = self.door_initial_states.get(door_path, {}).get(panel_name, {})
                            target_state = self.door_target_states.get(door_path, {}).get(panel_name, {})
                            
                            initial_rotation = initial_state.get(UsdGeom.XformOp.TypeRotateY, 0.0)
                            target_rotation = target_state.get(UsdGeom.XformOp.TypeRotateY, 0.0)
                            
                            xform = UsdGeom.Xformable(panel_prim)
                            ops = xform.GetOrderedXformOps()
                            
                            rotate_op = None
                            for op in ops:
                                if op.GetOpType() == UsdGeom.XformOp.TypeRotateY:
                                    rotate_op = op
                                    break
                            
                            if not rotate_op:
                                rotate_op = xform.AddRotateYOp()
                            
                            new_rotation = initial_rotation + (target_rotation - initial_rotation) * progress
                            rotate_op.Set(new_rotation)
                    
                    await asyncio.sleep(1/60)
                
                door_info["is_open"] = True
                self.is_animating[door_path] = False
                
            except Exception as e:
                print(f"Pivot door animation error: {str(e)}")
                self.is_animating[door_path] = False
        
        asyncio.ensure_future(animation_task())
        return True
    
    def close_door(self, door_info, animation_speed=1.0):
        """Close door operation - with animation effect"""
        try:
            if not door_info or "panels" not in door_info:
                return False
            
            door_path = door_info["path"]
            
            if self.is_animating.get(door_path, False):
                print(f"Door {door_path} is animating, skipping operation")
                return False
            
            if not door_info.get("is_open", False):
                return True
            
            panels = door_info["panels"]
            
            self.is_animating[door_path] = True
            
            async def close_animation():
                try:
                    animation_duration = 1.0 / animation_speed
                    steps = int(animation_duration * 60)
                    
                    for step in range(steps + 1):
                        if not self.is_animating.get(door_path, False):
                            break
                        
                        progress = step / steps
                        
                        for panel_name, panel_prim in panels.items():
                            if panel_prim and panel_prim.IsValid():
                                initial_state = self.door_initial_states.get(door_path, {}).get(panel_name, {})
                                target_state = self.door_target_states.get(door_path, {}).get(panel_name, {})
                                
                                xform = UsdGeom.Xformable(panel_prim)
                                ops = xform.GetOrderedXformOps()
                                
                                translate_op = None
                                for op in ops:
                                    if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                                        translate_op = op
                                        break
                                
                                if translate_op:
                                    initial_translation = initial_state.get(UsdGeom.XformOp.TypeTranslate, Gf.Vec3d(0, 0, 0))
                                    target_translation = target_state.get(UsdGeom.XformOp.TypeTranslate, Gf.Vec3d(0, 0, 0))
                                    
                                    reverse_progress = 1.0 - progress
                                    new_translation = Gf.Vec3d(
                                        target_translation[0] * reverse_progress + initial_translation[0] * progress,
                                        target_translation[1] * reverse_progress + initial_translation[1] * progress,
                                        target_translation[2] * reverse_progress + initial_translation[2] * progress
                                    )
                                    translate_op.Set(new_translation)
                                
                                rotate_op = None
                                for op in ops:
                                    if op.GetOpType() == UsdGeom.XformOp.TypeRotateY:
                                        rotate_op = op
                                        break
                                
                                if rotate_op:
                                    initial_rotation = initial_state.get(UsdGeom.XformOp.TypeRotateY, 0.0)
                                    target_rotation = target_state.get(UsdGeom.XformOp.TypeRotateY, 0.0)
                                    
                                    reverse_progress = 1.0 - progress
                                    new_rotation = target_rotation * reverse_progress + initial_rotation * progress
                                    rotate_op.Set(new_rotation)
                        
                        await asyncio.sleep(1/60)
                    
                    self._reset_door_to_initial_state(door_info)
                    
                    door_info["is_open"] = False
                    self.is_animating[door_path] = False
                    
                except Exception as e:
                    print(f"Close door animation error: {str(e)}")
                    self._reset_door_to_initial_state(door_info)
                    door_info["is_open"] = False
                    self.is_animating[door_path] = False
            
            asyncio.ensure_future(close_animation())
            return True
            
        except Exception as e:
            print(f"Error during close door operation: {str(e)}")
            self._reset_door_to_initial_state(door_info)
            door_info["is_open"] = False
            self.is_animating[door_path] = False
            return False
    
    def _reset_door_to_initial_state(self, door_info):
        """Reset door to initial state"""
        try:
            if not door_info:
                return
            
            door_path = door_info["path"]
            panels = door_info["panels"]
            
            initial_states = self.door_initial_states.get(door_path, {})
            
            for panel_name, panel_prim in panels.items():
                if panel_prim and panel_prim.IsValid():
                    xform = UsdGeom.Xformable(panel_prim)
                    ops = xform.GetOrderedXformOps()
                    
                    panel_initial_state = initial_states.get(panel_name, {})
                    
                    translate_op = None
                    for op in ops:
                        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                            translate_op = op
                            break
                    
                    if translate_op:
                        initial_translation = panel_initial_state.get(UsdGeom.XformOp.TypeTranslate, Gf.Vec3d(0, 0, 0))
                        translate_op.Set(initial_translation)
                    
                    rotate_op = None
                    for op in ops:
                        if op.GetOpType() == UsdGeom.XformOp.TypeRotateY:
                            rotate_op = op
                            break
                    
                    if rotate_op:
                        initial_rotation = panel_initial_state.get(UsdGeom.XformOp.TypeRotateY, 0.0)
                        rotate_op.Set(initial_rotation)
            
            door_info["is_open"] = False
            
        except Exception as e:
            print(f"Error resetting door state: {str(e)}")
    
    def set_door_parameters(self, door_info, slide_distance=None, hinge_angle=None, direction=None):
        """Set door parameters (not executed immediately)"""
        try:
            if not door_info:
                return False
            
            if slide_distance is not None:
                door_info["slide_distance"] = slide_distance
            if hinge_angle is not None:
                door_info["hinge_angle"] = hinge_angle
            if direction is not None:
                door_info["direction"] = direction
            
            return True
            
        except Exception as e:
            print(f"Error setting door parameters: {str(e)}")
            return False
    
    def stop_door_animation(self, door_info):
        """Stop door animation"""
        try:
            if not door_info:
                return
            
            door_path = door_info["path"]
            self.is_animating[door_path] = False
            
        except Exception as e:
            print(f"Error stopping door animation: {str(e)}")
    
    def set_search_config(self, include_references=True, max_depth=10):
        """设置搜索配置"""
        self.search_include_references = include_references
        self.search_max_depth = max_depth
    
    def find_referenced_stages(self):
        """查找所有引用的 USD 阶段"""
        referenced_stages = []
        stage = self.get_stage()
        
        def _traverse_prim_for_references(prim, depth=0):
            """递归遍历 Prim 查找引用"""
            if depth > 5:
                return
            
            if prim.HasAuthoredReferences():
                refs = prim.GetReferences()
                for ref in refs.GetAddedOrExplicitItems():
                    if ref.assetPath:
                        asset_path = ref.assetPath
                        print(f"Found reference: {prim.GetPath()} -> {asset_path}")
            
            for child_prim in prim.GetChildren():
                _traverse_prim_for_references(child_prim, depth + 1)
        
        if stage:
            root_prim = stage.GetPrimAtPath("/")
            _traverse_prim_for_references(root_prim)
        
        return referenced_stages