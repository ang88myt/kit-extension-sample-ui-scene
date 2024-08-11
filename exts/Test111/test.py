# def on_model_updated(self, _):
    #     # if we don't have selection then show nothing
    #     if not self.model or not self.model.get_item("name"):
    #         self._root.visible = False
    #         return

    #     selected_object = self.model.get_item("name")
    #     if selected_object:
    #         selected_object = selected_object.split('/')[-1]

    #         if not selected_object:
    #             self._root.visible = False
    #             return

    #     endpoint = f"pallet/{selected_object}/"
    #     print(f"Fetching stock info from endpoint: {endpoint}")

    #     stock_info = self._data_service.fetch_stock_info(endpoint)

    #     if stock_info:
    #         limited_items = list(stock_info.items())[:11]
    #         self.info_text = "\n".join([f"{key}: {value}" for key, value in limited_items])
    #         print(self.info_text)  # Assuming you want to use it somehow; replace this line accordingly.
    #          # Update the shape display with the fetched info
    #         if self._name_label:
    #             self._name_label.text = self.info_text

    #         # Update the transforms
    #         position = self.model.get_as_floats(self.model.get_item("position"))
    #         if position:
    #             self._root.transform = sc.Matrix44.get_translation_matrix(*position)
    #             self._root.visible = True
    #         else:
    #             self._root.visible = False

    #     else:
    #         self._root.visible = False