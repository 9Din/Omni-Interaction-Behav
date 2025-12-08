import pathlib
import omni.kit.app
import omni.ui as ui
from typing import Optional, List

# ==============================================================================
# Export all needed constants
# ==============================================================================

__all__ = [
    'main_window_style', 
    'ColorWidget', 
    'CustomCollsableFrame',
    'build_collapsable_header', 
    '_get_search_glyph',
    'cl_text_gray', 
    'cl_text', 
    'cls_button_gradient',
    'cl_attribute_red',
    'cl_attribute_dark',
    'cl_attribute_green', 
    'cl_attribute_blue',
    'cl_line',
    'cl_text_blue',
    'cl_text_hovered',
    'cl_field_text',
    'cl_widget_background',
    'cl_attribute_default',
    'cl_attribute_changed',
    'cl_slider',
    'cl_combobox_background',
    'cl_main_background',
    'cl_button_border',
    'cls_temperature_gradient',
    'cls_color_gradient',
    'cls_tint_gradient',
    'cls_grey_gradient'
]

# ==============================================================================
# Style definitions
# ==============================================================================

EXTENSION_FOLDER_PATH = pathlib.Path(
    omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__)
)

# Layout constants
fl_attr_hspacing = 10
fl_attr_spacing = 1
fl_group_spacing = 5

# Color constants
cl_attribute_dark = ui.color("#202324")
cl_attribute_red = ui.color("#ac6060")
cl_attribute_green = ui.color("#60ab7c")
cl_attribute_blue = ui.color("#35889e")
cl_line = ui.color("#404040")
cl_text_blue = ui.color("#5eb3ff")
cl_text_gray = ui.color("#707070")
cl_text = ui.color("#a1a1a1")
cl_text_hovered = ui.color("#ffffff")
cl_field_text = ui.color("#5f5f5f")
cl_widget_background = ui.color("#1f2123")
cl_attribute_default = ui.color("#505050")
cl_attribute_changed = ui.color("#55a5e2")
cl_slider = ui.color("#383b3e")
cl_combobox_background = ui.color("#252525")
cl_main_background = ui.color("#2a2b2c")
cl_button_border = ui.color("#555555")

# Gradient colors
cls_temperature_gradient = [ui.color("#fe0a00"), ui.color("#f4f467"), ui.color("#a8b9ea"), ui.color("#2c4fac"), ui.color("#274483"), ui.color("#1f334e")]
cls_color_gradient = [ui.color("#fa0405"), ui.color("#95668C"), ui.color("#4b53B4"), ui.color("#33C287"), ui.color("#9fE521"), ui.color("#ff0200")]
cls_tint_gradient = [ui.color("#1D1D92"), ui.color("#7E7EC9"), ui.color("#FFFFFF")]
cls_grey_gradient = [ui.color("#020202"), ui.color("#525252"), ui.color("#FFFFFF")]
cls_button_gradient = [ui.color("#232323"), ui.color("#656565")]

