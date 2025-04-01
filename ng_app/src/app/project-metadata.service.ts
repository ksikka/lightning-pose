import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ProjectMetadataService {

  constructor() { }

  getAllViews() {
    return ['A', 'B', 'C', 'D', 'E', 'F'];
  }

  getAllKeypoints() {
    return [
      "L1A", "L1B", "L1C", "L1D", "L1E",
      "L2A", "L2B", "L2C", "L2D", "L2E",
      "L3A", "L3B", "L3C", "L3D", "L3E",
      "R1A", "R1B", "R1C", "R1D", "R1E",
      "R2A", "R2B", "R2C", "R2D", "R2E",
      "R3A", "R3B", "R3C", "R3D", "R3E"
    ];
  }
}
