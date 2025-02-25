
__all__ = ["WidgetInfoManipulator"]

from omni.ui import color as cl
from omni.ui import scene as sc
import omni.ui as ui
import carb
from pxr import Gf
from my_company.my_python_ui_extension.data_service import DataService  # Importing DataService from your extension
import time
# import logging
# import omni.kit.app
from omni.ui import url
from omni.ui import color as cl
from omni.ui import constant as fl
import pathlib
from datetime import datetime

# manager = omni.kit.app.get_app().get_extension_manager()
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

EXTENSION_FOLDER_PATH = pathlib.Path("D:/Git/kit-extension-sample-ui-scene/exts/omni.example.ui_scene.widget_info/omni/example/ui_scene/widget_info/icons")

# Window Constants
WIN_WIDTH = 320
WIN_HEIGHT = 450

# Colors & Styling
cl.window_bg_color = cl(0.2, 0.2, 0.2, 1.0)
cl.label_text = cl(0.9, 0.9, 0.9, 1.0)
cl.section_bg = cl(0.18, 0.18, 0.18, 1.0)
cl.section_border = cl(1.0, 1.0, 1.0, 0.2)

fl.section_padding = 6
fl.section_spacing = 4
fl.label_font_size = 18
fl.value_font_size = 22
fl.border_radius = 4
# url.food_icon = f"{EXTENSION_FOLDER_PATH}/icons/mdi_food.svg"
# Style Dictionary
pallet_info_style = {
    #     "Image::food_icon": {
    #     "image_url": url.food_icon,
    #     "width": 16,
    #     "height": 16,
    # },
    "Label::title": {
        "color": cl.label_text,
        "font_size": fl.value_font_size,
        "font_weight": "bold"
    },
    "Label::header": {
        "color": cl.label_text,
        "font_size": fl.label_font_size,
        "font_weight": "bold"
    },
    "VStack::section": {
        "background_color": cl.section_bg,
        "border_radius": fl.border_radius,
        "padding": fl.section_padding,
    },
}

class _ViewportLegacyDisableSelection:
    """Disables selection in the Viewport Legacy"""

    def __init__(self):
        self._focused_windows = None
        focused_windows = []
        try:
            import omni.kit.viewport_legacy as vp

            vpi = vp.acquire_viewport_interface()
            for instance in vpi.get_instance_list():
                window = vpi.get_viewport_window(instance)
                if not window:
                    continue
                focused_windows.append(window)
            if focused_windows:
                self._focused_windows = focused_windows
                for window in self._focused_windows:
                    window.disable_selection_rect(True)
        except Exception:
            pass


class _DragPrioritize(sc.GestureManager):
    """Refuses preventing _DragGesture."""

    def can_be_prevented(self, gesture):
        return gesture.state != sc.GestureState.CHANGED

    def should_prevent(self, gesture, preventer):
        if preventer.state == sc.GestureState.BEGAN or preventer.state == sc.GestureState.CHANGED:
            return True


class _DragGesture(sc.DragGesture):
    """"Gesture to disable rectangle selection in the viewport legacy"""

    def __init__(self):
        super().__init__(manager=_DragPrioritize())

    def on_began(self):
        self.__disable_selection = _ViewportLegacyDisableSelection()

    def on_ended(self):
        self.__disable_selection = None