# Main style dictionary
main_window_style = {
    "Button::add": {"background_color": cl_widget_background},
    "Field::add": { "font_size": 14, "color": cl_text},
    "Field::search": { "font_size": 16, "color": cl_field_text},
    "Field::path": { "font_size": 14, "color": cl_field_text},
    "ScrollingFrame::main_frame": {"background_color": cl_main_background},

    "CollapsableFrame::group": {
        "margin_height": fl_group_spacing,
        "background_color": 0x0,
        "secondary_color": 0x0,
    },
    "CollapsableFrame::group:hovered": {
        "margin_height": fl_group_spacing,
        "background_color": 0x0,
        "secondary_color": 0x0,
    },

    "Circle::group_circle": {
        "background_color": cl_line,
    },

    "Line::group_line": {"color": cl_line},

    "Label::collapsable_name": {
        "alignment": ui.Alignment.LEFT_CENTER,
        "color": cl_text
        },

    "Label::attribute_bool": {
        "alignment": ui.Alignment.LEFT_BOTTOM,
        "margin_height": fl_attr_spacing,
        "margin_width": fl_attr_hspacing,
        "color": cl_text
    },
    
    "Label::attribute_name": {
        "alignment": ui.Alignment.RIGHT_CENTER,
        "margin_height": fl_attr_spacing,
        "margin_width": fl_attr_hspacing,
        "color": cl_text
    },
    "Label::attribute_name:hovered": {"color": cl_text_hovered},

    "Label::header_attribute_name": {
        "alignment": ui.Alignment.LEFT_CENTER,
        "color": cl_text,
        "font_size": 12,
    },

    "Label::details": {
        "alignment": ui.Alignment.LEFT_CENTER,
        "color": cl_text_blue,
        "font_size": 19,
    },

    "Label::layers": {
        "alignment": ui.Alignment.LEFT_CENTER,
        "color": cl_text_gray,
        "font_size": 19,
    },

    "Label::attribute_r": {
        "alignment": ui.Alignment.LEFT_CENTER,
        "color": cl_attribute_red
    },
    "Label::attribute_g": {
        "alignment": ui.Alignment.LEFT_CENTER,
        "color": cl_attribute_green
    },
    "Label::attribute_b": {
        "alignment": ui.Alignment.LEFT_CENTER,
        "color": cl_attribute_blue
    },

    "Slider::float_slider":{
        "background_color": cl_widget_background,
        "secondary_color": cl_slider,
        "border_radius": 3,
        "corner_flag": ui.CornerFlag.ALL,
        "draw_mode": ui.SliderDrawMode.FILLED,
    },

    "Circle::slider_handle":{"background_color": 0x0, "border_width": 2, "border_color": cl_combobox_background},

    "Rectangle::attribute_changed": {"background_color":cl_attribute_changed, "border_radius": 2},
    "Rectangle::attribute_default": {"background_color":cl_attribute_default, "border_radius": 1},

    "Image::pin": {"image_url": f"{EXTENSION_FOLDER_PATH}/icons/Pin.svg"},
    "Image::reset": {"image_url": f"{EXTENSION_FOLDER_PATH}/icons/Reset.svg"},
    "Image::transform": {"image_url": f"{EXTENSION_FOLDER_PATH}/icons/offset_dark.svg"},
    "Image::link": {"image_url": f"{EXTENSION_FOLDER_PATH}/icons/link_active_dark.svg"},
    "Image::on_off": {"image_url": f"{EXTENSION_FOLDER_PATH}/icons/on_off.svg"},
    "Image::header_frame": {"image_url": f"{EXTENSION_FOLDER_PATH}/icons/head.png"},
    "Image::checked": {"image_url": f"{EXTENSION_FOLDER_PATH}/icons/checked.svg"},
    "Image::unchecked": {"image_url": f"{EXTENSION_FOLDER_PATH}/icons/unchecked.svg"},
    "Image::separator":{"image_url": f"{EXTENSION_FOLDER_PATH}/icons/separator.svg"},
    "Image::collapsable_opened": {"color": cl_text, "image_url": f"{EXTENSION_FOLDER_PATH}/icons/closed.svg"},
    "Image::collapsable_closed": {"color": cl_text, "image_url": f"{EXTENSION_FOLDER_PATH}/icons/open.svg"},
    # "Image::combobox": {"image_url": f"{EXTENSION_FOLDER_PATH}/icons/combobox_bg.svg"},
    "Image::logo": {"image_url": f"{EXTENSION_FOLDER_PATH}/icons/HBAresidential.png"},

    "ImageWithProvider::gradient_slider":{"border_radius": 4, "corner_flag": ui.CornerFlag.ALL},
    "ImageWithProvider::button_background_gradient": {"border_radius": 3, "corner_flag": ui.CornerFlag.ALL},

    "ComboBox::dropdown_menu":{
        "color": cl_text,
        "background_color": cl_combobox_background,
        "secondary_color": 0x0,
    },

    "Button::turn_on_off": {
        "background_color": cl_widget_background,
        "border_color": cl_button_border,
        "border_width": 1,
        "border_radius": 4
    },
    "Button::reset_button": {
        "background_color": cl_widget_background,
        "border_color": cl_button_border,
        "border_width": 1,
        "border_radius": 4
    },
}

def hex_to_color(hex: int) -> tuple:
    """Convert hexadecimal color value to RGBA tuple"""
    red = hex & 255
    green = (hex >> 8) & 255
    blue = (hex >> 16) & 255
    alpha = (hex >> 24) & 255
    rgba_values = [red, green, blue, alpha]
    return rgba_values

