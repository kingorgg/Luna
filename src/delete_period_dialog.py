from gi.repository import Adw, Gtk, Gio, GObject


@Gtk.Template(resource_path="/io/github/kingorgg/Luna/delete_period_dialog.ui")
class DeletePeriodDialog(Adw.AlertDialog):
    __gtype_name__ = "DeletePeriodDialog"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
