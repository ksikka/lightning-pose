import logging
from typing import Dict

from nicegui import ui

from ..services.job_manager import JobManager, Job

# Set up logging
logger = logging.getLogger(__name__)

class Jobs:
    def __init__(self) -> None:
        self.job_manager = JobManager()
        # Register a callback to refresh the UI when job status changes
        self.job_manager.register_status_change_callback(self.build.refresh)

    async def start_job(self, name: str, command: str) -> None:
        """Start a new job with the given name and command."""
        if self.job_manager.start_job(name, command):
            ui.notify(f"Started job '{name}'", type="positive")
        else:
            ui.notify(f"Failed to start job '{name}'", type="negative")

    async def stop_job(self, name: str) -> None:
        """Stop a running job by name."""
        if self.job_manager.stop_job(name):
            ui.notify(f"Stopped job '{name}'", type="info")
        else:
            ui.notify(f"Failed to stop job '{name}'", type="warning")

    def _build_jobs_table(self):
        """Build the UI table for displaying jobs."""
        logger.debug("Building jobs table")
        columns = [
            {'name': 'name', 'label': 'Name', 'align': 'left', "sortable": True, "field": "name"},
            {'name': 'command', 'label': 'Command', "sortable": True, "field": "command"},
            {'name': 'status', 'label': 'Status', "sortable": True, "field": "status"},
            {'name': 'pid', 'label': 'PID', "sortable": True, "field": "pid"},
            {'name': 'actions', 'label': 'Actions', "field": "actions"},
        ]

        rows = []
        for job in self.job_manager.get_jobs().values():
            rows.append({
                'name': job.name,
                'command': job.command,
                'status': job.status,
                'pid': job.pid,
                'actions': 'stop' if job.is_running() else 'start'
            })

        table = ui.table(columns=columns, rows=rows, row_key='name').classes("w-full")

        # Add custom body slot with action buttons
        table.add_slot(
            "body",
            r"""
            <q-tr :props="props">
                <q-td key="name" :props="props">
                    {{ props.row.name }}
                </q-td>
                <q-td key="command" :props="props">
                    {{ props.row.command }}
                </q-td>
                <q-td key="status" :props="props">
                    <q-chip :color="props.row.status === 'Running' ? 'positive' : 'grey'" text-color="white">
                        {{ props.row.status }}
                    </q-chip>
                </q-td>
                <q-td key="pid" :props="props">
                    {{ props.row.pid || '-' }}
                </q-td>
                <q-td key="actions" :props="props">
                    <q-btn v-if="props.row.status === 'Running'" 
                           color="negative" 
                           icon="stop" 
                           size="sm" 
                           @click="$parent.$emit('stop', props.row.name)" />
                    <q-btn v-else 
                           color="positive" 
                           icon="play_arrow" 
                           size="sm" 
                           @click="$parent.$emit('start', props.row.name)" />
                </q-td>
            </q-tr>
            """
        )

        table.on("stop", lambda e: self.stop_job(e.args))
        table.on("start", lambda e: self.start_job(e.args, self.job_manager.get_job(e.args).command))

    @ui.refreshable
    def build(self):
        """Build the jobs tab UI."""
        ui.page_title("Lightning Pose | Jobs")
        
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("Job Manager").classes("text-h6")
                with ui.row():
                    job_name = ui.input("Job Name").classes("w-40")
                    job_command = ui.input("Command").classes("w-96")
                    ui.button("Start Job", on_click=lambda: self.start_job(
                        job_name.value, 
                        job_command.value
                    ), icon="play_arrow")
        
        with ui.card().classes("w-full mt-4"):
            self._build_jobs_table() 