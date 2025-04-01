import {Signal, WritableSignal} from '@angular/core';
import {KeypointModel} from './keypoint-model';

export interface VideoWidgetModel {
  id: string;
  videoSrc: string;
  keypointModels: KeypointModel[];
}
