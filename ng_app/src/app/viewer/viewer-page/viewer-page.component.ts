import {
  ChangeDetectionStrategy,
  Component,
  computed,
  effect, inject, Input,
  input,
  signal, untracked,
  viewChild
} from '@angular/core';
import {ViewerLeftPanelComponent} from '../viewer-left-panel/viewer-left-panel.component';
import {Session} from '../../session.model';
import {ViewSettings} from '../../view-settings.model';
import {ViewSettingsComponent} from '../../view-settings/view-settings.component';
import {VideoPlayerState} from '../../components/video-player/video-player-state';
import {ViewerCenterPanelComponent} from '../viewer-center-panel/viewer-center-panel.component';
import {ProjectMetadataService} from '../../project-metadata.service';

@Component({
  selector: 'app-viewer',
  imports: [
    ViewerLeftPanelComponent,
    ViewSettingsComponent,
    ViewerCenterPanelComponent,
  ],
  templateUrl: './viewer-page.component.html',
  styleUrl: './viewer-page.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [VideoPlayerState],
})
export class ViewerPageComponent {
  centerPanel = viewChild(ViewerCenterPanelComponent);

  /**
   * Set by the router when there is a session key in the path.
   *
   * Flow: user clicks link -> Router -> ViewerPageComponent.
   *
   * @param sessionKey
   */
  @Input() set sessionKey(sessionKey: string | null) {
    this._sessionKey.set(sessionKey);
    if (sessionKey == null) {
      // todo
      return;
    }
    this.centerPanel()?.loadSession(sessionKey);
  };

  _sessionKey = signal<string | null>(null);

  viewSettings: ViewSettings;
  projectMetadataService = inject(ProjectMetadataService);

  constructor() {
    this.viewSettings = {
      viewsShown: signal(this.projectMetadataService.getAllViews()),
      keypointsShown: signal(this.projectMetadataService.getAllKeypoints())
    };
  }

  selectedSession = computed<Session | null>(() => {
    const sessionKey = this._sessionKey();
    if (!sessionKey) {
      return null;
    } else {
      return {
        key: sessionKey,
      };
    }
  });
}
