import {Point} from '@angular/cdk/drag-drop';
import {Signal, WritableSignal} from '@angular/core';

/**
 * Represents a single keypoint displayed in KeypointContainerComponent.
 */
export interface KeypointModel {
  name: string;
  position: Signal<Point>;
  colorClass: WritableSignal<string>;
}
