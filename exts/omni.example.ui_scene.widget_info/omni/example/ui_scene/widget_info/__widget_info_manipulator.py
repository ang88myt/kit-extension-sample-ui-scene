from pxr import Sdf, UsdGeom, Gf, Usd, Kind
import omni.ui as ui
import carb
from omni.ui import color as cl
from omni.ui import scene as sc
import time
import logging
from my_company.my_python_ui_extension.data_service import DataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self._is_active = True  # Flag to check if the extension is active
        self._root = None  # Initialize _root to avoid the attribute error

    def on_startup(self, ext_id):
        self._is_active = True  # Mark the extension as active
        self._build_widgets()
        self.destroy()

    def on_shutdown(self):
        if hasattr(self, "_manipulator"):
            self._manipulator.destroy()
            self._manipulator = None
        self._is_active = False  # Mark the extension as inactive
        if self._data_service:
            self._data_service.close()
            self._data_service = None
        self.destroy()

    def destroy(self):
        self._is_active = False  # Ensure that the flag is set to False when destroying the extension
        if self._data_service:
            self._data_service.close()
            self._data_service = None
        self._root = None  # Properly clean up the _root
        self._slider_subscription = None
        self._slider_model = None
        self._name_label = None
        self._current_pallet_id = None
        self._cached_stock_info = None

    def on_build(self):
        # Initialize the _root transform object for use in the UI
        self._root = sc.Transform(visible=False)
        
        # Build your scene structure and UI components
        with self._root:
            with sc.Transform(scale_to=sc.Space.SCREEN):
                with sc.Transform(transform=sc.Matrix44.get_translation_matrix(300, 50, 0)):
                    with sc.Transform(look_at=sc.Transform.LookAt.CAMERA):
                        self._widget = sc.Widget(700, 480, update_policy=sc.Widget.UpdatePolicy.ON_MOUSE_HOVERED)
                        self._widget.frame.set_build_fn(self._on_build_widgets)

    def _on_build_widgets(self):
        with ui.ZStack():
            ui.Rectangle(
                style={
                    "background_color": cl(0.2),
                    "border_color": cl(0.7),
                    "border_width": 2,
                    "border_radius": 8,
                }
            )
            with ui.VStack(style={"font_size": 24}):
                ui.Spacer(height=4)
                with ui.ZStack(style={"margin": 4}, height=30):
                    ui.Rectangle(
                        style={"background_color": cl(0.0)},
                    )
                    ui.Line(style={"color": cl(0.7), "border_width": 2}, alignment=ui.Alignment.BOTTOM)
                    ui.Label("Stock Information", height=0, alignment=ui.Alignment.CENTER)
                ui.Spacer(height=10)
                self._name_label = ui.Label("", height=0, alignment=ui.Alignment.LEFT,
                                            style={"margin_right": 20, "margin_left": 20})

                self._slider_model = ui.SimpleFloatModel()

        self.on_model_updated(None)
        self._widget.gestures += [_DragGesture()]

    def on_model_updated(self, _):
        if not self.model or not self.model.get_item("name"):
            self._root.visible = False
            return

        selected_object = self.model.get_item("name")
        if selected_object:
            selected_object = selected_object.split('/')[-1]
            if not selected_object:
                self._root.visible = False
                return

        current_time = time.time()
        if selected_object != self._current_pallet_id or (current_time - self._last_fetch_time) > self._fetch_delay:
            self._current_pallet_id = selected_object
            self._last_fetch_time = current_time
            self._fetch_and_cache_stock_info()

        stock_info = self._cached_stock_info
        if stock_info:
            inventory = stock_info.get("inventory", {})
            fields_to_display = {
                " Owner": inventory.get("Owner"),
                " Warehouse Code": inventory.get("Warehouse Code"),
                " Lot Number": inventory.get("Lot Number"),
                " Floor No": inventory.get("Floor No"),
                " Quantity on Hand in Loose": inventory.get("Quantity on Hand in Loose"),
                " Location": inventory.get("Location"),
                " Description1": inventory.get("Description1"),
                " Expiry Date": inventory.get("Expiry Date"),
                " Pallet Number": inventory.get("Pallet Number"),
                " MANUFACTURING DATE": inventory.get("MANUFACTURING DATE"),
                " Product Shelf Life": inventory.get("Product Shelf Life"),
                " Balance Shelf Life to Expiry (days)": inventory.get("Balance Shelf Life to Expiry (days)"),
                " Pallet Denomination": inventory.get("Pallet Denomination"),
                " Inbound Container No": inventory.get("Inbound Container No"),
                "Stock Status Code": inventory.get("Stock Status Code"),
            }

            self.info_text = "\n".join(
                [f"{key}: {value}" for key, value in fields_to_display.items() if value is not None])
            logging.info(self.info_text)
            if self._name_label:
                self._name_label.text = self.info_text

            position = self.model.get_as_floats(self.model.get_item("position"))
            if position:
                self._root.transform = sc.Matrix44.get_translation_matrix(*position)
                self._root.visible = True
            else:
                self._root.visible = False
        else:
            self._root.visible = False

    def _fetch_and_cache_stock_info(self):
        if not self._is_active:  # Ensure no API calls are made when the extension is inactive
            logging.info("Extension is inactive. Skipping fetch.")
            return

        if self._current_pallet_id:
            endpoint = f"pallet/{self._current_pallet_id}/"
            logging.info(f"Fetching stock info from endpoint: {endpoint}")
            self._cached_stock_info = self._data_service.fetch_stock_info(endpoint)


# Viewport-related classes for disabling selection in legacy mode
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
