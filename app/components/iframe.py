from nicegui import ui

class Iframe(ui.element, component="../js/iframe.js"):
    """A custom iframe component for NiceGUI."""
    
    def __init__(self, src: str, width: str = '100%', height: str = '100%'):
        """
        Create a new iframe.
        
        Args:
            src: The URL to load in the iframe
            width: The width of the iframe (default: '100%')
            height: The height of the iframe (default: '100%')
        """
        super().__init__()
        self.props['src'] = src
        self.props['width'] = width
        self.props['height'] = height
    
    def set_source(self, src: str):
        """Set the source URL of the iframe."""
        self.props['src'] = src
        self.update()
    
    def set_visibility(self, visible: bool):
        """Set the visibility of the iframe."""
        if visible:
            self.classes('block')
        else:
            self.classes('hidden')
        self.update() 