def _interpolate_color(hex_min: int, hex_max: int, intep):
    """Interpolate between two colors"""
    max_color = hex_to_color(hex_max)
    min_color = hex_to_color(hex_min)
    color = [int((max - min) * intep) + min for max, min in zip(max_color, min_color)]
    return (color[3] << 8 * 3) + (color[2] << 8 * 2) + (color[1] << 8 * 1) + color[0]

def get_gradient_color(value, max, colors):
    """Get gradient color based on value and color list"""
    step_size = len(colors) - 1
    step = 1.0/float(step_size)
    percentage = value / float(max)

    idx = (int) (percentage / step)
    if idx == step_size:
        color = colors[-1]
    else:
        color = _interpolate_color(colors[idx], colors[idx+1], percentage)
    return color

def generate_byte_data(colors):
    """Generate byte data for gradient image"""
    data = []
    for color in colors:
        data += hex_to_color(color)

    _byte_provider = ui.ByteImageProvider()
    _byte_provider.set_bytes_data(data, [len(colors), 1])
    return _byte_provider

def build_gradient_image(colors, height, style_name):
    """Build gradient image"""
    byte_provider = generate_byte_data(colors)
    ui.ImageWithProvider(byte_provider, fill_policy=ui.IwpFillPolicy.IWP_STRETCH, height=height, name=style_name)
    return byte_provider


# ==============================================================================
# Color control
# ==============================================================================

