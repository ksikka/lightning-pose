import asyncio
import enum
import logging

from .. import config
from ..dao.model import Model
from nicegui import ui, background_tasks, events

# Set up logging
logger = logging.getLogger(__name__)

class LoadingState(enum.Enum):
    IDLE = 0
    LOADING = 1
    COMPLETED = 2
    FAILED = 3

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
        self.build.refresh()

    async def train_model(self):
        await asyncio.sleep(1)
        self.models = [
            {'name': 'Alice', 'created': 18},
            {'name': 'Bob', 'created': 21},
            {'name': 'Carol'},
        ]
        self.build.refresh()

    @ui.refreshable
    def build(self):
        if self.model_loading_state == LoadingState.IDLE:
            # Start loading models
            self.model_loading_state = LoadingState.LOADING
            background_tasks.create(self.load_models())
        elif self.model_loading_state == LoadingState.LOADING:
            ui.label("Loading...")
        elif self.model_loading_state == LoadingState.COMPLETED:
            if len(self.models) == 0:
                ui.label(f"No models found in {config.model_dir}.")
                ui.button("New model", on_click=self.train_model)
            else:
                ui.button("New model", on_click=self.train_model)

                columns = [
                    {'name': 'name', 'label': 'Name', 'align': 'left', "sortable": True, "field": "name"},
                    {'name': 'created', 'label': 'Created', "sortable": True, "field": "creation_timestamp_fmt"},
                    {'name': 'model_type', 'label': 'Model Type', "sortable": True, "field": "display_model_type"},
                ]

                # Make table wider and add debug info
                table = ui.table(columns=columns, rows=self.models, row_key='name').classes("w-full")

                # Add custom header slot
                table.add_slot(
                    "header",
                    r"""
                    <q-tr :props="props">
                        <q-th v-for="col in props.cols" :key="col.name" :props="props">
                            {{ col.label }}
                        </q-th>
                    </q-tr>
                    """
                )

                # Add custom body slot with editable cells
                table.add_slot(
                    "body",
                    r"""
                    <q-tr :props="props">
                        <q-td key="name" :props="props">
                            <div class="row items-center">
                                {{ props.row.name }}
                                <q-icon name="edit" class="q-ml-sm edit-icon" size="xs" />
                            </div>
                            <q-popup-edit v-model="props.row.name" v-slot="scope"
                                @update:model-value="() => $parent.$emit('rename', props.row)">
                                <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set" />
                            </q-popup-edit>
                        </q-td>
                        <q-td key="created" :props="props">
                            {{ props.row.creation_timestamp_fmt }}
                        </q-td>
                        <q-td key="model_type" :props="props">
                            {{ props.row.display_model_type }}
                        </q-td>
                    </q-tr>
                    """
                )

                # Add CSS to show/hide the edit icon on hover
                ui.add_css("""
                    .edit-icon {
                        opacity: 0;
                        transition: opacity 0.2s;
                    }
                    .q-tr:hover .edit-icon {
                        opacity: 1;
                    }
                """)

                table.on("rename", self.name_edit_callback)

