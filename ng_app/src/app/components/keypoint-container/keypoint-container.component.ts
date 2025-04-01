import {
  afterNextRender,
  ChangeDetectionStrategy,
  Component, computed,
  effect,
  Host,
  Injectable,
  input,
  Optional, Signal,
  signal,
  untracked
} from '@angular/core';
import {CdkDragEnd, DragDrop, DragDropModule, Point} from "@angular/cdk/drag-drop";
import {KeypointModel} from '../../keypoint-model';
import {VideoTileComponent} from '../video-player/video-tile/video-tile.component';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {VideoMetadata} from '../../video-metadata';

/**
 * Hack to override dragStartThreshold to 0.
 */
@Injectable()
class CustomDragDrop extends DragDrop {
  override createDrag<T = any>(element: any, config: any): any {

    const modifiedConfig = {
      ...config,
      dragStartThreshold: 0
    };
    return super.createDrag<T>(element, modifiedConfig);
  }
}

/**
 * KeypointContainerComponent is responsible for displaying a collection
 * of keypoints.
 *
 * LabelingMode (WIP) makes points draggable. Currently we update the keypoint
 * model position when the dragging has ended, not during dragging.
 * (Updating the position while dragging caused issues with the underlying cdkDrag machinery.)
 */
@Component({
  selector: 'app-keypoint-container',
  imports: [
    DragDropModule
  ],
  templateUrl: './keypoint-container.component.html',
  styleUrl: './keypoint-container.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [{ provide: DragDrop, useClass: CustomDragDrop }],
})
export class KeypointContainerComponent {
  labelerMode = input<boolean>(false);
  keypointModels = input.required<KeypointModel[]>();

  protected initialPosition = signal<Point | null>(null);

  protected parentVideoMetadata = signal<VideoMetadata | null>(null);

  protected scaledKeypointModels: Signal<KeypointModel[]>;

  constructor(@Optional() @Host() public parent?: VideoTileComponent) {
    if (!parent) {
      // this should never happen
      alert('KeypointContainerComponent must be used inside a VideoTileComponent for now.');
      throw new Error('KeypointContainerComponent must be used inside a VideoTileComponent for now.');
    }
    parent.videoMetadata.pipe(takeUntilDestroyed());

    this.scaledKeypointModels = computed(() => {
      return this.keypointModels().map((k) => {
        return {...k, position: computed(() => {
          return {x:k.position().x * parent.scaleFactor(), y: k.position().y * parent.scaleFactor()};
          })};
      });
    })

    effect(() => {
      // On keypoints initialization
      this.keypointModels();

      // TODO convert to inputTransform.
      untracked(() => {
        if (!this.initialPosition() && this.keypointModels().length > 0) {
          this.initialPosition.set(this.keypointModels()[0].position());
        }
      })
    });
  }

  protected onKeypointDragEnd(keypointModel: KeypointModel, event: CdkDragEnd) {
    const cdkPosition = event.source.getFreeDragPosition();
    //keypointModel.position.set(cdkPosition);
  }
}
