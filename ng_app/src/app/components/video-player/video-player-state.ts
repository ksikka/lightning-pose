import {
  afterNextRender,
  AfterRenderPhase,
  computed,
  effect,
  inject,
  Injectable,
  Injector,
  Signal,
  signal, untracked
} from '@angular/core';
import {VideoTileComponent} from './video-tile/video-tile.component';
import {animationFrameScheduler, BehaviorSubject, throttleTime} from 'rxjs';
import {toSignal} from '@angular/core/rxjs-interop';

/**
 * Monolith for controlling multiple video players and the time slider component.
 *
 * Seeking: Current time changes flow to subcomponents.
 * Regular playback: One video player controls the current time, syncs to the rest which are paused.
 */
@Injectable()
export class VideoPlayerState {

  currentTime = new BehaviorSubject<number>(0);
  isPlaying = new BehaviorSubject<boolean>(false);

  currentTimeSignal: Signal<number>;
  currentFrameSignal: Signal<number>;
  isPlayingSignal: Signal<boolean>;

  duration = signal<number>(0);

  private videoPlayers: VideoTileComponent[] = [];
  private injector = inject(Injector)

  constructor() {
    this.isPlayingSignal = toSignal(this.isPlaying, {requireSync: true});
    this.currentTimeSignal = toSignal(this.currentTime, {requireSync: true});
    // TODO replace 300 with framerate.
    this.currentFrameSignal = computed(() => Math.floor(this.currentTimeSignal() * 300));
    effect(() => {
      const isPlaying = this.isPlayingSignal();
      untracked(() => {
        if (isPlaying) {
          // Play logic:
          // Sync the start timestamp for all video players before playing
          this.videoPlayers.forEach((videoPlayer) => {
            const el = videoPlayer.videoElement?.nativeElement;
            if (el) {
              el.currentTime = this.currentTime.getValue();
            }
          });
          // Call play on all video elements.
          // Hope they stay in sync.
          this.videoPlayers.forEach((videoPlayer) => {
            videoPlayer.videoElement?.nativeElement.play();
            // Test if this makes UI updates more resopnsive:
          });
        } else {
          // Pause logic:
          // Pause, then sync their currentTimestamp just
          // in case there was any drift.
          this.videoPlayers.forEach((videoPlayer) => {
            videoPlayer.videoElement?.nativeElement.pause();
          });
          this.videoPlayers.forEach((videoPlayer) => {
            const el = videoPlayer.videoElement?.nativeElement;
            if (el) {
              el.currentTime = el.currentTime = this.currentTime.value;
            }
          });
        }
      });

    });

    effect(() => {
      // Seek logic:
      // When currentTime is changing, and we're not playing:
      // sync currentTime across all paused elements.
      // hack: dependency on current time change:
      this.currentTimeSignal()
      if (!this.isPlayingSignal()) {
        this.videoPlayers.forEach((videoPlayer) => {
          const el = videoPlayer.videoElement?.nativeElement;
          if (!el) return;
          afterNextRender({
              write: () => {
                el.currentTime = this.currentTimeSignal();
              }
            }, {
            injector: this.injector
          });
        });
      }
    });
  }

  reset() {
    this.isPlaying.next(false);
    this.currentTime.next(0);
    this.duration.set(0);
  }

  registerVideoPlayer(videoPlayer: VideoTileComponent) {
    this.videoPlayers.push(videoPlayer);
    if (this.videoPlayers.length == 1) {
      videoPlayer.isPrimary.set(true);
    }
  }

  unregisterVideoPlayer(videoPlayer: VideoTileComponent) {
    const i = this.videoPlayers.indexOf(videoPlayer);
    this.videoPlayers.splice(i, 1);
  }
}
