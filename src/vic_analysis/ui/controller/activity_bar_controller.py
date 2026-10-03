from vic_analysis.ui.model.application_state import AppState
from vic_analysis.ui.view.activity_bar import ActivityBar
from vic_analysis.ui.view.widgets.activity_button import ActivityButton


class ActivityBarController:
    def __init__(self, view: ActivityBar, state: AppState) -> None:
        self.view = view
        self.state = state
        self.view.group.buttonToggled.connect(self.on_click)

    def on_click(self, button: ActivityButton) -> None:
        if button.isChecked():
            self.state.activity_open_requested.emit(button)
        else:
            self.state.activity_close_requested.emit(button)
