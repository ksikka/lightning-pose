import {Signal} from '@angular/core';

export interface ViewSettings {
  keypointColorMapping?: Signal<Map<string, string>>;
  viewsShown: Signal<string[]>;
  keypointsShown: Signal<string[]>;
}