class ColorWidget:
    """Composite control for color input"""

    def __init__(self, *args, model=None, **kwargs):
        self.__defaults: List[float] = args
        self.__model: Optional[ui.AbstractItemModel] = kwargs.pop("model", None)
        self.__multifield: Optional[ui.MultiFloatDragField] = None
        self.__colorpicker: Optional[ui.ColorWidget] = None
        self.__draw_colorpicker = kwargs.pop("draw_colorpicker", True)
        self.on_color_changed = kwargs.pop("on_color_changed", None)

        self.__frame = ui.Frame()
        with self.__frame:
            self._build_fn()

    def destroy(self):
        """Destroy control"""
        self.__model = None
        self.__multifield = None
        self.__colorpicker = None
        self.__frame = None

    def __getattr__(self, attr):
        """Delegate to self.__frame for accessing width/height and callback functions"""
        return getattr(self.__frame, attr)

    @property
    def model(self) -> Optional[ui.AbstractItemModel]:
        """Control's model"""
        if self.__multifield:
            return self.__multifield.model

    @model.setter
    def model(self, value: ui.AbstractItemModel):
        """Set control's model"""
        self.__multifield.model = value
        if self.__colorpicker:
            self.__colorpicker.model = value

    def get_color(self):
        """Get current color value"""
        if self.__multifield and self.__multifield.model:
            try:
                r_model = self.__multifield.model.get_item_value_model(0)
                g_model = self.__multifield.model.get_item_value_model(1)
                b_model = self.__multifield.model.get_item_value_model(2)
                
                if r_model and g_model and b_model:
                    return [
                        r_model.get_value_as_float(),
                        g_model.get_value_as_float(),
                        b_model.get_value_as_float()
                    ]
            except Exception as e:
                print(f"Error getting color value: {str(e)}")
        return [1.0, 1.0, 1.0]

    def set_color(self, color):
        """Set color value"""
        if self.__multifield and self.__multifield.model:
            try:
                r_model = self.__multifield.model.get_item_value_model(0)
                g_model = self.__multifield.model.get_item_value_model(1)
                b_model = self.__multifield.model.get_item_value_model(2)
                
                if r_model and g_model and b_model:
                    r_model.set_value(color[0])
                    g_model.set_value(color[1])
                    b_model.set_value(color[2])
            except Exception as e:
                print(f"Error setting color value: {str(e)}")

    def _build_fn(self):
        """Build UI function"""
        SPACING = 16

        def _on_value_changed(model, rect_changed, rect_default):
            """Callback when value changes"""
            try:
                current_color = self.get_color()
                
                if current_color == [self.__defaults[0], self.__defaults[1], self.__defaults[2]]:
                    rect_changed.visible = False
                    rect_default.visible = True
                else:
                    rect_changed.visible = True
                    rect_default.visible = False
                
                if self.on_color_changed:
                    self.on_color_changed(current_color)
            except Exception as e:
                print(f"Color value change callback error: {str(e)}")

        def _restore_default(rect_changed, rect_default):
            """Callback to restore default values"""
            try:
                self.set_color(self.__defaults)
                rect_changed.visible = False
                rect_default.visible = True
                
                if self.on_color_changed:
                    self.on_color_changed(self.__defaults)
            except Exception as e:
                print(f"Error restoring default color: {str(e)}")

        with ui.HStack(spacing=SPACING):
            if self.__model:
                self.__multifield = ui.MultiFloatDragField(
                    min=0, max=1, model=self.__model, h_spacing=SPACING, name="attribute_color"
                )
                model = self.__model
            else:
                with ui.ZStack():
                    with ui.HStack():
                        self.color_button_gradient_R = build_gradient_image([cl_attribute_dark, cl_attribute_red], 22, "button_background_gradient")
                        ui.Spacer(width=9)
                        with ui.VStack(width=6):
                            ui.Spacer(height=8)
                            ui.Circle(name="group_circle", width=4, height=4)
                        self.color_button_gradient_G = build_gradient_image([cl_attribute_dark, cl_attribute_green], 22, "button_background_gradient")
                        ui.Spacer(width=9)
                        with ui.VStack(width=6):
                            ui.Spacer(height=8)
                            ui.Circle(name="group_circle", width=4, height=4)
                        self.color_button_gradient_B = build_gradient_image([cl_attribute_dark, cl_attribute_blue], 22, "button_background_gradient")
                        ui.Spacer(width=2)
                    with ui.HStack():
                        with ui.VStack():
                            ui.Spacer(height=1)
                            self.__multifield = ui.MultiFloatDragField(
                                *self.__defaults, min=0, max=1, h_spacing=SPACING, name="attribute_color")
                        ui.Spacer(width=3)
                    with ui.HStack(spacing=22):
                        labels = ["R", "G", "B"] if self.__draw_colorpicker else ["X", "Y", "Z"]
                        ui.Label(labels[0], name="attribute_r")
                        ui.Label(labels[1], name="attribute_g")
                        ui.Label(labels[2], name="attribute_b")
                model = self.__multifield.model
            
            if self.__draw_colorpicker:
                self.__colorpicker = ui.ColorWidget(model, width=0)
            
            rect_changed, rect_default = self.__build_value_changed_widget()
            
            if self.__multifield and self.__multifield.model:
                for i in range(3):
                    try:
                        item_model = self.__multifield.model.get_item_value_model(i)
                        if item_model:
                            item_model.add_value_changed_fn(
                                lambda model, rc=rect_changed, rd=rect_default: 
                                _on_value_changed(model, rc, rd)
                            )
                    except Exception as e:
                        print(f"Error adding color channel listener: {str(e)}")
            
            rect_changed.set_mouse_pressed_fn(
                lambda x, y, b, m: _restore_default(rect_changed, rect_default)
            )

    def __build_value_changed_widget(self):
        """Build value change indicator control"""
        with ui.VStack(width=0):
            ui.Spacer(height=3)
            rect_changed = ui.Rectangle(name="attribute_changed", width=15, height=15, visible= False)
            ui.Spacer(height=4)
            with ui.HStack():
                ui.Spacer(width=3)
                rect_default = ui.Rectangle(name="attribute_default", width=5, height=5, visible= True)
        return rect_changed, rect_default


# ==============================================================================
# Collapsable panel control
# ==============================================================================

def build_collapsable_header(collapsed, title):
    """Build custom title for collapsable frame"""
    with ui.HStack():
        ui.Spacer(width=10)
        ui.Label(title, name="collapsable_name")
        
        if collapsed:
            image_name = "collapsable_opened"
        else:
            image_name = "collapsable_closed"
        ui.Image(name=image_name, fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT, width=16, height=16)

class CustomCollsableFrame:
    """Custom collapsable frame control"""

    def __init__(self, frame_name, collapsed=False):
        with ui.ZStack():
            self.collapsable_frame = ui.CollapsableFrame(
                frame_name, name="group", build_header_fn=build_collapsable_header, collapsed=collapsed)
            
            with ui.VStack():
                ui.Spacer(height=29)
                with ui.HStack():
                    ui.Spacer(width=20)
                    ui.Image(name="separator", fill_policy=ui.FillPolicy.STRETCH, height=15)
                    ui.Spacer(width=20)


# ==============================================================================
# Utility functions
# ==============================================================================

def _get_search_glyph():
    """Get search icon"""
    return omni.kit.ui.get_custom_glyph_code("${glyphs}/menu_search.svg")

