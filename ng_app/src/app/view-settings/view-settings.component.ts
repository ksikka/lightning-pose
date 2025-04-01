import {ChangeDetectionStrategy, Component, input} from '@angular/core';
import {ViewSettings} from '../view-settings.model';

@Component({
  selector: 'app-view-settings',
  imports: [],
  templateUrl: './view-settings.component.html',
  styleUrl: './view-settings.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ViewSettingsComponent {
  viewSettings = input.required<ViewSettings>();

  setRandomViewSettings() {
    //this.viewSettings().tracesShown.update(x => !x);
  }
}
