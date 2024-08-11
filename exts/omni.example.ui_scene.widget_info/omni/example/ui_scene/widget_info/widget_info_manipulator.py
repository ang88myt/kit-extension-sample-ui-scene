## Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
##
## NVIDIA CORPORATION and its licensors retain all intellectual property
## and proprietary rights in and to this software, related documentation
## and any modifications thereto.  Any use, reproduction, disclosure or
## distribution of this software and related documentation without an express
## license agreement from NVIDIA CORPORATION is strictly prohibited.
##
__all__ = ["WidgetInfoManipulator"]

from omni.ui import color as cl
from omni.ui import scene as sc
import omni.ui as ui
import carb
from pxr import Gf
from my_company.my_python_ui_extension.data_service import DataService  # Importing DataService from your extension


class _ViewportLegacyDisableSelection:
    """Disables selection in the Viewport Legacy"""

    def __init__(self):
        self._focused_windows = None
        focused_windows = []
        try:
            # For some reason is_focused may return False, when a Window is definitely in fact is the focused window!
            # And there's no good solution to this when mutliple Viewport-1 instances are open; so we just have to
            # operate on all Viewports for a given usd_context.
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
                    # Disable the selection_rect, but enable_picking for snapping
                    window.disable_selection_rect(True)
        except Exception:
            pass


class _DragPrioritize(sc.GestureManager):
    """Refuses preventing _DragGesture."""

    def can_be_prevented(self, gesture):
        # Never prevent in the middle of drag
        return gesture.state != sc.GestureState.CHANGED

    def should_prevent(self, gesture, preventer):
        if preventer.state == sc.GestureState.BEGAN or preventer.state == sc.GestureState.CHANGED:
            return True


class _DragGesture(sc.DragGesture):
    """"Gesture to disable rectangle selection in the viewport legacy"""

    def __init__(self):
        super().__init__(manager=_DragPrioritize())

    def on_began(self):
        # When the user drags the slider, we don't want to see the selection
        # rect. In Viewport Next, it works well automatically because the
        # selection rect is a manipulator with its gesture, and we add the
        # slider manipulator to the same SceneView.
        # In Viewport Legacy, the selection rect is not a manipulator. Thus it's
        # not disabled automatically, and we need to disable it with the code.
        self.__disable_selection = _ViewportLegacyDisableSelection()

    def on_ended(self):
        # This re-enables the selection in the Viewport Legacy
        self.__disable_selection = None


class WidgetInfoManipulator(sc.Manipulator):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.destroy()
        self._data_service = DataService()
        self._radius = 2
        self._distance_to_top = 5
        self._thickness = 2
        self._radius_hovered = 20
       
        self.info_text = ""
        
    def on_startup(self, ext_id):
        self._build_widgets()
    
   
                    
    def destroy(self):
        self._root = None
        self._slider_subscription = None
        self._slider_model = None
        self._name_label = None
        # if self._data_service:
        #     self._data_service.close()  # Close any connections if applicable 
       
    def _on_build_widgets(self):
        
        with ui.ZStack():
            ui.Rectangle(
                style={
                    "background_color": cl(0.2),
                    "border_color": cl(0.7),
                    "border_width": 2,
                    "border_radius": 4,
                }
            )
            with ui.VStack(style={"font_size": 30}):
                ui.Spacer(height=4)
                with ui.ZStack(style={"margin": 1}, height=30):
                    ui.Rectangle(
                        style={
                            "background_color": cl(0.0),
                        }
                    )
                    ui.Line(style={"color": cl(0.7), "border_width": 2}, alignment=ui.Alignment.BOTTOM)
                    ui.Label("Stock Information", height=0, alignment=ui.Alignment.CENTER)

                ui.Spacer(height=10)
                self._name_label = ui.Label("", height=0, alignment=ui.Alignment.LEFT)

                # setup some model, just for simple demonstration here
                self._slider_model = ui.SimpleFloatModel()

        self.on_model_updated(None)

        # Additional gesture that prevents Viewport Legacy selection
        self._widget.gestures += [_DragGesture()]

    def on_build(self):
        self.endpoint_field = "UINT0000036621"
        
        """Called when the model is chenged and rebuilds the whole slider"""
        self._root = sc.Transform(visible=False)
        with self._root:
            with sc.Transform(scale_to=sc.Space.SCREEN):
                with sc.Transform(transform=sc.Matrix44.get_translation_matrix(600, 100, 0)):
                    # Label
                    with sc.Transform(look_at=sc.Transform.LookAt.CAMERA):
                        self._widget = sc.Widget(850, 450, update_policy=sc.Widget.UpdatePolicy.ON_MOUSE_HOVERED)
                        self._widget.frame.set_build_fn(self._on_build_widgets)

    def on_model_updated(self, _):
        # if we don't have selection then show nothing
        if not self.model or not self.model.get_item("name"):
            self._root.visible = False
            return

        selected_object = self.model.get_item("name")
        if selected_object:
            selected_object = selected_object.split('/')[-1]

            if not selected_object:
                self._root.visible = False
                return

        endpoint = f"pallet/{selected_object}/"
        print(f"Fetching stock info from endpoint: {endpoint}")

        stock_info = self._data_service.fetch_stock_info(endpoint)

        if stock_info:
            limited_items = list(stock_info.items())[:11]
            self.info_text = "\n".join([f"{key}: {value}" for key, value in limited_items])
            print(self.info_text)  # Assuming you want to use it somehow; replace this line accordingly.
             # Update the shape display with the fetched info
            if self._name_label:
                self._name_label.text = self.info_text

            # Update the transforms
            position = self.model.get_as_floats(self.model.get_item("position"))
            if position:
                self._root.transform = sc.Matrix44.get_translation_matrix(*position)
                self._root.visible = True
            else:
                self._root.visible = False

        else:
            self._root.visible = False
            
            
            
            