
__all__ = ["WidgetInfoManipulator"]

from omni.ui import color as cl
from omni.ui import scene as sc
import omni.ui as ui
import carb
from pxr import Gf
from my_company.my_python_ui_extension.data_service import DataService  # Importing DataService from your extension
import time
import logging
# import omni.kit.app

# manager = omni.kit.app.get_app().get_extension_manager()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# class _ViewportLegacyDisableSelection:
#     """Disables selection in the Viewport Legacy"""
#
#     def __init__(self):
#         self._focused_windows = None
#         focused_windows = []
#         try:
#             # For some reason is_focused may return False, when a Window is definitely in fact is the focused window!
#             # And there's no good solution to this when mutliple Viewport-1 instances are open; so we just have to
#             # operate on all Viewports for a given usd_context.
#             import omni.kit.viewport_legacy as vp
#
#             vpi = vp.acquire_viewport_interface()
#             for instance in vpi.get_instance_list():
#                 window = vpi.get_viewport_window(instance)
#                 if not window:
#                     continue
#                 focused_windows.append(window)
#             if focused_windows:
#                 self._focused_windows = focused_windows
#                 for window in self._focused_windows:
#                     # Disable the selection_rect, but enable_picking for snapping
#                     window.disable_selection_rect(True)
#         except Exception:
#             pass
#
#
# class _DragPrioritize(sc.GestureManager):
#     """Refuses preventing _DragGesture."""
#
#     def can_be_prevented(self, gesture):
#         # Never prevent in the middle of drag
#         return gesture.state != sc.GestureState.CHANGED
#
#     def should_prevent(self, gesture, preventer):
#         if preventer.state == sc.GestureState.BEGAN or preventer.state == sc.GestureState.CHANGED:
#             return True
#
#
# class _DragGesture(sc.DragGesture):
#     """"Gesture to disable rectangle selection in the viewport legacy"""
#
#     def __init__(self):
#         super().__init__(manager=_DragPrioritize())
#
#     def on_began(self):
#         # When the user drags the slider, we don't want to see the selection
#         # rect. In Viewport Next, it works well automatically because the
#         # selection rect is a manipulator with its gesture, and we add the
#         # slider manipulator to the same SceneView.
#         # In Viewport Legacy, the selection rect is not a manipulator. Thus it's
#         # not disabled automatically, and we need to disable it with the code.
#         self.__disable_selection = _ViewportLegacyDisableSelection()
#
#     def on_ended(self):
#         # This re-enables the selection in the Viewport Legacy
#         self.__disable_selection = None
#
#
# class WidgetInfoManipulator(sc.Manipulator):
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#
#         # self.destroy()
#         self._data_service = DataService()
#         self._current_pallet_id = None
#         self._cached_stock_info = None
#         self._last_fetch_time = 0
#         self._fetch_delay = 1  # Minimum delay between fetches in second
#         self._name_label = None
#         # self._radius = 2
#         # self._distance_to_top = 5
#         # self._thickness = 2
#         # self._radius_hovered = 20
#
#         self.info_text = ""
#
#     def on_startup(self, ext_id):
#         self._build_widgets()
#         self.destroy()
#
#     def on_shutdown(self):
#         # Destroy the manipulator and clean up resources
#         if hasattr(self, "_manipulator"):
#             self._manipulator.destroy()
#             self._manipulator = None
#         self._is_active = False  # Mark the extension as inactive
#         if self._data_service:
#             self._data_service.close()  # Close the data service connection
#             self._data_service = None
#         self.destroy()  # Perform other cleanup operations
#
#     def destroy(self):
#         # Cleanup resources
#         if self._data_service:
#             self._data_service.close()  # Assuming you have a close method to stop any ongoing operations
#             self._data_service = None
#
#         self._root = None
#         self._slider_subscription = None
#         self._slider_model = None
#         self._name_label = None
#         self._current_pallet_id = None
#         self._cached_stock_info = None
#
#     def _on_build_widgets(self):
#
#         with ui.ZStack():
#             ui.Rectangle(
#                 style={
#                     "background_color": cl(0.2),
#                     "border_color": cl(0.7),
#                     "border_width": 2,
#                     "border_radius": 8,
#                 }
#             )
#             with ui.VStack(style={"font_size": 30}):
#                 ui.Spacer(height=4)
#                 with ui.ZStack(style={"margin": 4}, height=30):
#                     ui.Rectangle(
#                         style={
#                             "background_color": cl(0.0),
#                         }
#                     )
#                     ui.Line(style={"color": cl(0.7), "border_width": 2}, alignment=ui.Alignment.BOTTOM)
#                     ui.Label("Stock Information", height=0, alignment=ui.Alignment.CENTER)
#
#
#                 ui.Spacer(height=10)
#                 # ui.Spacer(weidth=10)
#                 self._name_label = ui.Label("", height=0, alignment=ui.Alignment.LEFT, style={"margin_right": 20, "margin_left": 20})
#
#                 # setup some model, just for simple demonstration here
#                 self._slider_model = ui.SimpleFloatModel()
#
#         self.on_model_updated(None)
#
#         # Additional gesture that prevents Viewport Legacy selection
#         self._widget.gestures += [_DragGesture()]
#
#     def on_build(self):
#         # self.endpoint_field = "UINT0000036621"
#
#         """Called when the model is chenged and rebuilds the whole slider"""
#         self._root = sc.Transform(visible=False)
#         with self._root:
#             with sc.Transform(scale_to=sc.Space.SCREEN):
#                 with sc.Transform(transform=sc.Matrix44.get_translation_matrix(600, 100, 0)):
#                     # Label
#                     with sc.Transform(look_at=sc.Transform.LookAt.CAMERA):
#                         self._widget = sc.Widget(980, 600, update_policy=sc.Widget.UpdatePolicy.ON_MOUSE_HOVERED)
#                         self._widget.frame.set_build_fn(self._on_build_widgets)
#
#     # def on_model_updated(self, _): #Backup Code-working
#     #     # if we don't have selection then show nothing
#     #     if not self.model or not self.model.get_item("name"):
#     #         self._root.visible = False
#     #         return
#
#     #     selected_object = self.model.get_item("name")
#     #     if selected_object:
#     #         selected_object = selected_object.split('/')[-1]
#
#     #         if not selected_object:
#     #             self._root.visible = False
#     #             return
#
#     #     endpoint = f"pallet/{selected_object}/"
#     #     print(f"Fetching stock info from endpoint: {endpoint}")
#
#     #     stock_info = self._data_service.fetch_stock_info(endpoint)
#
#     #     if stock_info:
#     #         # Access the inventory data if it exists
#     #         inventory = stock_info.get("inventory", {})
#
#     #         # Mapping of the fields to display
#     #         fields_to_display = {
#     #             "Owner": inventory.get("Owner"),
#     #             "Warehouse Code": inventory.get("Warehouse Code"),
#     #             "Lot Number": inventory.get("Lot Number"),
#     #             "Floor No": inventory.get("Floor No"),
#     #             "Quantity on Hand in Loose": inventory.get("Quantity on Hand in Loose"),
#     #             "Location": inventory.get("Location"),
#     #             "Description1": inventory.get("Description1"),
#     #             "Expiry Date": inventory.get("Expiry Date"),
#     #             "Pallet Number": inventory.get("Pallet Number"),
#     #             "MANUFACTURING DATE": inventory.get("MANUFACTURING DATE"),
#     #             "Product Shelf Life": inventory.get("Product Shelf Life"),
#     #             "Balance Shelf Life to Expiry (days)": inventory.get("Balance Shelf Life to Expiry (days)")
#     #         }
#
#     #         # Creating the display text with only the specified fields
#     #         self.info_text = "\n".join([f"{key}: {value}" for key, value in fields_to_display.items() if value is not None])
#     #         print(self.info_text)  # Assuming you want to use it somehow; replace this line accordingly.
#
#     #         # Update the shape display with the fetched info
#     #         if self._name_label:
#     #             self._name_label.text = self.info_text
#
#     #         # Update the transforms
#     #         position = self.model.get_as_floats(self.model.get_item("position"))
#     #         if position:
#     #             self._root.transform = sc.Matrix44.get_translation_matrix(*position)
#     #             self._root.visible = True
#     #         else:
#     #             self._root.visible = False
#
#     #     else:
#     #         self._root.visible = False
#
#     def on_model_updated(self, _):
#         # if we don't have selection then show nothing
#         if not self.model or not self.model.get_item("name"):
#             self._root.visible = False
#             return
#
#         selected_object = self.model.get_item("name")
#         if selected_object:
#             selected_object = selected_object.split('/')[-1]
#
#             if not selected_object:
#                 self._root.visible = False
#                 return
#
#         current_time = time.time()
#         if selected_object != self._current_pallet_id or (current_time - self._last_fetch_time) > self._fetch_delay:
#             self._current_pallet_id = selected_object
#             self._last_fetch_time = current_time
#             self._fetch_and_cache_stock_info()
#
#         # Now use the cached stock info
#         stock_info = self._cached_stock_info
#
#         if stock_info:
#             # Access the inventory data if it exists
#             inventory = stock_info.get("inventory", {})
#
#             # Mapping of the fields to display
#             fields_to_display = {
#                 " Owner": inventory.get("Owner"),
#                 " Warehouse Code": inventory.get("Warehouse Code"),
#                 " Lot Number": inventory.get("Lot Number"),
#                 " Floor No": inventory.get("Floor No"),
#                 " Quantity on Hand in Loose": inventory.get("Quantity on Hand in Loose"),
#                 " Location": inventory.get("Location"),
#                 " Description1": inventory.get("Description1"),
#                 " Expiry Date": inventory.get("Expiry Date"),
#                 " Pallet Number": inventory.get("Pallet Number"),
#                 " MANUFACTURING DATE": inventory.get("MANUFACTURING DATE"),
#                 " Product Shelf Life": inventory.get("Product Shelf Life"),
#                 " Balance Shelf Life to Expiry (days)": inventory.get("Balance Shelf Life to Expiry (days)"),
#                 " Pallet Denomination": inventory.get("Pallet Denomination"),
#                 " Inbound Container No": inventory.get("Inbound Container No"),
#                 " Unit of Measure Code": inventory.get("Unit of Measure Code"),
#             }
#
#             # Creating the display text with only the specified fields
#             self.info_text = "\n".join([f"{key}: {value}" for key, value in fields_to_display.items() if value is not None])
#             logger.info(self.info_text)
#             # Update the shape display with the fetched info
#             if self._name_label:
#                 self._name_label.text = self.info_text
#
#             # Update the transforms
#             position = self.model.get_as_floats(self.model.get_item("position"))
#             if position:
#                 self._root.transform = sc.Matrix44.get_translation_matrix(*position)
#                 self._root.visible = True
#             else:
#                 self._root.visible = False
#
#         else:
#             self._root.visible = False
#     def _fetch_and_cache_stock_info(self):
#         """Fetch and cache stock information for the current pallet ID."""
#         if self._current_pallet_id:
#             endpoint = f"pallet/{self._current_pallet_id}/"
#             logger.info(f"Fetching stock info from endpoint: {endpoint}")
#             self._cached_stock_info = self._data_service.fetch_stock_info(endpoint)

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
        with ui.ZStack():
            ui.Rectangle(
                style={
                    "background_color": cl(0.2),
                    "border_color": cl(0.7),
                    "border_width": 2,
                    "border_radius": 8,
                }
            )
            with ui.VStack(style={"font_size": 25}):
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

    def on_build(self):
        self._root = sc.Transform(visible=False)
        with self._root:
            with sc.Transform(scale_to=sc.Space.SCREEN):
                with sc.Transform(transform=sc.Matrix44.get_translation_matrix(-400, 100, 0)):
                    with sc.Transform(look_at=sc.Transform.LookAt.CAMERA):
                        self._widget = sc.Widget(800,500, update_policy=sc.Widget.UpdatePolicy.ON_MOUSE_HOVERED)
                        self._widget.frame.set_build_fn(self._on_build_widgets)

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
                " Unit of Measure Code": inventory.get("Unit of Measure Code"),
            }

            self.info_text = "\n".join(
                [f"{key}: {value}" for key, value in fields_to_display.items() if value is not None])
            logger.info(self.info_text)
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
        if self._current_pallet_id:
            endpoint = f"pallet/{self._current_pallet_id}/"
            logger.info(f"Fetching stock info from endpoint: {endpoint}")
            self._cached_stock_info = self._data_service.fetch_stock_info(endpoint)
