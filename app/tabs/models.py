import asyncio
import enum
import logging

from nicegui.element import Element

from .. import config
from ..dao.model import Model
from nicegui import ui, background_tasks, events, binding

# Set up logging
logger = logging.getLogger(__name__)


class LoadingState(enum.Enum):
    IDLE = 0
    LOADING = 1
    COMPLETED = 2
    FAILED = 3


class ModelCreationForm(Element, component='../components/model_creation_form.vue'):
    def __init__(self):
        super().__init__()
        self.on('submit', self.handle_submit)
        self.on('cancel', self.handle_cancel)

    def handle_submit(self, data):
        print("great success")
        self._props["isDialogOpen"] = False
        self.update()

    def handle_cancel(self):
        self._props["isDialogOpen"] = False
        self.update()

@binding.bindable_dataclass
class ModelFormData:
    """Data structure to hold form values."""
    model_type: str = "supervised"  # Default model type
    loss: str = "pca"  # Default loss

class new_model_dialog(ui.dialog):

    def __init__(
        self,
    ) -> None:
        """new_model_dialog
        """
        super().__init__()


        """
        with self, ui.card():
            with ui.row():
                ui.label("Model Type").classes("font-semibold")
            with ui.row():
                with ui.list().props('tag="label" v-ripple'):
                    with ui.item().props('tag="label" v-ripple'):
                        with ui.item_section().props("avatar"):
                            ui.radio().props('val="supervised"').bind_value(self.data, "model_type")
                        with ui.item_section():
                            ui.item_label('Supervised')
                            ui.item_label('A good starting point to establish baseline performance.').props('caption')
                    with ui.item().props('tag="label" v-ripple'):
                        with ui.item_section().props("avatar"):
                            ui.radio().props('val="context"').bind_value(self.data, "model_type")
                        with ui.item_section():
                            ui.item_label('Context')
                            ui.item_label('Fancy model that may perform better but more GPU-intensive.').props('caption')

            with ui.row():
                ui.radio(
                    options=["Supervised", "Context", "Unsupervised", "Unsupervised context"],
                ).bind_value(self.data, "model_type")

            # Losses to use selection (bind directly to self.data.loss)
            with ui.row():
                ui.label("Losses to Use:").classes("font-semibold")
                ui.radio(
                    options=["pca", "temporal"],
                ).bind_value(self.data, "loss")

            # Action buttons (Save or Cancel)
            with ui.row().classes("justify-end mt-4"):
                ui.button("Create", on_click=self._handle_create).props("unelevated icon=check")
                ui.button("Cancel", on_click=self.close).props("unelevated icon=close")

    def _handle_create(self):
        self.submit(self.data)
"""


class Models:
    def __init__(self) -> None:
        self.model_loading_state = LoadingState.IDLE
        self.models = []

    # Asynchronously load models from filesystem.
    async def load_models(self):
        logger.debug("Starting to load models")
        self.model_loading_state = LoadingState.LOADING
        self.build.refresh()

        self.models = await Model.async_list()
        logger.debug(f"Loaded {len(self.models)} models")

        self.model_loading_state = LoadingState.COMPLETED
        self.build.refresh()

    async def name_edit_callback(self, e: events.GenericEventArguments) -> None:
        print("Hello")  # Placeholder for future implementation
        self._build_model_table.refresh()

    async def train_model(self):
        await asyncio.sleep(1)
        self.models = [
            {"name": "Alice", "created": 18},
            {"name": "Bob", "created": 21},
            {"name": "Carol"},
        ]
        self._build_model_table.refresh()

    async def _new_model_flow(self):
        #x = await new_model_dialog()
        self.data = ModelFormData()

        f = ModelCreationForm()
        f.props["modelData"] = self.data
        f.props["isDialogOpen"] = True
        #if x is not None:
        #    background_tasks.create(self.load_models())

    @ui.refreshable
    def _build_model_table(self):

        columns = [
            {
                "name": "name",
                "label": "Name",
                "align": "left",
                "sortable": True,
                "field": "name",
            },
            {
                "name": "model_type",
                "label": "Model Type",
                "sortable": True,
                "field": "display_model_type",
            },
            {
                "name": "created",
                "label": "Created",
                "sortable": True,
                "field": "creation_timestamp_fmt",
            },
        ]

        # Make table wider and add debug info
        ui.table.default_props(add="dense")
        table = ui.table(
            columns=columns, rows=self.models, row_key="name", selection="multiple"
        ).classes("w-full")

        # Add custom header slot
        table.add_slot(
            "header",
            r"""
            <q-tr :props="props">
                <q-th auto-width></q-th>
                <q-th v-for="col in props.cols" :key="col.name" :props="props">
                    {{ col.label }}
                </q-th>
            </q-tr>
            """,
        )

        # Add custom body slot with editable cells
        table.add_slot(
            "body",
            r"""
            <q-tr :props="props">
                <q-td auto-width>
                    <q-checkbox dense v-model="props.selected" val="props.row.name" />
                </q-td>
                <q-td key="name" :props="props">
                    <div class="row items-center">
                        <a :href="'/p/model/' + props.row.name.replaceAll('/', ':')" class="text-primary">
                            {{ props.row.name }}
                        </a>
                        <q-icon name="edit" class="q-ml-sm edit-icon" size="xs" />
                    </div>
                    <q-popup-edit v-model="props.row.name" v-slot="scope"
                        @update:model-value="() => $parent.$emit('rename', props.row)">
                        <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set" />
                    </q-popup-edit>
                </q-td>
                <q-td key="model_type" :props="props">
                    {{ props.row.display_model_type }}
                </q-td>
                <q-td key="created" :props="props">
                    {{ props.row.creation_timestamp_fmt }}
                </q-td>
            </q-tr>
            """,
        )

        # Add CSS to show/hide the edit icon on hover
        ui.add_css(
            """
            .edit-icon {
                opacity: 0;
                transition: opacity 0.2s;
            }
            .q-tr:hover .edit-icon {
                opacity: 1;
            }
        """
        )

        table.on("rename", self.name_edit_callback)

    @ui.refreshable
    def build(self):
        if self.model_loading_state == LoadingState.IDLE:
            background_tasks.create(self.load_models())
        elif self.model_loading_state == LoadingState.LOADING:
            ui.label("Loading...")
        elif self.model_loading_state == LoadingState.COMPLETED:
            if len(self.models) == 0:
                ui.label(f"No models found in {config.model_dir}.")
                ui.button("New model", on_click=self._new_model_flow)
            else:
                ui.button("New model", on_click=self._new_model_flow)
                with ui.splitter() as splitter:
                    with splitter.before:
                        with ui.row():
                            with ui.card().tight():
                                with ui.expansion("Select models"):
                                    self._build_model_table()
                        with ui.row():
                            with ui.card().tight():
                                with ui.expansion("Select files to predict"):
                                    ui.label("Hello")
                    with splitter.after:
                        with ui.card():
                            ui.label("Summary here")
