import {
  afterNextRender,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  inject,
  input,
  signal,
  ViewChild,
} from '@angular/core';
import {VideoPlayerState} from '../video-player-state';
import {DragDropModule, Point} from '@angular/cdk/drag-drop';
import {VideoMetadata} from '../../../video-metadata';
import {BehaviorSubject} from 'rxjs';

/**
 * The VideoTileComponent displays a video.
 *
 * Play / pause / seek are controlled by `VideoPlayerState`. If the component is deemed Primary by
 * the VideoPlayerState, it updates the VideoPlayerState of the currentTime of playback, in order
 * to synchronize with other video players.
 *
 * The parent component can content-project other components like Keypoints. The video player
 * projects such components into a relatively positioned div, so children can be absolutely positioned
 * within.
 *
 * Inputs:
 * - `src`: A signal input for the video source URL.
 * - `isPrimary`: Whether the element is primary.
 */
@Component({
  selector: 'app-video-tile',
  imports: [],
  templateUrl: './video-tile.component.html',
  styleUrl: './video-tile.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class VideoTileComponent {
  @ViewChild('videoEl', { static: true }) videoElement: ElementRef | null = null;


  src = input<string>("");
  isPrimary = signal<boolean>(false);
  localCurrentTime = signal<number>(0);

  // the main state, injected from parent so it can be easily shared across video players
  videoPlayerState: VideoPlayerState = inject(VideoPlayerState);

  constructor(private elementRef: ElementRef) {
    this.videoPlayerState.registerVideoPlayer(this);
  }

  protected onTimeUpdate() {
    this.localCurrentTime.set(this.videoElement?.nativeElement.currentTime ?? 0);

    if (this.isPrimary() && this.videoPlayerState.isPlaying.value) {
      this.videoPlayerState.currentTime.next(this.localCurrentTime());
    }
  }

  ngOnDestroy() {
    this.videoPlayerState.unregisterVideoPlayer(this);
  }

  videoMetadata = new BehaviorSubject<VideoMetadata>({
    duration: 0,
    width: 0,
    height: 0,
  });

  scaleFactor = signal<number>(1);

  onLoadedMetadata() {
    this.videoMetadata.next({
      height: this.videoElement?.nativeElement.videoHeight ?? 1,
      width: this.videoElement?.nativeElement.videoWidth ?? 1,
      duration: this.videoElement?.nativeElement.duration ?? 0,
    });

    this.scaleFactor.set(this.elementRef.nativeElement.clientWidth / this.videoMetadata.value.width);
  }
}