class WidgetInfoManipulator(sc.Manipulator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._data_service = DataService()
        self._current_pallet_id = None
        self._cached_stock_info = None
        self._last_fetch_time = 0
        self._fetch_delay = 1  # Minimum delay between fetches in second
        self._name_label = None
        self.info_text = ""
        self.info_dict = {}

    def on_startup(self, ext_id):
        self._build_widgets()
        self.destroy()

    def on_shutdown(self):
        if hasattr(self, "_manipulator"):
            self._manipulator.destroy()
            self._manipulator = None
        self._is_active = False
        if self._data_service:
            self._data_service.close()
            self._data_service = None
        self.destroy()

    def destroy(self):
        if self._data_service:
            self._data_service.close()
            self._data_service = None
        self._root = None
        self._slider_subscription = None
        self._slider_model = None
        self._name_label = None
        self._current_pallet_id = None
        self._cached_stock_info = None

    def _on_build_widgets(self):

        if self.info_text and isinstance(self.info_text, str):
            try:
                # ✅ Handle cases where ": " might not exist on a line (avoiding ValueError)
                info_dict = {k.strip(): v.strip() for line in self.info_text.split("\n") if ": " in line for k, v in
                             [line.split(": ", 1)]}
            except Exception as e:
                carb.log_error(f"❌ Error parsing info_text: {e}")
                info_dict = {}  # Fallback to empty dict if parsing fails
        else:
            carb.log_warn("⚠ info_text is empty or not a string!")
            info_dict = {}

        # ✅ Extract information safely, defaulting to "N/A" if missing
        pallet_id = info_dict.get("Pallet ID", "N/A")
        product_sku = info_dict.get("Product", "N/A")
        owner = info_dict.get("Owner", "N/A")
        loose_item_quantity = info_dict.get("Loose Item Quantity", "N/A")
        product_description = info_dict.get("Product Description", "N/A")
        expiry_date = info_dict.get("Expiry Date", "N/A")
        days_to_expire = info_dict.get("Days to Expiry", "N/A")
        stock_status_code = info_dict.get("Stock Status Code", "N/A")
        product_group = info_dict.get("Product Group", "N/A")

        # ✅ Ensure expiry_date is valid before formatting
        try:
            if expiry_date and expiry_date != "N/A":
                expiry_date = datetime.strptime(expiry_date, "%Y-%m-%dT%H:%M:%S").strftime("%d-%m-%Y")
            else:
                expiry_date = "N/A"
        except ValueError:
            carb.log_warn(f"⚠ Invalid expiry date format: {expiry_date}")
            expiry_date = "N/A"


        # ✅ Correct product group mapping
        if product_group == "HPC":
            product_group = "Non-Consumables"
            product_image = str(EXTENSION_FOLDER_PATH / "ic_outline-miscellaneous-services.svg")
        else:
            product_group = "Consumables"
            product_image = str(EXTENSION_FOLDER_PATH / "mdi_food.svg")
        # print(product_group)
        # print(product_image)
        # print(pallet_id)
        # ✅ Log extracted information
        # carb.log_info(
        #     f"✔ Processed Pallet: {pallet_id}, Product: {product_sku}, Group: {product_group}, Expiry: {expiry_date}")


        with ui.ZStack():
            ui.Rectangle(
                style={
                    "background_color": cl(0.0),
                    "border_color": cl(0.7),
                    "border_width": 2,
                    "border_radius": 12,
                }
            )
            self.ui_container = ui.VStack()
            self.ui_container.clear()

            with self.ui_container:
                ui.VStack().clear()
                ui.Spacer(height=4)
                with ui.ZStack(style={"margin": 5}, height=30):
                    # ui.Rectangle(
                    #     style={"background_color": cl(0.0)},
                    # )

                    # ui.Line(style={"color": cl(0.7), "border_width": 4}, alignment=ui.Alignment.BOTTOM)
                    with ui.VStack(style=pallet_info_style["Label::title"]):
                        ui.Label("Pallet Information", height=0, alignment=ui.Alignment.LEFT)

                        ui.Spacer(height=10)
                        with ui.ZStack():
                            ui.Rectangle(
                                alignment=ui.Alignment.CENTER,
                                # width=700,
                                height=200,
                                style={
                                    "background_color": cl(0.1),
                                    "border_color": cl(0.7),
                                    "border_width": 2,
                                    "border_radius": 12,
                                }
                            )
                            with ui.VStack(height=0, spacing=6,
                                           alignment=ui.Alignment.LEFT_CENTER):  # ✅ Adjusted to full center alignment
                                with ui.HStack(spacing=6,
                                               alignment=ui.Alignment.LEFT_CENTER):  # ✅ Center align Image & Labels

                                    ui.Image(product_image, width=40, height=40)

                                    with ui.VStack(height=0, alignment=ui.Alignment.LEFT_CENTER):  # ✅ Center align Labels
                                        ui.Label("Product Group", name="header",
                                                 style=pallet_info_style["Label::header"],
                                                 alignment=ui.Alignment.LEFT_CENTER)
                                        ui.Label(product_group, name="title", style=pallet_info_style["Label::title"],
                                                 alignment=ui.Alignment.LEFT_CENTER)

                                # ✅ Pallet ID and SKU Layout (Center aligned)
                                with ui.HStack(spacing=65, alignment=ui.Alignment.LEFT_CENTER):
                                    ui.Label("Pallet ID", name="header", style=pallet_info_style["Label::header"],
                                             width=ui.Fraction(2), alignment=ui.Alignment.LEFT_CENTER)
                                    ui.Label("Product/SKU", name="header", style=pallet_info_style["Label::header"],
                                             width=ui.Fraction(2), alignment=ui.Alignment.LEFT_CENTER)

                                with ui.HStack(spacing=65, alignment=ui.Alignment.LEFT_CENTER):
                                    ui.Label(pallet_id, name="title", style=pallet_info_style["Label::title"],
                                             width=ui.Fraction(1), alignment=ui.Alignment.LEFT_CENTER)
                                    # print(pallet_id)
                                    ui.Label(product_sku, name="title", style=pallet_info_style["Label::title"],
                                             width=ui.Fraction(1), alignment=ui.Alignment.LEFT_CENTER)
                                    # print(product_sku)
                                ui.Spacer(height=20)  # ✅ Reduced space for compactness

                                # ✅ Item Details Section (Center Aligned)
                                ui.Label("Item Details", name="header", style=pallet_info_style["Label::header"],
                                         alignment=ui.Alignment.LEFT_CENTER)
                                ui.Line(style_type_name_override="HeaderLine")
                                ui.Spacer(height=6)  # ✅ Reduced height for better spacing

                                # ✅ Product Description Section (Center Aligned)
                                ui.Label("Product Description", name="header", style=pallet_info_style["Label::header"],
                                         alignment=ui.Alignment.LEFT_CENTER)
                                ui.Label(
                                    product_description,
                                    word_wrap=True,
                                    alignment=ui.Alignment.LEFT_CENTER,  # ✅ Ensures text is centered
                                    width=410  # ✅ Ensures text wraps correctly
                                )
                                with ui.VStack():
                                    ui.Label("Owner", name="header",
                                             style=pallet_info_style["Label::header"],
                                             alignment=ui.Alignment.LEFT_CENTER)
                                    ui.Label(owner, name="header",
                                             style=pallet_info_style["Label::title"],
                                             alignment=ui.Alignment.LEFT_CENTER)
                                    with ui.HStack():
                                        ui.Label("Stock Status Code", name="header",
                                                 style=pallet_info_style["Label::header"],
                                                 alignment=ui.Alignment.LEFT_CENTER)
                                        ui.Label("Loose Item Quantity", name="header",
                                                 style=pallet_info_style["Label::header"],
                                                 alignment=ui.Alignment.LEFT_CENTER)
                                    with ui.VStack():
                                        with ui.HStack():
                                            ui.Label(stock_status_code, name="title",
                                                 style=pallet_info_style["Label::title"],
                                                 alignment=ui.Alignment.LEFT_CENTER)

                                            ui.Label(loose_item_quantity, name="title",
                                                     style=pallet_info_style["Label::title"],
                                                     alignment=ui.Alignment.LEFT_CENTER)
                                        with ui.HStack():
                                            ui.Label("Expiry Date", name="header",
                                                 style=pallet_info_style["Label::header"],
                                                 alignment=ui.Alignment.LEFT_CENTER)

                                            ui.Label("Day to Expire", name="header",
                                                     style=pallet_info_style["Label::header"],
                                                     alignment=ui.Alignment.LEFT_CENTER)
                                        with ui.VStack():
                                            with ui.HStack():
                                                ui.Label(expiry_date, name="title",
                                                         style=pallet_info_style["Label::title"],
                                                         alignment=ui.Alignment.LEFT_CENTER)

                                                ui.Label(days_to_expire, name="title",
                                                         style=pallet_info_style["Label::title"],
                                                     alignment=ui.Alignment.LEFT_CENTER)

                # self._name_label = ui.Label("", height=0, alignment=ui.Alignment.LEFT,
                #                             style=pallet_info_style["Label::title"])

                self._slider_model = ui.SimpleFloatModel()

        self.on_model_updated(None)
        self._widget.gestures += [_DragGesture()]

    def on_build(self):
        self._root = sc.Transform(visible=False)
        with self._root:
            with sc.Transform(scale_to=sc.Space.SCREEN):
                with sc.Transform(transform=sc.Matrix44.get_translation_matrix(-100, 300, 0)):
                    with sc.Transform(look_at=sc.Transform.LookAt.CAMERA):
                        self._widget = sc.Widget(450,750, update_policy=sc.Widget.UpdatePolicy.ON_MOUSE_HOVERED)
                        self._widget.frame.set_build_fn(self._on_build_widgets)

    def on_model_updated(self, _):
        """Handles updates when the model changes."""

        if not self.model or not self.model.get_item("name"):
            self._root.visible = False
            return

        # ✅ Extract selected object and sanitize its name
        selected_object = self.model.get_item("name")
        if selected_object:
            selected_object = selected_object.split('/')[-1].replace("hpc_", "").replace("food_", "").replace("_", "")
            if not selected_object:
                self._root.visible = False
                return

        # ✅ Fetch stock info if pallet ID is new or cache expired
        current_time = time.time()
        if selected_object != self._current_pallet_id or (current_time - self._last_fetch_time) > self._fetch_delay:
            self._current_pallet_id = selected_object
            self._last_fetch_time = current_time
            self._fetch_and_cache_stock_info()

        stock_info = self._cached_stock_info

        # ✅ Extract inventory details
        inventory = stock_info.get("inventory", {})
        fields_to_display = {
            "Product": inventory.get("Product"),
            "Pallet ID": inventory.get("Pallet Number"),
            "Loose Item Quantity": inventory.get("Quantity on Hand in Loose"),
            "Product Description": inventory.get("Description1"),
            "Expiry Date": inventory.get("Expiry Date"),
            "Owner": inventory.get("Owner"),
            "Days to Expiry": inventory.get("Balance Shelf Life to Expiry (days)"),
            "Stock Status Code": inventory.get("Stock Status Code"),
            "Product Group": inventory.get("Product Group"),
        }
        # print(fields_to_display["Pallet ID"])
        # ✅ Ensure all values are strings (avoiding NoneType issues)
        self.info_text = "\n".join(
            [f"{key}: {value}" for key, value in fields_to_display.items() if value is not None]
        )

        # ✅ Handle position transformation safely
        position = self.model.get_as_floats(self.model.get_item("position"))
        if position and len(position) == 3:
            self._root.transform = sc.Matrix44.get_translation_matrix(*position)
            self._root.visible = True
        else:
            self._root.visible = False

    def _fetch_and_cache_stock_info(self):
        if self._current_pallet_id:
            endpoint = f"pallet/{self._current_pallet_id}/"
            carb.log_info(f"Fetching stock info from endpoint: {endpoint}")
            self._cached_stock_info = self._data_service.fetch_stock_info(endpoint)
