import {
  ChangeDetectionStrategy, ChangeDetectorRef,
  Component,
  computed,
  inject, Injector,
  Input,
  OnInit,
  signal
} from '@angular/core';
import {
    VideoPlayerControlsComponent
} from "../../components/video-player/video-player-controls/video-player-controls.component";
import {VideoTileComponent} from "../../components/video-player/video-tile/video-tile.component";
import {ViewSettings} from '../../view-settings.model';
import {VideoPlayerState} from '../../components/video-player/video-player-state';
import {KeypointContainerComponent} from '../../components/keypoint-container/keypoint-container.component';
import {KeypointModel} from '../../keypoint-model';
import {VideoWidgetModel} from '../../video-widget-model';
import {HttpClient} from '@angular/common/http';
import ndarray, { NdArray } from 'ndarray'; // Import ndarray and its type

import Papa, { ParseResult } from 'papaparse';

import {ProjectMetadataService} from '../../project-metadata.service';
import {firstValueFrom} from 'rxjs';

@Component({
  selector: 'app-viewer-center-panel',
  imports: [
    VideoPlayerControlsComponent,
    VideoTileComponent,
    KeypointContainerComponent
  ],
  templateUrl: './viewer-center-panel.component.html',
  styleUrl: './viewer-center-panel.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ViewerCenterPanelComponent implements OnInit {
  sessionKey = signal<string | null>(null);
  private cdr = inject(ChangeDetectorRef);

  get currentTime() {
    return this.videoPlayerState.currentTimeSignal();
  }

  get currentFrame() {
    return this.videoPlayerState.currentFrameSignal();
  }

  @Input() viewSettings: ViewSettings = {} as ViewSettings;
  ngOnInit() {
    this.buildWidgetModels();
  }

  videoPlayerState = inject(VideoPlayerState);

  widgetModels = <VideoWidgetModel[]>[];
  buildWidgetModels(): void {
    const builder = [];
    const sessionKey = this.sessionKey();
    if (!sessionKey) return;
    for (const [i, view] of this.viewSettings.viewsShown().entries()) {
      builder.push(<VideoWidgetModel>{
        id: view,
        videoSrc: this.getVideoSrc(sessionKey, view),
        keypointModels: [],
      });
    }
    for (const [i, view] of this.viewSettings.viewsShown().entries()) {
      const predictions = this.predictions.get(0, i) as NdArray<Float64Array>;
      if (predictions) {
        let j = 0;
        for (const keypointName of this.viewSettings.keypointsShown()) {
          builder[i].keypointModels.push(((j): KeypointModel => ({
            name: keypointName,
            position: computed(() => ({
               /* tslint:disable-next-line */
              x: predictions.get(
                this.currentFrame,
                j, //keypoint index
                0), //x
               /* tslint:disable-next-line */
              y: predictions.get(
                this.currentFrame,
                j, //keypoint index
                1)
            })), //x
            colorClass: signal('bg-sky-100'),
          }))(j));
          j++;
        }
      }
    }
    this.widgetModels = builder;
  }
  videos = signal<any[]>([]);
  private httpClient = inject(HttpClient);
  private projectMetadataService = inject(ProjectMetadataService);
  private predictions = ndarray(<any>[], [1 /*numModels*/, 6 /*numViews*/]);

  getVideoSrc(sessionKey: string, view: string): string {
    return '/videos/' + sessionKey.replace(/Cam-N/g, 'Cam-'+view) + '.mp4';
    // return '/app/v0/files/<data_dir>/' + sessionKey.replace(/Cam-N/g, 'Cam-'+view) + '.mp4';
  }

  /**
   * Parses a CSV string from pose estimation into a 3D array (ndarray-like structure)
   * using the PapaParse library.
   * The output shape is (number of frames, number of bodyparts, 2 for x/y coordinates).
   *
   * @param csvString The CSV data as a string.
   * @returns A 3D array of numbers: number[][][].
   * Returns an empty array if the CSV is malformed, has no data, or PapaParse fails.
   */
  parsePredictionFile(csvString: string): NdArray<Float64Array> {
  const parseOutput: ParseResult<string[]> = Papa.parse(csvString.trim(), {
    dynamicTyping: false,
    skipEmptyLines: true,
  });

  if (parseOutput.errors.length > 0) {
    console.error("PapaParse errors:", parseOutput.errors);
    return ndarray(new Float64Array(0), [0, 0, 2]); // Return empty ndarray
  }

  const allRows = parseOutput.data;

  if (allRows.length < 4) {
    console.error("CSV must have at least 3 header lines and 1 data line.");
    return ndarray(new Float64Array(0), [0, 0, 2]);
  }

  const bodypartsHeader = allRows[1];
  if (!bodypartsHeader || bodypartsHeader.length <= 1 || (bodypartsHeader.length - 1) % 3 !== 0) {
    console.error("Malformed bodyparts header line (line 2 of CSV).", bodypartsHeader);
    return ndarray(new Float64Array(0), [0, 0, 2]);
  }
  const numBodyParts = (bodypartsHeader.length - 1) / 3;

  const coordsHeader = allRows[2];
  if (!coordsHeader || coordsHeader.length !== bodypartsHeader.length) {
    console.error("Coordinate header (line 3 of CSV) length mismatch with bodyparts header.");
    return ndarray(new Float64Array(0), [0, numBodyParts > 0 ? numBodyParts : 0, 2]);
  }

  const dataRowsOnly = allRows.slice(3);
  const numFrames = dataRowsOnly.length;

  if (numFrames === 0 || numBodyParts === 0) {
    // If no actual data frames or no body parts identified, return an appropriately shaped empty ndarray
    return ndarray(new Float64Array(0), [numFrames, numBodyParts, 2]);
  }

  // Create a flat Float64Array to store all x, y coordinates
  // Total elements = numFrames * numBodyParts * 2 (for x and y)
  const flatData = new Float64Array(numFrames * numBodyParts * 2);
  let flatIndex = 0;

  for (let rowIndex = 0; rowIndex < numFrames; rowIndex++) {
    const values = dataRowsOnly[rowIndex];

    if (values.length < 1 + numBodyParts * 3) {
      console.warn(`Skipping malformed data row ${rowIndex + 4} (not enough columns): "${values.slice(0,5).join(',')}..."`);
      // Fill corresponding part of flatData with NaNs for this frame
      for (let i = 0; i < numBodyParts; i++) {
        flatData[flatIndex++] = NaN; // x
        flatData[flatIndex++] = NaN; // y
      }
      continue;
    }

    for (let bodyPartIdx = 0; bodyPartIdx < numBodyParts; bodyPartIdx++) {
      const xDataIndex = 1 + (bodyPartIdx * 3);
      const yDataIndex = 1 + (bodyPartIdx * 3) + 1;

      if (xDataIndex >= values.length || yDataIndex >= values.length) {
        console.warn(`Skipping body part ${bodyPartIdx} in data row ${rowIndex + 4} due to insufficient data.`);
        flatData[flatIndex++] = NaN; // x
        flatData[flatIndex++] = NaN; // y
        continue;
      }

      const xString = values[xDataIndex];
      const yString = values[yDataIndex];

      const x = parseFloat(xString);
      const y = parseFloat(yString);

      if (isNaN(x) || isNaN(y)) {
        console.warn(`Could not parse x or y as number for body part ${bodyPartIdx} in data row ${rowIndex + 4}. Values: x='${xString}', y='${yString}'.`);
        flatData[flatIndex++] = NaN;
        flatData[flatIndex++] = NaN;
      } else {
        flatData[flatIndex++] = x;
        flatData[flatIndex++] = y;
      }
    }
  }

  // Create the ndarray with the flat data and the desired shape
  return ndarray(flatData, [numFrames, numBodyParts, 2]);
}

  async getPredictionFile(sessionKey: string, view: string): Promise<string> {
    const src = '/video_preds/' + sessionKey.replace(/Cam-N/g, 'Cam-'+view).replace('.fine','') + '.csv';
    // const src = '/app/v0/files/video_preds/' + sessionKey.replace(/Cam-N/g, 'Cam-'+view) + '/predictions.csv';
    return await firstValueFrom(this.httpClient.get(src, {responseType: 'text'}));
  }

  async loadSession(sessionKey: string) {
    // not currently used for anything?
    this.sessionKey.set(sessionKey);
    this.widgetModels = [];

    const allRequests = <Promise<any>[]>[];
    this.projectMetadataService.getAllViews().forEach((view, i) => {
      const r = this.getPredictionFile(sessionKey, view).then((x) => {
        const parsed = this.parsePredictionFile(x);
        this.predictions.set(0, i, <any>parsed);
      });
      allRequests.push(r);
    });

    Promise.allSettled(allRequests).then(() => {
      this.buildWidgetModels();
      this.cdr.markForCheck();
    });

    // reset video player
    this.videoPlayerState.reset();
  }
}
